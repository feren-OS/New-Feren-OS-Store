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
from subprocess import Popen, PIPE, STDOUT


def run_transaction(command, ontransfinished, onerror, ontransprogress, package):

    proc = Popen(command, bufsize=0, stdout=PIPE, stderr=STDOUT, close_fds=True)
    
    donothing = False

    for line in iter(proc.stdout.readline, b''):
        if donothing == False:
            output = line.decode("utf-8")
            if output.rstrip('\n') == "STOREDONE":
                donothing = True
            elif output.startswith("STORERRROR ["):
                onerror(output.rstrip('\n'), package)
                donothing = True
            elif output.rstrip('\n') != "STOREDONE" and not output.startswith("STOREERROR [") and output.rstrip('\n') != "":
                ontransprogress(output.rstrip('\n'))
    
    ontransfinished(package)

    proc.stdout.close()
    proc.wait()
