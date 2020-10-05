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

import subprocess
import time

class ICEMgmt():
    def __init__(self, classnetwork):
        self.classnetwork = classnetwork
        self.changesinaction = False
        self.packagename = ""

    def install(self, packagename, browser):
        self.packagename = packagename
        if browser == "Vivaldi":
            browser2 = "vivaldi"
        elif browser == "Google Chrome":
            browser2 = "google-chrome"
        elif browser == "Chromium":
            browser2 = "chromium-browser"
        elif browser == "Mozilla Firefox":
            browser2 = "firefox"
        elif browser == "M.Firefox (Flathub)":
            browser2 = "firefox-flatpak"
        elif browser == "Brave":
            browser2 = "brave"
        else:
            browser2 = "none"
        while self.changesinaction == True:
            pass
        self.changesinaction = True
        shortenedname = packagename.split("feren-ice-ssb-")[1]
        subprocess.Popen(["/usr/lib/feren-store-new/packagemanager/icemgmt.py", "install", self.classnetwork.JSONReader.icedata[shortenedname]["website"], self.classnetwork.JSONReader.icedata[shortenedname]["realname"], self.classnetwork.JSONReader.icedata[shortenedname]["category"], self.classnetwork.GlobalVariables.storagetemplocation+"/"+packagename+"-icon", browser2, self.classnetwork.JSONReader.icedata[shortenedname]["keywords"], packagename]).wait()

        self.on_transaction_finished()

    def remove(self, packagename):
        self.packagename = packagename
        while self.changesinaction == True:
            pass
        self.changesinaction = True
        subprocess.Popen(["/usr/lib/feren-store-new/packagemanager/icemgmt.py", "remove", "None", "None", "None", "None", "None", "None", packagename]).wait()

        self.on_transaction_finished()

    def on_transaction_finished(self):
        time.sleep(0.2)
        self.changesinaction = False
        self.classnetwork.AppDetailsHeader.switch_source(self.classnetwork.AppDetailsHeader.current_package, self.classnetwork.AppDetailsHeader.current_package_type, False)
