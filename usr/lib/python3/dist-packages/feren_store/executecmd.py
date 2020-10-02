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
                ontransfinished(package)
                break
            elif output.startswith("STORERRROR ["):
                onerror(output.rstrip('\n'), package)
                break
            elif output.rstrip('\n') != "STOREDONE" and not output.startswith("STOREERROR [") and output.rstrip('\n') != "":
                ontransprogress(output.rstrip('\n'))
        else:
            break

    #Eh, just in case.
    os.close(slave)
    os.close(master)
    
    proc.communicate()

    #Only way I found thus far to prevent Store from staying in the background and eating the CPU
    exit()
