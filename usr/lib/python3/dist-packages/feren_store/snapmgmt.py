# This file is part of the Feren Store program.
#
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
import pty
from threading import Thread
        
gi.require_version('Snapd', '1')
from gi.repository import GLib, Snapd

from feren_store.dialogs import ChangesConfirmDialog, ErrorDialog #IDK, Snap might gain profoundly-shown Application Dependencies in the future.


class SnapChecks():
    def checkinstalled(package):
        try:
            snapinfo = Snapd.Client().get_snap_sync(package)
        except Exception as e:
            return(2)
        else:
            return(1)


class SnapMgmt():
    def __init__(self, classnetwork):
        self.classnetwork = classnetwork
        self.changesinaction = False
        
    def check_real_changes(self, package, operationtype):
        pass #currently not needed

    def install_package(self, packagename):
        thread = Thread(target=self._install_package,
                        args=(packagename,))
        thread.daemon = True
        thread.start()
        
    def _install_package(self, packagename):
        #Who at GTK's team thought needing to go through this mess was adequate for Python code?
        GLib.idle_add(self.__install_package, [], [], [], packagename)
        
    def __install_package(self, packagesinstalled, packagesupgraded, packagesremoved, packagename):
        ChangesConfirmDialog(packagename, "install", self.classnetwork, packagesinstalled, packagesupgraded, packagesremoved, self, "snap")
        
    def confirm_install_package(self, packagename):
        self.classnetwork.TasksMgmt.add_task("snap:inst:"+packagename)
        self.classnetwork.TasksMgmt.start_now()

    #Snaps have automatic updates, so... don't think we really need to bother with having a GUI for managing updates when they're forced on automatic. If anyone wants to add one in, using the GUI for other package types' updates, feel free.

    def remove_package(self, packagename):
        thread = Thread(target=self._remove_package,
                        args=(packagename,))
        thread.daemon = True
        thread.start()
        
    def _remove_package(self, packagename):
        #Who at GTK's team thought needing to go through this mess was adequate for Python code?
        GLib.idle_add(self.__remove_package, [], [], [], packagename)
        
    def __remove_package(self, packagesinstalled, packagesupgraded, packagesremoved, packagename):
        
        ChangesConfirmDialog(packagename, "remove", self.classnetwork, packagesinstalled, packagesupgraded, packagesremoved, self, "snap")
        
    def confirm_remove_package(self, packagename):
        self.classnetwork.TasksMgmt.add_task("snap:rm:"+packagename)
        self.classnetwork.TasksMgmt.start_now()

    def on_error(self, error, package):
        self.classnetwork.AppDetailsHeader.on_installer_finished(package)
        self.changesinaction = False
        ErrorDialog(error, self.classnetwork, package, "snap")
    
    def on_transaction_progress(self, progress):
        try:
            self.classnetwork.AppDetailsHeader.app_mgmt_progress.set_fraction(int(progress)/100)
        except:
            pass

    def on_transaction_finished(self, package):
        self.changesinaction = False
        self.classnetwork.AppDetailsHeader.on_installer_finished(package)

    def run_transaction(self, package, optype):
        self.changesinaction = True

        command = ["/usr/bin/pkexec", "/usr/lib/feren-store-new/packagemanager/packagemgmt.py", "snap", optype, package]
        
        from feren_store import executecmd
        executecmd.run_transaction(command, self.on_transaction_finished, self.on_error, self.on_transaction_progress, package)
