## 
## File		: netstat.py 
## 
## Author       : Rod Telford  <rtelford@codefx.com.au>
##                Chris Miles  <cmiles@codefx.com.au>
## 
## Date		: 980122
## 
## Description	: Library of classes that deal with a solaris netstat list
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

import os, string, re, time
import log, utils

##
## Class netstat - holds all information about current network information
##
class netstat:
    # refresh_rate : amount of time current process list will be cached before
    #                refreshing with new process list (in seconds)
    refresh_rate = 60


    def __init__(self):
        self.refresh_time = 0   # process list must be refreshed at first request


    def refresh(self):
        """Refresh the network stats tables"""

	self.tcptable = tcptable()	# get tcp connections table
	self.udptable = udptable()	# get udp connections table
	self.iftable = iftable()	# get interface table
	self.statstable = statstable()	# get network statistics table

        # new refresh time is current time + refresh rate (seconds)
        self.refresh_time = time.time() + self.refresh_rate


    def checkCache(self):
        """Check if cached data is invalid, ie: refresh_time has
        been exceeded."""

        if time.time() > self.refresh_time:
            log.log( "<netstat>checkCache(), refreshing network data", 7 )
            self.refresh()
        else:
            log.log( "<netstat>checkCache(), using cache'd network data", 7 )


    def __str__(self):
	str = "tcptable: %s udptable: %s iftable: %s statstable: %s" % (tcptable, udptable, iftable, statstable)
	return(str)


    def portExists(self, proto, port, addr): 
	"""Return tcp/udp object if it exists, else None."""

        self.checkCache()       # refresh process data if necessary

	key = "%s:%s" % (addr, port)
	if proto == 'tcp':
	    return self.tcptable[key]
	elif proto == 'udp':
	    return self.udptable[key]
	else:
	    log.log( "<netstat>netstat.portExists(), error, proto not supported '%s'" % (proto), 3 )
	    raise "Netstat Exception", "proto not supported '%s'" % (proto)
	

    def getInterface(self, name):
	"""Return an interface object if it exists, else None."""

        self.checkCache()       # refresh process data if necessary

	return self.iftable[name]


    def getAllInterfaces(self):
	"""Return a dictionary of all interfaces containing dictionaries of their stats."""

        self.checkCache()       # refresh process data if necessary

	ifdict = {}
	for i in self.iftable.keys():
	    ifdict[i] = {}				# make sure it is a copy of the data
	    ifdict[i].update(self.iftable[i].ifinfo())

	return ifdict


    def getNetworkStats(self):
	"""Return a dictionary of network statistics."""

	self.checkCache()	# refresh process data if necessary

	return self.statstable.getHash()


class tcptable:
    """Contains current tcp connections table."""
     
    def __init__(self):

	self.list = []			# list of tcp objects
	self.hash = {}			# hash of same objects keyed on '<ip>:<port>'
	self.numsockets = 0

	# get the tcp stats
	rawList = utils.safe_popen('netstat -anf inet -P tcp', 'r')

	# skip to start of TCP (solves bug in Solaris 2.5.1)
	line = rawList.readline()
	while line[:3] != 'TCP' and len(line) > 0:
	    line = rawList.readline()

	# skip header lines
	rawList.readline()
	rawList.readline()

	for line in rawList.readlines():
	    f = string.split(line)

	    if len(f) != 7:
		continue		# should be 7 fields per line

	    t = tcp(f)			# new tcp instance

	    self.list.append(t)
	    self.hash['%s:%s' % (t.local_addr_ip,t.local_addr_port)] = t

	    self.numsockets = self.numsockets + 1	# count number of tcp sockets

	utils.safe_pclose( rawList )


    def __getitem__(self, key):
	try:
	    return self.hash[key]
	except KeyError:
	    return None


class tcp:
    """Holds information about a single tcp connection."""

    def __init__(self, fields):

	if len(fields) != 7:
	    raise "Netstat Parse Error", "tcp class requires 7 fields, not %d" % (len(fields))

	# local address
	dot = string.rfind(fields[0], '.')
	if dot == -1:
	    raise "Netstat Parse Error", "tcp, expected '<ip>.<port>', found '%s'" % (fields[0])
	self.local_addr_ip = fields[0][:dot]
	self.local_addr_port = fields[0][dot+1:]

	# remote address
	dot = string.rfind(fields[1], '.')
	if dot == -1:
	    raise "Netstat Parse Error", "tcp, expected '<ip>.<port>', found '%s'" % (fields[1])
	self.remote_addr_ip = fields[1][:dot]
	self.remote_addr_port = fields[1][dot+1:]

	# send window (bytes)
	self.send_window = int(fields[2])

	# send queue size (bytes)
	self.send_queue = int(fields[3])

	# receive window (bytes)
	self.receive_window = int(fields[4])

	# receive queue size (bytes)
	self.receive_queue = int(fields[5])

	# state
	self.state = fields[6]



class udptable:
    """Contains current udp connections table."""
     
    def __init__(self):

	self.list = []			# list of tcp objects
	self.hash = {}			# hash of same objects keyed on '<ip>:<port>'
	self.numsockets = 0

	# get the udp stats
	rawList = utils.safe_popen('netstat -anf inet -P udp', 'r')

	# skip header lines (4)
	rawList.readline()
	rawList.readline()
	rawList.readline()
	rawList.readline()

	for line in rawList.readlines():
	    f = string.split(line)

	    if len(f) != 2:
		continue		# should be 2 fields per line

	    t = udp(f)			# new udp instance

	    self.list.append(t)
	    self.hash['%s:%s' % (t.local_addr_ip,t.local_addr_port)] = t

	    self.numsockets = self.numsockets + 1	# count number of tcp sockets

	utils.safe_pclose( rawList )


    def __getitem__(self, key):
	try:
	    return self.hash[key]
	except KeyError:
	    return None



class udp:
    """Holds information about a single udp connection."""

    def __init__(self, fields):

	if len(fields) != 2:
	    raise "Netstat Parse Error", "udp class requires 2 fields, not %d" % (len(fields))

	# local address
	dot = string.rfind(fields[0], '.')
	if dot == -1:
	    raise "Netstat Parse Error", "udp, expected '<ip>.<port>', found '%s'" % (fields[0])
	self.local_addr_ip = fields[0][:dot]
	self.local_addr_port = fields[0][dot+1:]

	# state
	self.state = fields[1]


class iftable:
    """Contains current network interface table."""
     
    def __init__(self):

	self.list = []			# list of interface objects
	self.hash = {}			# hash of same objects keyed on interface name (eg: 'hme0')
	self.numinterfaces = 0

	# get the interface stats
	rawList = utils.safe_popen('netstat -in', 'r')

	# skip header line
	rawList.readline()

	for line in rawList.readlines():
	    f = string.split(line)

	    if len(f) != 10:
		continue		# should be 10 fields per line

	    t = interface(f)		# new interface instance

	    self.list.append(t)
	    self.hash[t.name] = t

	    self.numinterfaces = self.numinterfaces + 1		# count number of interfaces

	utils.safe_pclose( rawList )


    def __getitem__(self, key):
	try:
	    return self.hash[key]
	except KeyError:
	    return None


    def keys(self):
	return self.hash.keys()



class interface:
    """Holds information about a single network interface."""

    def __init__(self, fields):

	if len(fields) != 10:
	    raise "Netstat Parse Error", "interface class requires 10 fields, not %d" % (len(fields))

	# interface name address
	self.name = fields[0]

	# mtu
	self.mtu = int(fields[1])

	# net/dest
	self.net = fields[2]

	# address
	self.address = fields[3]

	# input packets
	self.ipkts = long(fields[4])

	# input errors
	self.ierrs = long(fields[5])

	# output packets
	self.opkts = long(fields[6])

	# output errors
	self.oerrs = long(fields[7])

	# collisions
	self.collis = long(fields[8])

	# queue
	self.queue = long(fields[9])


    def ifinfo(self):
	"""Return interface details as a dictionary."""

	info = {}
	info['name'] = self.name
	info['mtu'] = self.mtu
	info['net'] = self.net
	info['address'] = self.address
	info['ipkts'] = self.ipkts
	info['ierrs'] = self.ierrs
	info['opkts'] = self.opkts
	info['oerrs'] = self.oerrs
	info['collis'] = self.collis
	info['queue'] = self.queue

	return info



class statstable:
    """Contains current network statistics table."""
     
    def __init__(self):

	self.hash = {}			# hash of stats

	# get the network stats
	rawList = utils.safe_popen('netstat -s', 'r')

	# regexp for pulling out stats
	udpre = "\s*(\w+)\s*=\s*([-0-9]+)(.*)"
	sre = re.compile(udpre)

	line = rawList.readline()
	while 1:
	    inx = sre.search( line )
	    if inx == None:
		log.log("<netstat>statstable.init() getting udp stats: no re match for line '%s'" % (line), 9)
		line = rawList.readline()
		if len(line) == 0:
		    break
	    else:
		self.hash[inx.group(1)] = long(inx.group(2))
		line = inx.group(3)

	utils.safe_pclose( rawList )


    def __getitem__(self, key):
	try:
	    return self.hash[key]
	except KeyError:
	    return None


    def getHash(self):
	"""Return a copy of the internal hash."""

	hashcopy = {}
	hashcopy.update(self.hash)

	return hashcopy


##
## END - netstat.py
##
