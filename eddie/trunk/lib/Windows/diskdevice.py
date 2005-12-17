
'''
File		: diskdevice.py 

Start Date	: 20050730

Description	:
  This is an Eddie data collector.  It collects disk activity
  statistics using win32perf.

  Requires Mark Hammond's win32all package.

  The DataCollectors provided are:
    DiskStatistics : collects statistics about disk devices

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
import win32perf


##
## Globals
##

COUNTERS = (
	( "PhysicalDisk", "Disk Read Bytes/sec" ),
	( "PhysicalDisk", "Disk Write Bytes/sec" ),
	( "PhysicalDisk", "Disk Reads/sec" ),
	( "PhysicalDisk", "Disk Writes/sec" ),
#	( "PhysicalDisk", "% Idle Time" ),
	( "PhysicalDisk", "% Disk Read Time" ),
	( "PhysicalDisk", "% Disk Write Time" ),
    )


##
## Exceptions
##
 

##
## Classes
##

class DiskStatistics(datacollect.DataCollect):
    """Collects disk statistics using win32perf.
    """

    def __init__(self):
        apply( datacollect.DataCollect.__init__, (self,) )

	self.disks = {}


    ##################################################################
    # Public methods


    ##################################################################
    # Private methods

    def collectData(self):

	self.data.datahash = {}
	self.data.numdisks = 0

	disks = win32perf.getInstances('PhysicalDisk')

	for disk in disks:
	    try:
		# fetch already existing Disk object
	        diskstats = self.disks[disk]
	    except KeyError:
		# create new Disk object if needed
		diskstats = Disk( disk )
		self.disks[disk] = diskstats
	    diskstats.update()		# update disk counters
	    self.data.datahash[disk] = diskstats
	    self.data.numdisks = self.data.numdisks + 1

        log.log( "<diskdevice>DiskStatistics.collectData(): collected data for %d disks" % (self.data.numdisks), 6 )



class Disk:
    """Holds information about a physical disk.
    This could also represent '_TOTAL' which is total counters across
    all physical disks.
    """

    def __init__( self, name ):

	self.name = name
	self.stats = {}
	self.wp = None


    def update( self ):
	"""Update stats with new stats from win32perf."""

	self.stats = self._getDiskStats()


    def getHash( self ):
	"""Returns a dictionary of all the stats for this disk."""

	return self.stats.copy()


    def _getDiskStats(self):
	"""Get disk statistics from win32perf module.
	"""

	if not self.wp:
	    self.wp = win32perf.Win32Performance()
	    instance = self.name
	    for object, counter in COUNTERS:
		try:
		    self.wp.addCounter( object, counter, instance )
		except win32perf.Win32PerfError, err:
		    log.log( "<diskdevice>Disk._getDiskStats(): addCounter failed, %s" %(err), 5 )

	# re-use same wp every scan.
	perfcounters = self.wp.get()

	# Other method is to re-connect Win32Performance every time.
	#perfcounters = self.wp.get(pause=5)
	#self.wp.close()
	#self.wp = None

	return perfcounters



##
## END - diskdevice.py
##
