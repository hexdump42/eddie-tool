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
import regex

##
## Class procList - instantiates with a list or procs running
##
class netstatList:
    def __init__(self):
	self.hash = {}		# dict of bindings keyed by port
	self.list = []		# list of bindings

	self.regexp = ''
	 
	# ok first we want the tcp stats
	rawList = os.popen('netstat -anf inet | grep LISTEN', 'r')

	for line in rawList.readlines():
	    f = string.split(line)

	    self.parseLine( f[0] )

	    self.proto = "tcp"
	    p = netstat(self.proto, self.port, self.host)

	    key = self.proto + self.port + self.host
	    self.hash[key] = p
	    self.list.append(p)

	# ok now we want the udp stuff
	rawList = os.popen('netstat -anf inet -P udp | grep Idle', 'r')

	for line in rawList.readlines():
	    f = string.split(line)

	    self.parseLine( f[0] )

	    self.proto = "udp"
	    p = netstat(self.proto, self.port, self.host)

	    key = self.proto + self.port + self.host
	    self.hash[key] = p
	    self.list.append(p)

	log.log( "<netstat>netstatList(), created new instance", 8 )
	
    def __str__(self):
	rv = ""
 	for item in self.list:
	    rv = rv + str(item)

	return(rv)
	    

    def keys(self):
        return(self.hash.keys())


    # Overload '[]', eg: returns corresponding proc object for given process
    # name
    def __getitem__(self, key):
	try:
	    return self.hash[key]
	except KeyError:
	    return None

    def portExists(self, proto, port, addr): 
	key = proto + str(port) + addr
	return self[key]
	

    def parseLine(self, line):
  	re  = '\([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\)\.\([0-9]+\)'
	sre = regex.compile( re )
	inx = sre.search( line )

	if inx == -1:
            re  = '\(\*\)\.\([0-9]+\)'
	    sre = regex.compile( re )
	    inx = sre.search( line )
	fieldlist = ()
	i=1


	if inx != -1:
	    self.host = sre.group(1)
	    self.port = sre.group(2)

##
## Class netstat : holds a netstat record
##
## shoud I split this into tcp and udp records?? or just have 
## the proto field??
##
class netstat:
    def __init__(self, *arg):

	self.proto = arg[0]	        # the proto UDP or TCP
	self.port  = arg[1]		# port this entry is listening to 
	self.addr  = arg[2]		# The address this port is bound to

    def __str__(self):
        str = self.proto + "/" + self.port + " bound to " + self.addr 
	return(str)

##
## END - netstat.py
##
