
'''
File                : diskdevice.py 

Start Date        : 20051021

Description        :
  **TODO: this is currently a place-holder - it does not yet do anything.**

  This is an Eddie data collector.  It collects disk & tape -usage
  statistics.

  The DataCollectors provided are:
    DiskStatistics : collects statistics about disk devices
    TapeStatistics : collects statistics about tape devices

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 2006'

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
import os
import string

# Eddie modules
from eddietool.common import datacollect, log, utils


from linux_diskio import linux_diskio


##
## Globals
##


##
## Exceptions
##
 

##
## Classes
##

class DiskStatistics(datacollect.DataCollect):
    """Collects disk statistics. TODO
    """

    def __init__(self):
        apply( datacollect.DataCollect.__init__, (self,) )


    ##################################################################
    # Public methods


    ##################################################################
    # Private methods

    def collectData(self):

        self.data.datahash = {}

        for device_name in linux_diskio.get_device_names():
            device_stats = linux_diskio.LinuxDiskIO(device_name)
            self.data.datahash[device_name] = Disk(device_name)
            self.data.datahash[device_name].setStats(device_stats.getStats())

        log.log( "<diskdevice>DiskStatistics.collectData(): collected stats for devices %s"%str(self.data.datahash.keys()), 6 )



class TapeStatistics(datacollect.DataCollect):
    """Collects tape statistics. TODO
    """

    def __init__(self):
        apply( datacollect.DataCollect.__init__, (self,) )


    ##################################################################
    # Public methods


    ##################################################################
    # Private methods

    def collectData(self):

        # *TODO*
        self.data.datahash = {}

        log.log( "<diskdevice>TapeStatistics.collectData(): *not yet implemented*", 5 )


class Disk:
    """Holds information about a raw disk device.
    """

    def __init__(self, name):
        self.name = name                # eg, "sd100" or "md50"
        self.stats = {}

    def setStats(self, stats):
        """Set the disk I/O statistics - a dict.
        """
        self.stats = stats

    def getHash( self ):
        """Returns a dictionary of all the stats for this disk."""
        return self.stats.copy()


##
## END - diskdevice.py
##
