## 
## File		: netstat.py 
## 
## Author       : Chris Miles  <cmiles@codefx.com.au>
## 
## Date		: 19990929
## 
## Description	: Library of classes that deal with a Linux netstat list
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

# This fetches data by parsing system calls of common commands.  This was done because
# it was quick and easy to implement and port to multiple platforms.  I know this is
# a bit ugly, but will clean it up later with more efficient code that fetches data
# directly from /proc or the kernel.  CM 19990929


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
	#self.statstable = statstable()	# get network statistics table

        # new refresh time is current time + refresh rate (seconds)
        self.refresh_time = time.time() + self.refresh_rate


    def checkCache(self):
        """Check if cached data is invalid, ie: refresh_time has
        been exceeded."""

        if time.time() > self.refresh_time:
            log.log( "<netstat>checkCache(), refreshing network data", 8 )
            self.refresh()
        else:
            log.log( "<netstat>checkCache(), using cache'd network data", 8 )


    def __str__(self):
	str = "tcptable: %s udptable: %s iftable: %s " % (tcptable, udptable, iftable)
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
	#rawList = os.popen('netstat -anA inet -t', 'r')
	rawList = utils.safe_popen('netstat -anA inet -t', 'r')

	# skip header line
	rawList.readline()

	for line in rawList.readlines():
	    f = string.split(line)

	    if len(f) != 6:
		continue		# should be 7 fields per line

	    t = tcp(f)			# new tcp instance

	    self.list.append(t)
	    self.hash['%s:%s' % (t.local_addr_ip,t.local_addr_port)] = t

	    self.numsockets = self.numsockets + 1	# count number of tcp sockets

	#rawList.close()
	utils.safe_pclose( rawList )


    def __getitem__(self, key):
	try:
	    return self.hash[key]
	except KeyError:
	    return None


class tcp:
    """Holds information about a single tcp connection."""

    def __init__(self, fields):

	if len(fields) != 6:
	    raise "Netstat Parse Error", "tcp class requires 6 fields, not %d" % (len(fields))

	# fields[0] = 'tcp'

	# Recv-Q
	self.recv_q = int(fields[1])

	# Send-Q
	self.send_q = int(fields[2])

	# local address
	(self.local_addr_ip, self.local_addr_port) = string.split(fields[3], ':')

	# foreign address
	(self.foreign_addr_ip, self.foreign_addr_port) = string.split(fields[4], ':')

	# state
	self.state = fields[5]



class udptable:
    """Contains current udp connections table."""
     
    def __init__(self):

	self.list = []			# list of tcp objects
	self.hash = {}			# hash of same objects keyed on '<ip>:<port>'
	self.numsockets = 0

	# get the udp stats
	#rawList = os.popen('netstat -anA inet -u', 'r')
	rawList = utils.safe_popen('netstat -anA inet -u', 'r')

	# skip header lines (2)
	rawList.readline()
	rawList.readline()

	for line in rawList.readlines():
	    f = string.split(line)

	    if len(f) < 5 or len(f) > 6:
		continue		# should be 5 or 6 fields per line

	    t = udp(f)			# new udp instance

	    self.list.append(t)
	    self.hash['%s:%s' % (t.local_addr_ip,t.local_addr_port)] = t

	    self.numsockets = self.numsockets + 1	# count number of tcp sockets

	#rawList.close()
	utils.safe_pclose( rawList )


    def __getitem__(self, key):
	try:
	    return self.hash[key]
	except KeyError:
	    return None



class udp:
    """Holds information about a single udp connection."""

    def __init__(self, fields):

	if len(fields) < 5 or len(fields) > 6:
	    raise "Netstat Parse Error", "udp class requires 5-6 fields, not %d" % (len(fields))

	# fields[0] = 'udp'

	# Recv-Q
	self.recv_q = int(fields[1])

	# Send-Q
	self.send_q = int(fields[2])

	# local address
	(self.local_addr_ip, self.local_addr_port) = string.split(fields[3], ':')

	# foreign address
	(self.foreign_addr_ip, self.foreign_addr_port) = string.split(fields[4], ':')

	# state
	if len(fields) > 5:
	    self.state = fields[5]
	else:
	    self.state = None



class iftable:
    """Contains current network interface table."""
     
    def __init__(self):

	self.list = []			# list of interface objects
	self.hash = {}			# hash of same objects keyed on interface name (eg: 'hme0')
	self.numinterfaces = 0

	# get the interface stats
	#rawList = os.popen('netstat -i', 'r')
	rawList = utils.safe_popen('netstat -i', 'r')

	# skip header lines
	rawList.readline()
	rawList.readline()

	for line in rawList.readlines():
	    f = string.split(line)

	    if len(f) != 12:
		continue		# should be 12 fields per line

	    t = interface(f)		# new interface instance

	    self.list.append(t)
	    self.hash[t.name] = t

	    self.numinterfaces = self.numinterfaces + 1		# count number of interfaces

	#rawList.close()
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

	if len(fields) != 12:
	    raise "Netstat Parse Error", "interface class requires 12 fields, not %d" % (len(fields))

	# interface name address
	self.name = fields[0]

	# mtu
	self.mtu = int(fields[1])

	# Met
	self.met = fields[2]

	# RX-OK
	self.rx_ok = fields[3]

	# RX-ERR
	self.rx_err = long(fields[4])

	# RX-DRP
	self.rx_drop = long(fields[5])

	# RX-OVR
	self.rx_over = long(fields[6])

	# TX-OK
	self.tx_ok = long(fields[7])

	# TX-ERR
	self.tx_err = long(fields[8])

	# TX-DRP
	self.tx_drp = long(fields[9])

	# TX-OVR
	self.tx_ovr = long(fields[10])

	# Flg
	self.flg = fields[11]


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




##
## END - netstat.py
##
