#!/opt/local/bin/python 
## 
## File		: netstat.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 980122
## 
## Description	: Library of classes that deal with a solaris netstat list
##
## $Id$
##

import os
import string
import log

##
## Class procList - instantiates with a list or procs running
##
class netstatList:
    def __init__(self):
	self.hash = {}		# dict of processes keyed by pid
	self.list = []		# list of processes
	 
	rawList = os.popen('netstat -anf inet', 'r')
	rawList.readline()
 
	for line in rawList.readlines():
	    fields = string.split(line)
	    p = netstat(fields)
	    self.list.append(p)
	    self.hash[p.port] = p

	log.log( "<netstat>netstatList(), created new instance", 8 )
	
    def __str__(self):
 	for item in self.list:
 	    rv = rv + str(item) + '\n'

	return(rv)
	    

    def keys(self):
        return(self.hash.keys())

    # Searches the 'ps' dictionary and returns number of occurrences of procname
    def portExists(self, port):
	count = 0		# count number of occurrences of 'procname'
	for i in self.list:
	    if i.port == port:
		count = count + 1

	return count

    # Overload '[]', eg: returns corresponding proc object for given process
    # name
    def __getitem__(self, port):
	try:
	    return self.hash[port]
	except KeyError:
	    return None


##
## Class netstat : holds a netstat record
##
## shoud I split this into tcp and udp records?? or just have 
## the proto field??
##
class netstat:
    def __init__(self, *arg):
	self.raw = arg[0]

	self.port = self.raw[0]		# port this entry is listening to 
	self.proto = self.raw[1]	# the proto UDP or TCP
	self.addr = self.raw[2]		# The address this port is bound to

    def __str__(self):
	return(self.raw )

##
## END - netstat.py
##
