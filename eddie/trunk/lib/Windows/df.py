
'''
File		: df.py 

Start Date	: 20050629

Description	:
  This is an Eddie data collector.  It collects filesystem usage statistics
  using win32file.GetDiskFreeSpace()

  Requires Mark Hammond's win32all package.

  The following statistics are currently collected and made available to
  directives that request it (e.g., FS):

    fs      - Filesystem name (string)
    size    - Size of filesystem (int)
    used    - kB used (int)
    avail   - kB free (int)
    pctused - Percentage Used (int)
    mountpt - Mount point (string) [same as fs on Win32]

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


# Python Modules
import string
# Win32 Modules
import pywintypes
import win32file
import win32perf
# Eddie Modules
import datacollect
import log


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
        """Extends DataCollect.__getitem__() to search mounthash if default
	datahash fails.

	The dfList object can be treated like a dictionary and keyed by
	either device or mount point.
        """

	try:
	    r = apply( datacollect.DataCollect.__getitem__, (self, name) )
	except KeyError:
	    self.data_semaphore.acquire()	# thread-safe access to self.data
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
	"""Collect disk usage data.
	"""

	self.data.datahash = {}
	self.data.mounthash = {}

	drives = win32perf.getDriveNames(filter=(win32perf.DRIVE_FIXED,win32perf.DRIVE_REMOVABLE))
	drives = [d[:-1] for d in drives if d not in ('A:\\', 'B:\\')]	# remove '\'; ignore A: & B:

	for fs in drives:
	    try:
		fsinfo = win32file.GetDiskFreeSpace( fs+'\\' )
	    except pywintypes.error, err:
		log.log( "<df>dfList.collectData(): pywintypes.error, %s"%(err), 7 )
		continue	# skip invalid drives
	    assert len(fsinfo) == 4
	    p = df(fs, fsinfo)
	    self.data.datahash[fs] = p	# dictionary of filesystem devices
	    self.data.mounthash[fs] = p	# dictionary of mount points (hmm, same)

	log.log( "<df>dfList.collectData(): filesystem data collected", 7 )


##################################################################
# Define single filesystem information objects.

class df:
    """df object holds stats on disk usage for a file system."""

    def __init__(self, fsname, fsinfo):
	self.sectors_per_cluster = fsinfo[0]
	self.bytes_per_sector = fsinfo[1]
	self.free_clusters = fsinfo[2]
	self.total_clusters = fsinfo[3]

	self.data = {}
	self.data['fsname']  = fsname			# Filesystem name (device)
	self.data['size']    = self.total_clusters * self.bytes_per_sector * self.sectors_per_cluster / 1024	# Size of filesystem (kBytes)
	self.data['avail']   = self.free_clusters * self.bytes_per_sector * self.sectors_per_cluster / 1024	# kBytes free
	self.data['used']    = self.data['size'] - self.data['avail']	# kBytes used
	self.data['pctused'] = int(100.0 * self.data['used'] / self.data['size'])	# Percentage Used
	self.data['mountpt'] = fsname		# Mount point - same as fsname for Win32


    def __str__(self):
	str = "%-20s %10s %10s %10s %4s %-12s\n" % ("Filesystem","Size","Used","Available","Use%","Mounted on")
	str = str + "%-20s %10s %10s %10s %4s %-12s" % (self.data['fsname'],self.data['size'],self.data['used'],self.data['avail'],self.data['pctused'],self.data['mountpt'])

	return(str)


    def getHash(self):
	"""Return a copy of the filesystem data dictionary.
	"""

	return self.data.copy()


##
## END - df.py
##
