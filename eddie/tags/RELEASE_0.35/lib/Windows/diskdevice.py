## 
## File		: diskdevice.py 
## 
## Author       : Chris Miles - http://chrismiles.info/
## 
## Start Date	: 20050730
## 
## Description	: Eddie-Tool data collector for Win32 disk
##		  activity statistics.
##
## $Id$
##
########################################################################
## (C) Chris Miles 2005
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
  This is an Eddie data collector.  It collects disk activity
  statistics using win32perf.

  Requires Mark Hammond's win32all package.

  The DataCollectors provided are:
    DiskStatistics : collects statistics about disk devices
"""


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
