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

  loadavg1		- 1min load average (float)
  loadavg5		- 5min load average (float)
  loadavg15		- 15min load average (float)
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
  ctr_pages_out		- pages written out (int)
  ctr_pages_swapin	- swap pages read in (int)
  ctr_pages_swapout	- swap pages written out (int)
  ctr_interrupts	- number of interrupts received (int)
  ctr_contextswitches 	- number of context switches (int)
  ctr_processes		- number of processes started (I think?) (int)
  boottime		- time of boot (epoch) (int)
"""

# Python modules
import string, re
# Eddie modules
import datacollect, log


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
	    log.log( "<system>system.getSystemstate(), cannot read /proc/loadavg", 5 )
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
	    log.log( "<system>system.getSystemstate(), cannot read /proc/uptime", 5 )
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
	    log.log( "<system>system.getSystemstate(), cannot read /proc/stat", 5 )
	else:
	    line = fp.readline()
	    while line != "":
		if line[:4] == "cpu ":
		    # Total CPU stats
		    ( foo, user, nice, system, idle ) = string.split(line)
		    self.data.datahash['ctr_cpu_user'] = int(user)
		    self.data.datahash['ctr_cpu_nice'] = int(nice)
		    self.data.datahash['ctr_cpu_system'] = int(system)
		    self.data.datahash['ctr_cpu_idle'] = long(idle)
		elif re.match( '^cpu([0-9]+).*', line ):
		    # Stats for each CPU
		    m = re.match( '^cpu([0-9]+).*', line )
		    cpunum = int(m.group(1))
		    ( foo, user, nice, system, idle ) = string.split(line)
		    self.data.datahash['ctr_cpu%d_user'%cpunum] = int(user)
		    self.data.datahash['ctr_cpu%d_nice'%cpunum] = int(nice)
		    self.data.datahash['ctr_cpu%d_system'%cpunum] = int(system)
		    self.data.datahash['ctr_cpu%d_idle'%cpunum] = long(idle)
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
		    self.data.datahash['ctr_interrupts'] = int(ints)
		elif line[:5] == "ctxt ":
		    # Number of context switches
		    ( foo, ctxt ) = string.split(line)
		    self.data.datahash['ctr_contextswitches'] = int(ctxt)
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

	log.log( "<system>system.collectData(): system data collected", 7 )


##
## END - system.py
##
