## 
## File		: netstat.py 
## 
## Author       : Chris Miles  <chris@psychofx.com>
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

	# get the interface statistics
	fp = open('/proc/net/dev', 'r')

	# skip header lines
	fp.readline()
	fp.readline()

	for line in fp.readlines():
	    (name,data) = string.split( line, ':' )	# split interface name from data
	    f = string.split(data)

	    t = interface(f)		# new interface instance
	    if t == None:
		log.log( "<netstat>iftable, error parsing interface data for line '%s'"%(line), 5 )
		continue		# could not parse interface data

	    t.name = string.strip(name)

	    self.list.append(t)
	    self.hash[t.name] = t

	    self.numinterfaces = self.numinterfaces + 1		# count number of interfaces

	fp.close()


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

	if len(fields) != 16:
	    return None

	self.rx_bytes		= fields[0]
	self.rx_packets		= fields[1]
	self.rx_errs		= fields[2]
	self.rx_drop		= fields[3]
	self.rx_fifo		= fields[4]
	self.rx_frame		= fields[5]
	self.rx_compressed	= fields[6]
	self.rx_multicast	= fields[7]

	self.tx_bytes		= fields[8]
	self.tx_packets		= fields[9]
	self.tx_errs		= fields[10]
	self.tx_drop		= fields[11]
	self.tx_fifo		= fields[12]
	self.tx_colls		= fields[13]
	self.tx_carrier		= fields[14]
	self.tx_compressed	= fields[15]


    def ifinfo(self):
	"""Return interface details as a dictionary."""

	info = {}

	info['name']		= self.name
	info['rx_bytes']	= self.rx_bytes
	info['rx_packets']	= self.rx_packets
	info['rx_errs']		= self.rx_errs
	info['rx_drop']		= self.rx_drop
	info['rx_fifo']		= self.rx_fifo
	info['rx_frame']	= self.rx_frame
	info['rx_compressed']	= self.rx_compressed
	info['rx_multicast']	= self.rx_multicast

	info['tx_bytes']	= self.tx_bytes
	info['tx_packets']	= self.tx_packets
	info['tx_errs']		= self.tx_errs
	info['tx_drop']		= self.tx_drop
	info['tx_fifo']		= self.tx_fifo
	info['tx_colls']	= self.tx_colls
	info['tx_carrier']	= self.tx_carrier
	info['tx_compressed']	= self.tx_compressed

	return info




##
## END - netstat.py
##
