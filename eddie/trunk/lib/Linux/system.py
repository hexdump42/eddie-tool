#!/opt/local/bin/python 
## 
## File		: system.py
## 
## Author       : Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 19990929
## 
## Description	: Collect current snapshot of system state for Linux
##
## $Id$
##

import os, string, time, re
import log

# This fetches data by parsing system calls of common commands.  This was done because
# it was quick and easy to implement and port to multiple platforms.  I know this is
# a bit ugly, but will clean it up later with more efficient code that fetches data
# directly from /proc or the kernel.  CM 19990929

##
## Class system - holds information about current system state
##
class system:

    # refresh_rate : amount of time current information will be cached before
    #                being refreshed (in seconds)
    refresh_rate = 60

    def __init__(self):
	self.refresh_time = 0	# information must be refreshed at first request


    def refresh(self):
	"""Refresh the information"""

	self.getSystemstate()

	# new refresh time is current time + refresh rate (seconds)
	self.refresh_time = time.time() + self.refresh_rate


    def checkCache(self):
	"""Check if cached data is invalid, ie: refresh_time has been exceeded."""

	if time.time() > self.refresh_time:
	    log.log( "<system>checkCache(), refreshing system data", 8 )
	    self.refresh()
	else:
	    log.log( "<system>checkCache(), using cache'd system data", 8 )


    def getSystemstate(self):
	self.hash = {}		# dict of system data

	# Get load averages from /proc
	fp = open( '/proc/loadavg', 'r' )
	line = fp.read()
	fp.close()
	( loadavg1, loadavg5, loadavg15, foo, foo ) = string.split( line )
	self.hash['loadavg1'] = float(loadavg1)
	self.hash['loadavg5'] = float(loadavg5)
	self.hash['loadavg15'] = float(loadavg15)

	# Get uptime and idle-uptime from /proc
	fp = open( '/proc/uptime', 'r' )
	line = fp.read()
	fp.close()
	( uptime, uptimeidle ) = string.split( line )
	self.hash['uptime'] = float(uptime)
	self.hash['uptimeidle'] = float(uptimeidle)


	log.log( "<proc>system(), new system list created", 8 )


    def getHash(self):
	"""Returns hash of system stats."""

	self.checkCache()	# refresh data if necessary

	return self.hash


##
## END - system.py
##
