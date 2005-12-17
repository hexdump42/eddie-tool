
'''
File		: netstat.py 

Start Date	: 20050722

Description	:
  This is an Eddie data collector.  It collects Network-related statistics.
  It defines four Data Collectors:

  IntTable: collects network interface statistics.

  Requires Mark Hammond's win32all package.

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 2005'

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
# Eddie modules
import datacollect
import log
import utils
import win32perf
import pywintypes


COUNTERS = (
	( "Network Interface", "Bytes Received/sec" ),
	( "Network Interface", "Bytes Sent/sec" ),
	( "Network Interface", "Packets Outbound Errors" ),
	( "Network Interface", "Packets Received Errors" ),
	( "Network Interface", "Packets Received/sec" ),
	( "Network Interface", "Packets Sent/sec" ),
    )


class IntTable(datacollect.DataCollect):
    """The network interface statistics Data Collector.
    """

    def __init__(self):
	apply( datacollect.DataCollect.__init__, (self,) )

	self.wp = {}	# dictionary of wp queries keyed by instance


    ##################################################################
    # Public methods


    ##################################################################
    # Private methods

    def collectData(self):
	"""Collect network interface data.
	"""

	self.data.datahash = {}		# hash of same objects keyed on interface name
	self.data.numinterfaces = 0

	#interfaces = ( 'Intel[R] PRO_100 Network Connection - Packet Scheduler Miniport', 'ORiNOCO Wireless LAN Mini PCI Card - Packet Scheduler Miniport' )
	interfaces = win32perf.getInstances('Network Interface')

	for interface in interfaces:
	    netstats = self._getInterfaceStats( interface )
	    intf = Interface(interface, netstats)
	    self.data.datahash[intf.name] = intf
	    self.data.numinterfaces = self.data.numinterfaces + 1

	log.log( "<netstat>IntTable.collectData(): Collected data for %d interfaces" %(self.data.numinterfaces), 6 )


    def _getInterfaceStats(self, instance):
	"""Get system statistics from win32pdh module.
	"""

	perfcounters = {}

	if instance not in self.wp.keys():
	    wp = win32perf.Win32Performance()
	    self.wp[instance] = wp
	    for object, counter in COUNTERS:
		try:
		    wp.addCounter( object, counter, instance )
		except win32perf.Win32PerfError, err:
		    log.log( "<netstat>IntTable._getInterfaceStats(): addCounter failed, %s" %(err), 5 )

	# re-use same wp every scan.
	# Note that Win32 appears to only update the statistics about once
	# per minute.
	try:
	    perfcounters = self.wp[instance].get()
	except pywintypes.error, msg:
	    log.log( "<netstat>IntTable._getInterfaceStats(): failed wp.get(), %s" %(msg), 5 )

	return perfcounters


class Interface:
    """Holds information about a single network interface.
    """

    def __init__(self, name, stats):

	self.name = name

	self.rx_bytes		= stats.get( 'Network Interface Bytes Received/sec %s' %(name), None )
	self.rx_packets		= stats.get( 'Network Interface Packets Received/sec %s' %(name), None )
	self.rx_errs		= stats.get( 'Network Interface Packets Received Errors %s' %(name), None )

	self.tx_bytes		= stats.get( 'Network Interface Bytes Sent/sec %s' %(name), None )
	self.tx_packets		= stats.get( 'Network Interface Packets Sent/sec %s' %(name), None )
	self.tx_errs		= stats.get( 'Network Interface Packets Outbound Errors %s' %(name), None )


    def ifinfo(self):
	"""Return interface details as a dictionary."""

	info = {}

	info['name']		= self.name
	info['rx_bytes']	= self.rx_bytes
	info['rx_packets']	= self.rx_packets
	info['rx_errs']		= self.rx_errs

	info['tx_bytes']	= self.tx_bytes
	info['tx_packets']	= self.tx_packets
	info['tx_errs']		= self.tx_errs

	return info


##
## END - netstat.py
##
