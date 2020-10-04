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
import pty


def run_transaction(command, ontransfinished, onerror, ontransprogress, package):

    master, slave = pty.openpty()
    proc = subprocess.Popen(command, bufsize=0, shell=False, stdout=slave, stderr=slave, close_fds=True)     
    stdout = os.fdopen(master, 'r')

    while proc.poll() is None:
        output = stdout.readline()
        if output != "":
            if output.rstrip('\n') == "STOREDONE":
                break
            elif output.startswith("STORERRROR ["):
                onerror(output.rstrip('\n'), package)
                break
            elif output.rstrip('\n') != "STOREDONE" and not output.startswith("STOREERROR [") and output.rstrip('\n') != "":
                ontransprogress(output.rstrip('\n'))
        else:
            break
    
    ontransfinished(package)

    stdout.close()
    proc.communicate()

    #Eh, just in case.
    os.close(slave)

    #TODO: Figure out WTF is keeping this running thus stopping the application from quitting
