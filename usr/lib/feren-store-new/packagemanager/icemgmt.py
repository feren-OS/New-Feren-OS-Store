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
_HOME = os.getenv("HOME")
_ICE_DIR = "{0}/.local/share/feren-store-ice".format(_HOME)
_ICON_DIR = "{0}/icons".format(_ICE_DIR)
_APPS_DIR = "{0}/.local/share/applications".format(_HOME)
_PROFILES_DIR = "{0}/profiles".format(_ICE_DIR)
_FF_PROFILES_DIR = "{0}/firefox".format(_ICE_DIR)

# Requisite dirs
for directory in [_ICE_DIR, _APPS_DIR, _PROFILES_DIR,
                  _FF_PROFILES_DIR, _ICON_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)



class Ice():

    def __init__(self):
        self.known_profiles = []
    

    def normalize(self, url):
        (self.scheme, self.netloc,
         self.path, _, _, _) = urllib.parse.urlparse(url, "http")

        if not self.netloc and self.path:
            return urllib.parse.urlunparse((self.scheme,
                                            self.path, "", "", "", ""))

        return urllib.parse.urlunparse((self.scheme, self.netloc,
                                        self.path, "", "", ""))


    def applicate(self):
        self.address = self.normalize(sys.argv[2])
        self.title = sys.argv[3]
        self.loc = sys.argv[4]
        self.iconpath = sys.argv[5]

        if sys.argv[6] != "google-chrome" and sys.argv[6] != "chromium-browser" and sys.argv[6] != "brave" and sys.argv[6] != "vivaldi" and sys.argv[6] != "firefox":
            print("ERROR unsupportedbrowser")
            exit(1)

        self.formatted = sys.argv[8]
        
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

        if os.path.exists("{0}/{1}.desktop".format(_APPS_DIR, self.formatted)):
            os.remove("{0}/{1}.desktop".format(_APPS_DIR, self.formatted))
        if len(self.title) == 0:
            exit(1)
        else:
            self.writefile(self.title, self.formatted, self.address,
                           self.location)

    def writefile(self, title, formatted, address, location):
        shutil.copyfile(self.iconpath,
                        "{0}/{1}".format(_ICON_DIR, formatted))
        self.appfile = os.path.expanduser("{0}/{1}.desktop".format(_APPS_DIR,
                                                                   formatted))

        self.browser = sys.argv[6] #"google-chrome", "chromium-browser", "brave", "vivaldi", "firefox", "epiphany"

        with open(self.appfile, 'w') as self.appfile1:
            self.appfile1.truncate()

            self.appfile1.write("[Desktop Entry]\n")
            self.appfile1.write("Version=1.0\n")
            self.appfile1.write("Name={0}\n".format(title))
            self.appfile1.write("Comment={0}\n".format(title))

            self.profile_path = "{0}/{1}".format(_PROFILES_DIR,
                                                    formatted)

            if self.browser == "firefox":
                self.firefox_profile_path = "{0}/{1}".format(_FF_PROFILES_DIR,
                                                             formatted)
                self.appfile1.write("Exec=" + self.browser +
                                    " --class FEREN-STORE-ICE-SSB-" + formatted +
                                    " --profile " + self.firefox_profile_path +
                                    " --no-remote " + address + "\n")

                self.appfile1.write("IceFirefox={0}\n".format(formatted))
                os.system("/usr/lib/feren-store-new/ice/browsers/ice-firefox "+formatted)
            else:
                self.profile_path = "{0}/{1}".format(_PROFILES_DIR,
                                                        formatted)
                self.appfile1.write("Exec=" + self.browser +
                                    " --app=" + address +
                                    " --class=FEREN-STORE-ICE-SSB-" + formatted +
                                    " --user-data-dir=" +
                                    self.profile_path + "\n")

                self.appfile1.write("X-FEREN-STORE-ICE-SSB-Profile=" +
                                    formatted + "\n")

            self.appfile1.write("Terminal=false\n")
            self.appfile1.write("X-MultipleArgs=false\n")
            self.appfile1.write("Type=Application\n")

            self.appfile1.write(
                "Icon={0}/{1}\n".format(
                _ICON_DIR,
                formatted
            ))

            self.appfile1.write("Categories=GTK;{0}\n".format(location))
            self.appfile1.write("MimeType=text/html;text/xml;"
                                "application/xhtml_xml;\n")

            self.appfile1.write("Keywords="+sys.argv[7]+"\n")

            self.appfile1.write(
                "StartupWMClass=FEREN-STORE-ICE-SSB-{0}\n".format(formatted)
            )
            self.appfile1.write("StartupNotify=true\n")
            os.system("chmod +x " + self.appfile)

    def delete(self):
        self.address = self.normalize(sys.argv[2])
        self.title = sys.argv[3]

        self.formatted = sys.argv[8]

        self.appfile = "{0}/{1}.desktop".format(_APPS_DIR, self.formatted)

        self.appfileopen = open(self.appfile, 'r')
        self.appfilelines = self.appfileopen.readlines()
        self.appfileopen.close()

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
