#!/opt/local/bin/python 
## 
## File		: iostat.py
## 
## Author       : Chris Miles  <cmiles@connect.com.au>
##                Rod Telford  <rtelford@connect.com.au>
## 
## Date		: 20000520
## 
## Description	: Collect current snapshot of I/O statistics
##
## $Id$
##

import sys, os, string, time, re
import log, datastore
import solkstat


class iostat(datastore.DataStore):
    """Fetch and store current I/O statistics."""

    def __init__(self):
        #apply( datastore.DataStore.__init__, (self) )
        datastore.DataStore.__init__(self)


    def fetchData(self):
	"""Fetches the iostat statistics from kstat library."""

	self.hash = {}		# clear data store hash
	self.snaptimes = {}	# hash of snaptimes

	khead = solkstat.open()	# open kstat tree

	# walk kstat list
	k = khead
	while k:
	    if k.ks_type == 3:
		try:
		    name = k.ks_name
		    data = k.ks_data
		    snaptime = k.ks_snaptime

		    data['name'] = name		# add name to data hash
		    data['snaptime'] = snaptime	# add snaptime to data hash

		    self.hash[name] = data
		    self.snaptimes[name] = snaptime
		except AttributeError:
		    print "Error with kstat list: '%s'.  k.ks_name='%s'" % (sys.exc_value,k.ks_name)
		    log.log( "<iostat>iostat(), Error with kstat list: '%s'. k.ks_name='%s'" % (sys.exc_value,k.ks_name), 3 )

	    k = k.getnext()


	log.log( "<iostat>iostat(), new iostat data collected", 7 )
	khead.close()		# close kstat



##
## END - iostat.py
##
