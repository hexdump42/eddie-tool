## 
## File		: df.py 
## 
## Author       : Rod Telford  <rtelford@codefx.com.au>
##                Chris Miles  <cmiles@codefx.com.au>
## 
## Start Date	: 19971204 
## 
## Description	: Library of classes that deal with a solaris df list
##
## $Id$
##
########################################################################
## (C) Chris Miles 2001
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

# Python Modules
import os, string, threading, time
# Eddie Modules
import log, history, utils

class dfList:
    """dfList is a thread-friendly object providing access to disk usage statistics."""

    # refresh_rate : amount of time data will be cached before refreshing (in seconds)
    refresh_rate = 60

    def __init__(self):
        self.refresh_time = 0   # data must be refreshed at first request
        self.semaphore = threading.Semaphore()  # lock before accessing data
	self.dfheader = ""


    ##################################################################
    # Public, thread-safe, methods

    def refresh(self):
        """Force a refresh of the data."""

        self.semaphore.acquire()
        self._refresh()
        self.semaphore.release()


    def keys(self):
	"""Return the current list of filesystems."""

	self.semaphore.acquire()
	self._checkCache()      # refresh data if necessary
	k = self.hash.keys()
	self.semaphore.release()

        return(k)


    def __str__(self):
	"""Create string to display disk usage stats."""

	self.semaphore.acquire()
	self._checkCache()      # refresh data if necessary
	rv = self.dfheader
 	for item in self.list:
 	    rv = rv + str(item) + '\n'
	self.semaphore.release()

	return(rv)


    def __getitem__(self, name):
	"""
        Overload '[]', eg: returns corresponding df object for given filesystem
        device - if there isn't one, will try to find a df object based on the
        mount point.  If both fail, returns None.
	"""

	self.semaphore.acquire()
	self._checkCache()      	# refresh data if necessary
        try:
            r = self.hash[name]		# try to find filesystem device
        except KeyError:
	    try:
		r = self.mounthash[name]	# try to find mount point
	    except KeyError:
		r = None		# not found
	self.semaphore.release()

	return r


    ##################################################################
    # Private methods.  No thread safety if not using public methods.

    def _refresh(self):
	"""Refresh disk usage data."""

	# List all UFS and VXFS filesystems
	# Note: we don't bother with NFS filesystems at this point.
	# TODO: allow user-specified filesystem types
	rawList = utils.safe_popen('/usr/bin/df -kFufs | grep -v Filesystem ; /usr/bin/df -kFvxfs | grep -v Filesystem', 'r')

	self.list = []
	self.hash = {}
	self.mounthash = {}

	for line in rawList.readlines():
	    fields = string.split(line)
	    p = df(fields)
	    self.list.append(p)
	    self.hash[fields[0]] = p		# dict of filesystem devices
	    self.mounthash[fields[5]] = p	# dict of mount points

	utils.safe_pclose( rawList )

        # new refresh time is current time + refresh rate (seconds)
        self.refresh_time = time.time() + self.refresh_rate


    def _checkCache(self):
        """Check if cached data is invalid, ie: refresh_time has
        been exceeded."""

        if time.time() > self.refresh_time:
            log.log( "<df>dfList._checkCache(), refreshing dfList", 7 )
            self._refresh()
        else:
            log.log( "<df>dfList._checkCache(), using cache'd dfList", 7 )



class df:
    """df object holds stats on disk usage."""

    def __init__(self, *arg):
	self.raw = arg[0]

	self.fs      = self.raw[0]	# Filesystem
	self.size    = self.raw[1]	# Size of filesystem
	self.used    = self.raw[2]	# kb used
	self.avail   = self.raw[3]	# kb free
	self.pctused = self.raw[4][:-1]	# Percentage Used
	self.mountpt = self.raw[5]	# Mount point

	prevdf = history.eddieHistory.list('FS')
	if prevdf == []:
	    # No history - deltas are 0
	    self.usedDelta = "0"
	    self.availDelta = "0"
	    self.pctusedDelta = "0"
	else:
	    try:
		self.usedDelta = "%d" % (string.atoi(self.used) - string.atoi(prevdf[self.fs].getUsed()))
		self.availDelta = "%d" % (string.atoi(self.avail) - string.atoi(prevdf[self.fs].getAvail()))
		self.pctusedDelta = "%d" % (string.atoi(self.pctused) - string.atoi(prevdf[self.fs].getPctused()))
	    except AttributeError:
		# problem getting previous df
		self.usedDelta = "0"
		self.availDelta = "0"
		self.pctusedDelta = "0"


    def __str__(self):
	f = string.ljust(self.fs, 20)
	s = string.rjust(self.size, 7)
	u = string.rjust(self.used, 7)
	a = string.rjust(self.avail, 7)
	p = string.center(self.pctused, 5)
	m = string.ljust(self.mountpt, 15)

	return( '%s\t%s\t%s\t%s\t%s\t%s' % (f, s, u, a, p, m) )

    def getFs(self):
	return self.fs

    def getSize(self):
	return self.size

    def getUsed(self):
	return self.used

    def getAvail(self):
	return self.avail

    def getPctused(self):
	return self.pctused

    def getMountpt(self):
	return self.mountpt

    def getUsedDelta(self):
	return self.usedDelta

    def getAvailDelta(self):
	return self.availDelta

    def getPctusedDelta(self):
	return self.pctusedDelta

##
## END - df.py
##
