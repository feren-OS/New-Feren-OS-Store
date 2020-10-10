#!/usr/bin/python3
import os

if not os.path.isfile("/usr/bin/flatpak"):
    exit()


import time
fileName = os.path.expanduser("~")+'/.config/gtk-3.0/settings.ini'
originalTime = os.path.getmtime(fileName)

packagestolock = ["org.mozilla.firefox"]

for package in packagestolock:
    if os.path.isfile("/var/lib/flatpak/overrides/"+package):
        os.system("/bin/bash -c 'if [ "+'"$(grep '+"'gtk-application-prefer-dark-theme=' ~/.config/gtk-3.0/settings.ini)"+'" == "gtk-application-prefer-dark-theme=true" ]; then flatpak override --user --env=GTK_THEME="Adwaita:dark" '+package+'; else flatpak override --user --env=GTK_THEME="Adwaita:light" '+package+'; fi'+"'")

while(True):
    if(os.path.getmtime(fileName) > originalTime):
        for package in packagestolock:
            if os.path.isfile("/var/lib/flatpak/overrides/"+package):
                os.system("/bin/bash -c 'if [ "+'"$(grep '+"'gtk-application-prefer-dark-theme=' ~/.config/gtk-3.0/settings.ini)"+'" == "gtk-application-prefer-dark-theme=true" ]; then flatpak override --user --env=GTK_THEME="Adwaita:dark" '+package+'; else flatpak override --user --env=GTK_THEME="Adwaita:light" '+package+'; fi'+"'")
        originalTime = os.path.getmtime(fileName)
    time.sleep(0.1)
