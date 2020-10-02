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
import pty
from threading import Thread

from gi.repository import GLib

from feren_store.dialogs import ChangesConfirmDialog, ErrorDialog


class APTChecks():
    def checkinstalled(package):
        #Hopefully apt_cache1 means apt_cache doesn't interfere in any way shape or form, though...
        apt_cache1 = apt.Cache()
        try:
            pkginfo = apt_cache1[package]
        except:
            return(404)
        apt_cache1.upgrade(True) # dist-upgrade

        if (apt_cache1[pkginfo.name].is_installed and apt_cache1[pkginfo.name].marked_upgrade and apt_cache1[pkginfo.name].candidate.version != apt_cache1[pkginfo.name].installed.version):
            return(3)
        elif apt_cache1[pkginfo.name].is_installed:
            return(1)
        else:
            return(2)

    def checkneedsrepo(package):
        s = subprocess.run(["/usr/lib/feren-store-new/bash-tools/get-apt-dependencies", package], stdout=subprocess.PIPE).stdout.decode('utf-8')
        dependencies = s.split()
        stuffneeded = []
        if "snapd" in dependencies and not os.path.isfile("/usr/bin/snap"):
            stuffneeded.append("snap")
        if "flatpak" in dependencies and not os.path.isfile("/usr/bin/flatpak"):
            stuffneeded.append("flatpak")
        #TODO: Add checking for known App Sources

        return stuffneeded


class APTMgmt():
    def __init__(self, classnetwork):
        self.packagename = ""
        self.classnetwork = classnetwork
        self.changesinaction = False
        
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
        thread = Thread(target=self._install_package,
                        args=())
        thread.daemon = True
        thread.start()
        
    def _install_package(self):
        packagesinstalled, packagesupgraded, packagesremoved = self.check_real_changes(self.packagename, "install")
        #Who at GTK's team thought needing to go through this mess was adequate for Python code?
        GLib.idle_add(self.__install_package, packagesinstalled, packagesupgraded, packagesremoved)
        
    def __install_package(self, packagesinstalled, packagesupgraded, packagesremoved):
        #TODO: Add advanced mode setting which makes the dialog show ALL of the installs/upgrades/removals/etc.
        ChangesConfirmDialog(self.packagename, "install", self.classnetwork, packagesinstalled, packagesupgraded, packagesremoved, self, "apt")
        
    def confirm_install_package(self, packagename):
        self.classnetwork.TasksMgmt.add_task("apt:inst:"+packagename)
        if self.classnetwork.AppDetailsHeader.current_package == packagename:
            if self.classnetwork.TasksMgmt.currenttask != "":
                self.classnetwork.AppDetailsHeader.change_button_state("queued", False)
            else:
                self.classnetwork.AppDetailsHeader.change_button_state("busy", False)
        self.classnetwork.TasksMgmt.start_now()

    def upgrade_package(self, packagename):
        self.packagename = packagename
        thread = Thread(target=self._upgrade_package,
                        args=())
        thread.daemon = True
        thread.start()
        
    def _upgrade_package(self):
        packagesinstalled, packagesupgraded, packagesremoved = self.check_real_changes(self.packagename, "upgrade")
        #Who at GTK's team thought needing to go through this mess was adequate for Python code?
        GLib.idle_add(self.__upgrade_package, packagesinstalled, packagesupgraded, packagesremoved)
        
    def __upgrade_package(self, packagesinstalled, packagesupgraded, packagesremoved):
        ChangesConfirmDialog(self.packagename, "upgrade", self.classnetwork, packagesinstalled, packagesupgraded, packagesremoved, self, "apt")
        
    def confirm_upgrade_package(self, packagename):
        self.classnetwork.TasksMgmt.add_task("apt:upgr:"+packagename)
        if self.classnetwork.AppDetailsHeader.current_package == packagename:
            if self.classnetwork.TasksMgmt.currenttask != "":
                self.classnetwork.AppDetailsHeader.change_button_state("queued", False)
            else:
                self.classnetwork.AppDetailsHeader.change_button_state("busy", False)
        self.classnetwork.TasksMgmt.start_now()

    def remove_package(self, packagename):
        self.packagename = packagename
        thread = Thread(target=self._remove_package,
                        args=())
        thread.daemon = True
        thread.start()
        
    def _remove_package(self):
        packagesinstalled, packagesupgraded, packagesremoved = self.check_real_changes(self.packagename, "remove")
        #Who at GTK's team thought needing to go through this mess was adequate for Python code?
        GLib.idle_add(self.__remove_package, packagesinstalled, packagesupgraded, packagesremoved)
        
    def __remove_package(self, packagesinstalled, packagesupgraded, packagesremoved):
        
        ChangesConfirmDialog(self.packagename, "remove", self.classnetwork, packagesinstalled, packagesupgraded, packagesremoved, self, "apt")
        
    def confirm_remove_package(self, packagename):
        self.classnetwork.TasksMgmt.add_task("apt:rm:"+packagename)
        if self.classnetwork.AppDetailsHeader.current_package == packagename:
            if self.classnetwork.TasksMgmt.currenttask != "":
                self.classnetwork.AppDetailsHeader.change_button_state("queued", False)
            else:
                self.classnetwork.AppDetailsHeader.change_button_state("busy", False)
        self.classnetwork.TasksMgmt.start_now()

    def on_error(self, error, package):
        self.classnetwork.AppDetailsHeader.on_installer_finished(package)
        self.changesinaction = False
        ErrorDialog(error, self.classnetwork, package, "apt")
    
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

        master, slave = pty.openpty()
        command = ["/usr/bin/pkexec", "/usr/lib/feren-store-new/packagemanager/packagemgmt.py", "apt", optype, package]
        proc = subprocess.Popen(command, bufsize=0, shell=False, stdout=slave, stderr=slave, close_fds=True)     
        stdout = os.fdopen(master, 'r')

        while proc.poll() is None:
            output = stdout.readline()
            if output != "":
                if output.rstrip('\n') == "STOREDONE":
                    self.on_transaction_finished(package)
                    break
                elif output.startswith("STORERRROR ["):
                    self.on_error(output.rstrip('\n'), package)
                    break
                elif output.rstrip('\n') != "STOREDONE" and not output.startswith("STOREERROR [") and output.rstrip('\n') != "":
                    self.on_transaction_progress(output.rstrip('\n'))
            else:
                break

        #Eh, just in case.
        os.close(slave)
        os.close(master)

        #Only way I found thus far to prevent it from becoming a Minecraft mob
        proc.communicate()

        #Only way I found thus far to prevent Store from staying in the background and eating the CPU
        exit()
            