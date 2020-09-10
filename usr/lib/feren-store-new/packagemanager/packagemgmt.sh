#!/bin/bash

if [ "$1" == "snap" ]; then
    /usr/bin/python3 /usr/lib/feren-store-new/packagemanager/snapmgmt.py "$2" "$3"
    exit $?
fi
