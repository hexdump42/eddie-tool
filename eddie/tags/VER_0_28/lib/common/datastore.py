## 
## File		: datastore.py
## 
## Author       : Chris Miles  <chris@psychofx.com>
##                Rod Telford  <rtelford@psychofx.com>
## 
## Date		: 20000520
## 
## Description	: The Eddie data storage parent class
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

# Python modules
import time
# Eddie modules
import log


class DataStore:
    """Provides a data collection and store class with automatic
    caching and refreshing of data in the cache.  Data is cached
    for 60 seconds by default.  Assign self.refresh_rate to change
    this.  A fetchData() function must be supplied by any child
    class of DataStore.  Public functions are:
     getHash() - return hash of stored data
     refresh() - force a cache refresh
    """

    def __init__(self):
	self.refresh_rate = 60	# amount of time current information will be
	                        # cached before being refreshed (in seconds)
	self.refresh_time = 0	# information must be refreshed at first request
	self.hash = None	# a hash for storing the data


    def checkCache(self):
	"""Check if cached data is invalid, ie: refresh_time has been exceeded."""

	if time.time() > self.refresh_time:
	    log.log( "<DataStore>checkCache(), refreshing data", 8 )
	    self.refresh()
	else:
	    log.log( "<DataStore>checkCache(), using cache'd data", 8 )


    def fetchData(self):
	"""Must supply own fetchData() function."""
	pass


    ## PUBLIC functions ##

    def refresh(self):
	"""Refresh the data."""

	self.fetchData()

	# new refresh time is current time + refresh rate (seconds)
	self.refresh_time = time.time() + self.refresh_rate


    def getHash(self):
	"""Returns hash of stored data."""

	self.checkCache()	# refresh data if necessary

	return self.hash


##
## END - datastore.py
##
