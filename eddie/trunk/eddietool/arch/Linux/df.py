
'''
File                : df.py 

Start Date        : 20040506

Description        :
  This is an Eddie data collector.  It collects filesystem usage statistics
  using 'df'.

  The following statistics are currently collected and made available to
  directives that request it (e.g., FS):

    fs      - Filesystem name (string)
    size    - Size of filesystem (int)
    used    - kb used (int)
    avail   - kb free (int)
    pctused - Percentage Used (float)
    mountpt - Mount point (string)

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


# Python Modules
import re, string

# Eddie Modules
from eddietool.common import datacollect, log, utils


# This fetches data by parsing system calls of common commands.  This was done because
# it was quick and easy to implement and port to multiple platforms.  I know this is
# a bit ugly, but will clean it up later with more efficient code that fetches data
# directly from /proc or the kernel.  CM 19990929


class dfList(datacollect.DataCollect):
    """dfList provides access to disk usage statistics."""

    def __init__(self):
        apply( datacollect.DataCollect.__init__, (self,) )


    ##################################################################
    # Public, thread-safe, methods

    def __str__(self):
        """Create string to display disk usage stats."""

        d = self.getHash()

        rv = ""
        for item in d.keys():
            rv = rv + str(d[item]) + '\n'

        return(rv)


    def __getitem__(self, name):
        """
        Extends DataCollect.__getitem__() to search mounthash if default
        datahash fails.

        The dfList object can be treated like a dictionary and keyed by
        either device or mount point.
        """

        try:
            r = apply( datacollect.DataCollect.__getitem__, (self, name) )
        except KeyError:
            self.data_semaphore.acquire()        # thread-safe access to self.data
            try:
                r = self.data.mounthash[name]        # try to find mount point
            except KeyError:
                self.data_semaphore.release()
                raise KeyError, "Key %s not found in data hashes" % (name)
            self.data_semaphore.release()

        return r


    ##################################################################
    # Private methods.  No thread safety if not using public methods.

    def collectData(self):
        """
        Collect disk usage data.
        """

        # Get information about all local filesystems from 'df'.
        rawList = utils.safe_popen('df -l', 'r')
        rawList.readline()                        # skip header
 
        self.data.datahash = {}
        self.data.mounthash = {}

        lines = rawList.read()
        lines = re.sub( r'\n    ', '', lines)
        lines = string.split(lines, '\n')
        for line in lines:
            fields = string.split(line)
            if len(fields) == 6:
                p = df(fields)
                self.data.datahash[fields[0]] = p        # dictionary of filesystem devices
                self.data.mounthash[fields[5]] = p        # dictionary of mount points

        utils.safe_pclose( rawList )
        log.log( "<df>dfList.collectData(): filesystem data collected", 7 )


##################################################################
# Define single filesystem information objects.

class df:
    """df object holds stats on disk usage for a file system."""

    def __init__(self, *arg):
        self.raw = arg[0]

        self.data = {}
        self.data['fsname']  = self.raw[0]                # Filesystem name (device)
        self.data['size']    = int(self.raw[1])                # Size of filesystem
        self.data['used']    = int(self.raw[2])                # kb used
        self.data['avail']   = int(self.raw[3])                # kb free
        self.data['pctused'] = float(self.raw[4][:-1])        # Percentage Used
        self.data['mountpt'] = self.raw[5]                # Mount point


    def __str__(self):
        str = "%-20s %10s %10s %10s %4s %-12s\n" % ("Filesystem","Size","Used","Available","Use%","Mounted on")
        str = str + "%-20s %10s %10s %10s %4s %-12s" % (self.data['fsname'],self.data['size'],self.data['used'],self.data['avail'],self.data['pctused'],self.data['mountpt'])

        return(str)


    def getHash(self):
        """
        Return a copy of the filesystem data dictionary.
        """

        hash_copy = {}
        hash_copy.update(self.data)
        return hash_copy


##
## END - df.py
##
