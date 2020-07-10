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
import gi
from gi.repository import GObject, GLib, Gtk
from threading import Thread

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

class TasksMgmt(object):
    
    def __init__(self, storeheader):
        self.currenttasks = []
        #currenttaskseditable needs to exist, unless better code can be made, as directly modifying a list used in a loop, no matter the method, WILL cause ListChanged exceptions
        self.currenttask = ""
        self.dontcontinue = False
        self.inaction = False
        self.storeheader = storeheader
        self.existingwidgets = []
        
        GObject.threads_init()
        
    def add_task(self, newtask):
        if not newtask in self.currenttasks:
            self.currenttasks.append(newtask)
            self.gui_refresh_tasks()
        
    def start_now(self):
        #Code for initiating the installation process if it isn't already initialised
        if self.inaction == False:
            self.do_tasks()
        else:
            return
        
    def gui_refresh_tasks(self):
        thread = Thread(target=self._gui_refresh_tasks,
                        args=())
        thread.daemon = True
        thread.start()
    
    def _gui_refresh_tasks(self):
        #Tried threads - just crashes
        GLib.idle_add(self.__gui_refresh_tasks)
    
    def __gui_refresh_tasks(self):
        if len(self.currenttasks) >= 1:
            self.storeheader.status_btn.set_label(str(len(self.currenttasks)))
        else:
            self.storeheader.status_btn.set_label("")
        
        #Destoy the existing widgets
        for widget in self.existingwidgets:
            widget.destroy()
        
        self.existingwidgets = []
        
        for task in self.currenttasks:
            if task.startswith('apt:inst:'):
                packagenm = task.split('apt:inst:')[1]
            elif task.startswith('apt:upgr:'):
                packagenm = task.split('apt:upgr:')[1]
            elif task.startswith('apt:rm:'):
                packagenm = task.split('apt:rm:')[1]
            taskbutton = Gtk.Button(label=packagenm)
            taskbutton.connect('clicked', self.storeheader.webkit._btn_goto_packageview, packagenm)
            self.storeheader.tvtasksitems.pack_start(taskbutton, False, True, 0)
            self.existingwidgets.append(taskbutton)
            
        self.storeheader.tvtasksitems.show_all()
        self.storeheader.tvupdatesitems.show_all()
        self.storeheader.tvinstalleditems.show_all()
        
    def do_task(self, task):
        #Code for doing the task
        if task.startswith("apt:inst:"):
            self.storeheader.APTMgmt.apt_client.install_packages([task.split('apt:inst:')[1]],
                                        reply_handler=self.storeheader.APTMgmt.confirm_changes,
                                        error_handler=self.storeheader.APTMgmt.on_error) # dbus.DBusException
            #Since the do_task thing doesn't hold up code while it's doing it...
            while self.storeheader.APTMgmt.changesinaction == False:
                pass
            while self.storeheader.APTMgmt.changesinaction == True:
                pass
        elif task.startswith("apt:upgr:"):
            self.storeheader.APTMgmt.apt_client.upgrade_packages([task.split('apt:upgr:')[1]],
                                        reply_handler=self.storeheader.APTMgmt.confirm_changes,
                                        error_handler=self.storeheader.APTMgmt.on_error) # dbus.DBusException#Since the do_task thing doesn't hold up code while it's doing it...
            while self.storeheader.APTMgmt.changesinaction == False:
                pass
            while self.storeheader.APTMgmt.changesinaction == True:
                pass
        elif task.startswith("apt:rm:"):
            self.storeheader.APTMgmt.apt_client.remove_packages([task.split('apt:rm:')[1]],
                                        reply_handler=self.storeheader.APTMgmt.confirm_changes,
                                        error_handler=self.storeheader.APTMgmt.on_error) # dbus.DBusException#Since the do_task thing doesn't hold up code while it's doing it...
            while self.storeheader.APTMgmt.changesinaction == False:
                pass
            while self.storeheader.APTMgmt.changesinaction == True:
                pass
        elif task.startswith("flatpak:inst:"):
            pass
        elif task.startswith("flatpak:upgr:"):
            pass
        elif task.startswith("flatpak:rm:"):
            pass
        elif task.startswith("snap:inst:"):
            pass
        elif task.startswith("snap:upgr:"):
            pass
        elif task.startswith("snap:rm:"):
            pass
        elif task.startswith("ice:inst:"):
            pass
        elif task.startswith("ice:rm:"):
            pass
        elif task.startswith("apt:aptsource:"):
            pass
        self.currenttasks.remove(task)
        
    def do_tasks(self):
        self.inaction = True
        while self.currenttasks != []:
            self.do_task(self.currenttasks[0])
            self.gui_refresh_tasks()
            
        self.inaction = False
        
    def closing_check(self):
        if self.currenttasks != []:
            #Prevent closing and stop the tasks after the existing task is done, followed by closing Store
            pass
            
            
            
            
