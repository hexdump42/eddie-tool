#!/opt/local/bin/python 
## 
## File		: proc.py 
## 
## Author	: Rod Telford 
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
	self.hash = {}
	self.list = []
	 
	rawList = os.popen(' ps -e -o "pid user comm time pcpu s" ', 'r')
	rawList.readline()
 
	for line in rawList.readlines():
	    fields = string.split(line)
	    p = proc(fields)
	    self.list.append(p)
	    self.hash[fields[0]] = p

	
    def __str__(self):
	rv = 'PID     USER            COMMAND                 TIME            CPU     STATUS\n'
 	for item in self.list:
 	    rv = rv + str(item) + '\n'

	return(rv)
	    

    def keys(self):
        return(self.hash.keys())

##
## Class proc : holds a process record
##
class proc:
    def __init__(self, *arg):
	self.raw = arg[0]

	path = string.split(self.raw[2], "/")
	comm = path[ len(path) - 1 ]
	     
	self.pid = self.raw[0]		# pid
	self.user = self.raw[1]		# user
	self.command = comm		# command	
	self.time = self.raw[3]		# cpu time
	self.percent = self.raw[4]	# percentage of cpu
	self.status = self.raw[5]	# status


    def __str__(self):
	c = string.ljust(self.command, 20)
	u = string.ljust(self.user, 10)
	t = string.ljust(self.time, 10)

	return( '%s\t%s\t%s\t%s\t%s\t%s' % (self.pid, u, c, t, self.percent, self.status ) )

##
## END - proc.py
##
