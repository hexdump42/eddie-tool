## 
## File		: df.py 
## 
## Author(s)    : Rod Telford  <rtelford@eddie-tool.net>
##                Chris Miles  <chris@eddie-tool.net>
##                Dougal Scott
## 
## Start Date	: 19971204 
## 
## Description	: Library of classes that deal with a solaris df list
##
## $Id$
##
########################################################################
## (C) Chris Miles 2001-2004
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
  This is an Eddie data collector.  It collects filesystem usage statistics
  using a call to '/usr/bin/df'.

  It parses the output of '/usr/bin/df -g -l' so see df(1M) for more details.

  The following statistics are currently collected and made available to
  directives that request it (e.g., FS):

    fsname  - filesystem name (string)
    mountpt - mount point (string)
    size    - size of filesystem in kBytes (int)
    used    - kBytes used (int)
    avail   - kBytes free (int)
    pctused - percentage of filesystem used (float)
    totalblocks - total amount of physical blocks (512 Bytes/block) (int)
    usedblocks - number of physical blocks used (int)
    availblocks - number of physical blocks available for unprivileged users (int)
    freeblocks - number of physical blocks free (int)
    blocksize - filesystem (logical) block size (int)
    fragsize - filesystem fragmentation size (int)
    totalinodes - total inodes on filesystem (int)
    usedinodes - number of inodes used (int)
    availinodes - number of inodes left available (int)
    pctinodes - percentage of inodes used (float)
    filesysid - filesystem id (int)
    fstype - type of filesystem (string)
    flag - filesystem flags (string)
    filelen - max filename length (int)
"""


# Python Modules
import string
import re
# Eddie Modules
import datacollect
import log
import utils


class dfList(datacollect.DataCollect):
    """dfList provides access to disk usage statistics.
    """

    def __init__(self):
        apply( datacollect.DataCollect.__init__, (self,) )


    ##################################################################
    # Public, thread-safe, methods

    def __str__(self):
        """Create string to display disk usage stats.
	"""

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
            self.data_semaphore.acquire()       # thread-safe access to self.data
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
    	"""Collect full disk usage data
	"""

	# df -g -l : get detailed information for all local filesystems
	rawList = utils.safe_popen('/usr/bin/df -g -l', 'r')
	self.data.datahash = {}
	self.data.mounthash = {}
	data={}

	m1re = '(?P<mountpt>\S+)\s*\((?P<fsname>[^\)]+)\S*\):\s+(?P<blocksize>\d+) block size\s+(?P<fragsize>\d+) frag size'
	m2re = '\s*(?P<totalblocks>\d+) total blocks\s+(?P<freeblocks>\d+) free blocks\s+(?P<availblocks>\d+) available\s+(?P<totalfiles>\d+) total files'
	m3re = '\s*(?P<freefiles>\d+) free files\s+(?P<filesysid>\d+) filesys id.*'
	m4re = '\s*(?P<fstype>\S+) fstype \s+(?P<flag>\S+) flag\s+(?P<filelen>\d+) filename length'

	for line in rawList.readlines():
	    m1 = re.match( m1re, line )
	    if m1:
		data['mountpt'] = m1.group('mountpt').strip()
		data['fsname'] = m1.group('fsname').strip()
		data['blocksize'] = int(m1.group('blocksize'))	# filesystem (logical) block size
		data['fragsize'] = int(m1.group('fragsize'))
		continue

	    m2 = re.match( m2re, line )
	    if m2:
		data['totalblocks'] = int(m2.group('totalblocks')) # lots of physical block size (512B)
		data['size'] = data['totalblocks'] / 2				# kBytes
		data['freeblocks'] = int(m2.group('freeblocks'))
		data['usedblocks'] = data['totalblocks'] - data['freeblocks']
		data['used'] = data['usedblocks'] / 2				# kBytes
		data['availblocks'] = int(m2.group('availblocks'))
		data['avail'] = data['availblocks'] / 2				# kBytes
		data['totalinodes'] = int(m2.group('totalfiles'))
		# Some pseudo filesystems have no size (eg /proc)
		try:
		    data['pctused'] = 100.0 * data['usedblocks'] / data['totalblocks']
		except ZeroDivisionError:
		    data['pctused'] = 0.0
		continue

	    m3 = re.match( m3re, line )
	    if m3:
		data['availinodes'] = int(m3.group('freefiles'))
		data['usedinodes'] = data['totalinodes'] - data['availinodes']
		try:
		    data['pctinodes'] = 100.0 * data['usedinodes'] / data['totalinodes']
		except ZeroDivisionError:
		    data['pctinodes'] = 0.0
		data['filesysid'] = int(m3.group('filesysid'))
		continue

	    m4 = re.match(m4re, line)
	    if m4:
		data['fstype'] = m4.group('fstype')
		data['flag'] = m4.group('flag')
		data['filelen'] = int(m4.group('filelen'))
		continue

	    if line=='\n':		# empty line
		mount = df(data)	# so create df object
		self.data.mounthash[data['mountpt']] = mount
		self.data.datahash[data['fsname']] = mount
		data={}

	utils.safe_pclose( rawList )

        log.log( "<df>dfList.collectData(): collected data for %d filesystems" % (len(self.data.datahash.keys())), 6 )



class df:
    """df object holds stats on disk usage for a single filesystem.
    """

    def __init__(self, arg):
        self.data = arg


    def getHash(self):
        """Return a copy of the filesystem data dictionary.
        """

        return self.data.copy()


##
## END - df.py
##
