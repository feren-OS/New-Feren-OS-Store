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
        self.packagenamemgmt = ""
        self.classnetwork = classnetwork
        self.changesinaction = False
        
    def check_real_changes(self, package, operationtype):
        packagestoinstall = []
        packagestoupgrade = []
        packagestoremove = []
        apt_cache = apt.Cache()
        if package.endswith(".deb"):
            if self.classnetwork.AppView._deb.check():
                package2 = self.classnetwork.AppView._deb.pkgname
                (draftinstall, draftremove, draftunauthenticated) = self.classnetwork.AppView._deb.required_changes
                for item in draftinstall:
                    packagestoinstall.append(self.classnetwork.JSONReader.getInternalFromName(item, "apt"))
                for item in draftremove:
                    packagestoremove.append(self.classnetwork.JSONReader.getInternalFromName(item, "apt"))
        else:
            package2 = self.classnetwork.JSONReader.getNameFromInternal(package, "apt")
            if package2 == None:
                package2 = package #Fall back to package name if it isn't a known package
            if package2 == "debfile":
                package2 = self.classnetwork.AppView._deb.pkgname
            if operationtype == "install":
                apt_cache[package2].mark_install(True)
            elif operationtype == "upgrade":
                apt_cache[package2].mark_upgrade(True)
            elif operationtype == "remove":
                apt_cache[package2].mark_delete(True)
            for item in apt_cache:
                if apt_cache[item.name].marked_install:
                    packagestoinstall.append(self.classnetwork.JSONReader.getInternalFromName(item.name, "apt"))
                elif apt_cache[item.name].marked_upgrade:
                    packagestoupgrade.append(self.classnetwork.JSONReader.getInternalFromName(item.name, "apt"))
                elif apt_cache[item.name].marked_delete:
                    packagestoremove.append(self.classnetwork.JSONReader.getInternalFromName(item.name, "apt"))
        
        return(packagestoinstall, packagestoupgrade, packagestoremove)

    def install_package(self, packagename):
        thread = Thread(target=self._install_package,
                        args=(packagename,))
        thread.daemon = True
        thread.start()
        
    def _install_package(self, packagename):
        packagesinstalled, packagesupgraded, packagesremoved = self.check_real_changes(packagename, "install")
        #Who at GTK's team thought needing to go through this mess was adequate for Python code?
        GLib.idle_add(self.__install_package, packagesinstalled, packagesupgraded, packagesremoved, packagename)
        
    def __install_package(self, packagesinstalled, packagesupgraded, packagesremoved, packagename):
        #TODO: Add advanced mode setting which makes the dialog show ALL of the installs/upgrades/removals/etc.
        ChangesConfirmDialog(packagename, "install", self.classnetwork, packagesinstalled, packagesupgraded, packagesremoved, self, "apt")
        
    def confirm_install_package(self, packagename):
        if packagename.endswith(".deb"):
            self.classnetwork.TasksMgmt.add_task("aptdeb:inst:"+packagename)
        else:
            self.classnetwork.TasksMgmt.add_task("apt:inst:"+packagename)
        self.classnetwork.TasksMgmt.start_now()

    def upgrade_package(self, packagename):
        thread = Thread(target=self._upgrade_package,
                        args=(packagename,))
        thread.daemon = True
        thread.start()
        
    def _upgrade_package(self, packagename):
        packagesinstalled, packagesupgraded, packagesremoved = self.check_real_changes(packagename, "upgrade")
        #Who at GTK's team thought needing to go through this mess was adequate for Python code?
        GLib.idle_add(self.__upgrade_package, packagesinstalled, packagesupgraded, packagesremoved, packagename)
        
    def __upgrade_package(self, packagesinstalled, packagesupgraded, packagesremoved, packagename):
        ChangesConfirmDialog(packagename, "upgrade", self.classnetwork, packagesinstalled, packagesupgraded, packagesremoved, self, "apt")
        
    def confirm_upgrade_package(self, packagename):
        if packagename == "debfile":
            self.classnetwork.TasksMgmt.add_task("apt:upgr:"+self.classnetwork.AppView._deb.pkgname)
        else:
            self.classnetwork.TasksMgmt.add_task("apt:upgr:"+packagename)
        self.classnetwork.TasksMgmt.start_now()

    def remove_package(self, packagename):
        thread = Thread(target=self._remove_package,
                        args=(packagename,))
        thread.daemon = True
        thread.start()
        
    def _remove_package(self, packagename):
        packagesinstalled, packagesupgraded, packagesremoved = self.check_real_changes(packagename, "remove")
        #Who at GTK's team thought needing to go through this mess was adequate for Python code?
        GLib.idle_add(self.__remove_package, packagesinstalled, packagesupgraded, packagesremoved, packagename)
        
    def __remove_package(self, packagesinstalled, packagesupgraded, packagesremoved, packagename):
        ChangesConfirmDialog(packagename, "remove", self.classnetwork, packagesinstalled, packagesupgraded, packagesremoved, self, "apt")
        
    def confirm_remove_package(self, packagename):
        if packagename == "debfile":
            self.classnetwork.TasksMgmt.add_task("apt:rm:"+self.classnetwork.AppView._deb.pkgname)
        else:
            self.classnetwork.TasksMgmt.add_task("apt:rm:"+packagename)
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
        self.packagenamemgmt = package

        command = ["/usr/bin/pkexec", "/usr/lib/feren-store-new/packagemanager/packagemgmt.py", "apt", optype, package]
        
        from feren_store import executecmd
        executecmd.run_transaction(command, self.on_transaction_finished, self.on_error, self.on_transaction_progress, package)
