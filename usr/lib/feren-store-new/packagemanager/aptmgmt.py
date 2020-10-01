#!/usr/bin/python3

###################################################################################
# APT Management Python Script - use me for percentage obtaining in-GUI           #
#                                                                                 #
#  Note: This was stupidly painful to get working, and took A LOT of attempts     #
#  so for your sanity please just use this as it is and don't bother with editing #
#  it, etc, unless you REALLY know what you're doing. Some credit goes to         #
#  https://github.com/schlomo/apt-install/blob/master/apt-install.py, by the way. #
###################################################################################

import sys
import os

from aptdaemon.client import AptClient
import aptdaemon.errors
import aptdaemon.enums
import gi
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
            print(e)

    def on_error(self, error):
        print("ERROR", str([aptdaemon.enums.get_error_string_from_enum(error.code), aptdaemon.enums.get_error_description_from_enum(error.code)]))

    def run_transaction(self):
        self.apt_transaction.connect("finished", self.on_transaction_finished)
        self.apt_transaction.connect("progress-changed", self.on_transaction_progress)
        self.apt_transaction.connect("error", self.on_transaction_error)
        self.apt_transaction.run(reply_handler=lambda: None, error_handler=self.on_error)
    
    def on_transaction_progress(self, apt_transaction, progress):
        if not apt_transaction.error:
            print(progress)

    def on_transaction_error(self, apt_transaction, error_code, error_details):
        print("ERROR", str([error_code, error_details]))

    def on_transaction_finished(self, apt_transaction, exit_state):
        print("DONE")
        self.loop.quit()
        

loop = GLib.MainLoop()
aptmgmt = APTMgmt()

def apt_install():
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


#Rule of Python: [0] counts as an item in the length count.
if len(sys.argv) != 3:
    print("ERROR ['incorrectargumentsnumber']")
    exit(1)
    
aptmgmt.packages = sys.argv[2:]
aptmgmt.loop = loop

if sys.argv[1] == "install":
    GLib.timeout_add(10000,apt_install)
elif sys.argv[1] == "upgrade":
    GLib.timeout_add(10000,apt_upgrade)
elif sys.argv[1] == "remove":
    GLib.timeout_add(10000,apt_remove)
    
    
loop.run()
