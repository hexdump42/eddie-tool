## 
## File		: netstat.py 
## 
## Author       : Rod Telford  <rtelford@psychofx.com>
##                Chris Miles  <chris@psychofx.com>
## 
## Start Date	: 19980122
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

"""
  This is an Eddie data collector.  It collects Network-related statistics.
  It defines four Data Collectors:

  TCPtable: collects list of current TCP connections.
  UDPtable: collects list of current UDP connections.
  IntTable: collects network interface statistics.
  stats_ctrs: collects network stats counters.
"""


# Python modules
import string, re
# Eddie modules
import datacollect, log, utils




class TCPtable(datacollect.DataCollect):
    """
    Collects current TCP connections table.
    """

    def __init__(self):
        apply( datacollect.DataCollect.__init__, (self,) )


    ##################################################################
    # Public methods


    ##################################################################
    # Private methods

    def collectData(self):

	self.data.datalist = []		# list of tcp objects
	self.data.datahash = {}		# hash of same objects keyed on '<ip>:<port>'
	self.data.numconnections = 0

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

	    self.data.datalist.append(t)
	    self.data.datahash['%s:%s' % (t.local_addr_ip,t.local_addr_port)] = t

	    self.data.numconnections = self.data.numconnections + 1

	utils.safe_pclose( rawList )

        log.log( "<netstat>TCPtable.collectData(): Collected %d TCP connections" %(self.data.numconnections), 6 )



class tcp:
    """
    Holds information about a single tcp connection.
    """

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



class UDPtable(datacollect.DataCollect):
    """
    Collects current UDP connections table.
    """

    def __init__(self):
        apply( datacollect.DataCollect.__init__, (self,) )


    ##################################################################
    # Public methods


    ##################################################################
    # Private methods

    def collectData(self):

	self.data.datalist = []		# list of tcp objects
	self.data.datahash = {}		# hash of same objects keyed on '<ip>:<port>'
	self.data.numconnections = 0

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

	    self.data.datalist.append(t)
	    self.data.datahash['%s:%s' % (t.local_addr_ip,t.local_addr_port)] = t

	    self.data.numconnections = self.data.numconnections + 1

	utils.safe_pclose( rawList )

        log.log( "<netstat>UDPtable.collectData(): Collected %d UDP connections" %(self.data.numconnections), 6 )



class udp:
    """
    Holds information about a single udp connection.
    """

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



class IntTable(datacollect.DataCollect):
    """
    The network interface statistics Data Collector.
    """

    def __init__(self):
        apply( datacollect.DataCollect.__init__, (self,) )


    ##################################################################
    # Public methods


    ##################################################################
    # Private methods

    def collectData(self):
        """
        Collect network interface data.
        """

	self.data.datahash = {}		# hash of same objects keyed on interface name
	self.data.numinterfaces = 0

	# get the interface stats
	rawList = utils.safe_popen('netstat -in', 'r')

	# skip header line
	rawList.readline()

	for line in rawList.readlines():
	    f = string.split(line)

	    if len(f) != 10:
		continue		# should be 10 fields per line

	    t = interface(f)		# new interface instance

	    self.data.datahash[t.name] = t

	    self.data.numinterfaces = self.data.numinterfaces + 1

	utils.safe_pclose( rawList )

        log.log( "<netstat>IntTable.collectData(): Collected data for %d interfaces" %(self.data.numinterfaces), 6 )



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



class stats_ctrs(datacollect.DataCollect):
    """
    Collect network statistics counters.
    """

    def __init__(self):
        apply( datacollect.DataCollect.__init__, (self,) )


    ##################################################################
    # Public methods


    ##################################################################
    # Private methods

    def collectData(self):
        """
        Collect network statistics.
        """

	self.data.datahash = {}			# hash of stats

	# get the network stats
	rawList = utils.safe_popen('netstat -s', 'r')

	# regexp for pulling out stats
	udpre = "\s*(\w+)\s*=\s*([-0-9]+)(.*)"
	sre = re.compile(udpre)

	line = rawList.readline()
	while 1:
	    inx = sre.search( line )
	    if inx == None:
		#log.log("<netstat>stats_ctrs: getting udp stats, no re match for line '%s'" % (line), 9)
		line = rawList.readline()
		if len(line) == 0:
		    break
	    else:
		self.data.datahash[inx.group(1)] = long(inx.group(2))
		line = inx.group(3)

	utils.safe_pclose( rawList )

        log.log( "<netstat>stats_ctrs.collectData(): Collected %d network counters" %(len(self.data.datahash)), 6 )


##
## END - netstat.py
##
