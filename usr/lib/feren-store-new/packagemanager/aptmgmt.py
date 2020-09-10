#!/usr/bin/python3

###################################################################################
# APT Management Python Script - use me for percentage obtaining in-GUI           #
###################################################################################

import sys
import os

import aptdaemon.client
import aptdaemon.errors
import aptdaemon.enums
import apt

inprogress = False
apt_client = aptdaemon.client.AptClient()


def progress_apt_cb(apt_transaction, progress):
    print(progress / 100)
    

def apt_run_transaction(apt_transaction):
    print(2)
    inprogress = True
    apt_transaction.connect("finished", on_transaction_finished)
    apt_transaction.connect("progress-changed", progress_apt_cb)
    apt_transaction.connect("error", on_transaction_error)
    apt_transaction.run(reply_handler=lambda: None, error_handler=on_error)


def apt_confirm_changes(apt_transaction):
    print(1)
    
    try:
        apt_run_transaction(apt_transaction)
    except Exception as e:
        print("1e", e)
        inprogress = False


def on_error(error):
    print(str("ERROR", [aptdaemon.enums.get_error_string_from_enum(error.code), aptdaemon.enums.get_error_description_from_enum(error.code)]))


def on_transaction_error(apt_transaction, error_code, error_details):
    on_error(apt_transaction.error)


def on_transaction_finished(apt_transaction, exit_state):
    # finished signal is always called whether successful or not
    # Only call here if we succeeded, to prevent multiple calls
    if (exit_state == aptdaemon.enums.EXIT_SUCCESS) or apt_transaction.error_code == "error-not-authorized":
        print("DONE")
        inprogress = False


def apt_install(packagename):
    print(0, packagename)
    apt_client.install_packages([packagename],
                                reply_handler=apt_confirm_changes,
                                error_handler=on_error) # dbus.DBusException
    while inprogress == False:
        pass
    while inprogress == True:
        pass
    

def apt_upgrade(packagename):
    apt_client.upgrade_packages([packagename],
                                reply_handler=apt_confirm_changes,
                                error_handler=on_error) # dbus.DBusException
    while inprogress == False:
        pass
    while inprogress == True:
        pass
    

def apt_remove(packagename):
    apt_client.remove_packages([packagename],
                                reply_handler=apt_confirm_changes,
                                error_handler=on_error) # dbus.DBusException
    while inprogress == False:
        pass
    while inprogress == True:
        pass


#Rule of Python: [0] counts as an item in the length count.
if len(sys.argv) != 3:
    print("Incorrect number of arguments.")
    exit(1)

if sys.argv[1] == "install":
    apt_install(sys.argv[2])
elif sys.argv[1] == "upgrade":
    apt_upgrade(sys.argv[2])
elif sys.argv[1] == "remove":
    apt_remove(sys.argv[2])