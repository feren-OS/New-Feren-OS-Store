# This file is part of the Feren Store program.
#
# Copyright 2009-2014 Linux Mint and Clement Lefebvre
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

import os
import subprocess

import gettext
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject, GLib, Gio

from threading import Thread
import urllib
import time
import ast

t = gettext.translation('feren-store', '/usr/share/locale', fallback=True)
_ = t.gettext

#TODO: Put Snap permissions management in the Store settings

class ErrorDialog():

    ###Dialog to let users know of transaction fails.

    def __init__(self, error, classnetwork, package):
        self.classnetwork = classnetwork
        
        self.w = Gtk.Window()
        self.w.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.w.set_position(Gtk.WindowPosition.CENTER)
        self.w.set_title("Oops")

        if error != "ERROR": #If it's not just "ERROR" as a string, meaning the code ran if this is TRUE would then cause an exception
            errorlist = error.split("ERROR ")[1]
            errorlist = ast.literal_eval(errorlist)
            self.w.set_size_request(500, 340)
        else: #Just give no description, output, etc since we don't have any - currently the Snap implementation lacks any visible messages
            errorlist = ["", ""]
            self.w.set_size_request(500, 100)
        if len(errorlist) == 1: #If there's only one piece of error - only time there isn't right now is APT
            errorlist = ["", errorlist[0]] #The message should be in the description
        

        self.w.set_destroy_with_parent(True)
        self.w.set_resizable(False)
        
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path('/usr/share/feren-store-new/css/application.css')
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider,
                                          Gtk.STYLE_PROVIDER_PRIORITY_USER)
        
        mainwindow = Gtk.VBox()
        mainwindow.set_spacing(4)
        self.w.add(mainwindow)
        
        strlabelbox = Gtk.VBox()
        first_string = Gtk.Label(label="An error occured")
        first_string.get_style_context().add_class("14scale")
        first_string_box = Gtk.Box()
        first_string_box.pack_start(first_string, False, False, 0)
        if errorlist == ["", ""]:
            second_string = Gtk.Label(label="Unfortunately something went wrong when managing "+package+".")
        else:
            second_string = Gtk.Label(label="Unfortunately something went wrong when managing "+package+".\nThe error is as shown below:")
        second_string_box = Gtk.Box()
        second_string_box.pack_start(second_string, False, False, 0)
        if errorlist != ["", ""]:
            third_string = Gtk.Label(label=errorlist[0])
            third_string_box = Gtk.Box()
            third_string_box.pack_start(third_string, False, False, 0)
        strlabelbox.pack_start(first_string_box, False, False, 0)
        strlabelbox.pack_start(second_string_box, False, False, 0)
        mainwindow.pack_start(strlabelbox, False, False, 0)
        if errorlist != ["", ""]:
            mainwindow.pack_start(third_string_box, False, False, 0)
        
        if errorlist != ["", ""]:
            # build scrolled window widget and add our appview container
            sw = Gtk.ScrolledWindow()
            sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

            # build a an autoexpanding box and add our scrolled window
            b = Gtk.Box(homogeneous=False, spacing=4)
            b.pack_start(sw, expand=True, fill=True, padding=0)
            
            self.errortext = Gtk.Label(label=errorlist[1])
            sw.add(self.errortext)
        
        
        okbtn = Gtk.Button(stock=Gtk.STOCK_OK)
        
        okbtn.connect('clicked', self.ok)
        
        buttonbox = Gtk.Box(spacing=4, homogeneous=True)
        buttonbox.pack_end(okbtn, False, True, 0)
        
        mainwindow.pack_end(buttonbox, False, True, 0)
        
        mainwindow.set_margin_bottom(8)
        mainwindow.set_margin_top(8)
        mainwindow.set_margin_left(10)
        mainwindow.set_margin_right(10)
        
        if errorlist != ["", ""]:
            mainwindow.pack_end(b, True, True, 0)
        
        self.w.show_all()
    
    def ok(self, btn):
        self.w.destroy()

class ChangesConfirmDialog():

    ###Dialog to confirm the changes that would be required by a transaction.

    def __init__(self, packagename, optype, classnetwork, packagesinstalled, packagesupgraded, packagesremoved, pkgmgmt):
        self.classnetwork = classnetwork
        self.packagename = packagename
        self.pkgmgmt = pkgmgmt
        
        packagesdisplayedinst = []
        packagesdisplayedupgr = []
        packagesdisplayedrm = []
        for packagenm in packagesinstalled:
            if not packagenm == packagename:
                try:
                    test = classnetwork.JSONReader().availablesources[packagenm]["apt"]
                    packagesdisplayedinst.append(packagenm)
                except:
                    pass
        for packagenm in packagesupgraded:
            if not packagenm == packagename:
                try:
                    test = classnetwork.JSONReader().availablesources[packagenm]["apt"]
                    packagesdisplayedupgr.append(packagenm)
                except:
                    pass
        for packagenm in packagesremoved:
            if not packagenm == packagename:
                try:
                    test = classnetwork.JSONReader().availablesources[packagenm]["apt"]
                    packagesdisplayedrm.append(packagenm)
                except:
                    pass
                
        if not packagesdisplayedinst and not packagesdisplayedupgr and not packagesdisplayedrm:
            if optype == "install":
                Thread(target=self.confirm_install,
                                args=()).start()
            elif optype == "upgrade":
                Thread(target=self.confirm_upgrade,
                                args=()).start()
            elif optype == "remove":
                Thread(target=self.confirm_remove,
                                args=()).start()
            return
        
        self.w = Gtk.Window()
        self.w.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.w.set_position(Gtk.WindowPosition.CENTER)
        self.w.set_title("Continue?")
        self.w.set_default_size(500, 340)
        self.w.set_destroy_with_parent(True)
        self.w.set_resizable(False)
        self.classnetwork.StoreWindow.w.set_sensitive(False)
        self.w.connect('delete-event', self.close)
        
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path('/usr/share/feren-store-new/css/application.css')
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider,
                                          Gtk.STYLE_PROVIDER_PRIORITY_USER)
        
        mainwindow = Gtk.VBox()
        mainwindow.set_spacing(4)
        self.w.add(mainwindow)
        
        packagerealname = JSONReader().genericpkgdata[packagename]["realname"]
        
        if optype == "install":
            operationtext = "Install"
        elif optype == "remove":
            operationtext = "Remove"
        elif optype == "upgrade":
            operationtext = "Update"
        
        strlabelbox = Gtk.VBox()
        firststrlabel = ("%s %s?" % (operationtext, packagerealname))
        first_string = Gtk.Label(label=firststrlabel)
        first_string.get_style_context().add_class("14scale")
        first_string_box = Gtk.Box()
        first_string_box.pack_start(first_string, False, False, 0)
        second_string = Gtk.Label(label="It wants to make the following additional changes:")
        second_string_box = Gtk.Box()
        second_string_box.pack_start(second_string, False, False, 0)
        strlabelbox.pack_start(first_string_box, False, False, 0)
        strlabelbox.pack_start(second_string_box, False, False, 0)
        mainwindow.pack_start(strlabelbox, False, False, 0)
        
        # build scrolled window widget and add our appview container
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # build a an autoexpanding box and add our scrolled window
        b = Gtk.Box(homogeneous=False, spacing=4)
        b.pack_start(sw, expand=True, fill=True, padding=0)
        
        self.changes_list_box = Gtk.VBox()
        self.changes_list_box.set_spacing(4)
        sw.add(self.changes_list_box)
        
        self.tempdir = GlobalVariables().storagetemplocation
        
        thread = Thread(target=self.confirm_window_populate,
                        args=(packagesdisplayedinst, packagesdisplayedupgr, packagesdisplayedrm, packagename))
        thread.start()
        
        yesbtn = Gtk.Button(stock=Gtk.STOCK_YES)
        nobtn = Gtk.Button(stock=Gtk.STOCK_NO)
        
        yesbtn.connect('clicked', self.confirm, optype)
        nobtn.connect('clicked', self.reject_operation)
        
        buttonbox = Gtk.Box(spacing=4, homogeneous=True)
        buttonbox.pack_end(yesbtn, False, True, 0)
        buttonbox.pack_end(nobtn, False, True, 0)
        
        mainwindow.pack_end(buttonbox, False, True, 0)
        
        mainwindow.set_margin_bottom(8)
        mainwindow.set_margin_top(8)
        mainwindow.set_margin_left(10)
        mainwindow.set_margin_right(10)
        
        mainwindow.pack_end(b, True, True, 0)
        
        self.w.show_all()
        
    def get_img(self, iconuri, imageobj, loadingobj, loadingboxobj, imagestackobj, packagetoview):
        loadingobj.start()
        imagestackobj.set_visible_child(loadingboxobj)
                
        desired_width = 48
        desired_height = 48
        try:
            if not iconuri.startswith("file://"):
                #Download the application icon
                if not os.path.isfile(self.tempdir+"/"+packagetoview+"-icon"):
                    urllib.request.urlretrieve(iconuri, self.tempdir+"/"+packagetoview+"-icon")
                #Set it as the icon in the Store
                icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.tempdir+"/"+packagetoview+"-icon")
            else:
                #Set it as the icon in the Store
                icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file(iconuri.split('file://')[1])
        except Exception as exceptionstring:
            print("Could not retrieve icon -", exceptionstring)
            #TODO: Change to store-missing-icon
            icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file("/usr/share/icons/Inspire/256/apps/feren-store.png")
        icon_pixbuf = icon_pixbuf.scale_simple(desired_width, desired_height, GdkPixbuf.InterpType.BILINEAR)
        imageobj.set_from_pixbuf(icon_pixbuf)
        #The stacks randomly don't switch from loading to the icon object without this delay in place
        time.sleep(0.2)
        imagestackobj.set_visible_child(imageobj)
        loadingobj.stop()
        
    def confirm_window_populate(self, packagesdisplayedinst, packagesdisplayedupgr, packagesdisplayedrm, packagename):
        GLib.idle_add(self._confirm_window_populate, packagesdisplayedinst, packagesdisplayedupgr, packagesdisplayedrm, packagename)
        
    def _confirm_window_populate(self, packagesdisplayedinst, packagesdisplayedupgr, packagesdisplayedrm, packagename):
        desired_width = 48
        desired_height = 48
        self.icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file("/usr/share/feren-os/logos/blank.png")
        self.icon_pixbuf = self.icon_pixbuf.scale_simple(desired_width, desired_height, GdkPixbuf.InterpType.BILINEAR)
        
        packagesdisplayedinstbox = Gtk.VBox()
        if packagesdisplayedinst:
            for packagenm in packagesdisplayedinst:
                try:
                    box_application_icontext = Gtk.Box()
                    box_application_namedesc = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                    #Application Icon
                    app_iconimg = Gtk.Image()
                    
                    app_iconimg.set_from_pixbuf(self.icon_pixbuf)
                    
                    app_iconimg_loading = Gtk.Spinner()
                    app_iconimg_stack = Gtk.Stack()
                    app_iconimg_loading_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                    app_iconimg_loading_box.set_center_widget(app_iconimg_loading)
                    app_iconimg_stack.add_named(app_iconimg_loading_box, "Loading")
                    app_iconimg_stack.add_named(app_iconimg, "AppIcon")
                    app_iconimg_stack.set_visible_child(app_iconimg)
                    #Application Title
                    app_title = Gtk.Label()
                    app_title.get_style_context().add_class("12scale")
                    #Application Description
                    app_desc = Gtk.Label()
                    
                    app_title.set_label(self.classnetwork.JSONReader().genericpkgdata[packagenm]["realname"])
                    app_desc.set_label(self.classnetwork.JSONReader().genericpkgdata[packagenm]["shortdescription"])
                    
                    #Make sure application name and short descriptions are left-aligned in there
                    app_title_box = Gtk.Box()
                    app_desc_box = Gtk.Box()
                    app_title_box.pack_start(app_title, False, False, 0)
                    app_desc_box.pack_start(app_desc, False, False, 0)
                    
                    #Make the column for application name and short description
                    box_application_namedesc.pack_start(app_title_box, False, False, 0)
                    box_application_namedesc.pack_end(app_desc_box, False, False, 0)
                    
                    #Stuff for centering items vertically
                    centering_titledesc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                    centering_titledesc_box.set_center_widget(box_application_namedesc)
                    
                    #Structure building
                    box_application_icontext.pack_start(app_iconimg_stack, False, False, 0)
                    box_application_icontext.pack_start(centering_titledesc_box, False, True, 8)
                    
                    #Margins
                    app_iconimg.set_margin_top(8)
                    app_iconimg.set_margin_bottom(8)
                    
                    packagesdisplayedinstbox.pack_start(box_application_icontext, False, True, 0)
                    
                    Thread(target=self.get_img,
                                args=(self.classnetwork.JSONReader().genericpkgdata[packagenm]["iconurl"], app_iconimg, app_iconimg_loading, app_iconimg_loading_box, app_iconimg_stack, packagenm)).start()
                except:
                    pass
                    
            installedlabel = Gtk.Label(label="The following items will also be installed:")
            installedlabel.get_style_context().add_class("12scale")
            installedlabelbox = Gtk.Box()
            installedlabelbox.pack_start(installedlabel, False, False, 0)
            self.changes_list_box.pack_start(installedlabelbox, False, False, 4)
            self.changes_list_box.pack_start(packagesdisplayedinstbox, False, True, 0)
        
        packagesdisplayedupgrbox = Gtk.VBox()
        if packagesdisplayedupgr:
            for packagenm in packagesupgraded:
                try:
                    box_application_icontext = Gtk.Box()
                    box_application_namedesc = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                    #Application Icon
                    app_iconimg = Gtk.Image()
                    
                    app_iconimg.set_from_pixbuf(self.icon_pixbuf)
                    
                    app_iconimg_loading = Gtk.Spinner()
                    app_iconimg_stack = Gtk.Stack()
                    app_iconimg_loading_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                    app_iconimg_loading_box.set_center_widget(app_iconimg_loading)
                    app_iconimg_stack.add_named(app_iconimg_loading_box, "Loading")
                    app_iconimg_stack.add_named(app_iconimg, "AppIcon")
                    app_iconimg_stack.set_visible_child(app_iconimg)
                    #Application Title
                    app_title = Gtk.Label()
                    app_title.get_style_context().add_class("12scale")
                    #Application Description
                    app_desc = Gtk.Label()
                    
                    app_title.set_label(self.classnetwork.JSONReader().genericpkgdata[packagenm]["realname"])
                    app_desc.set_label(self.classnetwork.JSONReader().genericpkgdata[packagenm]["shortdescription"])
                    
                    #Make sure application name and short descriptions are left-aligned in there
                    app_title_box = Gtk.Box()
                    app_desc_box = Gtk.Box()
                    app_title_box.pack_start(app_title, False, False, 0)
                    app_desc_box.pack_start(app_desc, False, False, 0)
                    
                    #Make the column for application name and short description
                    box_application_namedesc.pack_start(app_title_box, False, False, 0)
                    box_application_namedesc.pack_end(app_desc_box, False, False, 0)
                    
                    #Stuff for centering items vertically
                    centering_titledesc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                    centering_titledesc_box.set_center_widget(box_application_namedesc)
                    
                    #Structure building
                    box_application_icontext.pack_start(app_iconimg_stack, False, False, 0)
                    box_application_icontext.pack_start(centering_titledesc_box, False, True, 8)
                    
                    #Margins
                    app_iconimg.set_margin_top(8)
                    app_iconimg.set_margin_bottom(8)
                    
                    packagesdisplayedupgrbox.pack_start(box_application_icontext, False, True, 0)
                    
                    packagesdisplayedupgr.append(packagenm)
                    
                    Thread(target=self.get_img,
                                args=(self.classnetwork.JSONReader().genericpkgdata[packagenm]["iconurl"], app_iconimg, app_iconimg_loading, app_iconimg_loading_box, app_iconimg_stack, packagenm)).start()
                except:
                    pass
                    
            upgradelabel = Gtk.Label(label="The following items will be updated:")
            upgradelabel.get_style_context().add_class("12scale")
            upgradelabelbox = Gtk.Box()
            upgradelabelbox.pack_start(upgradelabel, False, False, 0)
            self.changes_list_box.pack_start(upgradelabelbox, False, False, 4)
            self.changes_list_box.pack_start(packagesdisplayedupgrbox, False, True, 0)
        
        packagesdisplayedrmbox = Gtk.VBox()
        if packagesdisplayedrm:
            for packagenm in packagesremoved:
                try:
                    box_application_icontext = Gtk.Box()
                    box_application_namedesc = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                    #Application Icon
                    app_iconimg = Gtk.Image()
                    
                    app_iconimg.set_from_pixbuf(self.icon_pixbuf)
                    
                    app_iconimg_loading = Gtk.Spinner()
                    app_iconimg_stack = Gtk.Stack()
                    app_iconimg_loading_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                    app_iconimg_loading_box.set_center_widget(app_iconimg_loading)
                    app_iconimg_stack.add_named(app_iconimg_loading_box, "Loading")
                    app_iconimg_stack.add_named(app_iconimg, "AppIcon")
                    app_iconimg_stack.set_visible_child(app_iconimg)
                    #Application Title
                    app_title = Gtk.Label()
                    app_title.get_style_context().add_class("12scale")
                    #Application Description
                    app_desc = Gtk.Label()
                    
                    app_title.set_label(self.classnetwork.JSONReader().genericpkgdata[packagenm]["realname"])
                    app_desc.set_label(self.classnetwork.JSONReader().genericpkgdata[packagenm]["shortdescription"])
                    
                    #Make sure application name and short descriptions are left-aligned in there
                    app_title_box = Gtk.Box()
                    app_desc_box = Gtk.Box()
                    app_title_box.pack_start(app_title, False, False, 0)
                    app_desc_box.pack_start(app_desc, False, False, 0)
                    
                    #Make the column for application name and short description
                    box_application_namedesc.pack_start(app_title_box, False, False, 0)
                    box_application_namedesc.pack_end(app_desc_box, False, False, 0)
                    
                    #Stuff for centering items vertically
                    centering_titledesc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                    centering_titledesc_box.set_center_widget(box_application_namedesc)
                    
                    #Structure building
                    box_application_icontext.pack_start(app_iconimg_stack, False, False, 0)
                    box_application_icontext.pack_start(centering_titledesc_box, False, True, 8)
                    
                    #Margins
                    app_iconimg.set_margin_top(8)
                    app_iconimg.set_margin_bottom(8)
                    
                    packagesdisplayedrmbox.pack_start(box_application_icontext, False, True, 0)
                    
                    packagesdisplayedrm.append(packagenm)
                    
                    Thread(target=self.get_img,
                                args=(self.classnetwork.JSONReader().genericpkgdata[packagenm]["iconurl"], app_iconimg, app_iconimg_loading, app_iconimg_loading_box, app_iconimg_stack, packagenm)).start()
                except:
                    pass
                    
            removelabel = Gtk.Label(label="The following items will be removed:")
            removelabel.get_style_context().add_class("12scale")
            removelabelbox = Gtk.Box()
            removelabelbox.pack_start(removelabel, False, False, 0)
            self.changes_list_box.pack_start(removelabelbox, False, False, 4)
            self.changes_list_box.pack_start(packagesdisplayedrmbox, False, True, 0)
            
        self.changes_list_box.show_all()
    
    def confirm(self, btn, optype):
        if optype == "install":
            Thread(target=self.confirm_install,
                            args=()).start()
        elif optype == "upgrade":
            Thread(target=self.confirm_upgrade,
                            args=()).start()
        elif optype == "remove":
            Thread(target=self.confirm_remove,
                            args=()).start()
        self.w.destroy()
    
    def confirm_install(self):
        self.classnetwork.StoreWindow.w.set_sensitive(True)
        self.pkgmgmt.confirm_install_package(self.packagename)
    
    def confirm_upgrade(self):
        self.classnetwork.StoreWindow.w.set_sensitive(True)
        self.pkgmgmt.confirm_upgrade_package(self.packagename)
    
    def confirm_remove(self):
        self.classnetwork.StoreWindow.w.set_sensitive(True)
        self.pkgmgmt.confirm_remove_package(self.packagename)
    
    def reject_operation(self, btn):
        self.classnetwork.StoreWindow.w.set_sensitive(True)
        self.classnetwork.AppDetailsHeader.on_installer_finished(self.packagename)
        self.w.destroy()

    def close(self, p1, p2):
        self.classnetwork.StoreWindow.w.set_sensitive(True)
        self.classnetwork.AppDetailsHeader.on_installer_finished(self.packagename)