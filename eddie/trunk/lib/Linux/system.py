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

	rawList = os.popen('/usr/bin/top -bn2', 'r')

	# the above 'top' command actually performs two 'tops', 1 second apart,
	# so that we can get current cpu time allocation (idle/etc).
	# We must skip through the output to the start of the second 'top'.

	rawList.readline()	# skip start of first 'top'
	rawList.readline()	# skip start of first 'top'
	rawList.readline()	# skip start of first 'top'
	rawList.readline()	# skip start of first 'top'

	while 1:
	    line = rawList.readline()
	    if len(line) == 0:
		log.log( "<system>system.getSystemstate() error parsing 'top' output looking for 'load averages:'.", 2 )
		return

	    if string.find(line, 'load average:') != -1:
		break
 
	# regexps for parsing top of 'top' output to get info we want
	reline1 = "\s*(\S+)\s+up (\d+:\d+), (\d+) users,  load average: (\d+\.\d+), (\d+\.\d+), (\d+\.\d+)"
	reline2 = "(\d+) processes: (\d+) sleeping, (\d+) running, (\d+) zombie, (\d+) stopped"
	reline3 = "CPU states:\s*(\d+\.\d+)% user,\s*(\d+\.\d+)% system,\s*(\d+\.\d+)% nice,\s*(\d+\.\d+)% idle"
	reline4 = "Mem:\s*(\d+[A-Za-z]) av,\s*(\d+[A-Za-z]) used,\s*(\d+[A-Za-z]) free,\s*(\d+[A-Za-z]) shrd,\s*(\d+[A-Za-z]) buff"
	reline5 = "Swap:\s*(\d+[A-Za-z]) av,\s*(\d+[A-Za-z]) used,\s*(\d+[A-Za-z]) free\s*(\d+[A-Za-z]) cached"

	# line 1
##	Get line1 stuff from elsewhere...
#	inx = re.search( reline1, line )
#	if inx == None:
#	    log.log( "<system>system.getSystemstate() error parsing line1 'top' output.", 2 )
#	    return
#	self.hash['time'] = inx.group(1)
#	self.hash['uptime'] = inx.group(2)
#	self.hash['users'] = inx.group(3)
	#self.hash['loadavg1'] = float(inx.group(4))
	#self.hash['loadavg5'] = float(inx.group(5))
	#self.hash['loadavg15'] = float(inx.group(6))

	# line 2
	line = rawList.readline()
	inx = re.search( reline2, line )
	if inx == None:
	    log.log( "<system>system.getSystemstate() error parsing line2 'top' output.", 2 )
	    return
	self.hash['processes'] = int(inx.group(1))
	self.hash['sleeping'] = int(inx.group(2))
	self.hash['running'] = int(inx.group(3))
	self.hash['zombie'] = int(inx.group(4))
	self.hash['stopped'] = int(inx.group(5))

	# line 3
	line = rawList.readline()
	inx = re.search( reline3, line )
	if inx == None:
	    log.log( "<system>system.getSystemstate() error parsing line3 'top' output.", 2 )
	    return
	self.hash['cpu_user'] = float(inx.group(1))
	self.hash['cpu_system'] = float(inx.group(2))
	self.hash['cpu_nice'] = float(inx.group(3))
	self.hash['cpu_idle'] = float(inx.group(4))

	# line 4
	line = rawList.readline()
	inx = re.search( reline4, line )
	if inx == None:
	    log.log( "<system>system.getSystemstate() error parsing line4 'top' output.", 2 )
	    return
	mem_avg = inx.group(1)
	mem_used = inx.group(2)
	mem_free = inx.group(3)
	mem_shrd = inx.group(4)
	mem_buff = inx.group(5)

	if mem_avg[-1] == 'K':
	    self.hash['mem_avg'] = int(mem_avg[:-1]) * 1024
	elif mem_avg[-1] == 'M':
	    self.hash['mem_avg'] = int(mem_avg[:-1]) * 1024 * 1024
	else:
	    self.hash['mem_avg'] = int(mem_avg)

	if mem_used[-1] == 'K':
	    self.hash['mem_used'] = int(mem_used[:-1]) * 1024
	elif mem_used[-1] == 'M':
	    self.hash['mem_used'] = int(mem_used[:-1]) * 1024 * 1024
	else:
	    self.hash['mem_used'] = int(mem_used)

	if mem_free[-1] == 'K':
	    self.hash['mem_free'] = int(mem_free[:-1]) * 1024
	elif mem_free[-1] == 'M':
	    self.hash['mem_free'] = int(mem_free[:-1]) * 1024 * 1024
	else:
	    self.hash['mem_free'] = int(mem_free)

	if mem_shrd[-1] == 'K':
	    self.hash['mem_shrd'] = int(mem_shrd[:-1]) * 1024
	elif mem_shrd[-1] == 'M':
	    self.hash['mem_shrd'] = int(mem_shrd[:-1]) * 1024 * 1024
	else:
	    self.hash['mem_shrd'] = int(mem_shrd)

	if mem_buff[-1] == 'K':
	    self.hash['mem_buff'] = int(mem_buff[:-1]) * 1024
	elif mem_buff[-1] == 'M':
	    self.hash['mem_buff'] = int(mem_buff[:-1]) * 1024 * 1024
	else:
	    self.hash['mem_buff'] = int(mem_buff)

	# line 5
	line = rawList.readline()
	inx = re.search( reline5, line )
	if inx == None:
	    log.log( "<system>system.getSystemstate() error parsing line5 'top' output.", 2 )
	    return
	swap_avg = inx.group(1)
	swap_used = inx.group(2)
	swap_free = inx.group(3)
	swap_cached = inx.group(4)

	if swap_avg[-1] == 'K':
	    self.hash['swap_avg'] = int(swap_avg[:-1]) * 1024
	elif swap_avg[-1] == 'M':
	    self.hash['swap_avg'] = int(swap_avg[:-1]) * 1024 * 1024
	else:
	    self.hash['swap_avg'] = int(swap_avg)

	if swap_used[-1] == 'K':
	    self.hash['swap_used'] = int(swap_used[:-1]) * 1024
	elif swap_used[-1] == 'M':
	    self.hash['swap_used'] = int(swap_used[:-1]) * 1024 * 1024
	else:
	    self.hash['swap_used'] = int(swap_used)

	if swap_free[-1] == 'K':
	    self.hash['swap_free'] = int(swap_free[:-1]) * 1024
	elif swap_free[-1] == 'M':
	    self.hash['swap_free'] = int(swap_free[:-1]) * 1024 * 1024
	else:
	    self.hash['swap_free'] = int(swap_free)

	if swap_cached[-1] == 'K':
	    self.hash['swap_cached'] = int(swap_cached[:-1]) * 1024
	elif swap_cached[-1] == 'M':
	    self.hash['swap_cached'] = int(swap_cached[:-1]) * 1024 * 1024
	else:
	    self.hash['swap_cached'] = int(swap_cached)



	rawList.close()

	#print "hash:",self.hash

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
