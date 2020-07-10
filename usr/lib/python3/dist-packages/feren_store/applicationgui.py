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

import gi
import gettext
import os
import urllib.request
import urllib.error
import time
from threading import Thread

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib, GObject, GLib

from feren_store import storeutils, aptmgmt
from .aptmgmt import APTChecks, APTMgmt

#if os.path.isfile("/usr/bin/snapd"):
#    from feren_store import snapmgmt
#if os.path.isfile("/usr/bin/flatpak"):
#    from feren_store import flatpakmgmt


t = gettext.translation('feren-store', '/usr/share/locale', fallback=True)
_ = t.gettext

#TODO: Put Snap permissions management in the Store settings

class PackageHeader(Gtk.Box):

    def __init__(self, mainwind, status_btn):
        global globalvars
        global jsonreader
        globalvars = storeutils.GlobalVariables()
        jsonreader = storeutils.JSONReader()
        
        
        Gtk.Box.__init__(self)
        
        self.get_style_context().add_class("only-toolbar")
        
        
        box_application_namedesc = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        #Application Icon
        self.app_iconimg = Gtk.Image()
        self.app_iconimg_loading = Gtk.Spinner()
        self.app_iconimg_stack = Gtk.Stack()
        self.app_iconimg_loading_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.app_iconimg_loading_box.set_center_widget(self.app_iconimg_loading)
        self.app_iconimg_stack.add_named(self.app_iconimg_loading_box, "Loading")
        self.app_iconimg_stack.add_named(self.app_iconimg, "AppIcon")
        self.app_iconimg_stack.set_visible_child(self.app_iconimg)
        
        #Application Title
        self.app_title = Gtk.Label()
        self.app_title.get_style_context().add_class("14scale")
        
        #Application Description
        self.app_desc = Gtk.Label()
        
        #Application Management Buttons
        self.app_mgmt_button = Gtk.Stack()
        self.app_mgmt_installbtn = Gtk.Button(label=("Install"))
        self.app_mgmt_installunavailbtn = Gtk.Button(label=("Install..."))
        self.app_mgmt_removebtn = Gtk.Button(label=("Remove"))
        self.app_mgmt_updatebtn = Gtk.Button(label=("Update"))
        self.app_mgmt_installbtn.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        self.app_mgmt_installunavailbtn.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        self.app_mgmt_updatebtn.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        self.app_mgmt_removebtn.get_style_context().add_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)
        self.app_mgmt_preparingbtns = Gtk.Spinner()
        self.app_mgmt_button.add_named(self.app_mgmt_preparingbtns, "Preparing")
        self.app_mgmt_button.add_named(self.app_mgmt_installbtn, "Standard")
        self.app_mgmt_button.add_named(self.app_mgmt_installunavailbtn, "InstallRepo")
        self.app_mgmt_button.add_named(self.app_mgmt_removebtn, "Remove")
        self.app_mgmt_button.set_visible_child(self.app_mgmt_preparingbtns)
        self.app_mgmt_preparingbtns.start()
        
        #Application Source Combobox
        self.app_source_dropdown = Gtk.ComboBox()
        #NOTE TO SELF: NEVER put this in the dropdown refreshing code - it'll cause duplicated labels
        cell = Gtk.CellRendererText()
        self.app_source_dropdown.pack_start(cell, True)
        self.app_source_dropdown.add_attribute(cell, "text", 0)
        
        #Progress Bar
        self.app_mgmt_progress = Gtk.ProgressBar()
        self.app_mgmt_progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.app_mgmt_progress_box.set_center_widget(self.app_mgmt_progress)
        
        #Make sure application name and short descriptions are left-aligned in there
        app_title_box = Gtk.Box()
        app_desc_box = Gtk.Box()
        app_title_box.pack_start(self.app_title, False, False, 0)
        app_desc_box.pack_start(self.app_desc, False, False, 0)
        
        #Make the column for application name and short description
        box_application_namedesc.pack_start(app_title_box, False, False, 0)
        box_application_namedesc.pack_end(app_desc_box, False, False, 0)
        
        #Stuff for centering items vertically
        centering_titledesc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        centering_titledesc_box.set_center_widget(box_application_namedesc)
        centering_btnactions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        inside_btnactions_box = Gtk.Box()
        inside_btnactions_box.pack_start(self.app_source_dropdown, False, False, 4)
        inside_btnactions_box.pack_start(self.app_mgmt_progress_box, False, False, 4)
        inside_btnactions_box.pack_start(self.app_mgmt_updatebtn, False, False, 4)
        inside_btnactions_box.pack_start(self.app_mgmt_button, False, False, 4)
        
        centering_btnactions_box.set_center_widget(inside_btnactions_box)
        
        #Header building
        self.pack_start(self.app_iconimg_stack, False, False, 8)
        self.pack_start(centering_titledesc_box, False, True, 4)
        self.pack_end(centering_btnactions_box, False, True, 4)
        
        #Margins
        self.app_iconimg.set_margin_top(8)
        self.app_iconimg.set_margin_bottom(8)
        
        #Header image temp
        desired_width = 48
        desired_height = 48
        icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file("/usr/share/feren-os/logos/blank.png")
        icon_pixbuf = icon_pixbuf.scale_simple(desired_width, desired_height, GdkPixbuf.InterpType.BILINEAR)
        self.app_iconimg.set_from_pixbuf(icon_pixbuf)
        
        #Button Assignment
        self.app_mgmt_installbtn.connect('clicked', self.install_pressed)
        self.app_mgmt_installunavailbtn.connect('clicked', self.install_with_source_pressed)
        self.app_mgmt_updatebtn.connect('clicked', self.update_pressed)
        self.app_mgmt_removebtn.connect('clicked', self.remove_pressed)
        
        #Variables
        self.current_package = ""
        self.sources_visible = True
        self.status_btn = status_btn
        
        #Initialize Management
        self.tasksmgmttool = storeutils.TasksMgmt(self)
        self.APTMgmt = APTMgmt(self, mainwind, self.tasksmgmttool)
        
        GObject.threads_init()
        
    def set_current_package(self, packagename):
        self.current_package = packagename

    def show(self):
        self.set_visible(True)
    
    def hide(self):
        self.set_visible(False)
    
    def set_icon(self, iconuri, packagetoview):
        tempdir = storeutils.GlobalVariables().storagetemplocation
        
        self.app_iconimg_loading.start()
        self.app_iconimg_stack.set_visible_child(self.app_iconimg_loading_box)
        #Set the icon shown on the package header
                
        desired_width = 48
        desired_height = 48
        try:
            if not iconuri.startswith("file://"):
                #Download the application icon
                if not os.path.isfile(tempdir+"/"+packagetoview+"-icon"):
                    urllib.request.urlretrieve(iconuri, tempdir+"/"+packagetoview+"-icon")
                #Set it as the icon in the Store
                icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file(tempdir+"/"+packagetoview+"-icon")
            else:
                #Set it as the icon in the Store
                icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file(iconuri.split('file://')[1])
        except Exception as exceptionstring:
            print("Could not retrieve icon for", packagetoview, "-", exceptionstring)
            #TODO: Change to store-missing-icon
            icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file("/usr/share/icons/Inspire/256/apps/feren-store.png")
        icon_pixbuf = icon_pixbuf.scale_simple(desired_width, desired_height, GdkPixbuf.InterpType.BILINEAR)
        self.app_iconimg.set_from_pixbuf(icon_pixbuf)
        self.app_iconimg_stack.set_visible_child(self.app_iconimg)
        self.app_iconimg_loading.stop()
    
    def set_app_details(self, apprname, appshortdesc):
        #Set the application real name (apprname) and short description (appshortdesc) on the package header
        self.app_title.set_label(apprname)
        self.app_desc.set_label(appshortdesc)
    
    def set_source(self, packagesource):
        #Set the application source to the one selected in the source dropdown
        pass
    
    def get_sources(self, jsondata, package):
        #Using the JSON Data from sources/packages.json, populate the sources dropdown according to what's available
        sourcenames, orderofsources = [jsonreader.availablesources[package]["apt"], jsonreader.availablesources[package]["flatpak"], jsonreader.availablesources[package]["snap"]], jsonreader.availablesources[package]["order-of-importance"]
        
        
        iface_list_store = Gtk.ListStore(GObject.TYPE_STRING)
        amount_of_sources = 0
        
        for sourcename in orderofsources:
            if sourcename == "apt":
                #apt source
                friendlysourcename = storeutils.ApplicationSourceTranslator().TranslateToHumanReadable(sourcenames[0])
                if friendlysourcename:
                    iface_list_store.append([friendlysourcename])
                    amount_of_sources += 1
            elif sourcename == "flatpak":
                #flatpak source
                friendlysourcename = storeutils.ApplicationSourceTranslator().TranslateToHumanReadable(sourcenames[1])
                if friendlysourcename:
                    iface_list_store.append([friendlysourcename])
                    amount_of_sources += 1
            elif sourcename == "snap":
                #snap source
                friendlysourcename = storeutils.ApplicationSourceTranslator().TranslateToHumanReadable(sourcenames[2])
                if friendlysourcename:
                    iface_list_store.append([friendlysourcename])
                    amount_of_sources += 1
        
        self.app_source_dropdown.set_model(iface_list_store)
        self.app_source_dropdown.set_active(0)
        if amount_of_sources <= 1:
            self.app_source_dropdown.set_visible(False)
            self.sources_visible = False
        else:
            self.app_source_dropdown.set_visible(True)
            self.sources_visible = True
            
    def change_button_state(self, newstate, disableremove):
        thread = Thread(target=self._change_button_state,
                        args=(newstate, disableremove))
        thread.daemon = True
        thread.start()
        
    def _change_button_state(self, newstate, disableremove):
        GLib.idle_add(self.__change_button_state, newstate, disableremove)
    
    def __change_button_state(self, newstate, disableremove):
        #Change button state between 4 states:
        #uninstalled: Install is visible
        #sourcemissing: Install... is visible
        #installed: Remove is visible
        #updatable: Update and Remove are visible
        
        self.app_mgmt_installbtn.set_sensitive(False)
        self.app_mgmt_installunavailbtn.set_sensitive(False)
        self.app_mgmt_removebtn.set_sensitive(False)
        self.app_mgmt_updatebtn.set_sensitive(False)
        if self.sources_visible:
            self.app_source_dropdown.set_visible(True)
        
        if newstate == "loading":
            self.app_mgmt_progress_box.set_visible(False)
            self.app_mgmt_button.set_visible(True)
            self.app_mgmt_preparingbtns.start()
            self.app_mgmt_updatebtn.set_visible(False)
            self.app_mgmt_button.set_visible_child(self.app_mgmt_preparingbtns)
        elif newstate == "busy":
            #TODO: Add cancel button for non-running tasks once the tasks system is implemented
            self.app_source_dropdown.set_visible(False)
            self.app_mgmt_progress_box.set_visible(True)
            self.app_mgmt_button.set_visible(False)
        elif newstate == "uninstalled":
            self.app_mgmt_progress_box.set_visible(False)
            self.app_mgmt_button.set_visible(True)
            self.app_mgmt_installbtn.set_sensitive(True)
            self.app_mgmt_updatebtn.set_visible(False)
            self.app_mgmt_button.set_visible_child(self.app_mgmt_installbtn)
            self.app_mgmt_preparingbtns.stop()
        elif newstate == "sourcemissing":
            self.app_mgmt_progress_box.set_visible(False)
            self.app_mgmt_button.set_visible(True)
            self.app_mgmt_installunavailbtn.set_sensitive(True)
            self.app_mgmt_updatebtn.set_visible(False)
            self.app_mgmt_button.set_visible_child(self.app_mgmt_installunavailbtn)
            self.app_mgmt_preparingbtns.stop()
        elif newstate == "installed":
            self.app_mgmt_progress_box.set_visible(False)
            self.app_mgmt_button.set_visible(True)
            if disableremove == False:
                self.app_mgmt_removebtn.set_sensitive(True)
            self.app_mgmt_updatebtn.set_visible(False)
            self.app_mgmt_button.set_visible_child(self.app_mgmt_removebtn)
            self.app_mgmt_preparingbtns.stop()
        elif newstate == "updatable":
            self.app_mgmt_progress_box.set_visible(False)
            self.app_mgmt_button.set_visible(True)
            if disableremove == False:
                self.app_mgmt_removebtn.set_sensitive(True)
            self.app_mgmt_updatebtn.set_sensitive(True)
            self.app_mgmt_updatebtn.set_visible(True)
            self.app_mgmt_button.set_visible_child(self.app_mgmt_removebtn)
            self.app_mgmt_preparingbtns.stop()
    
    def btns_get_package_status(self, packagetype, package):
        #Get the state of the package for changing the buttons presented to the user accordingly - is it installed? does it need an update?
        #packagetype is whether it's native, snap, ice or flatpak
        self.change_button_state("loading", False)
        if packagetype == "apt":
            #TODO: Add support for checking for updates
            #TODO: Add support here for checking the application is in the Tasks area as being currently managed
            #LAG HERE
            ifinstalled = APTChecks.checkinstalled(package)
            if ifinstalled == 1:
                self.change_button_state("installed", package == "feren-store")
            elif ifinstalled == 3:
                self.change_button_state("updatable", package == "feren-store")
            else:
                #TODO: Check for package source if necessary
                self.change_button_state("uninstalled", False)
                
    def on_installer_finished(self, package):
        if self.current_package == package:
            thread = Thread(target=self._on_installer_finished,
                            args=(package,))
            thread.daemon = True
            thread.start()
    
    def _on_installer_finished(self, package):
        #Tried threads - just crashes
        GLib.idle_add(self.__on_installer_finished, package)
            
    def __on_installer_finished(self, package):
        #TODO: Make this work depending on the package type
        self.btns_get_package_status("apt", package)
        self.app_mgmt_progress.set_fraction(0.0)
    
    def install_with_source_pressed(self, button):
        #When you press 'Install...'
        pass
    
    def install_pressed(self, button):
        #When you press 'Install'
        self.change_button_state("busy", False)
        self.APTMgmt.install_package(self.current_package)
    
    def update_pressed(self, button):
        #When you press 'Update'
        self.change_button_state("busy", False)
        self.APTMgmt.upgrade_package(self.current_package)
    
    def remove_pressed(self, button):
        #When you press 'Remove'
        self.change_button_state("busy", False)
        self.APTMgmt.remove_package(self.current_package)
