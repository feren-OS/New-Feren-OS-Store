import gi
from gi.repository import GLib, Gtk, GObject, Gdk

import gettext
APP = 'mintinstall'
LOCALE_DIR = "/usr/share/linuxmint/locale"
gettext.bindtextdomain(APP, LOCALE_DIR)
gettext.textdomain(APP)
_ = gettext.gettext

from aptdaemon.gtk3widgets import AptConfirmDialog

######################### Subclass Apt's dialog to keep consistency

class ChangesConfirmDialog(AptConfirmDialog):

    """Dialog to confirm the changes that would be required by a
    transaction.
    """

    def __init__(self, transaction, task):
        super(ChangesConfirmDialog, self).__init__(transaction, cache=None, parent=task.parent_window)

        self.task = task

    def _show_changes(self):
        """Show a message and the dependencies in the dialog."""
        self.treestore.clear()

        if not self.task.parent_window:
            self.set_skip_taskbar_hint(True)
            self.set_keep_above(True)

        # Run parent method for apt
        if self.task.pkginfo.pkg_hash.startswith("a"):
            super(ChangesConfirmDialog, self)._show_changes()
        else:
            # flatpak
            self.set_title(_("Flatpaks"))

            if len(self.task.to_install) > 0:
                piter = self.treestore.append(None, ["<b>%s</b>" % _("Install")])

                for ref in self.task.to_install:
                    if self.task.pkginfo.refid == ref.format_ref():
                        continue

                    self.treestore.append(piter, [ref.get_name()])

            if len(self.task.to_remove) > 0:
                piter = self.treestore.append(None, ["<b>%s</b>" % _("Remove")])

                for ref in self.task.to_remove:
                    if self.task.pkginfo.refid == ref.format_ref():
                        continue

                    self.treestore.append(piter, [ref.get_name()])

            if len(self.task.to_update) > 0:
                piter = self.treestore.append(None, ["<b>%s</b>" % _("Upgrade")])

                for ref in self.task.to_update:
                    if self.task.pkginfo.refid == ref.format_ref():
                        continue

                    self.treestore.append(piter, [ref.get_name()])

            msg = _("Please take a look at the list of changes below.")

            if len(self.treestore) == 1:
                filtered_store = self.treestore.filter_new(
                    Gtk.TreePath.new_first())
                self.treeview.expand_all()
                self.treeview.set_model(filtered_store)
                self.treeview.set_show_expanders(False)

                if len(self.task.to_install) > 0:
                    title = _("Additional software has to be installed")
                elif len(self.task.to_remove) > 0:
                    title = _("Additional software has to be removed")
                elif len(self.task.to_update) > 0:
                    title = _("Additional software has to be upgraded")

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

            if self.task.download_size > 0:
                msg += "\n"
                msg += (_("%s will be downloaded in total.") %
                        GLib.format_size(self.task.download_size))
            if self.task.freed_size > 0:
                msg += "\n"
                msg += (_("%s of disk space will be freed.") %
                        GLib.format_size(self.task.freed_size))
            elif self.task.install_size > 0:
                msg += "\n"
                msg += (_("%s more disk space will be used.") %
                        GLib.format_size(self.task.install_size))
            self.label.set_markup("<b><big>%s</big></b>\n\n%s" % (title, msg))

    def render_package_desc(self, column, cell, model, iter, data):
        value = model.get_value(iter, 0)

        cell.set_property("markup", value)
