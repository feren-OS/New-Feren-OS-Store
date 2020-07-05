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

import json
import os
import getpass

class GlobalVariables(object):
    def __init__(self):
        self.storagetemplocation = "/tmp/feren-store-"+getpass.getuser()
        #Make the folder if it doesn't exist
        if not os.path.isdir("/tmp/feren-store-"+getpass.getuser()):
            os.mkdir("/tmp/feren-store-"+getpass.getuser())


class ApplicationSourceTranslator():
    #Class for all things translating an application source internal name into human readable, keyrings and repositories to add
    
    def TranslateToHumanReadable(self, appsourceintname):
        if appsourceintname == "standard":
            return "Standard Install"
        elif appsourceintname == "google-chrome":
            return "Google Chrome Repository"
        elif appsourceintname == "snapstore":
            return "Snapcraft"
        elif appsourceintname == "flatpak-flathub":
            return "Flathub"
        else:
            return appsourceintname
        #TODO: Add more
        

class JSONReader(object):
    '''
    Map some short codes with packages. Install/Remove buttons
    will be represented by short code like #code-remove and
    #code-install. This will allow one to check installation status
    of each package using a loop instead of checking separately
    '''

    def __init__(self):
        with open("/usr/share/feren-store-new/curated/apt/packages.json") as file:
            self.aptdata = json.load(file)
        #with open("/usr/share/feren-store-new/curated/snap/packages.json") as file:
        #    self.snapdata = json.load(file)
        #with open("/usr/share/feren-store-new/curated/flatpak/packages.json") as file:
        #    self.flatpakdata = json.load(file)
        #with open("/usr/share/feren-store-new/curated/ice/packages.json") as file:
        #    self.icedata = json.load(file)
        with open("/usr/share/feren-store-new/curated/sources/packages.json") as file:
            self.availablesources = json.load(file)

    def getPackageInfo(self, packagename):
        #TODO: Change this to have an extra argument for which package type this should be for
        try:
            return self.aptdata[packagename]["realname"], self.aptdata[packagename]["shortdescription"], self.aptdata[packagename]["iconurl"]
        except KeyError:
            return None, None, None
        
    def getPackageSiteInfo(self, packagename):
        #TODO: Change this to have an extra argument for which package type this should be for
        try:
            return self.aptdata[packagename]["description"], self.aptdata[packagename]["author"], self.aptdata[packagename]["bugreporturl"], self.aptdata[packagename]["website"], self.aptdata[packagename]["tos"], self.aptdata[packagename]["category"], self.aptdata[packagename]["image1"], self.aptdata[packagename]["image2"], self.aptdata[packagename]["image3"]
        except KeyError:
            return None, None, None
