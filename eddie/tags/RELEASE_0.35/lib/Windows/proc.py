## 
## File		: proc.py 
## 
## Author       : Chris Miles http://chrismiles.info/
## 
## Start Date	: 20050708 
## 
## Description	: Library of classes that deal with the process table for: Win32
##
## $Id$
##
########################################################################
## (C) Chris Miles 2005
##
## The author accepts no responsibility for the use of this software and
## provides it on an ``as is'' basis without express or implied warranty.
##
## Redistribution and use in source and binary forms are permitted
## provided that this notice is preserved and due credit is given
## to the original author and the contributors.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
########################################################################

"""
  This is an Eddie data collector.  It collects process information on
  a Win32 system.

  Requires Mark Hammond's win32all package.

  The following statistics are currently collected and made available to
  directives that request it (e.g., PROC):

  Stats available for processes are:
      pid		- Process ID [int]
      exe		- Full executable name [string]
      procname		- Base executable name (without path) [string]
"""


# Python modules
import os
# Win32 modules
import win32process
import win32api
import win32con
import pywintypes
# Eddie modules
import datacollect
import log


# List of interpreters - default empty - not used for Windows
interpreters = []

class procList(datacollect.DataCollect):
    """Class procList, holds a list of running processes and related information.
    """

    def __init__(self):
        apply( datacollect.DataCollect.__init__, (self,) )


    ##################################################################
    # Public, thread-safe, methods

    def procExists(self, procname):
        """Search the process list and return the number of occurrences
        of procname.
        """

        proclist = self.getList( 'proclist' )   # safely get copy of process list

        count = 0               # count number of occurrences of 'procname'
        for i in proclist:
            if i.procname == procname:
                count = count + 1

        return count


    def pidExists(self, pid):
        """Return true (1) if a process with 'pid' exists,
        or false (0) otherwise.
        """

        prochash = self.getHash( 'datahash' )   # safely get copy of process dict

        try:
            prochash[pid]
            return 1
        except KeyError:
            return 0


    def __getitem__(self, name):
        """Overload '[]' to return corresponding process object for given
        process name.

	Note that when processes are collected there may be multiple
	processes with the same name.  This dictionary only keeps a
	reference to one of those (no guarantee which one).
        """

        processes = self.getHash( 'nameHash' )  # safely get copy of process name dictionary

        try:
            r = processes[name]
        except KeyError:
            r = None            # no such process called 'name'

        return r


    def allprocs(self):
        """Return dictionary of all processes (which are dictionaries of each
        process' details).
        """

        processes = self.getHash( 'nameHash' )  # safely get copy of process name dictionary

        allprocs = {}

        for p in processes.keys():
            allprocs[p] = processes[p].procinfo()

        return allprocs


    ##################################################################
    # Private methods.  No thread safety if not using public methods.

    def collectData(self):
        """Collect process list.
        """

	self.data.datahash = {}		# dict of processes keyed by pid
	self.data.proclist = []		# list of processes
	self.data.nameHash = {}		# dict of processes keyed by process name

	procs = win32process.EnumProcesses()

	for pid in procs:
	    try:
		han = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION|win32con.PROCESS_VM_READ, 0, pid)
	    except:
		# privileges may prevent querying the process details
		han = None
	    p = proc(pid, han)

	    if han:
		han.Close()

	    self.data.proclist.append(p)
	    self.data.datahash[p.pid] = p
	    self.data.nameHash[p.procname] = p

	log.log( "<proc>procList.collectData(): new proc list created", 7 )



class proc:
    """Class proc : holds information about a single process.
    """

    def __init__(self, pid, han):

	if han:
	    try:
		exe = win32process.GetModuleFileNameEx(han, 0)
	    except pywintypes.error, msg:
		if msg[0] != 299 : # we keep getting this error for some reason..?
		    # Error is "Only part of a ReadProcessMemory or WriteProcessMemory request was completed."
		    log.log( "<proc>proc.__init__(): failed win32process.GetModuleFileNameEx(), %s" %(msg), 5 )
		exe = "<unknown>"
	else:
	    exe = "<unknown>"

	self.pid = pid			# process ID
	self.exe = exe			# full executable name (incl path)
	self.procname = os.path.basename(exe)	# executable name (no path)


    def procinfo(self):
	"""Return process details as a dictionary.
        """

	info = {}
	info["pid"] = self.pid
	info["exe"] = self.exe
	info["procname"] = self.procname

	return info


##
## END - proc.py
##
