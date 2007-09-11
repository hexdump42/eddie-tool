
'''
File                : netstat.py 

Start Date        : 19990929

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

__copyright__ = 'Copyright (c) Chris Miles 1999-2005'

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

# Eddie modules
from eddietool.common import datacollect, log, utils


# This fetches data by parsing system calls of common commands.  This was done because
# it was quick and easy to implement and port to multiple platforms.  I know this is
# a bit ugly, but will clean it up later with more efficient code that fetches data
# directly from /proc or the kernel.  CM 19990929



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
        self.data.datalist = []                        # list of TCP objects
        self.data.datahash = {}                        # hash of same objects keyed on '<ip>:<port>'
        self.data.numconnections = 0

        # get list of current TCP connections
        rawList = utils.safe_popen('netstat -an -t', 'r')

        # skip header line
        rawList.readline()

        for line in rawList.readlines():
            f = string.split(line)

            if len(f) != 6:
                continue                # should be 7 fields per line

            t = tcp(f)                        # new TCP instance

            self.data.datalist.append(t)
            self.data.datahash['%s:%s' % (t.local_addr_ip,t.local_addr_port)] = t

            self.data.numconnections = self.data.numconnections + 1        # count number of TCP connections

        utils.safe_pclose( rawList )

        log.log( "<netstat>TCPtable.collectData(): Collected %d TCP connections" %(self.data.numconnections), 6 )



class tcp:
    """
    Holds information about a single TCP connection.
    """

    def __init__(self, fields):

        if len(fields) != 6:
            raise "Netstat Parse Error", "tcp class requires 6 fields, not %d" % (len(fields))

        # fields[0] = 'tcp'

        # Recv-Q
        self.recv_q = int(fields[1])

        # Send-Q
        self.send_q = int(fields[2])

        # local address
        local_addr = string.split(fields[3], ':')
        if len(local_addr) == 2:
            (self.local_addr_ip, self.local_addr_port) = local_addr
        elif len(local_addr) == 4:
            (self.local_addr_ip, self.local_addr_port) = ('0.0.0.0', local_addr[3])
        elif len(local_addr) == 5:
            (self.local_addr_ip, self.local_addr_port) = (local_addr[3], local_addr[4])
        else:
            log.log( "<netstat>tcp: Could not parse local address: %s" % (fields), 5 )

        # foreign address
        foreign_addr = string.split(fields[4], ':')
        if len(foreign_addr) == 2:
            (self.foreign_addr_ip, self.foreign_addr_port) = foreign_addr
        elif len(foreign_addr) == 4:
            (self.foreign_addr_ip, self.foreign_addr_port) = ('0.0.0.0', foreign_addr[3])
        elif len(foreign_addr) == 5:
            (self.foreign_addr_ip, self.foreign_addr_port) = (foreign_addr[3], foreign_addr[4])
        else:
            log.log( "<netstat>tcp: Could not parse foreign address: %s" % (fields), 5 )

        # state
        self.state = fields[5]



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

        self.data.datalist = []                        # list of UDP objects
        self.data.datahash = {}                        # hash of same objects keyed on '<ip>:<port>'
        self.data.numconnections = 0

        # get the UDP stats
        rawList = utils.safe_popen('netstat -anA inet -u', 'r')

        # skip header lines (2)
        rawList.readline()
        rawList.readline()

        for line in rawList.readlines():
            f = string.split(line)

            if len(f) < 5 or len(f) > 6:
                continue                # should be 5 or 6 fields per line

            t = udp(f)                        # new udp instance

            self.data.datalist.append(t)
            self.data.datahash['%s:%s' % (t.local_addr_ip,t.local_addr_port)] = t

            self.data.numconnections = self.data.numconnections + 1        # count number of UDP connections

        utils.safe_pclose( rawList )

        log.log( "<netstat>UDPtable.collectData(): Collected %d UDP connections" %(self.data.numconnections), 6 )


class udp:
    """
    Holds information about a single UDP connection.
    """

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

        self.data.datahash = {}                # hash of same objects keyed on interface name
        self.data.numinterfaces = 0

        # get the interface statistics
        fp = open('/proc/net/dev', 'r')

        # skip header lines
        fp.readline()
        fp.readline()

        for line in fp.readlines():
            (name,data) = string.split( line, ':' )        # split interface name from data
            f = string.split(data)

            t = interface(f)                # new interface instance
            if t == None:
                log.log( "<netstat>iftable: error parsing interface data for line '%s'"%(line), 5 )
                continue                # could not parse interface data

            t.name = string.strip(name)

            self.data.datahash[t.name] = t

            self.data.numinterfaces = self.data.numinterfaces + 1        # count number of interfaces

        fp.close()

        log.log( "<netstat>IntTable.collectData(): Collected data for %d interfaces" %(self.data.numinterfaces), 6 )



class interface:
    """
    Holds information about a single network interface.
    """

    def __init__(self, fields):

        if len(fields) != 16:
            return None

        self.rx_bytes                = fields[0]
        self.rx_packets                = fields[1]
        self.rx_errs                = fields[2]
        self.rx_drop                = fields[3]
        self.rx_fifo                = fields[4]
        self.rx_frame                = fields[5]
        self.rx_compressed        = fields[6]
        self.rx_multicast        = fields[7]

        self.tx_bytes                = fields[8]
        self.tx_packets                = fields[9]
        self.tx_errs                = fields[10]
        self.tx_drop                = fields[11]
        self.tx_fifo                = fields[12]
        self.tx_colls                = fields[13]
        self.tx_carrier                = fields[14]
        self.tx_compressed        = fields[15]


    def ifinfo(self):
        """Return interface details as a dictionary."""

        info = {}

        info['name']                = self.name
        info['rx_bytes']        = self.rx_bytes
        info['rx_packets']        = self.rx_packets
        info['rx_errs']                = self.rx_errs
        info['rx_drop']                = self.rx_drop
        info['rx_fifo']                = self.rx_fifo
        info['rx_frame']        = self.rx_frame
        info['rx_compressed']        = self.rx_compressed
        info['rx_multicast']        = self.rx_multicast

        info['tx_bytes']        = self.tx_bytes
        info['tx_packets']        = self.tx_packets
        info['tx_errs']                = self.tx_errs
        info['tx_drop']                = self.tx_drop
        info['tx_fifo']                = self.tx_fifo
        info['tx_colls']        = self.tx_colls
        info['tx_carrier']        = self.tx_carrier
        info['tx_compressed']        = self.tx_compressed

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

        self.data.datahash = {}                        # hash of statistics

        # get the network statistics from /proc/net/snmp on Linux 2.x
        fp = open('/proc/net/snmp', 'r')

        line1 = fp.readline()                # read pairs
        line2 = fp.readline()                # of lines
        while len(line2) > 0:
            (proto1, stats_names) = string.split(line1, ':')
            (proto2, stats_values) = string.split(line2, ':')
            # both lines should have same protocol
            if proto1 != proto2:
                log.log( "<netstat>stats_ctrs.__init__(): error, protocol mis-match reading /proc/net/snmp for stats", 3 )
                raise "Netstat Error", "Error, protocol mis-match reading /proc/net/snmp for stats."
            stats_names = string.split(stats_names)        # convert to list
            stats_values = string.split(stats_values)        # convert to list
            # make sure lists are the same length
            if len(stats_names) != len(stats_values):
                log.log( "<netstat>stats_ctrs.__init__(): warning, list lengths differ, reading /proc/net/snmp for stats, stats_names=%s, stats_values=%s" % (stats_names,stats_values), 4 )
            else:
                for i in range(0, len(stats_names)):
                    self.data.datahash[proto1+stats_names[i]] = int(stats_values[i])

            line1 = fp.readline()                # read pairs
            line2 = fp.readline()                # of lines

        fp.close()

        log.log( "<netstat>stats_ctrs.collectData(): Collected %d network counters" %(len(self.data.datahash)), 6 )

##
## END - netstat.py
##
