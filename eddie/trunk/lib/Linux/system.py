## 
## File		: system.py
## 
## Author       : Chris Miles  <chris@psychofx.com>
## 
## Start Date	: 19990929
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

"""
  This is an Eddie data collector.  It collects System data and statistics on
  a generic Linux system.
  The following statistics are currently collected and made available to
  directives that request it (e.g., SYS):

  Instantaneous stats:
   loadavg1		- 1min load average (float)
   loadavg5		- 5min load average (float)
   loadavg15		- 15min load average (float)
   mem_total            - total memory, bytes (int)
   mem_used             - memory in use, bytes (int)
   mem_free             - memory free, bytes (int)
   mem_shared           - memory shared, bytes (int)
   mem_buffers          - memory used as buffers, bytes (int)
   mem_cached           - memory cached, bytes (int)
   swap_total           - total swap, bytes (int)
   swap_used            - swap in use, bytes (int)
   swap_free            - swap free, bytes (int)

  System counters:
   ctr_uptime		- uptime in seconds (float)
   ctr_uptimeidle	- idle uptime in seconds (float)
   ctr_cpu_user		- total cpu in user space (int)
   ctr_cpu_nice		- total cpu in user nice space (int)
   ctr_cpu_system	- total cpu in system space (int)
   ctr_cpu_idle		- total cpu in idle thread (long)
   ctr_cpu%d_user	- per cpu in user space (e.g., cpu0, cpu1, etc) (int)
   ctr_cpu%d_nice	- per cpu in user nice space (e.g., cpu0, cpu1, etc) (int)
   ctr_cpu%d_system	- per cpu in system space (e.g., cpu0, cpu1, etc) (int)
   ctr_cpu%d_idle	- per cpu in idle thread (e.g., cpu0, cpu1, etc) (long)
   ctr_pages_in		- pages read in (int)
   ctr_pages_out	- pages written out (int)
   ctr_pages_swapin	- swap pages read in (int)
   ctr_pages_swapout	- swap pages written out (int)
   ctr_interrupts	- number of interrupts received (long)
   ctr_contextswitches 	- number of context switches (float)
   ctr_processes	- number of processes started (I think?) (int)
 
  Misc:
   boottime		- time of boot (epoch) (int)

"""

# Python modules
import string
import re
# Eddie modules
import datacollect
import log


class system(datacollect.DataCollect):
    """
    Class system - collects current system statistics.
    """

    def __init__(self):
	apply( datacollect.DataCollect.__init__, (self,) )


    ##################################################################
    # Private methods

    def collectData(self):
	"""
	Collect system statistics data.
	"""

	self.data.datahash = {}

	# Get load averages from /proc
	try:
	    fp = open( '/proc/loadavg', 'r' )
	except IOError:
	    log.log( "<system>system.getSystemstate(): cannot read /proc/loadavg", 5 )
	else:
	    line = fp.read()
	    fp.close()
	    ( loadavg1, loadavg5, loadavg15, foo, foo ) = string.split( line )
	    self.data.datahash['loadavg1'] = float(loadavg1)
	    self.data.datahash['loadavg5'] = float(loadavg5)
	    self.data.datahash['loadavg15'] = float(loadavg15)

	# Get uptime and idle-uptime counters from /proc
	try:
	    fp = open( '/proc/uptime', 'r' )
	except IOError:
	    log.log( "<system>system.getSystemstate(): cannot read /proc/uptime", 5 )
	else:
	    line = fp.read()
	    fp.close()
	    ( uptime, uptimeidle ) = string.split( line )
	    self.data.datahash['ctr_uptime'] = float(uptime)
	    self.data.datahash['ctr_uptimeidle'] = float(uptimeidle)

	# Get system statistics from /proc
	try:
	    fp = open( '/proc/stat', 'r' )
	except IOError:
	    log.log( "<system>system.getSystemstate(): cannot read /proc/stat", 5 )
	else:
	    line = fp.readline()
	    while line != "":
		if line[:4] == "cpu ":
		    # Total CPU stats
		    cpusplit = string.split(line)
		    if len(cpusplit) == 5:
			# Redhat Linux (probably other Linuxes?)
			( foo, user, nice, system, idle ) = cpusplit
			self.data.datahash['ctr_cpu_user'] = long(user)
			self.data.datahash['ctr_cpu_nice'] = long(nice)
			self.data.datahash['ctr_cpu_system'] = long(system)
			self.data.datahash['ctr_cpu_idle'] = long(idle)
		    elif len(cpusplit) == 8:
			# Redhat Enterprise Linux (not sure if this is specific to RHEL
			# or is a change in kernel 2.4.21+)
			( foo, user, nice, system, idle, iowait, hardirq, softirq ) = cpusplit
			self.data.datahash['ctr_cpu_user'] = long(user)
			self.data.datahash['ctr_cpu_nice'] = long(nice)
			self.data.datahash['ctr_cpu_system'] = long(system)
			self.data.datahash['ctr_cpu_idle'] = long(idle)
			self.data.datahash['ctr_cpu_iowait'] = long(iowait)
			self.data.datahash['ctr_cpu_hardirq'] = long(hardirq)
			self.data.datahash['ctr_cpu_softirq'] = long(softirq)
		    else:
			# Which kernel is this???
			raise datacollect.DataFailure, "Cannot read cpu line in /proc/stat: %s" % (line)
		elif re.match( '^cpu([0-9]+).*', line ):
		    # Stats for each CPU
		    m = re.match( '^cpu([0-9]+).*', line )
		    cpunum = int(m.group(1))
		    cpusplit = string.split(line)
		    #( foo, user, nice, system, idle ) = string.split(line)
		    if len(cpusplit) == 5:
			# Redhat Linux (probably other Linuxes?)
			( foo, user, nice, system, idle ) = cpusplit
			self.data.datahash['ctr_cpu%d_user'%cpunum] = long(user)
			self.data.datahash['ctr_cpu%d_nice'%cpunum] = long(nice)
			self.data.datahash['ctr_cpu%d_system'%cpunum] = long(system)
			self.data.datahash['ctr_cpu%d_idle'%cpunum] = long(idle)
		    elif len(cpusplit) == 8:
			# Redhat Enterprise Linux (not sure if this is specific to RHEL
			# or is a change in kernel 2.4.21+)
			( foo, user, nice, system, idle, iowait, hardirq, softirq ) = cpusplit
			self.data.datahash['ctr_cpu%d_user'%cpunum] = long(user)
			self.data.datahash['ctr_cpu%d_nice'%cpunum] = long(nice)
			self.data.datahash['ctr_cpu%d_system'%cpunum] = long(system)
			self.data.datahash['ctr_cpu%d_idle'%cpunum] = long(idle)
			self.data.datahash['ctr_cpu%d_iowait'%cpunum] = long(iowait)
			self.data.datahash['ctr_cpu%d_hardirq'%cpunum] = long(hardirq)
			self.data.datahash['ctr_cpu%d_softirq'%cpunum] = long(softirq)
		    else:
			# Which kernel is this???
			raise datacollect.DataFailure, "Cannot read cpu line in /proc/stat: %s" % (line)

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
		    self.data.datahash['ctr_pages_in'] = int(pagein)
		    self.data.datahash['ctr_pages_out'] = int(pageout)
		elif line[:5] == "swap ":
		    # Swap Pages in/out
		    ( foo, swapin, swapout ) = string.split(line)
		    self.data.datahash['ctr_pages_swapin'] = int(swapin)
		    self.data.datahash['ctr_pages_swapout'] = int(swapout)
		elif line[:5] == "intr ":
		    # Number of interrupts - only using first number
		    ints = string.split(line)[1]
		    self.data.datahash['ctr_interrupts'] = long(ints)
		elif line[:5] == "ctxt ":
		    # Number of context switches
		    ( foo, ctxt ) = string.split(line)
		    self.data.datahash['ctr_contextswitches'] = long(ctxt)
		elif line[:6] == "btime ":
		    # boot time, in seconds since the epoch (January 1, 1970)
		    ( foo, btime ) = string.split(line)
		    self.data.datahash['boottime'] = int(btime)
		elif line[:10] == "processes ":
		    # number of processes started (I presume?)
		    ( foo, processes ) = string.split(line)
		    self.data.datahash['ctr_processes'] = int(processes)
		line = fp.readline()
		# any other stats are ignored.

	    fp.close()

	# Get memory statistics from /proc/meminfo
	try:
	    fp = open( '/proc/meminfo', 'r' )
	except IOError:
	    log.log( "<system>system.getSystemstate(): cannot read /proc/meminfo", 5 )
	else:
	    foo = fp.readline()		# skip header
	    memline = fp.readline()	# read Memory stats
	    swapline = fp.readline()	# read Swap stats
	    fp.close()

	    memline_list = string.split( memline )
	    if memline_list[0] != "Mem:" or len(memline_list) != 7:
		log.log( "<system>system.getSystemstate(): error parsing Memory information from /proc/meminfo", 5 )
	    else:
		self.data.datahash['mem_total'] = long( memline_list[1] )
		self.data.datahash['mem_used'] = long( memline_list[2] )
		self.data.datahash['mem_free'] = long( memline_list[3] )
		self.data.datahash['mem_shared'] = long( memline_list[4] )
		self.data.datahash['mem_buffers'] = long( memline_list[5] )
		self.data.datahash['mem_cached'] = long( memline_list[6] )

	    swapline_list = string.split( swapline )
	    if swapline_list[0] != "Swap:" or len(swapline_list) != 4:
		log.log( "<system>system.getSystemstate(): error parsing Swap information from /proc/meminfo", 5 )
	    else:
		self.data.datahash['swap_total'] = long( swapline_list[1] )
		self.data.datahash['swap_used'] = long( swapline_list[2] )
		self.data.datahash['swap_free'] = long( swapline_list[3] )


	log.log( "<system>system.collectData(): system data collected", 7 )


##
## END - system.py
##
