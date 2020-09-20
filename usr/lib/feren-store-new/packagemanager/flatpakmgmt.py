#!/usr/bin/python3

#######################################################################################
# Flatpak Management Python Script - use me for percentage obtaining in-GUI           #
#                                                                                     #
# PS: Do yourself a favour and use this: https://lazka.github.io/pgi-docs/Flatpak-1.0 #
#######################################################################################


#TODO: Make the code so it just accepts a dict of things to change as an argument and make it change according to those.
#   Also make the code be able to interpret a JSON file of known Flatpak repositories to be able to add repositories manually if needed
#   Finally move getthemes and the ability to see what changes will be made into flatpakmgmt in the Store itself



import sys
import gi
import getpass
import math
import os
import re

gi.require_version('Gtk', '3.0')
gi.require_version('Flatpak', '1.0')
from gi.repository import Flatpak, Gtk, GLib


#determine if Superuser or not to determine install target
if getpass.getuser() == "root":
    superuser = True
else:
    superuser = False

arch = Flatpak.get_default_arch()

item_count = 0
current_count = 0

taskstbinstalled = {}
taskstbupdated = {}
taskstbremoved = {}


def progress_flatpak_cb(status, progress, estimating, data=None):
    package_chunk_size = 1.0 / item_count
    partial_chunk = (progress / 100.0) * package_chunk_size

    print(math.floor(((current_count * package_chunk_size) + partial_chunk) * 100.0))


def on_flatpak_error(error_details):
    print("ERROR", [error_details])


def on_flatpak_finished(self):
    print("DONE")


def is_flatpak_installed(ref):
    try:
        iref = flatpakclassthing.get_installed_ref(ref.get_kind(),
                                        ref.get_name(),
                                        ref.get_arch(),
                                        ref.get_branch(),
                                        None)

        if iref:
            return True
    except GLib.Error:
        pass
    except AttributeError: # bad/null ref
        pass
    return False


def _add_ref_to_task(refname, remotename, optype, verboseoutput=False):
    global taskstbinstalled
    global taskstbupdated
    global taskstbremoved

    if optype == "install":
        if verboseoutput:
            taskstbinstalled[remotename].append(refname.get_name())
        else:
            taskstbinstalled[remotename].append(refname)
    elif optype == "remove":
        if verboseoutput:
            taskstbremoved[remotename].append(refname.get_name())
        else:
            taskstbremoved[remotename].append(refname)
    else:
        if verboseoutput:
            taskstbupdated[remotename].append(refname)
        else:
            taskstbupdated[remotename].append(refname)
    print("Added", refname.format_ref(), "to", optype)

def _find_remote_ref_from_list(remote_name, basic_ref):
    remote_ref = None

    try:
        all_refs = flatpakclassthing.list_remote_refs_sync(remote_name, None)
    except:
        all_refs = flatpakclassthingalt.list_remote_refs_sync(remote_name, None)

    ref_str = basic_ref.format_ref()

    for ref in all_refs:
        if ref_str == ref.format_ref():
            remote_ref = ref
            break

    if remote_ref == None:
        try:
            remote_ref = flatpakclassthing.fetch_remote_ref_sync(remote_name,
                                                      basic_ref.get_kind(),
                                                      basic_ref.get_name(),
                                                      basic_ref.get_arch(),
                                                      basic_ref.get_branch(),
                                                      None)
        except:
            remote_ref = flatpakclassthingalt.fetch_remote_ref_sync(remote_name,
                                                      basic_ref.get_kind(),
                                                      basic_ref.get_name(),
                                                      basic_ref.get_arch(),
                                                      basic_ref.get_branch(),
                                                      None)
    return remote_ref

def _get_runtime_ref(ref, remote_name):
    runtime_ref = None

    try:
        meta = flatpakclassthing.fetch_remote_metadata_sync(remote_name, ref, None)

        keyfile = GLib.KeyFile.new()

        data = meta.get_data().decode()

        keyfile.load_from_data(data, len(data), GLib.KeyFileFlags.NONE)

        runtime = keyfile.get_string("Application", "runtime")
        basic_ref = Flatpak.Ref.parse("runtime/%s" % runtime)

        # use the same-remote's runtimes
        try:
            runtime_ref = _find_remote_ref_from_list(remote_name, basic_ref)
        except GLib.Error:
            pass
    except:
        runtime_ref = None

    return runtime_ref

def _get_remote_related_refs(remote_name, ref):
    return_refs = []

    try:
        related_refs = flatpakclassthing.list_remote_related_refs_sync(remote_name,
                                                            ref.format_ref(),
                                                            None)
    except:
        try:
            related_refs = flatpakclassthingalt.list_remote_related_refs_sync(remote_name,
                                                                ref.format_ref(),
                                                                None)
        except:
            pass
    
    try:
        for related_ref in related_refs:
            if not related_ref.should_download():
                continue

            # Convert to a RemoteRef so that later functions know what remote
            # this is from.  Related refs should never fail from the given remote,
            # but if they're no-enumerate (as .flatpakref installs can be) then a listing
            # will be empty, so we have ..._from_list construct a synthetic one (nofail).
            remote_ref = _find_remote_ref_from_list(remote_name, related_ref)

            return_refs.append(remote_ref)
    except:
        pass

    return return_refs

def add_install_to_transaction(refthing, remotename, verboseoutput=False):
    try:
        taskstbinstalled[remotename] = []
        taskstbupdated[remotename] = []
        taskstbremoved[remotename] = []

        _add_ref_to_task(refthing, remotename, "install", verboseoutput)
        update_list = flatpakclassthing.list_installed_refs_for_update(None)

        all_related_refs = _get_remote_related_refs(remotename, refthing)

        runtime_ref = _get_runtime_ref(refthing, remotename)

        if not runtime_ref == None:
            if not is_flatpak_installed(runtime_ref):
                _add_ref_to_task(runtime_ref, remotename, "install", verboseoutput)
            else:
                if runtime_ref in update_list:
                    _add_ref_to_task(runtime_ref, remotename, "update", verboseoutput)
            all_related_refs += _get_remote_related_refs(remotename, runtime_ref)

        for related_ref in all_related_refs:
            if not is_flatpak_installed(related_ref):
                _add_ref_to_task(related_ref, remotename, "install", verboseoutput)
            else:
                if related_ref in update_list:
                    _add_ref_to_task(related_ref, remotename, "update", verboseoutput)

    except Exception as e:
        print(e)
        # Something went wrong, bail out
        if verboseoutput:
            print({"install": {}, "update": {}, "remove": {}})
        taskstbinstalled[remotename] = []
        taskstbupdated[remotename] = []
        taskstbremoved[remotename] = []
        return

    if verboseoutput:
        print({"install": taskstbinstalled, "update": taskstbupdated, "remove": taskstbremoved})

def add_remove_to_transaction(refthing, remotename, verboseoutput=False):
    try:
        taskstbinstalled[remotename] = []
        taskstbupdated[remotename] = []
        taskstbremoved[remotename] = []

        _add_ref_to_task(refthing, remotename, "remove", verboseoutput)

        related_refs = flatpakclassthing.list_installed_related_refs_sync(remotename,
                                                            refthing.format_ref(),
                                                            None)

        for related_ref in related_refs:
            if is_flatpak_installed(related_ref) and related_ref.should_delete():
                if related_ref.get_remote_name() not in taskstbremoved:
                    taskstbremoved[related_ref.get_remote_name()] = []
                _add_ref_to_task(related_ref, related_ref.get_remote_name(), "remove", verboseoutput)

    except Exception as e:
        print(e)
        if verboseoutput:
            print({"install": {}, "update": {}, "remove": {}})
        taskstbinstalled[remotename] = []
        taskstbupdated[remotename] = []
        taskstbremoved[remotename] = []
        return

    if verboseoutput:
        print({"install": taskstbinstalled, "update": taskstbupdated, "remove": taskstbremoved})


def flatpak_transaction_commit():
    global item_count
    global current_count

    #Count things to do
    for remote in taskstbinstalled:
        item_count += len(taskstbinstalled[remote])
    for remote in taskstbupdated:
        item_count += len(taskstbupdated[remote])
    for remote in taskstbremoved:
        item_count += len(taskstbremoved[remote])
    
    print(item_count, taskstbinstalled, taskstbupdated, taskstbremoved)
    pass


def get_ref_from_name(flatpakname):
    for i in all_refs:
        if i.get_name() == flatpakname and i.get_arch() == arch:
            return i


def flatpak_install(flatpakname, remote):
    #Get ref using name
    ref = get_ref_from_name(flatpakname)
    #Get full lists of things to change
    add_install_to_transaction(ref, remote)
    #Commit the transaction
    flatpak_transaction_commit()


def flatpak_upgrade(flatpakname, remote):
    #Get ref using name
    ref = get_ref_from_name(flatpakname)
    #Get full lists of things to change
    add_install_to_transaction(ref, remote)
    #Commit the transaction
    flatpak_transaction_commit()


def flatpak_remove(flatpakname, remote):
    #Get ref using name
    ref = get_ref_from_name(flatpakname)
    #Get full lists of things to change
    add_remove_to_transaction(ref, remote)
    #Commit the transaction
    flatpak_transaction_commit()

    
if superuser == True:
    flatpakclassthing = Flatpak.Installation.new_system()
    flatpakclassthingalt = flatpakclassthing
else:
    flatpakclassthing = Flatpak.Installation.new_user()
    flatpakclassthingalt = Flatpak.Installation.new_system()
transaction = Flatpak.Transaction.new_for_installation(flatpakclassthing)

flatpakremotes = flatpakclassthing.list_remotes()
if flatpakclassthing != flatpakclassthingalt:
    for flatpakremote in flatpakclassthingalt.list_remotes():
        if flatpakremote not in flatpakremotes:
            flatpakremotes.append(flatpakremote)

all_refs = []
for remote_name in flatpakremotes:
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
            pass



def sortref(ref):
    try:
        val = float(ref.get_branch())
    except ValueError:
        val = 9.9

    return val

if len(sys.argv) == 4:
    pass
elif len(sys.argv) == 2:
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
                        matching_refs = []

                        for listed_ref in all_refs:
                            #FIXME: Flatpak doesn't list them by their closest architecture to the one it detects to your system's
                            if listed_ref.get_arch() != arch:
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
    flatpak_install(sys.argv[2], sys.argv[3])
elif sys.argv[1] == "upgrade":
    flatpak_upgrade(sys.argv[2], sys.argv[3])
elif sys.argv[1] == "remove":
    flatpak_remove(sys.argv[2], sys.argv[3])
