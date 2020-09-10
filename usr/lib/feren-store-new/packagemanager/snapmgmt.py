#!/usr/bin/python3

###################################################################################
# Snap Management Python Script - use me for percentage obtaining in-GUI          #
# Cheers Wimpy for making such a useful example script                            #
# https://gist.github.com/flexiondotorg/84c3f137d70f4e21ea46419833c0aff4          #
#                                                                                 #
# PS: Do yourself a favour and use this: https://lazka.github.io/pgi-docs/Snapd-1 #
###################################################################################

import sys
import gi

gi.require_version('Snapd', '1')
from gi.repository import Snapd

def progress_snap_cb(client, change, _, user_data):
    # Interate over tasks to determine the aggregate tasks for completion.
    total = 0
    done = 0
    for task in change.get_tasks():
        total += task.get_progress_total()
        done += task.get_progress_done()
    percent = round((done/total)*100)
    print(percent)
    

def snap_install(snapname):
    return client.install2_sync(Snapd.InstallFlags.NONE, snapname, None, None, progress_snap_cb, (None,), None)
    #install2_sync(flags, name, channel, revision, progress_callback, progress_callback_data, cancellable)


def snap_remove(snapname):
    return client.remove2_sync(Snapd.InstallFlags.NONE, snapname, progress_snap_cb, (None,), None)
    #remove2_sync(flags, name, progress_callback, progress_callback_data, cancellable)


def is_installed(snapname):
    try:
        snapinfo = client.get_snap_sync(snapname)
    except Exception as e:
        return False
    else:
        return True
    



client = Snapd.Client()

if len(sys.argv) != 3:
    print("Incorrect number of arguments.")
    exit(1)

if sys.argv[1] == "install":
    if snap_install(sys.argv[2]):
        print("DONE")
    else:
        print("ERROR")
elif sys.argv[1] == "remove":
    if snap_remove(sys.argv[2]):
        print("DONE")
    else:
        print("ERROR")
elif sys.argv[1] == "isinstalled":
    print(is_installed(sys.argv[2]))

