## 
## File		: proc.py 
## 
## Author       : Rod Telford  <rtelford@psychofx.com>
##                Chris Miles  <chris@psychofx.com>
## 
## Date		: 971203 
## 
## Description	: Library of classes that deal with a machine's process table
##
## $Id$
##
########################################################################
## (C) Chris Miles 2001
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

import os, string, time, threading
import log, utils

# List of interpreters - default empty
interpreters = []

class procList:
    """Class procList - holds a list of running processes and related information."""

    # refresh_rate : amount of time current process list will be cached before
    #                refreshing with new process list (in seconds)
    refresh_rate = 60

    def __init__(self):
	self.refresh_time = 0	# process list must be refreshed at first request

	self.semaphore = threading.Semaphore()  # must be thread-friendly now


    ##################################################################
    # Public, thread-safe, methods

    def refresh(self):
	"""Force a refresh of the process list."""

	self.semaphore.acquire()
	self._refresh()
	self.semaphore.release()


    def procExists(self, procname):
	"""Searches the 'ps' dictionary and returns number of occurrences
	of procname."""

	self.semaphore.acquire()
	self._checkCache()	# refresh process data if necessary

	count = 0		# count number of occurrences of 'procname'
	for i in self.list:
	    command = string.split(i.comm, '/')[-1]
	    #if procname == 'radiusd':
		#print "command: '%16s'  i.procname: '%16s'  procname: '%16s'  i.comm: '%s'" % (command,i.procname,procname,i.comm)
	    if command == procname or i.procname == procname:
		#print "command: '%s' i.procname: '%s'  procname: '%s'" % (command,i.comm,procname)
		count = count + 1

	self.semaphore.release()

	return count


    def pidExists(self, pid):
        """Searches the 'ps' dictionary and returns number of occurrences
	of pid (should be 0 or 1 for any sane system...)"""

	self.semaphore.acquire()
	self._checkCache()	# refresh process data if necessary

	count = 0		# count number of occurrences of 'pid'
	for i in self.list:
	    if i.pid == pid:
		count = count + 1

	self.semaphore.release()

	return count


    def getList(self):
	"""Return copy of process list."""

	return self.list


    def __getitem__(self, name):
	"""Overload '[]', eg: returns corresponding proc object for given
	process name."""

	self.semaphore.acquire()
	self._checkCache()	# refresh process data if necessary

	try:
	    r = self.nameHash[name]
	except KeyError:
	    r = None

	self.semaphore.release()

	return r


    def allprocs(self):
	"""Return dictionary of all processes (which are dictionaries of each process' details."""

	self.semaphore.acquire()
	self._checkCache()	# refresh process data if necessary

	allprocs = {}

	for p in self.nameHash.keys():
	    allprocs[p] = self.nameHash[p].procinfo()

	self.semaphore.release()

	return allprocs


    def __str__(self):

	# note: don't do cache check - assume we want to display current data

	#rv = 'PID     USER            COMMAND                 TIME            CPU     STATUS\n'
	rv = ''

	self.semaphore.acquire()
 	for item in self.list:
 	    rv = rv + str(item) + '\n'
	self.semaphore.release()

	return(rv)


    ##################################################################
    # Private methods.  No thread safety if not using public methods.

    def _refresh(self):
	"""Refresh the process list"""

	self._getProcList()

	# new refresh time is current time + refresh rate (seconds)
	self.refresh_time = time.time() + self.refresh_rate


    def _checkCache(self):
	"""Check if cached procList data is invalid, ie: refresh_time has
	been exceeded."""

	if time.time() > self.refresh_time:
	    log.log( "<proc>_checkCache(), refreshing procList", 7 )
	    self._refresh()
	else:
	    log.log( "<proc>_checkCache(), using cache'd procList", 7 )


    def _getProcList(self):
	self.hash = {}		# dict of processes keyed by pid
	self.list = []		# list of processes
	self.nameHash = {}	# dict of processes keyed by process name
	 
	rawList = utils.safe_popen('ps -e -o "s user ruser group rgroup uid ruid gid rgid pid ppid pgid sid pri opri pcpu pmem vsz rss osz time etime stime f c tty addr nice class wchan fname comm args"', 'r')
	rawList.readline()
 
	for line in rawList.readlines():
	    p = proc(line)
	    self.list.append(p)
	    self.hash[p.pid] = p
	    #self.nameHash[string.split(p.comm, '/')[-1]] = p
	    self.nameHash[p.procname] = p

	utils.safe_pclose( rawList )

	log.log( "<proc>_procList(), new proc list created", 7 )



##
## Class proc : holds a process record
##
class proc:
    def __init__(self, rawline):

	fields = string.split(rawline)

	#self.pid = fields[0]		# pid
	#self.user = fields[1]		# user
	#self.time = fields[2]		# cpu time
	#self.percent = fields[3]	# percentage of cpu
	#self.status = fields[4]		# status
	#self.command = comm		# command	

	#log.log("<proc>proc.__init__(), fields: %s" % (fields), 8)


	self.s =       fields[ 0]       # state of the process
	self.user =    fields[ 1]       # effective user ID of the process (text or decimal)
	self.ruser =   fields[ 2]       # real user ID of the process (text or decimal)
	self.group =   fields[ 3]       # effective group ID of the process (text or decimal)
	self.rgroup =  fields[ 4]       # real group ID of the process (text or decimal)
	self.uid = int(fields[ 5])      # effective user ID number of the process as a decimal integer
	self.ruid =int(fields[ 6])      # real user ID number of the process as a decimal integer
	self.gid = int(fields[ 7])      # effective group ID number of the process as a decimal integer
	self.rgid =int(fields[ 8])      # real group ID number of the process as a decimal integer
	self.pid = int(fields[ 9])      # decimal value of the process ID
	self.ppid =int(fields[10])      # decimal value of the parent process ID
	self.pgid =int(fields[11])      # decimal value of the process group ID
	self.sid = int(fields[12])      # process ID of the session leader
	self.pri = int(fields[13])      # priority of the process
	self.opri =int(fields[14])      # obsolete priority of the process
	self.pcpu =float(fields[15])       # ratio of CPU time used recently to CPU time available in the same period, expressed as a percentage
	self.pmem =float(fields[16])       # ratio of the process's resident set size to the physical memory on the machine, expressed as a percentage
	self.vsz = int(fields[17])      # size of the process in (virtual) memory in kilobytes as a decimal integer
	self.rss = int(fields[18])      # resident set size of the process, in kilobytes as a decimal integer
	self.osz = int(fields[19])      # size (in pages) of the swappable process's image in main memory
	self.time =    fields[20]       # cumulative CPU time of the process in the form: [dd-]hh:mm:ss
	self.etime =   fields[21]       # elapsed time since the process was started, in the form: [[dd-]hh:]mm:ss
	self.stime =   fields[22]       # starting time or date of the process
	self.f =       fields[23]       # flags (hexadecimal and additive) associated with the process
	self.c =       fields[24]       # processor utilization for scheduling
	self.tty =     fields[25]       # name of the controlling terminal of the process (if any)
	self.addr =    fields[26]       # memory address of the process

	if self.s == 'Z':
	    # Zombied (or <defunct>) processes don't show any information after addr
	    self.nice =    ""
	    self.sclass =  ""
	    self.wchan =   ""
	    self.fname =   "<defunct>"
	    self.comm =    "<defunct>"
	    self.args =    "<defunct>"
	    self.procname = "<defunct>"
	else:
	    self.nice =    fields[27]       # decimal value of the system scheduling priority of the process
	    self.sclass =  fields[28]       # scheduling class of the process
	    self.wchan =   fields[29]       # address of an event for which the process is sleeping (if -, the process is running)
	    self.fname =   fields[30]       # first 8 bytes of the base name of the process's executable file
	    self.comm =    fields[31]       # name of the command being executed (argv[0] value) as a string
	    self.args =    string.join(fields[32:], " ")      # command with all its arguments as a string (truncated to 80 bytes in Solaris)

	    # Actual 'command' name with no path or interpreter - Eddie will mainly use this
	    self.procname = string.split(self.comm, '/')[-1]
	    if self.procname in interpreters:
		# this command is an interpreter (eg: 'perl', 'python', etc)
		# let's set procname to the name of the script (if there is a script)
		if len(fields) > 33:
		    i = 33
		    self.procname = string.split(fields[i], '/')[-1]
		    # ignore arguments (strings starting with '-')
		    try:
		        while self.procname[0] == '-':
			    i = i + 1
			    self.procname = string.split(fields[i], '/')[-1]
                    except IndexError:
			# can't determine procname.....
			self.procname = ''


    def __str__(self):
	# display process details (OLD, doesn't show many details)
	c = string.ljust(self.procname, 20)
	u = string.ljust(self.comm, 20)
	t = string.ljust(self.time, 10)

	#return( '%s\t%s\t%s\t%s\t%s\t%s' % (self.pid, u, c, t, self.percent, self.status ) )
	return( '%s\t%s\t%s\t%s\t%s\t%s' % (self.pid, u, c, t, self.pcpu, self.s) )


    def procinfo(self):
	"""Return process details as a dictionary."""

	info = {}
	info['s'] = self.s
	info['user'] = self.user
	info['ruser'] = self.ruser
	info['grp'] = self.group
	info['rgrp'] = self.rgroup
	info['uid'] = self.uid
	info['ruid'] = self.ruid
	info['gid'] = self.gid
	info['rgid'] = self.rgid
	info['pid'] = self.pid
	info['ppid'] = self.ppid
	info['pgid'] = self.pgid
	info['sid'] = self.sid
	info['pri'] = self.pri
	info['opri'] = self.opri
	info['pcpu'] = self.pcpu
	info['pmem'] = self.pmem
	info['vsz'] = self.vsz
	info['rss'] = self.rss
	info['osz'] = self.osz
	info['time'] = self.time
	info['etime'] = self.etime
	info['stime'] = self.stime
	info['f'] = self.f
	info['c'] = self.c
	info['tty'] = self.tty
	info['addr'] = self.addr
	info['nice'] = self.nice
	info['sclass'] = self.sclass
	info['wchan'] = self.wchan
	info['fname'] = self.fname
	info['comm'] = self.comm
	info['args'] = self.args
	info['procname'] = self.procname

	return info


##
## END - proc.py
##
