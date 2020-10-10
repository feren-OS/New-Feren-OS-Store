# Feren Store

The Store application for Feren OS.

Currently a very huge work-in-progress and currently barely functional in functionality. Pending a lot of further development before it's considered ready.

---

Mockups:

https://github.com/feren-OS/Bug-Reporting-Center/issues/128#issuecomment-651418078

---

Ideas I want to implement into this application:

- [x] APT support
- [ ] DEB support
- [x] Flatpak support
- [x] Snap support
- [x] ICE SSBs Support
- [x] Add custom messages to command-not-found (nevermind, just used MITMs)
- [ ] Add FYI dialog when opening DEBs for packages already in the Store
- [ ] Support for KDE Store
- [x] Separate Games and Themes sections
- [ ] Updates section in Tasks/Installed
- [ ] Notifications for successful installs, updates now being available, installing system-wide automatic updates, etc.
- [x] Tasks management for queuing multiple install/remove/update/etc tasks at once
- [ ] Pre-defined application lists on the Home page for different topics
- [ ] Settings: Allow toggling of automatic updates
- [ ] Settings: Allow toggling and management of application sources
- [ ] Allow installation of programs that don't have their application sources enabled, but rename their Install buttons to 'Install...' and treat the application source as an extra '(pre-)dependency'
- [ ] Settings: Allow exporting and importing of 'application playlists' (a file that, when exported lists all of the things you installed in the Feren Store, and then imported adds everything in that list that is current available to that same installation queue)
- [ ] Restore Editors' Picks
- [ ] 'Noob Mode' where the sources dropdown next to Install buttons is hidden to prevent any confusion
- [ ] Add category for other non-curated Stores
- [ ] Add options for beta-testing certain applications (switch over to Beta)
- [ ] Allow easy control of important unattended-upgrades settings
- [ ] Snaps: ONLY allow Snaps that are known to be maintained by their official developers to be shown in the Store
- [ ] Allow the user, in an advanced setting, to turn the Store from curated only into show all available packages (low priority idea here)
- [ ] If this is on, any non-curated applications should have a persistent warning saying something along the lines of "This application is not curated by us. Feren OS's developers take no responsibility for any damage this package may do to your system. There is also no assurance that this application is officially maintained by its original developers. Please take caution when installing this application."
- [ ] 'Advanced Mode' where all dependencies are mentioned in the confirmation dialog

---

Current Status: Can install and remove APT packages in a queued task order
