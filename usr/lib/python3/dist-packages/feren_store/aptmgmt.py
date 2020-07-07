# This file is part of the Feren Store program.
#
# Copyright 2009-2014 Linux Mint and Clement Lefebvre
# Copyright 2020 Feren OS Team
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 3, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.

import os
import apt
import aptdaemon.client
from aptdaemon.gtk3widgets import AptErrorDialog, AptProgressDialog, AptConfirmDialog
import aptdaemon.errors
import gettext
import subprocess
import gi
from gi.repository import Gtk

#if os.path.isfile("/usr/bin/snapd"):
#    from feren_store import snapmgmt
#if os.path.isfile("/usr/bin/flatpak"):
#    from feren_store import flatpakmgmt

t = gettext.translation('feren-store', '/usr/share/locale', fallback=True)
_ = t.gettext

#TODO: Put Snap permissions management in the Store settings

class ChangesConfirmDialog(AptConfirmDialog):

    """Dialog to confirm the changes that would be required by a
    transaction.
    """

    def __init__(self, transaction, parentwindow):
        self.parentwindow = parentwindow
        super(ChangesConfirmDialog, self).__init__(transaction, cache=None, parent=parentwindow)

    def _show_changes(self):
        """Show a message and the dependencies in the dialog."""
        self.treestore.clear()

        if not self.parentwindow:
            self.set_skip_taskbar_hint(True)
            self.set_keep_above(True)
            
        #TEMPORARY
        piter = self.treestore.append(None, ["<b>%s</b>" % _("Enable Application Source")])

        self.treestore.append(piter, ["Google Chrome Repository"])
        
        print(self.apt_transaction.dependencies)

        #if len(self.task.to_install) > 0:
            #piter = self.treestore.append(None, ["<b>%s</b>" % _("Install")])

            #for ref in self.task.to_install:
                #if self.task.pkginfo.refid == ref.format_ref():
                    #continue

                #self.treestore.append(piter, [ref.get_name()])

        #if len(self.task.to_remove) > 0:
            #piter = self.treestore.append(None, ["<b>%s</b>" % _("Remove")])

            #for ref in self.task.to_remove:
                #if self.task.pkginfo.refid == ref.format_ref():
                    #continue

                #self.treestore.append(piter, [ref.get_name()])

        #if len(self.task.to_update) > 0:
            #piter = self.treestore.append(None, ["<b>%s</b>" % _("Upgrade")])

            #for ref in self.task.to_update:
                #if self.task.pkginfo.refid == ref.format_ref():
                    #continue

                #self.treestore.append(piter, [ref.get_name()])

        msg = _("Please take a look at the list of changes below.")

        if len(self.treestore) == 1:
            filtered_store = self.treestore.filter_new(
                Gtk.TreePath.new_first())
            self.treeview.expand_all()
            self.treeview.set_model(filtered_store)
            self.treeview.set_show_expanders(False)

            #if len(self.task.to_install) > 0:
                #title = _("Additional software has to be installed")
            #elif len(self.task.to_remove) > 0:
                #title = _("Additional software has to be removed")
            #elif len(self.task.to_update) > 0:
                #title = _("Additional software has to be upgraded")
            #elif len(self.task.to_appsource) > 0:
            title = _("An Application Source will be enabled")

            if len(filtered_store) < 6:
                self.set_resizable(False)
                self.scrolled.set_policy(Gtk.PolicyType.AUTOMATIC,
                                            Gtk.PolicyType.NEVER)
            else:
                self.treeview.set_size_request(350, 200)
        else:
            title = _("Additional changes are required")
            self.treeview.set_size_request(350, 200)
            self.treeview.collapse_all()
            
        msg = "test size message"

        #if self.task.download_size > 0:
            #msg += "\n"
            #msg += (_("%s will be downloaded in total.") %
                    #GLib.format_size(self.task.download_size))
        #if self.task.freed_size > 0:
            #msg += "\n"
            #msg += (_("%s of disk space will be freed.") %
                    #GLib.format_size(self.task.freed_size))
        #elif self.task.install_size > 0:
            #msg += "\n"
            #msg += (_("%s more disk space will be used.") %
                    #GLib.format_size(self.task.install_size))
        self.label.set_markup("<b><big>%s</big></b>\n\n%s" % (title, msg))

    def render_package_desc(self, column, cell, model, iter, data):
        value = model.get_value(iter, 0)

        cell.set_property("markup", value)


class APTChecks():
    def checkinstalled(package):
        output = subprocess.run(["/usr/lib/feren-store-new/check-updatable", package],
                            stdout=subprocess.PIPE).stdout.decode("utf-8")
        return output


class APTMgmt():
    def __init__(self, storegui):
        self.apt_client = aptdaemon.client.AptClient()
        self.apt_transaction = None
        self.packagename = ""
        self.storegui = storegui
        
    def check_real_changes(self, package, operationtype):
        packagestoinstall = []
        packagestoupgrade = []
        packagestoremove = []
        apt_cache = apt.Cache()
        pkginfo = apt_cache[package]
        if operationtype == "install":
            apt_cache[package].mark_install(True)
        elif operationtype == "upgrade":
            apt_cache[package].mark_upgrade(True)
        elif operationtype == "remove":
            apt_cache[package].mark_delete(True)
        for item in apt_cache:
            if apt_cache[item.name].marked_install:
                packagestoinstall.append(item.name)
            elif apt_cache[item.name].marked_upgrade:
                packagestoupgrade.append(item.name)
            elif apt_cache[item.name].marked_delete:
                packagestoremove.append(item.name)
        return(packagestoinstall, packagestoupgrade, packagestoremove)
        
        
    def install_package(self, packagename):
        self.packagename = packagename
        #TODO: Turn this into its own confirmation dialog and exclude both unlisted Store items (unless advanced mode's on) and the package being managed itself
        packagesinstalled, packagesupgraded, packagesremoved = self.check_real_changes(packagename, "install")
        print("""These packages will be installed:
"""+str(packagesinstalled)+"""

These packages will be upgraded:
"""+str(packagesupgraded)+"""

These packages will be removed:
"""+str(packagesremoved))
        self.apt_client.install_packages([packagename],
                                        reply_handler=self.confirm_changes,
                                        error_handler=self.on_error) # dbus.DBusException
        
    def remove_package(self, packagename):
        self.packagename = packagename
        packagesinstalled, packagesupgraded, packagesremoved = self.check_real_changes(packagename, "remove")
        print("""These packages will be installed:
"""+str(packagesinstalled)+"""

These packages will be upgraded:
"""+str(packagesupgraded)+"""

These packages will be removed:
"""+str(packagesremoved))
        self.apt_client.remove_packages([packagename],
                                        reply_handler=self.confirm_changes,
                                        error_handler=self.on_error) # dbus.DBusException

    def confirm_changes(self, apt_transaction):
        self.apt_transaction = apt_transaction
        try:
            #if [pkgs for pkgs in self.apt_transaction.dependencies if pkgs]:
                #dia = ChangesConfirmDialog(self.apt_transaction, self.task)
                #res = dia.run()
                #dia.hide()
                #if res != Gtk.ResponseType.OK:
                    #GObject.idle_add(self.task.finished_cleanup_cb, self.task)
                    #return
            self.run_transaction()
        except Exception as e:
            print(e)

    def on_error(self, error):
        print("ERROR", error)
        self.storegui.on_installer_finished(self.packagename)
        if self.apt_transaction.error_code == "error-not-authorized":
            # Silently ignore auth failures

            #self.task.error_message = None # Should already be none, but this is a reminder
            return
        elif not isinstance(error, aptdaemon.errors.TransactionFailed):
            # Catch internal errors of the client
            error = aptdaemon.errors.TransactionFailed(aptdaemon.enums.ERROR_UNKNOWN,
                                                       str(error))

        #if self.task.progress_state != self.task.PROGRESS_STATE_FAILED:
            #self.task.progress_state = self.task.PROGRESS_STATE_FAILED

            #self.task.error_message = self.apt_transaction.error_details

            #dia = AptErrorDialog(error)
            #dia.run()
            #dia.hide()
            #GObject.idle_add(self.task.error_cleanup_cb, self.task)

    def run_transaction(self):
        self.apt_transaction.connect("finished", self.on_transaction_finished)

        self.apt_transaction.connect("progress-changed", self.on_transaction_progress)
        self.apt_transaction.connect("error", self.on_transaction_error)
        self.apt_transaction.run(reply_handler=lambda: None, error_handler=self.on_error)
    
    def on_transaction_progress(self, apt_transaction, progress):
        if not apt_transaction.error:
            self.storegui.app_mgmt_progress.set_fraction(progress / 100)

    def on_transaction_error(self, apt_transaction, error_code, error_details):
        pass
        #if self.task.progress_state != self.task.PROGRESS_STATE_FAILED:
            #self.on_error(apt_transaction.error)

    def on_transaction_finished(self, apt_transaction, exit_state):
        # finished signal is always called whether successful or not
        # Only call here if we succeeded, to prevent multiple calls
        if (exit_state == aptdaemon.enums.EXIT_SUCCESS) or apt_transaction.error_code == "error-not-authorized":
            self.storegui.on_installer_finished(self.packagename)
