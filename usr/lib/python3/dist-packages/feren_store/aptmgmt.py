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

import os
import apt
import aptdaemon.client
from aptdaemon.gtk3widgets import AptErrorDialog, AptProgressDialog
import aptdaemon.errors
import gettext
import subprocess

#if os.path.isfile("/usr/bin/snapd"):
#    from feren_store import snapmgmt
#if os.path.isfile("/usr/bin/flatpak"):
#    from feren_store import flatpakmgmt

t = gettext.translation('feren-store', '/usr/share/locale', fallback=True)
_ = t.gettext

#TODO: Put Snap permissions management in the Store settings

class APTChecks():
    def checkinstalled(package):
        output = subprocess.run(["/usr/lib/feren-store-new/check-updatable", package],
                            stdout=subprocess.PIPE).stdout.decode("utf-8")
        return output
