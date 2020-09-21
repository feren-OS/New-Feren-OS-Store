#!/usr/bin/python3

#######################################################################################
# ICE Management Python Script - use me for all the ICEy stuff, and RIP Mark G.       #
#                                                                                     #
# Largely based on ICE from the Peppermint OS Linux Project                           #
# https://github.com/peppermintos/ice                                                 #
#######################################################################################

import bs4
import gettext
import locale
import os
import os.path
import requests
import shutil
import string
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib
from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf

_BRAVE_BIN = "/usr/bin/brave-browser"
_CHROME_BIN = "/usr/bin/google-chrome"
_CHROMIUM_BIN = "/usr/bin/chromium-browser"
_VIVALDI_BIN = "/usr/bin/vivaldi-stable"
_FIREFOX_BIN = "/usr/bin/firefox"
_EPIPHANY_BIN = "/usr/bin/epiphany-browser"
_HOME = os.getenv("HOME")
_ICE_DIR = "{0}/.local/share/feren-store-ice".format(_HOME)
_ICON_DIR = "{0}/icons".format(_ICE_DIR)
_APPS_DIR = "{0}/.local/share/applications".format(_HOME)
_PROFILES_DIR = "{0}/profiles".format(_ICE_DIR)
_FF_PROFILES_DIR = "{0}/firefox".format(_ICE_DIR)
_EPIPHANY_PROFILES_DIR = "{0}/epiphany".format(_ICE_DIR)

# Requisite dirs
for directory in [_ICE_DIR, _APPS_DIR, _PROFILES_DIR,
                  _FF_PROFILES_DIR, _ICON_DIR, _EPIPHANY_PROFILES_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)



class Ice():

    def __init__(self):
        self.known_profiles = []

        self.address = self.normalize(sys.argv[2])
        self.title = sys.argv[3]
        self.loc = sys.argv[4]
        self.iconpath = sys.argv[5]
    

    def normalize(self, url):
        (self.scheme, self.netloc,
         self.path, _, _, _) = urllib.parse.urlparse(url, "http")

        if not self.netloc and self.path:
            return urllib.parse.urlunparse((self.scheme,
                                            self.path, "", "", "", ""))

        return urllib.parse.urlunparse((self.scheme, self.netloc,
                                        self.path, "", "", ""))


    def applicate(self):
        self.semiformatted = ""
        self.array = filter(str.isalpha, self.title)
        for obj in self.array:
            self.semiformatted = self.semiformatted + obj
        self.formatted = self.semiformatted.lower()
        
        if self.loc == "Accessories":
            self.location = "Utility;"
        elif self.loc == "Games":
            self.location = "Game;"
        elif self.loc == "Graphics":
            self.location = "Graphics;"
        elif self.loc == "Internet":
            self.location = "Network;"
        elif self.loc == "Office":
            self.location = "Office;"
        elif self.loc == "Programming":
            self.location = "Development;"
        elif self.loc == "Multimedia":
            self.location = "AudioVideo;"
        elif self.loc == "System":
            self.location = "System;"

        self.iconname = self.iconpath.replace("/", " ").split()[-1]
        self.iconext = self.iconname.replace(".", " ").split()[-1]

        if os.path.exists("{0}/{1}.desktop".format(_APPS_DIR, self.formatted)):
            os.remove("{0}/{1}.desktop".format(_APPS_DIR, self.formatted))
        if len(self.title) == 0:
            exit(1)
        else:
            self.writefile(self.title, self.formatted, self.address,
                           self.iconext, self.location)

    def writefile(self, title, formatted, address, iconext, location):
        shutil.copyfile(self.iconpath,
                        "{0}/{1}.{2}".format(_ICON_DIR, formatted, iconext))
        self.appfile = os.path.expanduser("{0}/feren-store-ssb-{1}.desktop".format(_APPS_DIR,
                                                                   formatted))

        with open(self.appfile, 'w') as self.appfile1:
            self.appfile1.truncate()

            self.appfile1.write("[Desktop Entry]\n")
            self.appfile1.write("Version=1.0\n")
            self.appfile1.write("Name={0}\n".format(title))
            self.appfile1.write("Comment={0}\n".format(title))

            self.profile_path = "{0}/{1}".format(_PROFILES_DIR,
                                                    formatted)
            #TODO: Change this to be one shortcut that launches the user's preferred browser accordingly
            self.appfile1.write("Exec=/usr/lib/feren-store-new/ice/ice-launcher " + formatted + " " + address + " vivaldi\n")

            self.appfile1.write("X-FEREN-STORE-ICE-SSB-Profile=" + formatted + "\n")

            self.appfile1.write("Terminal=false\n")
            self.appfile1.write("X-MultipleArgs=false\n")
            self.appfile1.write("Type=Application\n")

            self.epiphany_profile_path = "{0}/{1}".format(
                _EPIPHANY_PROFILES_DIR, "epiphany-" + formatted
            )
            self.appfile1.write(
                "Icon={0}/app-icon.{2}\n".format(
                self.epiphany_profile_path,
                formatted,
                iconext
            ))
            #else:
            #    self.appfile1.write(
            #        "Icon={0}/{1}.{2}\n".format(
            #        _ICON_DIR,
            #        formatted,
            #        iconext
            #    ))

            self.appfile1.write("Categories=GTK;{0}\n".format(location))
            self.appfile1.write("MimeType=text/html;text/xml;"
                                "application/xhtml_xml;\n")

            self.appfile1.write(
                "StartupWMClass=FEREN-STORE-ICE-SSB-{0}\n".format(formatted)
            )
            self.appfile1.write("StartupNotify=true\n")
            os.system("chmod +x " + self.appfile)

            self.init_epiphany_profile(self.epiphany_profile_path, formatted, iconext, self.appfile)

    def init_epiphany_profile(self, path, formatted, iconext, appfile):
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path)
        shutil.copyfile("{0}/{1}.{2}".format(_ICON_DIR, formatted, iconext),
                        "{0}/app-icon.{1}".format(path, iconext))
        os.replace(appfile, "{0}/epiphany-{1}.desktop".format(path, formatted))
        os.symlink("{0}/epiphany-{1}.desktop".format(path, formatted), appfile)
        os.system("chmod +x {0}/epiphany-{1}.desktop".format(path, formatted))

    def delete(self):
        self.semiformatted = ""
        self.array = filter(str.isalpha, self.title)
        for obj in self.array:
            self.semiformatted = self.semiformatted + obj
        self.formatted = self.semiformatted.lower()

        self.appfile = "{0}/feren-store-ssb-{1}.desktop".format(_APPS_DIR, self.formatted)

        self.appfileopen = open(self.appfile, 'r')
        self.appfilelines = self.appfileopen.readlines()
        self.appfileopen.close()

        for line in self.appfilelines:
            try:
                shutil.rmtree("{0}/{1}".format(_PROFILES_DIR, self.formatted))
            except:
                pass
            try:
                shutil.rmtree("{0}/{1}".format(_FF_PROFILES_DIR, self.formatted))
            except:
                pass
            try:
                shutil.rmtree("{0}/epiphany-{1}".format(_EPIPHANY_PROFILES_DIR, self.formatted))
            except:
                pass

        os.remove(self.appfile)








icebackend = Ice()

if sys.argv[1] == "install":
    icebackend.applicate()
elif sys.argv[1] == "remove":
    icebackend.delete()
