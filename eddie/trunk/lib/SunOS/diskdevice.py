## 
## File		: diskdevice.py 
## 
## Author       : Chris Miles  <chris@psychofx.com>
## 
## Start Date	: 20041005
## 
## Description	: Eddie-Tool data collector for SunOS/Solaris disk
##		  activity statistics.
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
  This is an Eddie data collector.  It collects disk & tape -usage
  statistics using /usr/bin/kstat.

  See the stats available by looking at output of '/usr/bin/kstat -p -c disk'

  The DataCollectors provided are:
    DiskStatistics : collects statistics about disk devices
    TapeStatistics : collects statistics about tape devices
"""


# Python modules
import os
import string
# Eddie modules
import datacollect
import log
import utils


##
## Globals
##

KSTAT_CMD = '/usr/bin/kstat'
KSTAT_ARG = '-p -c '	# needs a class after it, eg: "disk" or "/tape|disk/"


##
## Exceptions
##
 

##
## Classes
##

class DiskStatistics(datacollect.DataCollect):
    """Collects disk statistics using: /usr/bin/kstat -p -c disk
    """

    def __init__(self):
        apply( datacollect.DataCollect.__init__, (self,) )

	self.kstat_class = "disk"	# default kstat class


    ##################################################################
    # Public methods


    ##################################################################
    # Private methods

    def collectData(self):

	self.data.datalist = []		# list of disk objects
	self.data.datahash = {}		# hash of same objects keyed on device name (eg: sd100, md10)
	self.data.numdisks = 0

	if not os.path.isfile( KSTAT_CMD ):
	    #log.log( "<diskdevice>DiskStatistics.collectData(): No kstat command '%s'" %(KSTAT_CMD), 4 )
	    raise datacollect.DataFailure, "No kstat command '%s'" %(KSTAT_CMD)

	# get the tcp stats
	cmd = "%s %s %s" % (KSTAT_CMD, KSTAT_ARG, self.kstat_class)
	rawList = utils.safe_popen( cmd, 'r' )

	for line in rawList.readlines():
	    try:
	        (keys,value) = string.split( line )
	    except ValueError:
		# should be 2 white-space separated fields per line
		log.log( "<diskdevice>DiskStatistics.collectData(): cannot parse kstat line '%s'" %(lines), 5 )
		continue

	    try:
		(type,index,name,key) = string.split( keys, ':' )
	    except ValueError:
		# should be 4 colon separated fields for keys
		log.log( "<diskdevice>DiskStatistics.collectData(): cannot parse kstat keys '%s'" %(keys), 5 )
		continue

	    try:
		# fetch already existing Disk object
	        disk = self.data.datahash[name]
	    except KeyError:
		# create new Disk object if needed
		disk = Disk( type, index, name )
	        self.data.datahash[name] = disk
	        self.data.datalist.append( disk )
	        self.data.numdisks = self.data.numdisks + 1

	    disk.setStat( key, value )

	utils.safe_pclose( rawList )

        log.log( "<diskdevice>DiskStatistics.collectData(): Collected stats for %d disks" %(self.data.numdisks), 6 )


class TapeStatistics(datacollect.DataCollect):
    """Collects tape statistics using: /usr/bin/kstat -p -c tape
    It uses a Disk object for the tape devices, as they are really
    the same data type.
    """

    def __init__(self):
        apply( datacollect.DataCollect.__init__, (self,) )

	self.kstat_class = "tape"	# default kstat class


    ##################################################################
    # Public methods


    ##################################################################
    # Private methods

    def collectData(self):

	self.data.datalist = []		# list of tape objects
	self.data.datahash = {}		# hash of same objects keyed on device name (eg: sd100, md10)
	self.data.numtapes = 0

	if not os.path.isfile( KSTAT_CMD ):
	    #log.log( "<diskdevice>TapeStatistics.collectData(): No kstat command '%s'" %(KSTAT_CMD), 4 )
	    raise datacollect.DataFailure, "No kstat command '%s'" %(KSTAT_CMD)

	# get the tcp stats
	cmd = "%s %s %s" % (KSTAT_CMD, KSTAT_ARG, self.kstat_class)
	rawList = utils.safe_popen( cmd, 'r' )

	for line in rawList.readlines():
	    try:
	        (keys,value) = string.split( line )
	    except ValueError:
		# should be 2 white-space separated fields per line
		log.log( "<diskdevice>TapeStatistics.collectData(): cannot parse kstat line '%s'" %(lines), 5 )
		continue

	    try:
		(type,index,name,key) = string.split( keys, ':' )
	    except ValueError:
		# should be 4 colon separated fields for keys
		log.log( "<diskdevice>TapeStatistics.collectData(): cannot parse kstat keys '%s'" %(keys), 5 )
		continue

	    try:
		# fetch already existing Disk object
	        tape = self.data.datahash[name]
	    except KeyError:
		# create new Disk object if needed
		tape = Disk( type, index, name )
	        self.data.datahash[name] = tape
	        self.data.datalist.append( tape )
	        self.data.numtapes = self.data.numtapes + 1

	    tape.setStat( key, value )

	utils.safe_pclose( rawList )

        log.log( "<diskdevice>TapeStatistics.collectData(): Collected stats for %d tapes" %(self.data.numtapes), 6 )



class Disk:
    """Holds information about a raw disk.
    A raw disk could actually be an ODS metadevice or some other logical
    volume or RAID array (or even tape device).
    """

    def __init__( self, type, index, name ):

	self.kstat_type = type		# eg, "sd" or "md"
	self.kstat_index = int(index)	# eg, 100
	self.name = name		# eg, "sd100" or "md50"
	self.stats = {}


    def setStat( self, key, value ):
	"""Set a statistic named key to value."""

	try:
	    propervalue = eval( value )	# convert to actual type (eg, int, float)
	except NameError:
	    propervalue = value		# otherwise leave as string

	self.stats[key] = propervalue


    def getHash( self ):
	"""Returns a dictionary of all the stats for this disk."""

	return self.stats.copy()


##
## END - diskdevice.py
##
