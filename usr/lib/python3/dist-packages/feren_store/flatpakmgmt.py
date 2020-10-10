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
import subprocess
import apt
import gettext
import gi
from threading import Thread

gi.require_version('Flatpak', '1.0')
from gi.repository import GLib, Flatpak

from feren_store.dialogs import ChangesConfirmDialog, ErrorDialog


class FlatpakChecks():
    def checkinstalled(ref, userland):
        if userland == False:
            flatpakclassthing = Flatpak.Installation.new_system()
        else:
            flatpakclassthing = Flatpak.Installation.new_user()
        flatpakremotes = flatpakclassthing.list_remotes()
        all_refs = []
        for remote_name in flatpakremotes:
            try:
                for i in flatpakclassthing.list_remote_refs_sync(remote_name.get_name(), None):
                    if i not in all_refs:
                        all_refs.append(i)
            except:
                pass
        ref2 = ""
        arch = Flatpak.get_default_arch()
        for i in all_refs:
                if i.get_name() == ref and i.get_arch() == arch:
                    ref2 = i
        
        try:
            iref = flatpakclassthing.get_installed_ref(ref2.get_kind(),
                                            ref2.get_name(),
                                            ref2.get_arch(),
                                            ref2.get_branch(),
                                            None)

            if iref:
                if ref2 in flatpakclassthing.list_installed_refs_for_update(None):
                    return(3)
                else:
                    return(1)
        except GLib.Error:
            pass
        except AttributeError: # bad/null ref
            pass
        return(2)

    def checkneedsrepo(package, repositoryname, userland):
        if userland == False:
            flatpakclassthing = Flatpak.Installation.new_system()
        else:
            flatpakclassthing = Flatpak.Installation.new_user()
        flatpakremotes = flatpakclassthing.list_remotes()
        
        for i in flatpakremotes:
            if i.get_name() == repositoryname:
                return []
        return [i.get_name()]


class FlatpakMgmt():
    def __init__(self, classnetwork):
        self.packagenamemgmt = ""
        self.classnetwork = classnetwork
        self.changesinaction = False
        self.userland = False
        #Prevent userland from being changed while tasks are running
        self.userlandlock = False
        
    def check_real_changes(self, package, operationtype, userland):
        import ast
        packagestoinstall = []
        packagestoupgrade = []
        packagestoremove = []
        package2 = self.classnetwork.JSONReader.getNameFromInternal(package, "flatpak")
        remote_name = self.classnetwork.JSONReader.availablesources[package]["flatpak"].split("flatpak-")[1]
        changesdictlist = ast.literal_eval(subprocess.check_output(['/usr/lib/feren-store-new/packagemanager/packagemgmt.py', 'flatpak', 'simul'+operationtype, str(not userland), remote_name, package2]).decode("utf-8"))

        for ref in changesdictlist[0][remote_name]:
            packagestoinstall.append(self.classnetwork.JSONReader.getInternalFromName(ref, "flatpak"))
        for ref in changesdictlist[1][remote_name]:
            packagestoupgrade.append(self.classnetwork.JSONReader.getInternalFromName(ref, "flatpak"))
        for ref in changesdictlist[2][remote_name]:
            packagestoremove.append(self.classnetwork.JSONReader.getInternalFromName(ref, "flatpak"))
        
        packagestoinstall = [i for i in packagestoinstall if i]
        packagestoupgrade = [i for i in packagestoupgrade if i]
        packagestoremove = [i for i in packagestoremove if i]
        return(packagestoinstall, packagestoupgrade, packagestoremove)

    def install_package(self, packagename, userland):
        thread = Thread(target=self._install_package,
                        args=(packagename, userland))
        thread.daemon = True
        thread.start()
        
    def _install_package(self, packagename, userland):
        packagesinstalled, packagesupgraded, packagesremoved = self.check_real_changes(packagename, "install", userland)
        #Who at GTK's team thought needing to go through this mess was adequate for Python code?
        GLib.idle_add(self.__install_package, packagesinstalled, packagesupgraded, packagesremoved, packagename, userland)
        
    def __install_package(self, packagesinstalled, packagesupgraded, packagesremoved, packagename, userland):
        self.userland = userland
        ChangesConfirmDialog(packagename, "install", self.classnetwork, packagesinstalled, packagesupgraded, packagesremoved, self, "flatpak")
        
    def confirm_install_package(self, packagename):
        if self.userland == True:
            self.classnetwork.TasksMgmt.add_task("flatpak:localinst:"+packagename)
        else:
            self.classnetwork.TasksMgmt.add_task("flatpak:inst:"+packagename)
        self.classnetwork.TasksMgmt.start_now()

    def upgrade_package(self, packagename, userland):
        thread = Thread(target=self._upgrade_package,
                        args=(packagename, userland))
        thread.daemon = True
        thread.start()
        
    def _upgrade_package(self, packagename, userland):
        packagesinstalled, packagesupgraded, packagesremoved = self.check_real_changes(packagename, "upgrade", userland)
        #Who at GTK's team thought needing to go through this mess was adequate for Python code?
        GLib.idle_add(self.__upgrade_package, packagesinstalled, packagesupgraded, packagesremoved, packagename, userland)
        
    def __upgrade_package(self, packagesinstalled, packagesupgraded, packagesremoved, packagename, userland):
        self.userland = userland
        ChangesConfirmDialog(packagename, "upgrade", self.classnetwork, packagesinstalled, packagesupgraded, packagesremoved, self, "flatpak")
        
    def confirm_upgrade_package(self, packagename):
        if self.userland == True:
            self.classnetwork.TasksMgmt.add_task("flatpak:localupgr:"+packagename)
        else:
            self.classnetwork.TasksMgmt.add_task("flatpak:upgr:"+packagename)
        self.classnetwork.TasksMgmt.start_now()

    def remove_package(self, packagename, userland):
        thread = Thread(target=self._remove_package,
                        args=(packagename, userland))
        thread.daemon = True
        thread.start()
        
    def _remove_package(self, packagename, userland):
        packagesinstalled, packagesupgraded, packagesremoved = self.check_real_changes(packagename, "remove", userland)
        #Who at GTK's team thought needing to go through this mess was adequate for Python code?
        GLib.idle_add(self.__remove_package, packagesinstalled, packagesupgraded, packagesremoved, packagename, userland)
        
    def __remove_package(self, packagesinstalled, packagesupgraded, packagesremoved, packagename, userland):
        
        ChangesConfirmDialog(packagename, "remove", self.classnetwork, packagesinstalled, packagesupgraded, packagesremoved, self, "flatpak")
        
    def confirm_remove_package(self, packagename):
        if self.userland == True:
            self.classnetwork.TasksMgmt.add_task("flatpak:localrm:"+packagename)
        else:
            self.classnetwork.TasksMgmt.add_task("flatpak:rm:"+packagename)
        self.classnetwork.TasksMgmt.start_now()

    def on_error(self, error, package):
        self.classnetwork.AppDetailsHeader.on_installer_finished(package)
        self.changesinaction = False
        ErrorDialog(error, self.classnetwork, package, "flatpak")
    
    def on_transaction_progress(self, progress):
        try:
            self.classnetwork.AppDetailsHeader.app_mgmt_progress.set_fraction(int(progress)/100)
        except:
            pass

    def on_transaction_finished(self, package):
        self.changesinaction = False
        self.classnetwork.AppDetailsHeader.on_installer_finished(package)

    def run_transaction(self, package, remote, optype):
        self.changesinaction = True

        if self.userland == True:
            command = ["/usr/lib/feren-store-new/packagemanager/packagemgmt.py", "flatpak", optype, remote, package]
        else:
            command = ["/usr/bin/pkexec", "/usr/lib/feren-store-new/packagemanager/packagemgmt.py", "flatpak", optype, remote, package]

        from feren_store import executecmd
        executecmd.run_transaction(command, self.on_transaction_finished, self.on_error, self.on_transaction_progress, package)
