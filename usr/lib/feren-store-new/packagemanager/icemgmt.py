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

        if sys.argv[6] != "google-chrome" and sys.argv[6] != "chromium-browser" and sys.argv[6] != "brave" and sys.argv[6] != "vivaldi" and sys.argv[6] != "firefox" and sys.argv[6] != "firefox-flatpak":
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
            elif self.browser == "firefox-flatpak":
                self.firefox_profile_path = "{0}/{1}".format(_FF_PROFILES_DIR,
                                                             formatted)
                self.appfile1.write("Exec=/usr/bin/flatpak run org.mozilla.firefox --class FEREN-STORE-ICE-SSB-" +
                                    formatted +
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

                os.mkdir("{0}/{1}".format(_PROFILES_DIR, formatted))
                os.mkdir("{0}/{1}/Default".format(_PROFILES_DIR, formatted))
                with open("{0}/{1}/Default/Preferences".format(_PROFILES_DIR, formatted), 'w') as self.profileprefs: # '//' needs to be '////' for the '//' to be written correctly to the file, 'cos logic I guess '//'...
                    self.profileprefs.write('{"browser":{"custom_chrome_frame":true},"extensions":{"settings":{"pdcjjgefkpoemmlcjfcfkeminneboaob":{"location":1,"manifest":{"key":"MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCEetbb+aZag1Su2EOp1gOdRwJd2mBJo5HqX6cdZzXOZ3Ag1eoXzMFVikqDH8dgOEyWUTwGXh5ruDHy9Nztg8oPIFfx6xPi5mrDjuENAK9GtBHEvHOdmwx8jU+dUNB/5Vx+Fs6ngIQLy9cFRQegVP8P9zwc6rO8w/KL1R8RQaLJDwIDAQAB","name":"Modern Flat","permissions":[],"update_url":"http://clients2.google.com/service/update2/crx","version":"0.0","manifest_version":2,"theme":{"colors":{"bookmark_text":[33,38,41],"button_background":[0,0,0,0],"frame":[33,38,41],"ntp_background":[255,255,255],"ntp_text":[104,104,104],"tab_background_text":[228,228,228],"tab_text":[33,38,41],"toolbar":[223,223,223]},"images":{"theme_frame":"images/theme_frame.png","theme_tab_background":"images/theme_tab_background.png","theme_toolbar":"images/theme_toolbar.png"},"properties":{"ntp_background_alignment":"bottom","ntp_background_repeat":"no-repeat"},"tints":{"buttons":[0,0,0.5]}}},"path":"pdcjjgefkpoemmlcjfcfkeminneboaob\\\\0.0","state":1},"cjpalhdlnbpafiamejdnhcphjbkeiagm":{"location":1,"manifest":{"key":"MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAmJNzUNVjS6Q1qe0NRqpmfX/oSJdgauSZNdfeb5RV1Hji21vX0TivpP5gq0fadwmvmVCtUpOaNUopgejiUFm/iKHPs0o3x7hyKk/eX0t2QT3OZGdXkPiYpTEC0f0p86SQaLoA2eHaOG4uCGi7sxLJmAXc6IsxGKVklh7cCoLUgWEMnj8ZNG2Y8UKG3gBdrpES5hk7QyFDMraO79NmSlWRNgoJHX6XRoY66oYThFQad8KL8q3pf3Oe8uBLKywohU0ZrDPViWHIszXoE9HEvPTFAbHZ1umINni4W/YVs+fhqHtzRJcaKJtsTaYy+cholu5mAYeTZqtHf6bcwJ8t9i2afwIDAQAB","name":"uBlock Origin (Installing...)","permissions":["contextMenus","privacy","storage","tabs","unlimitedStorage","webNavigation","webRequest","webRequestBlocking","<all_urls>"],"update_url":"http://clients2.google.com/service/update2/crx","version":"0.0","manifest_version":2},"path":"cjpalhdlnbpafiamejdnhcphjbkeiagm\\\\0.0","state":1,"was_installed_by_default":true},"gmopgnhbhiniibbiilmbjilcmgaocokj":{"location":1,"manifest":{"key":"MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAgxAzXBWt/o0z5yjDmUHDR8joIf6bAAxvfioMbfAdaL2VKVLTXgaLpnugSDbma1CvRU2VB/53EstafAcIg7kNVlT3WULNSuFsJHg4mEQUteOkNwnjXsBQICm04WswC1LfQQgUw3E3pJHiNnHp74ISy6Sncv0MfSWNIi9rFehDN2nXfbdDXNJNheZCMMF/HhLreyeaq2oCy4BIMqQp825kpfRRkCNG+mlvjpseCM6Nde3dPtByt2SplNKB4/O5LnOyfYTsjoDOU/0ak/CtwGqxkrYyeaI3pJrLXQAe35r8GLeO0EJQ7bElpBQuXVosrcNqp6HFqSxiHpWHYUrqoZxjcwIDAQAB","name":"NekoCap (Installing...)","permissions":["storage","webNavigation"],"update_url":"http://clients2.google.com/service/update2/crx","version":"0.0","manifest_version":2},"path":"cjpalhdlnbpafiamejdnhcphjbkeiagm\\\\0.0","state":1,"was_installed_by_default":true}},"theme":{"id":"pdcjjgefkpoemmlcjfcfkeminneboaob"}}}')


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
