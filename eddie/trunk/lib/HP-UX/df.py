## 
## File		: df.py 
## 
## Author       : Chris Miles  <chris@psychofx.com>
## 
## Date		: 20010709
## 
## Description	: Library of classes that deal with a HP-UX bdf list
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
import os, string
# Eddie Modules
import log, history, utils

##
## Class dfList - instantiates with a list of disk stats
##
class dfList:
    def __init__(self):
	self.hash = {}
	self.mounthash = {}
	self.list = []
	self.dfheader = ""

	self.refresh()


    def refresh(self):
	"""Force df refresh."""

	dfre = "^([/0-9a-zA-Z]+)\s*\(([/0-9a-zA-Z])\s*\)\s*:\s*([0-9]+)\s*total allocated Kb\s*([0-9]+)\s*free allocated Kb\s*([0-9]+)\s*used allocated Kb\s*([0-9]+)\s*% allocation used"

	rawList = utils.safe_popen('bdf', 'r')
	#self.dfheader = rawList.readline()
 
	prevline = None
	for line in rawList.readlines():
	    if prevline:
		line = prevline + " " + line	# join any previous line to current
		prevline = None
	    fields = string.split(line)
	    if len(fields) == 1:		# if 1 field, assume rest on next line
		prevline = line
		continue
	    p = df(fields)
	    self.list.append(p)
	    self.hash[fields[0]] = p		# dict of filesystem devices
	    self.mounthash[fields[5]] = p	# dict of mount points
 	    prevline = None

	utils.safe_pclose( rawList )


    def __str__(self):
	rv = 'Filesystem               kbytes    used   avail  pct    Mount on\n'
 	for item in self.list:
 	    rv = rv + str(item) + '\n'

	return(rv)


    def keys(self):
	self.refresh()
        return(self.hash.keys())

    # Overload '[]', eg: returns corresponding df object for given filesystem
    # device - if there isn't one, will try to find a df object based on the
    # mount point.  If both fail, returns None.
    def __getitem__(self, name):
	self.refresh()
        try:
            return self.hash[name]		# try to find filesystem device
        except KeyError:
	    try:
		return self.mounthash[name]	# try to find mount point
	    except KeyError:
		return None

	return None		# just in case...


##
## Class df : holds stats on disk usage
##
class df:
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

	log.log( '%s\t%s\t%s\t%s\t%s\t%s' % (f, s, u, a, p, m), 9 )
	
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
	return self.pctused	# strip '%' off end

    def getMountpt(self):
	return self.mountpt

    def getUsedDelta(self):
	return self.usedDelta

    def getAvailDelta(self):
	return self.availDelta

    def getPctusedDelta(self):
	return self.pctusedDelta	# strip '%' off end

##
## END - df.py
##
