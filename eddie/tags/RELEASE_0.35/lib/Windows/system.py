## 
## File		: system.py
## 
## Author       : Chris Miles http://chrismiles.info/
## 
## Start Date	: 20050709
## 
## Description	: Collect current snapshot of system stats for Win32
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
  This is an Eddie data collector.  It collects System data and statistics
  on a Win32 system.

  Requires Mark Hammond's win32all package.

  Data collectors provided by this module:
    - system: collects system stats.  See the class doc below for details
      of exactly which statistics are gathered and what they are called in
      the EDDIE environment.
"""


# Python modules
import string
import re
# Eddie modules
import datacollect
import log
import utils
import win32perf


COUNTERS = (
	( "System", "Context Switches/sec", None ),
	( "System", "System Calls/sec", None ),
	( "System", "Processes", None ),
	( "System", "System Up Time", None ),
	( "System", "Threads", None ),
	( "Processor", "% Processor Time", "_TOTAL" ),
	( "Processor", "% Idle Time", "_TOTAL" ),
	( "Processor", "% Interrupt Time", "_TOTAL" ),
	( "Processor", "% Privileged Time", "_TOTAL" ),
	( "Processor", "% User Time", "_TOTAL" ),
	( "Processor", "Interrupts/sec", "_TOTAL" ),
    )


class system(datacollect.DataCollect):
    """Gathers system statistics.

    Uses win32perf module which relies on win32pdh from
    Mark Hammond's win32all package.

    The names of all the stats collected by the system class are:

	"System Context Switches/sec"
	"System System Calls/sec"
	"System Processes"
	"System System Up Time"
	"System Threads"
	"Processor % Processor Time _TOTAL"
	"Processor % Idle Time _TOTAL"
	"Processor % Interrupt Time _TOTAL"
	"Processor % Privileged Time _TOTAL"
	"Processor % User Time _TOTAL"
	"Processor Interrupts/sec _TOTAL"
    """

    def __init__(self):
	apply( datacollect.DataCollect.__init__, (self,) )

	self.wp = None



    ##################################################################
    # Public, thread-safe, methods

    # none special to this class


    ##################################################################
    # Private methods.  No thread safety if not using public methods.

    def collectData(self):
        """Collect system statistics data.
        """

	self.data.datahash = {}		# dict of system data


	system_dict = self._getSystemStats()
	if system_dict:
	    self.data.datahash.update(system_dict)

        log.log( "<system>system.collectData(): collected data for %d system statistics" % (len(self.data.datahash.keys())), 6 )



    def _getSystemStats(self):
	"""Get system statistics from win32perf module.
	"""

	if not self.wp:
	    self.wp = win32perf.Win32Performance()
	    for object, counter, instance in COUNTERS:
		try:
		    self.wp.addCounter( object, counter, instance )
		except win32perf.Win32PerfError, err:
		    log.log( "<system>system._getSystemStats(): addCounter failed, %s" %(err), 5 )

	# re-use same wp every scan.
	# Note that Win32 appears to only update the statistics about once
	# per minute.
	perfcounters = self.wp.get()

	# Other method is to re-connect Win32Performance every time.
	#perfcounters = self.wp.get(pause=5)
	#self.wp.close()
	#self.wp = None

	return perfcounters


##
## END - system.py
##
