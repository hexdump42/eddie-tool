#!/opt/local/bin/python 
## 
## File		: proc.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 971203 
## 
## Description	: Library of classes that deal with a solaris proc list
##
## $Id$
##

import os
import string

##
## Class procList - instantiates with a list or procs running
##
class procList:
    def __init__(self):
	self.hash = {}		# dict of processes keyed by pid
	self.list = []		# list of processes
	self.nameHash = {}	# dict of processes keyed by process name
	 
	rawList = os.popen(' ps -e -o "pid user time pcpu s comm " ', 'r')
	rawList.readline()
 
	for line in rawList.readlines():
	    fields = string.split(line)
	    p = proc(fields)
	    self.list.append(p)
	    self.hash[fields[0]] = p
	    self.nameHash[p.command] = p

	
    def __str__(self):
	rv = 'PID     USER            COMMAND                 TIME            CPU     STATUS\n'
 	for item in self.list:
 	    rv = rv + str(item) + '\n'

	return(rv)
	    

    def keys(self):
        return(self.hash.keys())

    # Searches the 'ps' dictionary and returns number of occurrences of procname
    def procExists(self, procname):
	count = 0		# count number of occurrences of 'procname'
	for i in self.list:
	    if i.command == procname:
		count = count + 1

	return count

    # Overload '[]', eg: returns corresponding proc object for given process
    # name
    def __getitem__(self, name):
	try:
	    return self.nameHash[name]
	except KeyError:
	    return None


##
## Class proc : holds a process record
##
class proc:
    def __init__(self, *arg):
	self.raw = arg[0]

	try:
	    path = string.split(self.raw[5], "/")
	    comm = path[ len(path) - 1 ]
	except IndexError:
	    # This process has no command associated with it.  This can happen
	    # when a process is <defunct>.
	    # For now, let's call it "<defunct>"...
	    comm = '<defunct'

	self.pid = self.raw[0]		# pid
	self.user = self.raw[1]		# user
	self.time = self.raw[2]		# cpu time
	self.percent = self.raw[3]	# percentage of cpu
	self.status = self.raw[4]	# status
	self.command = comm		# command	


    def __str__(self):
	c = string.ljust(self.command, 20)
	u = string.ljust(self.user, 10)
	t = string.ljust(self.time, 10)

	return( '%s\t%s\t%s\t%s\t%s\t%s' % (self.pid, u, c, t, self.percent, self.status ) )

##
## END - proc.py
##
