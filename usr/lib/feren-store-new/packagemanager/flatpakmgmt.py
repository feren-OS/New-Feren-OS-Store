#!/usr/bin/python3

#######################################################################################
# Flatpak Management Python Script - use me for percentage obtaining in-GUI           #
#                                                                                     #
# PS: Do yourself a favour and use this: https://lazka.github.io/pgi-docs/Flatpak-1.0 #
#                                                                                     #
# Credits to Linux Mint (mintcommon) for most of this code                            #
# https://github.com/linuxmint/mintcommon                                             #
#######################################################################################


#TODO: Make the code be able to interpret a JSON file of known Flatpak repositories to be able to add repositories manually if needed
#   Finally move getthemes and the ability to see what changes will be made into flatpakmgmt in the Store itself



import sys
import gi
import getpass
import math
import os
import re

gi.require_version('Gtk', '3.0')

gtksettings = Gtk.Settings.get_default()

if superuser == True:
    themesdirs = next(os.walk('/usr/share/themes/'))[1]
else:
    themesdirs = next(os.walk(os.path.expanduser("~")+"/.themes"))[1]
    if os.path.isdir(os.path.expanduser("~")+"/.local/share/themes"):
        themesdirs.extend(next(os.walk(os.path.expanduser("~")+"/.local/share/themes"))[1])
    themesdirs.extend(next(os.walk('/usr/share/themes/'))[1])

if not gtksettings.props.gtk_theme_name in themesdirs:
    themesdirs.append(gtksettings.props.gtk_theme_name)

theme_refs = []

flatpakremotes = flatpakclassthing.list_remotes()
if flatpakclassthing != flatpakclassthingalt:
    for flatpakremote in flatpakclassthingalt.list_remotes():
        if flatpakremote not in flatpakremotes:
            flatpakremotes.append(flatpakremote)

for remote_name in flatpakremotes:
    for name in (themesdirs):
        if os.path.isdir("/usr/share/themes/"+name+"/gtk-3.0") or os.path.isdir(os.path.expanduser("~")+"/.themes/"+name+"/gtk-3.0") or os.path.isdir(os.path.expanduser("~")+"/.local/share/themes/"+name+"/gtk-3.0"):
            theme_ref = None
            
            matching_refs = []

            #TODO: Put this in main flatpakmgmt.py and make it be all known theme Flatpaks in a predefined JSON that it checks for their values in, and if they're there it adds them to the list
            if listed_ref.get_name() == "org.gtk.Gtk3theme."+name:
                matching_refs.append(listed_ref)

print(theme_refs)
