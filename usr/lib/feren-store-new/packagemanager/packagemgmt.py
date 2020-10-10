#!/usr/bin/python3 -u
#THE -u ON THERE MAKES THE OUTPUT COME OUT ON THE FLY. DO NOT REMOVE IT.

import sys
import gi

#Snap Class
if sys.argv[1] == "snap":
    ###################################################################################
    # Snap Management Python Script - use me for percentage obtaining in-GUI          #
    # Cheers Wimpy for making such a useful example script                            #
    # https://gist.github.com/flexiondotorg/84c3f137d70f4e21ea46419833c0aff4          #
    #                                                                                 #
    # PS: Do yourself a favour and use this: https://lazka.github.io/pgi-docs/Snapd-1 #
    ###################################################################################
    
    gi.require_version('Snapd', '1')
    from gi.repository import Snapd
    class SnapMgmt():
        def __init__(self):
            self.client = Snapd.Client()
            
        def progress_snap_cb(self, client, change, _, user_data):
            # Interate over tasks to determine the aggregate tasks for completion.
            total = 0
            done = 0
            for task in change.get_tasks():
                total += task.get_progress_total()
                done += task.get_progress_done()
            percent = round((done/total)*100)
            print(percent)
            

        def snap_install(self, snapname):
            return self.client.install2_sync(Snapd.InstallFlags.NONE, snapname, None, None, self.progress_snap_cb, (None,), None)
            #install2_sync(flags, name, channel, revision, progress_callback, progress_callback_data, cancellable)


        def snap_remove(self, snapname):
            return self.client.remove2_sync(Snapd.InstallFlags.NONE, snapname, self.progress_snap_cb, (None,), None)
            #remove2_sync(flags, name, progress_callback, progress_callback_data, cancellable)


#Flatpak Class
if sys.argv[1] == "flatpak":
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
    import getpass
    import math
    import os
    import re

    gi.require_version('Gtk', '3.0')
    gi.require_version('Flatpak', '1.0')
    from gi.repository import Flatpak, Gtk, GLib, Gio
    class FlatpakMgmt():
        def __init__(self):
            #determine if Superuser or not to determine install target
            if getpass.getuser() == "root":
                self.superuser = True
            else:
                self.superuser = False

            self.arch = Flatpak.get_default_arch()

            self.item_count = 0
            self.current_count = 0

            self.taskstbinstalled = {}
            self.taskstbupdated = {}
            self.taskstbremoved = {}

            self.flatpakoverridesiceaccess = ["org.mozilla.firefox"]
            self.flatpakoverridesonlyadwaita = ["org.mozilla.firefox"]
            
            if self.superuser == True:
                self.flatpakclassthing = Flatpak.Installation.new_system()
                self.flatpakclassthingalt = self.flatpakclassthing
            else:
                self.flatpakclassthing = Flatpak.Installation.new_user()
                self.flatpakclassthingalt = Flatpak.Installation.new_system()
            self.transaction = Flatpak.Transaction.new_for_installation(self.flatpakclassthing)

            self.flatpakremotes = self.flatpakclassthing.list_remotes()
            if self.flatpakclassthing != self.flatpakclassthingalt:
                for flatpakremote in self.flatpakclassthingalt.list_remotes():
                    if flatpakremote not in self.flatpakremotes:
                        self.flatpakremotes.append(flatpakremote)

            self.all_refs = []
            for remote_name in self.flatpakremotes:
                try:
                    self.all_refs.extend(self.flatpakclassthing.list_remote_refs_sync(remote_name.get_name(), None))
                    if self.flatpakclassthing != self.flatpakclassthingalt:
                        for i in self.flatpakclassthingalt.list_remote_refs_sync(remote_name.get_name(), None):
                            if i not in self.all_refs:
                                self.all_refs.append(i)
                except:
                    try:
                        self.all_refs.extend(self.flatpakclassthingalt.list_remote_refs_sync(remote_name.get_name(), None))
                    except:
                        pass

        def progress_flatpak_cb(self, status, progress, estimating, data=None):
            package_chunk_size = 1.0 / self.item_count
            partial_chunk = (progress / 100.0) * package_chunk_size

            print(math.floor(((self.current_count * package_chunk_size) + partial_chunk) * 100.0))

        def on_flatpak_error(self, error_details):
            print("STOREERROR", str([error_details]))

        def on_flatpak_finished(self):
            print("STOREDONE")

        def is_flatpak_installed(self, ref):
            try:
                iref = self.flatpakclassthing.get_installed_ref(ref.get_kind(),
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


        def _add_ref_to_task(self, refname, remotename, optype):
            if optype == "install":
                self.taskstbinstalled[remotename].append(refname)
            elif optype == "remove":
                self.taskstbremoved[remotename].append(refname)
            else:
                self.taskstbupdated[remotename].append(refname)

        def _find_remote_ref_from_list(self, remote_name, basic_ref):
            remote_ref = None

            ref_str = basic_ref.format_ref()

            for ref in self.all_refs:
                if ref_str == ref.format_ref():
                    remote_ref = ref
                    break

            if remote_ref == None:
                try:
                    remote_ref = self.flatpakclassthing.fetch_remote_ref_sync(remote_name,
                                                            basic_ref.get_kind(),
                                                            basic_ref.get_name(),
                                                            basic_ref.get_arch(),
                                                            basic_ref.get_branch(),
                                                            None)
                except:
                    remote_ref = self.flatpakclassthingalt.fetch_remote_ref_sync(remote_name,
                                                            basic_ref.get_kind(),
                                                            basic_ref.get_name(),
                                                            basic_ref.get_arch(),
                                                            basic_ref.get_branch(),
                                                            None)
            return remote_ref

        def _get_runtime_ref(self, ref, remote_name):
            runtime_ref = None

            try:
                meta = self.flatpakclassthing.fetch_remote_metadata_sync(remote_name, ref, None)
            except:
                try:
                    meta = self.flatpakclassthingalt.fetch_remote_metadata_sync(remote_name, ref, None)
                except:
                    meta = None
            
            try:
                keyfile = GLib.KeyFile.new()

                data = meta.get_data().decode()

                keyfile.load_from_data(data, len(data), GLib.KeyFileFlags.NONE)

                runtime = keyfile.get_string("Application", "runtime")
                basic_ref = Flatpak.Ref.parse("runtime/%s" % runtime)

                # use the same-remote's runtimes
                try:
                    runtime_ref = self._find_remote_ref_from_list(remote_name, basic_ref)
                except GLib.Error:
                    pass
            except:
                runtime_ref = None

            return runtime_ref

        def _get_remote_related_refs(self, remote_name, ref):
            return_refs = []

            try:
                related_refs = self.flatpakclassthing.list_remote_related_refs_sync(remote_name,
                                                                    ref.format_ref(),
                                                                    None)
            except:
                try:
                    related_refs = self.flatpakclassthingalt.list_remote_related_refs_sync(remote_name,
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
                    remote_ref = self._find_remote_ref_from_list(remote_name, related_ref)

                    return_refs.append(remote_ref)
            except:
                pass

            return return_refs

        def add_install_to_transaction(self, refthing, remotename):
            try:
                self.taskstbinstalled[remotename] = []
                self.taskstbupdated[remotename] = []
                self.taskstbremoved[remotename] = []

                self._add_ref_to_task(refthing, remotename, "install")
                update_list = self.flatpakclassthing.list_installed_refs_for_update(None)

                all_related_refs = self._get_remote_related_refs(remotename, refthing)

                runtime_ref = self._get_runtime_ref(refthing, remotename)

                if not runtime_ref == None:
                    if not self.is_flatpak_installed(runtime_ref):
                        self._add_ref_to_task(runtime_ref, remotename, "install")
                    else:
                        if runtime_ref in update_list:
                            self._add_ref_to_task(runtime_ref, remotename, "update")
                    all_related_refs += self._get_remote_related_refs(remotename, runtime_ref)

                for related_ref in all_related_refs:
                    if not self.is_flatpak_installed(related_ref):
                        self._add_ref_to_task(related_ref, remotename, "install")
                    else:
                        if related_ref in update_list:
                            self._add_ref_to_task(related_ref, remotename, "update")

            except:
                # Something went wrong, bail out
                self.taskstbinstalled[remotename] = []
                self.taskstbupdated[remotename] = []
                self.taskstbremoved[remotename] = []
                return

        def add_remove_to_transaction(self, refthing, remotename):
            try:
                self.taskstbinstalled[remotename] = []
                self.taskstbupdated[remotename] = []
                self.taskstbremoved[remotename] = []

                self._add_ref_to_task(refthing, remotename, "remove")

                related_refs = self.flatpakclassthing.list_installed_related_refs_sync(remotename,
                                                                    refthing.format_ref(),
                                                                    None)

                for related_ref in related_refs:
                    if self.is_flatpak_installed(related_ref) and related_ref.should_delete():
                        self._add_ref_to_task(related_ref, remotename, "remove")

            except:
                self.taskstbinstalled[remotename] = []
                self.taskstbupdated[remotename] = []
                self.taskstbremoved[remotename] = []
                return


        def get_ref_from_name(self, flatpakname):
            for i in self.all_refs:
                if i.get_name() == flatpakname and i.get_arch() == self.arch:
                    return i


        def flatpak_transaction_commit(self):
            #Count things to do
            for remote in self.taskstbinstalled:
                self.item_count += len(self.taskstbinstalled[remote])
            for remote in self.taskstbupdated:
                self.item_count += len(self.taskstbupdated[remote])
            for remote in self.taskstbremoved:
                self.item_count += len(self.taskstbremoved[remote])

            for remote in self.taskstbinstalled:
                for ref in self.taskstbinstalled[remote]:
                    try:
                        self.flatpakclassthing.install(ref.get_remote_name(),
                                            ref.get_kind(),
                                            ref.get_name(),
                                            ref.get_arch(),
                                            ref.get_branch(),
                                            self.progress_flatpak_cb,
                                            None,
                                            None)
                    except GLib.Error as e:
                        if e.code != Gio.IOErrorEnum.CANCELLED:
                            print("STOREERROR", str([e.message]))
                            return

                    self.current_count += 1
                    
                    print(math.floor(((self.current_count * (1.0/self.item_count)) * 100.0)))

                    #Flatpak overrides - ICE profiles folder access
                    if ref.get_name() in self.flatpakoverridesiceaccess:
                        os.system("/usr/bin/flatpak override "+ref.get_name()+" --filesystem=~/.local/share/feren-store-ice")
                    #Flatpak overrides - only Adwaita
                    if ref.get_name() in self.flatpakoverridesonlyadwaita:
                        os.system("/usr/bin/flatpak override "+ref.get_name()+" --env=GTK_THEME='Adwaita'")

            for remote in self.taskstbremoved:
                for ref in self.taskstbremoved[remote]:
                    try:
                        #Fake 90% because Flatpak doesn't actually mark progress when removing
                        print(math.floor(((self.current_count * (1.0 / self.item_count)) + (0.9 / self.item_count)) * 100.0))
                        self.flatpakclassthing.uninstall(ref.get_kind(),
                                            ref.get_name(),
                                            ref.get_arch(),
                                            ref.get_branch(),
                                            self.progress_flatpak_cb,
                                            None,
                                            None)
                    except GLib.Error as e:
                        if e.code != Gio.IOErrorEnum.CANCELLED:
                            print("STOREERROR", str([e.message]))
                            return

                    self.current_count += 1
                    
                    print(math.floor(((self.current_count * (1.0/self.item_count)) * 100.0)))

                    if os.path.isfile("/var/lib/flatpak/overrides/"+ref.get_name()):
                        os.system("/bin/rm -f /var/lib/flatpak/overrides/"+ref.get_name())
                    

            for remotes in self.taskstbupdated:
                for ref in self.taskstbupdated[remotes]:
                    try:
                        self.flatpakclassthing.update(Flatpak.UpdateFlags.NONE,
                                            ref.get_remote_name(),
                                            ref.get_kind(),
                                            ref.get_name(),
                                            ref.get_arch(),
                                            ref.get_branch(),
                                            self.progress_flatpak_cb,
                                            None,
                                            None)
                    except GLib.Error as e:
                        if e.code != Gio.IOErrorEnum.CANCELLED:
                            print("STOREERROR", str([e.message]))
                            return

                    self.current_count += 1
                    
                    print(math.floor(((self.current_count * (1.0/self.item_count)) * 100.0)))

                    #Flatpak overrides - ICE profiles folder access
                    if ref.get_name() in self.flatpakoverridesiceaccess:
                        os.system("/usr/bin/flatpak override "+ref.get_name()+" --filesystem=~/.local/share/feren-store-ice")
                    #Flatpak overrides - only Adwaita
                    if ref.get_name() in self.flatpakoverridesonlyadwaita:
                        os.system("/usr/bin/flatpak override "+ref.get_name()+" --env=GTK_THEME='Adwaita'")
                    

            print("STOREDONE")


        def flatpak_install(self, remote):
            self.add_install_to_transaction(self.get_ref_from_name(sys.argv[4]), remote)
            #Commit the transaction
            self.flatpak_transaction_commit()


        def flatpak_upgrade(self, remote):
            self.add_install_to_transaction(self.get_ref_from_name(sys.argv[4]), remote)
            #Commit the transaction
            self.flatpak_transaction_commit()


        def flatpak_remove(self, remote):
            self.add_remove_to_transaction(self.get_ref_from_name(sys.argv[4]), remote)
            #Commit the transaction
            self.flatpak_transaction_commit()


        def flatpak_simulate_install(self, root, remote):
            if root == True:
                self.superuser = True
                self.flatpakclassthing = Flatpak.Installation.new_system()
                self.flatpakclassthingalt = self.flatpakclassthing
            else:
                self.superuser = False
                self.flatpakclassthing = Flatpak.Installation.new_user()
                self.flatpakclassthingalt = Flatpak.Installation.new_system()
            self.add_install_to_transaction(self.get_ref_from_name(sys.argv[5]), remote)
            simultaskstbinstalled = {}
            simultaskstbupdated = {}
            simultaskstbremoved = {}
            for remote in self.taskstbinstalled:
                simultaskstbinstalled[remote] = []
                for ref in self.taskstbinstalled[remote]:
                    simultaskstbinstalled[remote].append(ref.get_name())
            for remote in self.taskstbupdated:
                simultaskstbupdated[remote] = []
                for ref in self.taskstbupdated[remote]:
                    simultaskstbupdated[remote].append(ref.get_name())
            for remote in self.taskstbremoved:
                simultaskstbremoved[remote] = []
                for ref in self.taskstbremoved[remote]:
                    simultaskstbremoved[remote].append(ref.get_name())
            print([simultaskstbinstalled, simultaskstbupdated, simultaskstbremoved])


        def flatpak_simulate_upgrade(self, root, remote):
            if root == True:
                self.superuser = True
                self.flatpakclassthing = Flatpak.Installation.new_system()
                self.flatpakclassthingalt = self.flatpakclassthing
            else:
                self.superuser = False
                self.flatpakclassthing = Flatpak.Installation.new_user()
                self.flatpakclassthingalt = Flatpak.Installation.new_system()
            self.add_install_to_transaction(self.get_ref_from_name(sys.argv[5]), remote)
            simultaskstbinstalled = {}
            simultaskstbupdated = {}
            simultaskstbremoved = {}
            for remote in self.taskstbinstalled:
                simultaskstbinstalled[remote] = []
                for ref in self.taskstbinstalled[remote]:
                    simultaskstbinstalled[remote].append(ref.get_name())
            for remote in self.taskstbupdated:
                simultaskstbupdated[remote] = []
                for ref in self.taskstbupdated[remote]:
                    simultaskstbupdated[remote].append(ref.get_name())
            for remote in self.taskstbremoved:
                simultaskstbremoved[remote] = []
                for ref in self.taskstbremoved[remote]:
                    simultaskstbremoved[remote].append(ref.get_name())
            print([simultaskstbinstalled, simultaskstbupdated, simultaskstbremoved])


        def flatpak_simulate_remove(self, root, remote):
            if root == True:
                self.superuser = True
                self.flatpakclassthing = Flatpak.Installation.new_system()
                self.flatpakclassthingalt = self.flatpakclassthing
            else:
                self.superuser = False
                self.flatpakclassthing = Flatpak.Installation.new_user()
                self.flatpakclassthingalt = Flatpak.Installation.new_system()
            self.add_remove_to_transaction(self.get_ref_from_name(sys.argv[5]), remote)
            simultaskstbinstalled = {}
            simultaskstbupdated = {}
            simultaskstbremoved = {}
            for remote in self.taskstbinstalled:
                simultaskstbinstalled[remote] = []
                for ref in self.taskstbinstalled[remote]:
                    simultaskstbinstalled[remote].append(ref.get_name())
            for remote in self.taskstbupdated:
                simultaskstbupdated[remote] = []
                for ref in self.taskstbupdated[remote]:
                    simultaskstbupdated[remote].append(ref.get_name())
            for remote in self.taskstbremoved:
                simultaskstbremoved[remote] = []
                for ref in self.taskstbremoved[remote]:
                    simultaskstbremoved[remote].append(ref.get_name())
            print([simultaskstbinstalled, simultaskstbupdated, simultaskstbremoved])


        def sortref(self, ref):
            try:
                val = float(ref.get_branch())
            except ValueError:
                val = 9.9

            return val


#APT Class
if sys.argv[1] == "apt":
    ###################################################################################
    # APT Management Python Script - use me for percentage obtaining in-GUI           #
    #                                                                                 #
    #  Note: This was stupidly painful to get working, and took A LOT of attempts     #
    #  so for your sanity please just use this as it is and don't bother with editing #
    #  it, etc, unless you REALLY know what you're doing. Some credit goes to         #
    #  https://github.com/schlomo/apt-install/blob/master/apt-install.py, by the way. #
    ###################################################################################
    
    from aptdaemon.client import AptClient
    import aptdaemon.errors
    import aptdaemon.enums
    from gi.repository import GLib
    
    class APTMgmt():
        def __init__(self):
            self.apt_client = AptClient()
            self.apt_transaction = None
            self.packages = []
            self.loop = None

        def confirm_changes(self, apt_transaction):
            self.apt_transaction = apt_transaction
            try:
                self.run_transaction()
            except Exception as e:
                print("STOREERROR", str([e]))
                self.loop.quit()
                exit(0)

        def on_error(self, error):
            print("STOREERROR", str([aptdaemon.enums.get_error_string_from_enum(error.code), aptdaemon.enums.get_error_description_from_enum(error.code)]))
            self.loop.quit()
            exit(0)

        def run_transaction(self):
            self.apt_transaction.connect("finished", self.on_transaction_finished)
            self.apt_transaction.connect("progress-changed", self.on_transaction_progress)
            self.apt_transaction.connect("error", self.on_transaction_error)
            self.apt_transaction.run(reply_handler=lambda: None, error_handler=self.on_error)
        
        def on_transaction_progress(self, apt_transaction, progress):
            if not apt_transaction.error:
                print(progress)

        def on_transaction_error(self, apt_transaction, error_code, error_details):
            print("STOREERROR", str([error_code, error_details]))
            self.loop.quit()
            exit(0)

        def on_transaction_finished(self, apt_transaction, exit_state):
            print("STOREDONE")
            self.loop.quit()
            exit(0)
    
    def apt_install():
        if aptmgmt.packages[0].endswith(".deb"):
            aptmgmt.apt_client.install_file(aptmgmt.packages[0],
                                        reply_handler=aptmgmt.confirm_changes,
                                        error_handler=aptmgmt.on_error) # dbus.DBusException
        else:
            aptmgmt.apt_client.install_packages(aptmgmt.packages,
                                        reply_handler=aptmgmt.confirm_changes,
                                        error_handler=aptmgmt.on_error) # dbus.DBusException
    

    def apt_upgrade():
        aptmgmt.apt_client.upgrade_packages(aptmgmt.packages,
                                    reply_handler=aptmgmt.confirm_changes,
                                    error_handler=aptmgmt.on_error) # dbus.DBusException
        

    def apt_remove():
        aptmgmt.apt_client.remove_packages(aptmgmt.packages,
                                    reply_handler=aptmgmt.confirm_changes,
                                    error_handler=aptmgmt.on_error) # dbus.DBusException




if sys.argv[1] == "snap":
    snapmgmt = SnapMgmt()
    if sys.argv[2] == "install":
        if snapmgmt.snap_install(sys.argv[3]):
            print("STOREDONE")
        else:
            print("STOREERROR []")
        exit()
    elif sys.argv[2] == "remove":
        if snapmgmt.snap_remove(sys.argv[3]):
            print("STOREDONE")
        else:
            print("STOREERROR []")
        exit()

elif sys.argv[1] == "flatpak":
    flatpakmgmt = FlatpakMgmt()
    if sys.argv[2] == "install":
        flatpakmgmt.flatpak_install(sys.argv[3])
    elif sys.argv[2] == "upgrade":
        flatpakmgmt.flatpak_upgrade(sys.argv[3])
    elif sys.argv[2] == "remove":
        flatpakmgmt.flatpak_remove(sys.argv[3])
    elif sys.argv[2] == "simulinstall":
        flatpakmgmt.flatpak_simulate_install(bool(sys.argv[3] == "True"), sys.argv[4])
    elif sys.argv[2] == "simulupgrade":
        flatpakmgmt.flatpak_simulate_upgrade(bool(sys.argv[3] == "True"), sys.argv[4])
    elif sys.argv[2] == "simulremove":
        flatpakmgmt.flatpak_simulate_remove(bool(sys.argv[3] == "True"), sys.argv[4])

elif sys.argv[1] == "apt":
    loop = GLib.MainLoop()
    aptmgmt = APTMgmt()
    aptmgmt.packages = sys.argv[3:]
    aptmgmt.loop = loop
    if sys.argv[2] == "install":
        GLib.timeout_add(10000,apt_install)
    elif sys.argv[2] == "upgrade":
        GLib.timeout_add(10000,apt_upgrade)
    elif sys.argv[2] == "remove":
        GLib.timeout_add(10000,apt_remove)
    loop.run()
