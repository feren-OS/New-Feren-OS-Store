#!/usr/bin/python3

#######################################################################################
# Flatpak Management Python Script - use me for percentage obtaining in-GUI           #
#                                                                                     #
# PS: Do yourself a favour and use this: https://lazka.github.io/pgi-docs/Flatpak-1.0 #
#######################################################################################

import sys
import gi
import getpass
import math
import os

gi.require_version('Gtk', '3.0')
gi.require_version('Flatpak', '1.0')
from gi.repository import Flatpak, Gtk


#determine if Superuser or not to determine install target
if getpass.getuser() == "root":
    superuser = True
else:
    superuser = False

arch = Flatpak.get_default_arch()
if arch == "i386":
    availablearches = ["i386"]
elif arch == "x86_64":
    availablearches = ["x86_64", "i386"]
else:
    availablearches = []

item_count = 0
current_count = 0

def progress_flatpak_cb(status, progress, estimating, data=None):
    package_chunk_size = 1.0 / item_count
    partial_chunk = (progress / 100.0) * package_chunk_size

    print(math.floor(((current_count * package_chunk_size) + partial_chunk) * 100.0))


def on_flatpak_error(error_details):
    print("ERROR", [error_details])


def on_flatpak_finished(self):
    print("DONE")


def flatpak_install(snapname):
    pass


def flatpak_upgrade(snapname):
    pass


def flatpak_remove(snapname):
    pass

    
if superuser == True:
    flatpakclassthing = Flatpak.Installation.new_system()
    flatpakclassthingalt = flatpakclassthing
else:
    flatpakclassthing = Flatpak.Installation.new_user()
    flatpakclassthingalt = Flatpak.Installation.new_system()
transaction = Flatpak.Transaction.new_for_installation(flatpakclassthing)

def sortref(ref):
    try:
        val = float(ref.get_branch())
    except ValueError:
        val = 9.9

    return val

if len(sys.argv) == 3:
    pass
if len(sys.argv) == 2:
    if sys.argv[1] == "getthemes":
        gtksettings = Gtk.Settings.get_default()

        if superuser == True:
            themesdirs = next(os.walk('/usr/share/themes/'))[1]
        else:
            themesdirs = next(os.walk(os.path.expanduser("~")+"/.themes"))[1]
            if os.path.isdir(os.path.expanduser("~")+"/.local/share/themes"):
                themesdirs.extend(next(os.walk(os.path.expanduser("~")+"/.local/share/themes"))[1])
        
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

                    try:
                        all_refs = flatpakclassthing.list_remote_refs_sync(remote_name.get_name(), None)
                        if flatpakclassthing != flatpakclassthingalt:
                            for i in flatpakclassthingalt.list_remote_refs_sync(remote_name.get_name(), None):
                                if i not in all_refs:
                                    all_refs.append(i)
                    except:
                        try:
                            all_refs = flatpakclassthingalt.list_remote_refs_sync(remote_name.get_name(), None)
                        except:
                            all_refs = []
                    
                    try:
                        matching_refs = []

                        for listed_ref in all_refs:
                            #FIXME: Flatpak doesn't list them by their closest architecture to the one it detects to your system's
                            if not listed_ref.get_arch() in availablearches:
                                continue
                            
                            if listed_ref.get_name() == "org.gtk.Gtk3theme."+name:
                                matching_refs.append(listed_ref)

                        if not matching_refs:
                            continue

                        # Sort highest version first.
                        matching_refs = sorted(matching_refs, key=sortref, reverse=True)

                        for matching_ref in matching_refs:
                            theme_ref = matching_ref
                    except:
                        pass

                    if theme_ref:
                        theme_refs.append(theme_ref.format_ref())

        print(theme_refs)
    else:
        print("Incorrect number of arguments.")
        exit(1)
else:
    print("Incorrect number of arguments.")
    exit(1)

if sys.argv[1] == "install":
    flatpak_install(sys.argv[2])
elif sys.argv[1] == "upgrade":
    flatpak_upgrade(sys.argv[2])
elif sys.argv[1] == "remove":
    flatpak_remove(sys.argv[2])
