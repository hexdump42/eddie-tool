## 
## File		: system.py
## 
## Author       : Chris Miles  <cmiles@codefx.com.au>
##                Rod Telford  <rtelford@codefx.com.au>
## 
## Date		: 19990520
## 
## Description	: Collect current snapshot of system state
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

import os, string, time, re
import log, utils


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
	    log.log( "<system>checkCache(), refreshing system data", 7 )
	    self.refresh()
	else:
	    log.log( "<system>checkCache(), using cache'd system data", 7 )


    def getSystemstate(self):
	self.hash = {}		# dict of system data

	rawList = utils.safe_popen('/opt/local/bin/top -nud2 -s1', 'r')

	# the above 'top' command actually performs two 'tops', 1 second apart,
	# so that we can get current cpu time allocation (idle/etc).
	# We must skip through the output to the start of the second 'top'.

	rawList.readline()	# skip start of first 'top'

	while 1:
	    line = rawList.readline()
	    if len(line) == 0:
		log.log( "<system>system.getSystemstate() error parsing 'top' output looking for 'last pid'.", 2 )
		return

	    if line[:8] == 'last pid':
		break
 
	# regexps for parsing top of 'top' output to get info we want
	reline1 = "last pid:\s*([0-9]+);\s*load averages:\s*([0-9]+\.[0-9]+),\s*([0-9]+\.[0-9]+),\s*([0-9]+\.[0-9]+)\s+([0-9]+:[0-9]+:[0-9]+)"
	reline2 = "([0-9]+)\s+processes:(?:\s+(?P<sleeping>[0-9]+)\s+sleeping,)?(?:\s+(?P<zombie>[0-9]+)\s+zombie,)?(?:\s+(?P<running>[0-9]+)\s+running,)?(?:\s+(?P<stopped>[0-9]+)\s+stopped,)?(?:\s+(?P<oncpu>[0-9]+)\s+on cpu)?.*"
	reline3 = "CPU states:\s*([0-9.]+)% idle,\s*([0-9.]+)% user,\s*([0-9.]+)% kernel,\s*([0-9.]+)% iowait,\s*([0-9.]+)% swap"
	reline4 = "Memory:\s*(?P<mem_real>\w+)\s*real,\s*(?P<mem_free>\w+)\s*free,(?:\s*(?P<mem_swapuse>\w+)\s*swap in use,)?\s*(?P<mem_swapfree>\w+)\s*swap free"

	# line 1
	inx = re.search( reline1, line )
	if inx == None:
	    log.log( "<system>system.getSystemstate() error parsing line1 'top' output.", 2 )
	    return
	self.lastpid = int(inx.group(1))
	self.loadavg1 = float(inx.group(2))
	self.loadavg5 = float(inx.group(3))
	self.loadavg15 = float(inx.group(4))
	self.time = inx.group(5)

	# line 2
	line = rawList.readline()
	inx = re.search( reline2, line )
	if inx == None:
	    log.log( "<system>system.getSystemstate() error parsing line2 'top' output.", 2 )
	    return
	self.processes = int(inx.group(1))
	try:
	    self.sleeping = int(inx.group('sleeping'))
	except:
	    self.sleeping = 0
	try:
	    self.zombie = int(inx.group('zombie'))
	except:
	    self.zombie = 0
	try:
	    self.running = int(inx.group('running'))
	except:
	    self.running = 0
	try:
	    self.stopped = int(inx.group('stopped'))
	except:
	    self.stopped = 0
	try:
	    self.oncpu = int(inx.group('oncpu'))
	except:
	    self.oncpu = 0

	# line 3
	line = rawList.readline()
	inx = re.search( reline3, line )
	if inx == None:
	    log.log( "<system>system.getSystemstate() error parsing line3 'top' output.", 2 )
	    return
	self.cpu_idle = float(inx.group(1))
	self.cpu_user = float(inx.group(2))
	self.cpu_kernel = float(inx.group(3))
	self.cpu_iowait = float(inx.group(4))
	self.cpu_swap = float(inx.group(5))

	# line 4
	line = rawList.readline()
	inx = re.search( reline4, line )
	if inx == None:
	    log.log( "<system>system.getSystemstate() error parsing line4 'top' output.", 2 )
	    return
	mem_real = inx.group('mem_real')
	mem_free = inx.group('mem_free')
	mem_swapuse = inx.group('mem_swapuse')
	mem_swapfree = inx.group('mem_swapfree')

        try:
	    if mem_real[-1] == 'K':
	        self.mem_real = int(mem_real[:-1]) * 1024
	    elif mem_real[-1] == 'M':
	        self.mem_real = int(mem_real[:-1]) * 1024 * 1024
	    else:
	        self.mem_real = int(mem_real)
        except:
            self.mem_real = 0

        try:
	    if mem_free[-1] == 'K':
	        self.mem_free = int(mem_free[:-1]) * 1024
	    elif mem_free[-1] == 'M':
	        self.mem_free = int(mem_free[:-1]) * 1024 * 1024
	    else:
	        self.mem_free = int(mem_free)
        except:
            self.mem_free = 0

        try:
	    if mem_swapuse[-1] == 'K':
	        self.mem_swapuse = int(mem_swapuse[:-1]) * 1024
	    elif mem_swapuse[-1] == 'M':
	        self.mem_swapuse = int(mem_swapuse[:-1]) * 1024 * 1024
	    else:
	        self.mem_swapuse = int(mem_swapuse)
        except:
            self.mem_swapuse = 0

        try:
	    if mem_swapfree[-1] == 'K':
	        self.mem_swapfree = int(mem_swapfree[:-1]) * 1024
	    elif mem_swapfree[-1] == 'M':
	        self.mem_swapfree = int(mem_swapfree[:-1]) * 1024 * 1024
	    else:
	        self.mem_swapfree = int(mem_swapfree)
        except:
            self.mem_swapfree = 0


	rawList.close()

	#print "system debug:"
	#print " - lastpid:",self.lastpid
	#print " - loadavg1:",self.loadavg1
	#print " - loadavg5:",self.loadavg5
	#print " - loadavg15:",self.loadavg15
	#print " - time:",self.time

	#print " - processes:",self.processes
	#print " - sleeping:",self.sleeping
	#print " - zombie:",self.zombie
	#print " - running:",self.running
	#print " - stopped:",self.stopped
	#print " - oncpu:",self.oncpu

	#print " - cpu_idle:",self.cpu_idle
	#print " - cpu_user:",self.cpu_user
	#print " - cpu_kernel:",self.cpu_kernel
	#print " - cpu_iowait:",self.cpu_iowait
	#print " - cpu_swap:",self.cpu_swap

	#print " - mem_real:",self.mem_real
	#print " - mem_free:",self.mem_free
	#print " - mem_swapuse:",self.mem_swapuse
	#print " - mem_swapfree:",self.mem_swapfree

	# Fill hash
	self.hash['lastpid'] = self.lastpid
	self.hash['loadavg1'] = self.loadavg1
	self.hash['loadavg5'] = self.loadavg5
	self.hash['loadavg15'] = self.loadavg15
	self.hash['time'] = self.time

	self.hash['processes'] = self.processes
	self.hash['sleeping'] = self.sleeping
	self.hash['zombie'] = self.zombie
	self.hash['running'] = self.running
	self.hash['stopped'] = self.stopped
	self.hash['oncpu'] = self.oncpu

	self.hash['cpu_idle'] = self.cpu_idle
	self.hash['cpu_user'] = self.cpu_user
	self.hash['cpu_kernel'] = self.cpu_kernel
	self.hash['cpu_iowait'] = self.cpu_iowait
	self.hash['cpu_swap'] = self.cpu_swap

	self.hash['mem_real'] = self.mem_real
	self.hash['mem_free'] = self.mem_free
	self.hash['mem_swapuse'] = self.mem_swapuse
	self.hash['mem_swapfree'] = self.mem_swapfree


	log.log( "<proc>system(), new system list created", 7 )


    def getHash(self):
	"""Returns hash of system stats."""

	self.checkCache()	# refresh data if necessary

	return self.hash


##
## END - system.py
##
