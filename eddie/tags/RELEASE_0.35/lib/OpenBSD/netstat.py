## 
## File		: netstat.py 
## 
## Author       : Chris Miles <chris@psychofx.com>
##              : John McInnes <john@dissension.net>
## 
## Start Date	: 20040522
## 
## Description	: Data Collectors for OpenBSD network statistics
##
## $Id$
##
########################################################################
## (C) Chris Miles 2004
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
  This is an Eddie data collector module.  It collects Network-related statistics.
  It defines four Data Collectors:

  TCPtable: collects list of current TCP connections.
  UDPtable: collects list of current UDP connections.
  IntTable: collects network interface statistics.
"""


# Python modules
import string
import re
# Eddie modules
import datacollect
import log
import utils



class TCPtable(datacollect.DataCollect):
    """Collects current TCP connections table.
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
	rawList = utils.safe_popen('netstat -anf inet | grep ^tcp | grep LISTEN', 'r')

	for line in rawList.readlines():
	    f = string.split(line)

	    if len(f) != 6:
		continue		# should be 6 fields per line

	    t = tcp(f)			# new tcp instance

	    self.data.datalist.append(t)
	    self.data.datahash['%s:%s' % (t.local_addr_ip,t.local_addr_port)] = t

	    self.data.numconnections = self.data.numconnections + 1

	utils.safe_pclose( rawList )

        log.log( "<netstat>TCPtable.collectData(): Collected %d TCP connections" %(self.data.numconnections), 6 )



class tcp:
    """Holds information about a single tcp connection.
    """

    def __init__(self, fields):

	if len(fields) != 6:
	    raise "Netstat Parse Error", "tcp class requires 6 fields, not %d" % (len(fields))

	# local address
	dot = string.rfind(fields[3], '.')
	if dot == -1:
	    raise "Netstat Parse Error", "tcp, expected '<ip>.<port>', found '%s'" % (fields[3])
	self.local_addr_ip = fields[3][:dot]
	self.local_addr_port = fields[3][dot+1:]
        if self.local_addr_ip == '*':
            self.local_addr_ip = '0.0.0.0'

	# remote address
	dot = string.rfind(fields[4], '.')
	if dot == -1:
	    raise "Netstat Parse Error", "tcp, expected '<ip>.<port>', found '%s'" % (fields[4])
	self.remote_addr_ip = fields[4][:dot]
	self.remote_addr_port = fields[4][dot+1:]

	# send queue size
	self.send_queue = int(fields[2])

	# receive queue size
	self.receive_queue = int(fields[1])

	# state
	self.state = fields[5]



class UDPtable(datacollect.DataCollect):
    """Collects current UDP connections table.
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
	rawList = utils.safe_popen('netstat -anf inet | grep ^udp', 'r')

	for line in rawList.readlines():
	    f = string.split(line)

	    if len(f) != 5:
		continue		# should be 2 fields per line

	    t = udp(f)			# new udp instance

	    self.data.datalist.append(t)
	    self.data.datahash['%s:%s' % (t.local_addr_ip,t.local_addr_port)] = t

	    self.data.numconnections = self.data.numconnections + 1

	utils.safe_pclose( rawList )

        log.log( "<netstat>UDPtable.collectData(): Collected %d UDP connections" %(self.data.numconnections), 6 )



class udp:
    """Holds information about a single udp connection.
    """

    def __init__(self, fields):

	if len(fields) != 5:
	    raise "Netstat Parse Error", "udp class requires 5 fields, not %d" % (len(fields))

	# local address
	dot = string.rfind(fields[3], '.')
	if dot == -1:
	    raise "Netstat Parse Error", "tcp, expected '<ip>.<port>', found '%s'" % (fields[3])
	self.local_addr_ip = fields[3][:dot]
	self.local_addr_port = fields[3][dot+1:]
        if self.local_addr_ip == '*':
            self.local_addr_ip = '0.0.0.0'

	# remote address
	dot = string.rfind(fields[4], '.')
	if dot == -1:
	    raise "Netstat Parse Error", "tcp, expected '<ip>.<port>', found '%s'" % (fields[4])
	self.remote_addr_ip = fields[4][:dot]
	self.remote_addr_port = fields[4][dot+1:]

	# send queue size
	self.send_queue = int(fields[2])

	# receive queue size
	self.receive_queue = int(fields[1])



class IntTable(datacollect.DataCollect):
    """The network interface statistics Data Collector.
    """

    def __init__(self):
        apply( datacollect.DataCollect.__init__, (self,) )


    ##################################################################
    # Public methods


    ##################################################################
    # Private methods

    def collectData(self):
        """Collect network interface data.
        """

	self.data.datahash = {}		# hash of same objects keyed on interface name
	self.data.numinterfaces = 0

	# get the interface packet stats
	rawList = utils.safe_popen('netstat -ind', 'r')

	for line in rawList.readlines():
	    f = string.split(line)

	    if len(f) != 10:
		continue		# should be 10 fields per line

	    # only want lines where Address is a valid IP address
	    int_re = "[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+"
	    sre = re.compile(int_re)
	    inx = sre.search( f[3] )
	    if inx != None:
		t = interface(f)		# new interface instance

		self.data.datahash[t.name] = t
		self.data.numinterfaces = self.data.numinterfaces + 1

	utils.safe_pclose( rawList )

	# get the interface bytes stats
	rawList = utils.safe_popen('netstat -inb', 'r')

	for line in rawList.readlines():
	    f = string.split(line)

	    if len(f) != 6:
		continue		# should be 6 fields per line

	    # only want lines where Address is a valid IP address
	    int_re = "[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+"
	    sre = re.compile(int_re)
	    inx = sre.search( f[3] )
	    if inx != None:
		# only want interfaces that were found above
		if f[0] in self.data.datahash.keys():
		    self.data.datahash[f[0]].interface_bytes(f)	# update interface data
		else:
		    log.log( "<netstat>IntTable.collectData(): interface mismatch in netstat -inb, %s" %(f[0]), 5 )

	utils.safe_pclose( rawList )


        log.log( "<netstat>IntTable.collectData(): Collected data for %d interfaces" %(self.data.numinterfaces), 6 )



class interface:
    """Holds information about a single network interface.
    """

    def __init__(self, fields):

	if len(fields) != 10:
	    raise "Netstat Parse Error", "interface class requires 9 fields, not %d" % (len(fields))

	# interface name address
	self.name = fields[0]

	# mtu
	self.mtu = int(fields[1])

	# net
	self.net = fields[2]

	# MAC address
	self.mac = fields[3]

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

	# drops
	self.drops = long(fields[9])

	# ibytes & obytes have to be collected by a separate netstat call
	self.ibytes = 0.0
	self.obytes = 0.0


    def ifinfo(self):
	"""Return interface details as a dictionary.
	"""

	info = {}
	info['name'] = self.name
	info['mtu'] = self.mtu
	info['net'] = self.net
	info['mac'] = self.mac
	info['ipkts'] = self.ipkts
	info['opkts'] = self.opkts
	info['ierrs'] = self.ierrs
	info['oerrs'] = self.oerrs
	info['collis'] = self.collis
	info['drops'] = self.drops
	info['ibytes'] = self.ibytes
	info['obytes'] = self.obytes

	return info


    def interface_bytes(self, fields):
	"""Update interface stats with bytes counters from a netstat -inb call.
	"""

	# ibytes
	self.ibytes = long(fields[4])

	# obytes
	self.obytes = long(fields[5])


##
## END - netstat.py
##
