
'''
File                : netstat.py 

Start Date        : 20041206

Description        :
  This is an Eddie data collector.  It collects Network-related statistics.
  It defines four Data Collectors:

  TCPtable: collects list of current TCP connections.
  UDPtable: collects list of current UDP connections.
  IntTable: collects network interface statistics.
  stats_ctrs: collects network stats counters.

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 2004-2005'

__author__ = 'Chris Miles'

__license__ = '''
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
'''



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

        self.data.datalist = []                # list of tcp objects
        self.data.datahash = {}                # hash of same objects keyed on '<ip>:<port>'
        self.data.numconnections = 0

        # get the tcp stats
        rawList = utils.safe_popen('/usr/bin/netstat -anf inet -p tcp', 'r')

        # skip header lines
        rawList.readline()
        rawList.readline()

        for line in rawList.readlines():
            f = string.split(line)

            if len(f) != 6:
                continue                # should be 6 fields per line

            t = tcp(f)                        # new tcp instance

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

        # protcol
        self.protocol = fields[0]

        # receive queue size
        self.receive_queue = int(fields[1])

        # send queue size
        self.send_queue = int(fields[2])

        # local address
        dot = string.rfind(fields[3], '.')
        if dot == -1:
            raise "Netstat Parse Error", "tcp, expected '<ip>.<port>', found '%s'" % (fields[0])
        self.local_addr_ip = fields[3][:dot]
        self.local_addr_port = fields[3][dot+1:]
        # CM 2004-05-16: convert '*' to standard wildcard address '0.0.0.0'
        if self.local_addr_ip == '*':
            self.local_addr_ip = '0.0.0.0'

        # remote address
        dot = string.rfind(fields[4], '.')
        if dot == -1:
            raise "Netstat Parse Error", "tcp, expected '<ip>.<port>', found '%s'" % (fields[1])
        self.remote_addr_ip = fields[4][:dot]
        self.remote_addr_port = fields[4][dot+1:]

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

        self.data.datalist = []                # list of tcp objects
        self.data.datahash = {}                # hash of same objects keyed on '<ip>:<port>'
        self.data.numconnections = 0

        # get the udp stats
        rawList = utils.safe_popen('/usr/bin/netstat -anf inet -p udp', 'r')

        # skip header lines (2)
        rawList.readline()
        rawList.readline()

        for line in rawList.readlines():
            f = string.split(line)

            if len(f) != 5:
                continue                # should be 5 fields per line

            t = udp(f)                        # new udp instance

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

        # protocol
        self.protocol = fields[0]

        # receive queue size
        self.receive_queue = int(fields[1])

        # send queue size
        self.send_queue = int(fields[2])

        # local address
        dot = string.rfind(fields[3], '.')
        if dot == -1:
            raise "Netstat Parse Error", "udp, expected '<ip>.<port>', found '%s'" % (fields[0])
        self.local_addr_ip = fields[3][:dot]
        self.local_addr_port = fields[3][dot+1:]
        # CM 2004-05-16: convert '*' to standard wildcard address '0.0.0.0'
        if self.local_addr_ip == '*':
            self.local_addr_ip = '0.0.0.0'

        # remote address
        dot = string.rfind(fields[4], '.')
        if dot == -1:
            raise "Netstat Parse Error", "tcp, expected '<ip>.<port>', found '%s'" % (fields[1])
        self.remote_addr_ip = fields[4][:dot]
        self.remote_addr_port = fields[4][dot+1:]



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

        self.data.datahash = {}                # hash of same objects keyed on interface name
        self.data.numinterfaces = 0

        # get the interface stats
        rawList = utils.safe_popen('/usr/bin/netstat -in', 'r')

        # skip header line
        rawList.readline()

        for line in rawList.readlines():
            f = string.split(line)

            if len(f) != 9:
                continue                # should be 9 fields per line

            if string.find( f[2], "Link" ) == -1:
                continue                # only want real interfaces

            t = interface(f)                # new interface instance

            self.data.datahash[t.name] = t

            self.data.numinterfaces = self.data.numinterfaces + 1

        utils.safe_pclose( rawList )

        log.log( "<netstat>IntTable.collectData(): Collected data for %d interfaces" %(self.data.numinterfaces), 6 )



class interface:
    """Holds information about a single network interface.
    """

    def __init__(self, fields):

        if len(fields) != 9:
            raise "Netstat Parse Error", "interface class requires 9 fields, not %d" % (len(fields))

        # interface name address
        self.name = fields[0]

        # mtu
        self.mtu = int(fields[1])

        # network
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


    def ifinfo(self):
        """Return interface details as a dictionary.
        """

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

        return info



class stats_ctrs(datacollect.DataCollect):
    """Collect network statistics counters.
    """

    def __init__(self):
        apply( datacollect.DataCollect.__init__, (self,) )


    ##################################################################
    # Public methods


    ##################################################################
    # Private methods

    def collectData(self):
        """Collect network statistics.
        """

        self.data.datahash = {}                        # hash of stats

        # get the network stats
        rawList = utils.safe_popen('/usr/bin/netstat -s', 'r')

        # regexp for pulling out stats
        statsre = "\s*([0-9]+)\s*(.*)"
        sre = re.compile(statsre)

        line = rawList.readline()
        while 1:
            if len(line) == 0:
                break
            inx = sre.search( line )
            if inx != None:
                self.data.datahash[inx.group(2)] = long(inx.group(1))
            line = rawList.readline()

        utils.safe_pclose( rawList )

        log.log( "<netstat>stats_ctrs.collectData(): Collected %d network counters" %(len(self.data.datahash)), 6 )


##
## END - netstat.py
##
