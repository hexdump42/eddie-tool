## 
## File		: system.py
## 
## Author       : Chris Miles  <chris@psychofx.com>
## 
## Date		: 19990929
## 
## Description	: Collect current snapshot of system state for Linux
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

# This is an Eddie data collector.  It collects System data and statistics on
# a generic Linux system.
# The following statistics are currently collected and made available to the
# appropriate directives (e.g., SYS):
# 
# loadavg1	- 1min load average
# loadavg5	- 5min load average
# loadavg15	- 15min load average
# uptime	- uptime in seconds
# uptimeidle	- idle uptime in seconds
# cpu_user	- total cpu in user space
# cpu_nice	- total cpu in user nice space
# cpu_system	- total cpu in system space
# cpu_idle	- total cpu in idle thread
# cpu%d_user	- per cpu in user space (e.g., cpu0, cpu1, etc)
# cpu%d_nice	- per cpu in user nice space (e.g., cpu0, cpu1, etc)
# cpu%d_system	- per cpu in system space (e.g., cpu0, cpu1, etc)
# cpu%d_idle	- per cpu in idle thread (e.g., cpu0, cpu1, etc)
# pages_in	- pages read in
# pages_out	- pages written out
# pages_swapin	- swap pages read in
# pages_swapout	- swap pages written out
# interrupts	- number of interrupts received
# contextswitches - number of context switches
# boottime	- time of boot (epoch)
# processes	- number of processes started (I think?)


import os, string, time, re
import log


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
	try:
	    fp = open( '/proc/loadavg', 'r' )
	except IOError:
	    log.log( "<system>getSystemstate(), cannot read /proc/loadavg", 4 )
	else:
	    line = fp.read()
	    fp.close()
	    ( loadavg1, loadavg5, loadavg15, foo, foo ) = string.split( line )
	    self.hash['loadavg1'] = float(loadavg1)
	    self.hash['loadavg5'] = float(loadavg5)
	    self.hash['loadavg15'] = float(loadavg15)

	# Get uptime and idle-uptime from /proc
	try:
	    fp = open( '/proc/uptime', 'r' )
	except IOError:
	    log.log( "<system>getSystemstate(), cannot read /proc/uptime", 4 )
	else:
	    line = fp.read()
	    fp.close()
	    ( uptime, uptimeidle ) = string.split( line )
	    self.hash['uptime'] = float(uptime)
	    self.hash['uptimeidle'] = float(uptimeidle)

	# Get system statistics from /proc
	try:
	    fp = open( '/proc/stat', 'r' )
	except IOError:
	    log.log( "<system>getSystemstate(), cannot read /proc/stat", 4 )
	else:
	    line = fp.readline()
	    while line != "":
		if line[:4] == "cpu ":
		    # Total CPU stats
		    ( foo, user, nice, system, idle ) = string.split(line)
		    self.hash['cpu_user'] = int(user)
		    self.hash['cpu_nice'] = int(nice)
		    self.hash['cpu_system'] = int(system)
		    self.hash['cpu_idle'] = int(idle)
		elif re.match( '^cpu([0-9]+).*', line ):
		    # Stats for each CPU
		    m = re.match( '^cpu([0-9]+).*', line )
		    cpunum = int(m.group(1))
		    ( foo, user, nice, system, idle ) = string.split(line)
		    self.hash['cpu%d_user'%cpunum] = int(user)
		    self.hash['cpu%d_nice'%cpunum] = int(nice)
		    self.hash['cpu%d_system'%cpunum] = int(system)
		    self.hash['cpu%d_idle'%cpunum] = int(idle)
		elif line[:5] == "disk ":
		    # TODO - need info on meaning
		    pass
		elif line[:9] == "disk_rio ":
		    # TODO - need info on meaning
		    pass
		elif line[:9] == "disk_wio ":
		    # TODO - need info on meaning
		    pass
		elif line[:10] == "disk_rblk ":
		    # TODO - need info on meaning
		    pass
		elif line[:10] == "disk_wblk ":
		    # TODO - need info on meaning
		    pass
		elif line[:5] == "page ":
		    # Pages in/out
		    ( foo, pagein, pageout ) = string.split(line)
		    self.hash['pages_in'] = int(pagein)
		    self.hash['pages_out'] = int(pageout)
		elif line[:5] == "swap ":
		    # Swap Pages in/out
		    ( foo, swapin, swapout ) = string.split(line)
		    self.hash['pages_swapin'] = int(swapin)
		    self.hash['pages_swapout'] = int(swapout)
		elif line[:5] == "intr ":
		    # Number of interrupts - only using first number
		    ints = string.split(line)[1]
		    self.hash['interrupts'] = int(ints)
		elif line[:5] == "ctxt ":
		    # Number of context switches
		    ( foo, ctxt ) = string.split(line)
		    self.hash['contextswitches'] = int(ctxt)
		elif line[:6] == "btime ":
		    # boot time, in seconds since the epoch (January 1, 1970)
		    ( foo, btime ) = string.split(line)
		    self.hash['boottime'] = int(btime)
		elif line[:10] == "processes ":
		    # number of processes started (I presume?)
		    ( foo, processes ) = string.split(line)
		    self.hash['processes'] = int(processes)
		line = fp.readline()
		# any other stats are ignored.

	    fp.close()

	log.log( "<proc>system(), new system list created", 8 )


    def getHash(self):
	"""Returns hash of system stats."""

	self.checkCache()	# refresh data if necessary

	return self.hash


##
## END - system.py
##
