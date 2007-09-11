
'''
File                : netstat.py 

Start Date        : 19980122

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

__copyright__ = 'Copyright (c) Chris Miles 1998-2005'

__author__ = 'Chris Miles; Rod Telford'

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
import sys
import platform
# Eddie modules
import datacollect
import log
import utils


##
## Exceptions
##
 
class InterfaceError(Exception):
    """InterfaceError: could not create an Interface instance.
    """
    pass


##
## Classes
##

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
                continue                # should be 7 fields per line

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

        if len(fields) != 7:
            raise "Netstat Parse Error", "tcp class requires 7 fields, not %d" % (len(fields))

        # local address
        dot = string.rfind(fields[0], '.')
        if dot == -1:
            raise "Netstat Parse Error", "tcp, expected '<ip>.<port>', found '%s'" % (fields[0])
        self.local_addr_ip = fields[0][:dot]
        self.local_addr_port = fields[0][dot+1:]
        # CM 2004-05-16: convert '*' to standard wildcard address '0.0.0.0'
        if self.local_addr_ip == '*':
            self.local_addr_ip = '0.0.0.0'

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
        rawList = utils.safe_popen('netstat -anf inet -P udp', 'r')

        # skip header lines (4)
        rawList.readline()
        rawList.readline()
        rawList.readline()
        rawList.readline()

        for line in rawList.readlines():
            f = string.split(line)

            if len(f) != 2:
                continue                # should be 2 fields per line

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

        if len(fields) != 2:
            raise "Netstat Parse Error", "udp class requires 2 fields, not %d" % (len(fields))

        # local address
        dot = string.rfind(fields[0], '.')
        if dot == -1:
            raise "Netstat Parse Error", "udp, expected '<ip>.<port>', found '%s'" % (fields[0])
        self.local_addr_ip = fields[0][:dot]
        self.local_addr_port = fields[0][dot+1:]
        # CM 2004-05-16: convert '*' to standard wildcard address '0.0.0.0'
        if self.local_addr_ip == '*':
            self.local_addr_ip = '0.0.0.0'

        # state
        self.state = fields[1]



class IntTable(datacollect.DataCollect):
    """The network interface statistics Data Collector.
    Collects stats for every physical interface.
    It gets all interface names from 'netstat -in' call.
    Then for every physical (or non-logical) interface it fetches
    stats from a 'netstat -k <int>' call.
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

        self.data.phys_interfaces = []        # list of physical (non-logical) interface names
        self.data.datahash = {}                # hash of same objects keyed on interface name
        self.data.numinterfaces = 0
        interfacelines = {}

        # get list of network interfaces
        rawList = utils.safe_popen('netstat -in', 'r')

        # skip header line
        rawList.readline()

        # collect all non-logical interface names
        for line in rawList.readlines():
            f = string.split(line)
            if len(f) > 0 and ':' not in f[0]:
                # not a logical interface so remember it
                self.data.phys_interfaces.append( f[0] )
                interfacelines[f[0]] = line                # store the line to parse a little later

        utils.safe_pclose( rawList )

        # now collect stats for all interfaces found above
        for intname in self.data.phys_interfaces:
            try:
                newint = Interface( intname )                                # new Interface instance
                newint.parse_netstat_in( interfacelines[intname] )        # parse 'netstat -in' line
                newint.collect_stats()                                        # get stats from 'netstat -k'
                self.data.datahash[intname] = newint
                self.data.numinterfaces = self.data.numinterfaces + 1
            except InterfaceError, msg:
                log.log( "<netstat>IntTable.collectData(): Could not create interface for '%s', %s" %(intname,msg), 5 )

        log.log( "<netstat>IntTable.collectData(): Collected data for %d interfaces" %(self.data.numinterfaces), 6 )



class Interface:
    """An Interface instance represents one physical interface on the system
    and collects and stores information and statistics related to the interface.

    Use collect_stats() method to fetch stats from a 'netstat -k <int>' call.

    Use parse_netstat_in(line) to parse a 'netstat -in' output line and collect
    details (mtu, address, etc).

    TODO: use ndd to get physical interface settings, eg:
            ndd -set /dev/hme instance #
            ndd -get /dev/hme link_status
            ndd -get /dev/hme link_speed
            ndd -get /dev/hme link_mode
    """

    def __init__( self, name ):
        if not name:
            raise InterfaceError, "Interface name '%s' is invalid" %(name)

        self.name = name        # the interface name (e.g., hme0)
        self.stats = {}                # dictionary to hold all collected stats


    def collect_stats( self ):
        """Collect all the statistics from a call to 'netstat -k <intname>'.
        """

        if int(platform.release().split('.')[1]) <= 9:  # Sol <= 9
            # interfaces stats
            rawList = utils.safe_popen( '/usr/bin/netstat -k %s'%(self.name), 'r' )

            # skip header line - but bail if there is no output at all
            if not rawList.readline():
                utils.safe_pclose( rawList )
                #raise InterfaceError, "No stats for interface '%s'" %(name)
                return

            # collect all non-logical interface names
            for line in rawList.readlines():
                f = string.split(line)
                try:
                    d = dict( [(f[x],int(f[x+1])) for x in range(0, len(f), 2)] )
                    self.stats.update( d )
                except:
                    log.log( "<netstat>Interface.collect_stats(): Could not parse line (skipped), %s: %s" %(sys.exc_info()[0],line), 5 )

        else:        # Sol 10+
            # interfaces stats
            rawList = utils.safe_popen( '/usr/bin/kstat -p -c net -n %s'%(self.name), 'r' )

            # collect all non-logical interface names
            for line in rawList.readlines():
                try:
                    k,v = string.split(line)
                    interface,num,instance,key = string.split(k, ':')
                    self.stats[key] = v
                except ValueError:
                    pass
                except:
                    log.log( "<netstat>Interface.collect_stats(): Could not parse line (skipped), %s: %s" %(sys.exc_info()[0],line), 5 )

        utils.safe_pclose( rawList )


    def parse_netstat_in( self, line ):
        """Parse 'netstat -in' line and fetch interface details.
        """

        fields = line.split()

        if len( fields ) != 10:
            # expecting 10 fields per line
            log.log( "<netstat>Interface.parse_netstat_in(): Could not parse line (skipped), expected 10 fields: %s" %(line), 5 )
            return

        # mtu
        self.mtu = int(fields[1])

        # net/dest
        self.net = fields[2]

        # address
        self.address = fields[3]

        # queue
        self.queue = int(fields[9])


    def ifinfo( self ):
        """Return interface details & statistics as a dictionary.
        """

        info = {}
        info['name'] = self.name
        info['mtu'] = self.mtu
        info['net'] = self.net
        info['address'] = self.address
        info['queue'] = self.queue
        info.update( self.stats )

        # backwards compatability - support some older stats names
        if 'ipackets' in info.keys():
            info['ipkts'] = info['ipackets']
        else:
            info['ipkts'] = 0
        if 'opackets' in info.keys():
            info['opkts'] = info['opackets']
        else:
            info['opkts'] = 0
        if 'ierrors' in info.keys():
            info['ierrs'] = info['ierrors']
        else:
            info['ierrs'] = 0
        if 'oerrors' in info.keys():
            info['oerrs'] = info['oerrors']
        else:
            info['oerrs'] = 0
        if 'collisions' in info.keys():
            info['collis'] = info['collisions']
        else:
            info['collis'] = 0

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
        """
        Collect network statistics.
        """

        self.data.datahash = {}                        # hash of stats

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
