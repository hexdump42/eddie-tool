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
	self.hash = {}		# dict of bindings keyed by port
	self.list = []		# list of bindings

	self.regexp = ''
	 
	# ok first we want the tcp stats
	rawList = os.popen('netstat -anf inet | grep LISTEN', 'r')

	for line in rawList.readlines():
	    #print line
	    # fields = string.split(line)
	    # p = netstat(fields)
	    self.list.append(line)
	    # self.hash[p.port] = p

	# ok first we want the tcp stats
	rawList = os.popen('netstat -anf inet -P udp', 'r')

	# skip over header gumph
	rawList.readline()
	rawList.readline()
	rawList.readline()
	rawList.readline()

	for line in rawList.readlines():
	    #print line
	    self.list.append(line)

	# log.log( "<netstat>netstatList(), created new instance", 8 )
	
    def __str__(self):
	rv = ""
 	for item in self.list:
	    rv = rv + str(item)

	return(rv)
	    

    def keys(self):
        return(self.hash.keys())

    # Searches the 'ps' dictionary and returns number of occurrences of procname
#    def portExists(self, port):
#	count = 0		# count number of occurrences of 'procname'
#	for i in self.list:
#	    if i.port == port:
#		count = count + 1
#
#	return count

    # Overload '[]', eg: returns corresponding proc object for given process
    # name
    def __getitem__(self, port):
	try:
	    return self.hash[port]
	except KeyError:
	    return None

    def parseRaw(self):
	sre = regex.compile( self.regexp )
	inx = sre.search( self.raw )
	if inx == -1:
	    raise ParseFailure, "Error while parsing line: "+self.raw
	fieldlist = ()
	i=1

        while( sre.group(i) != None ):
	    fieldlist = fieldlist + (sre.group(i),)
	    i = i + 1

	return fieldlist



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
