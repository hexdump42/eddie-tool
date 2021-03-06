## 
## File		: system.py
## 
## Author       : Chris Miles  <chris@psychofx.com>
##                Rod Telford  <rtelford@psychofx.com>
## 
## Start Date	: 19990520
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

"""
  This is an Eddie data collector.  It collects System data and statistics on
  a Solaris system.
  The following statistics are currently collected and made available to
  directives that request it (e.g., SYS):

  (See system class doc info below.)
"""


# Python modules
import string, re
# Eddie modules
import datacollect, log, utils


class system(datacollect.DataCollect):
    """
    Gathers system statistics.

        Calls the following external commands to get stats from:
        /usr/bin/vmstat -s: standard with Solaris 2.5.1 and greater
	/usr/bin/uptime: standard with Solaris 2.5.1 and greater
        /opt/local/bin/top: top version 3.5beta9 (compiled by user)
	  (use of /opt/local/bin/top is being phased out and should not be needed)

	The names of all the stats collected by the system class are:

	    System stats from '/usr/bin/uptime':
		uptime		- time since last boot (string)
		users		- number of logged on users (int)
		loadavg1	- 1 minute load average (float)
		loadavg5	- 5 minute load average (float)
		loadavg15	- 15 minute load average (float)

	    System counters from '/usr/bin/vmstat -s' (see vmstat(1M)):
		ctr_swap_ins				- (long)
		ctr_swap_outs				- (long)
		ctr_pages_swapped_in			- (long)
		ctr_pages_swapped_out			- (long)
		ctr_total_address_trans_faults_taken	- (long)
		ctr_page_ins				- (long)
		ctr_page_outs				- (long)
		ctr_pages_paged_in			- (long)
		ctr_pages_paged_out			- (long)
		ctr_total_reclaims			- (long)
		ctr_reclaims_from_free_list		- (long)
		ctr_micro_hat_faults			- (long)
		ctr_minor_as_faults			- (long)
		ctr_major_faults			- (long)
		ctr_copyonwrite_faults			- (long)
		ctr_zero_fill_page_faults		- (long)
		ctr_pages_examined_by_the_clock_daemon	- (long)
		ctr_revolutions_of_the_clock_hand	- (long)
		ctr_pages_freed_by_the_clock_daemon	- (long)
		ctr_forks				- (long)
		ctr_vforks				- (long)
		ctr_execs				- (long)
		ctr_cpu_context_switches		- (long)
		ctr_device_interrupts			- (long)
		ctr_traps				- (long)
		ctr_system_calls			- (long)
		ctr_total_name_lookups			- (long)
		ctr_toolong				- (long)
		ctr_user_cpu				- (long)
		ctr_system_cpu				- (long)
		ctr_idle_cpu				- (long)
		ctr_wait_cpu				- (long)

	    Process/memory stats from '/usr/bin/vmstat' (see vmstat(1M)):
	        procs_running	- number of processes running (int)
	        procs_blocked	- number of processes blocked (int)
	        procs_waiting	- number of processes waiting (int)
	        mem_swapfree	- amount of free swap (kB) (int)
	        mem_free	- amount of free RAM (kB) (int)

	    System stats from '/opt/local/bin/top' (phasing out):
		processes	- total number of processes (int)
		sleeping	- number of processes in sleeping state (int)
		zombie		- number of processes in zombie state (int)
		running		- number of processes in running state (int)
		stopped		- number of processes in stopped state (int)
		oncpu		- number of processes on cpus (int)
		cpu_idle	- percentage of cpu in idle thread (float)
		cpu_user	- percentage of cpu in user mode (float)
		cpu_kernel	- percentage of cpu in kernel mode (float)
		cpu_iowait	- percentage of cpu blocked on iowait (float)
		cpu_swap	- percentage of cpu blocked on swap (float)
    """

    def __init__(self):
	apply( datacollect.DataCollect.__init__, (self,) )



    ##################################################################
    # Public, thread-safe, methods



    ##################################################################
    # Private methods.  No thread safety if not using public methods.

    def collectData(self):
        """
        Collect system statistics data.
        """

	self.data.datahash = {}		# dict of system data


	vmstat_dict = self._getvmstat()
	if vmstat_dict:
	    self.data.datahash.update(vmstat_dict)

	vmstat2_dict = self._getvmstat2()
	if vmstat2_dict:
	    self.data.datahash.update(vmstat2_dict)

	uptime_dict = self._getuptime()
	if uptime_dict:
	    self.data.datahash.update(uptime_dict)

	top_dict = self._getTop()
	if top_dict:
	    self.data.datahash.update(top_dict)


        log.log( "<system>system.collectData(): collected data for %d system statistics" % (len(self.data.datahash.keys())), 6 )



    def _getvmstat(self):
	"""Get system statistics from the 'vmstat -s' call.
	This should work for Solaris 2.5.1/2.6/2.7/2.8."""

	vmstat_cmd = "/usr/bin/vmstat -s"

	(retval, output) = utils.safe_getstatusoutput( vmstat_cmd )

	if retval != 0:
	    log.log( "<system>system._getvmstat(): error calling '%s'"%(vmstat_cmd), 5 )
	    return None

	vmstat_dict = {}

	for l in string.split( output, '\n' ):
	    if string.find( l, 'swap ins' ) != -1:
		vmstat_dict['ctr_swap_ins'] = long(string.split(l)[0])
	    elif string.find( l, 'swap outs' ) != -1:
		vmstat_dict['ctr_swap_outs'] = long(string.split(l)[0])
	    elif string.find( l, 'pages swapped in' ) != -1:
		vmstat_dict['ctr_pages_swapped_in'] = long(string.split(l)[0])
	    elif string.find( l, 'pages swapped out' ) != -1:
		vmstat_dict['ctr_pages_swapped_out'] = long(string.split(l)[0])
	    elif string.find( l, 'total address trans. faults taken' ) != -1:
		vmstat_dict['ctr_total_address_trans_faults_taken'] = long(string.split(l)[0])
	    elif string.find( l, 'page ins' ) != -1:
		vmstat_dict['ctr_page_ins'] = long(string.split(l)[0])
	    elif string.find( l, 'page outs' ) != -1:
		vmstat_dict['ctr_page_outs'] = long(string.split(l)[0])
	    elif string.find( l, 'pages paged in' ) != -1:
		vmstat_dict['ctr_pages_paged_in'] = long(string.split(l)[0])
	    elif string.find( l, 'pages paged out' ) != -1:
		vmstat_dict['ctr_pages_paged_out'] = long(string.split(l)[0])
	    elif string.find( l, 'total reclaims' ) != -1:
		vmstat_dict['ctr_total_reclaims'] = long(string.split(l)[0])
	    elif string.find( l, 'reclaims from free list' ) != -1:
		vmstat_dict['ctr_reclaims_from_free_list'] = long(string.split(l)[0])
	    elif string.find( l, 'micro (hat) faults' ) != -1:
		vmstat_dict['ctr_micro_hat_faults'] = long(string.split(l)[0])
	    elif string.find( l, 'minor (as) faults' ) != -1:
		vmstat_dict['ctr_minor_as_faults'] = long(string.split(l)[0])
	    elif string.find( l, 'major faults' ) != -1:
		vmstat_dict['ctr_major_faults'] = long(string.split(l)[0])
	    elif string.find( l, 'copy-on-write faults' ) != -1:
		vmstat_dict['ctr_copyonwrite_faults'] = long(string.split(l)[0])
	    elif string.find( l, 'zero fill page faults' ) != -1:
		vmstat_dict['ctr_zero_fill_page_faults'] = long(string.split(l)[0])
	    elif string.find( l, 'pages examined by the clock daemon' ) != -1:
		vmstat_dict['ctr_pages_examined_by_the_clock_daemon'] = long(string.split(l)[0])
	    elif string.find( l, 'revolutions of the clock hand' ) != -1:
		vmstat_dict['ctr_revolutions_of_the_clock_hand'] = long(string.split(l)[0])
	    elif string.find( l, 'pages freed by the clock daemon' ) != -1:
		vmstat_dict['ctr_pages_freed_by_the_clock_daemon'] = long(string.split(l)[0])
	    elif string.find( l, 'forks' ) != -1:
		vmstat_dict['ctr_forks'] = long(string.split(l)[0])
	    elif string.find( l, 'vforks' ) != -1:
		vmstat_dict['ctr_vforks'] = long(string.split(l)[0])
	    elif string.find( l, 'execs' ) != -1:
		vmstat_dict['ctr_execs'] = long(string.split(l)[0])
	    elif string.find( l, 'cpu context switches' ) != -1:
		vmstat_dict['ctr_cpu_context_switches'] = long(string.split(l)[0])
	    elif string.find( l, 'device interrupts' ) != -1:
		vmstat_dict['ctr_device_interrupts'] = long(string.split(l)[0])
	    elif string.find( l, 'traps' ) != -1:
		vmstat_dict['ctr_traps'] = long(string.split(l)[0])
	    elif string.find( l, 'system calls' ) != -1:
		vmstat_dict['ctr_system_calls'] = long(string.split(l)[0])
	    elif string.find( l, 'total name lookups' ) != -1:
		vmstat_dict['ctr_total_name_lookups'] = long(string.split(l)[0])
	    elif string.find( l, 'toolong' ) != -1:
		vmstat_dict['ctr_toolong'] = long(string.split(l)[0])
	    elif string.find( l, 'user   cpu' ) != -1:
		vmstat_dict['ctr_user_cpu'] = long(string.split(l)[0])
	    elif string.find( l, 'system cpu' ) != -1:
		vmstat_dict['ctr_system_cpu'] = long(string.split(l)[0])
	    elif string.find( l, 'idle   cpu' ) != -1:
		vmstat_dict['ctr_idle_cpu'] = long(string.split(l)[0])
	    elif string.find( l, 'wait   cpu' ) != -1:
		vmstat_dict['ctr_wait_cpu'] = long(string.split(l)[0])

	return vmstat_dict


    def _getuptime(self):
	"""Get system statistics from the output of the 'uptime' command.
	This should work for Solaris 2.5.1/2.6/2.7/2.8."""

	uptime_cmd = "/usr/bin/uptime"

	(retval, output) = utils.safe_getstatusoutput( uptime_cmd )

	if retval != 0:
	    log.log( "<system>system._getuptime(): error calling '%s'"%(uptime_cmd), 5 )
	    return None

	uptime_dict = {}

	uptime_re = ".+up (?P<uptime>.+),\s*(?P<users>[0-9]+) users?,\s+ load average:\s+(?P<loadavg1>[0-9.]+),\s*(?P<loadavg5>[0-9.]+),\s*(?P<loadavg15>[0-9.]+)"
	inx = re.compile( uptime_re )
	sre = inx.search( output )
	if sre:
	    uptime_dict = sre.groupdict()
	else:
	    log.log( "<system>system._getuptime(): could not parse uptime output '%s'"%(output), 5 )
	    return None

	# convert types
	uptime_dict['users'] = int(uptime_dict['users'])
	uptime_dict['loadavg1'] = float(uptime_dict['loadavg1'])
	uptime_dict['loadavg5'] = float(uptime_dict['loadavg5'])
	uptime_dict['loadavg15'] = float(uptime_dict['loadavg15'])

	return uptime_dict


    def _getvmstat2(self):
	"""Get system statistics from the output of the 'vmstat' command.
	This is only used to get free memory and free swap currently.
	This should work for Solaris 2.5.1/2.6/2.7/2.8."""

	vmstat_cmd = "/usr/bin/vmstat 1 2 | /usr/bin/tail -1"

	(retval, output) = utils.safe_getstatusoutput( vmstat_cmd )

	if retval != 0:
	    log.log( "<system>system._getvmstat2(): error calling '%s'"%(vmstat_cmd), 5 )
	    return None

	v_split = string.split( output )
	if len(v_split) < 5:
	    log.log( "<system>system._getvmstat2(): vmstat output invalid, '%s'"%(output), 5 )
	    return None

	vmstat_dict = {}
	try:
	    vmstat_dict['procs_running'] = int(v_split[0])
	    vmstat_dict['procs_blocked'] = int(v_split[1])
	    vmstat_dict['procs_waiting'] = int(v_split[2])
	    vmstat_dict['mem_swapfree'] = int(v_split[3])
	    vmstat_dict['mem_free'] = int(v_split[4])
	except ValueError:
	    log.log( "<system>system._getvmstat2(): could not parse vmstat output '%s'"%(output), 5 )
	    return None

	return vmstat_dict


    def _getTop(self):
        """Get some stastics from the 'top' command.
        This was the old way and is being replaced by the above calls.
	This should be removed by the next release...
	"""

	datahash = {}

	if not os.path.exists('/opt/local/bin/top'):
	    return None

	# Use of /opt/local/bin/top to get system stats is being phased out...
	rawList = utils.safe_popen('/opt/local/bin/top -nud2 -s1', 'r')

	# the above 'top' command actually performs two 'tops', 1 second apart,
	# so that we can get current cpu time allocation (idle/etc).
	# We must skip through the output to the start of the second 'top'.

	rawList.readline()	# skip start of first 'top'

	while 1:
	    line = rawList.readline()
	    if len(line) == 0:
		log.log( "<system>system._getSystemstate(): error parsing 'top' output looking for 'load averages:'.", 5 )
		utils.safe_pclose( rawList )
		return None

	    #if line[:8] == 'last pid':
	    if string.find(line, 'load averages:') != -1:
		break
 
	# regexps for parsing top of 'top' output to get info we want
	#reline1 = "last pid:\s*([0-9]+);\s*load averages:\s*([0-9]+\.[0-9]+),\s*([0-9]+\.[0-9]+),\s*([0-9]+\.[0-9]+)\s+([0-9]+:[0-9]+:[0-9]+)"
	reline1 = ".*load averages:\s*([0-9]+\.[0-9]+),\s*([0-9]+\.[0-9]+),\s*([0-9]+\.[0-9]+)\s+([0-9]+:[0-9]+:[0-9]+)"
	reline2 = "([0-9]+)\s+processes:(?:\s+(?P<sleeping>[0-9]+)\s+sleeping,)?(?:\s+(?P<zombie>[0-9]+)\s+zombie,)?(?:\s+(?P<running>[0-9]+)\s+running,)?(?:\s+(?P<stopped>[0-9]+)\s+stopped,)?(?:\s+(?P<oncpu>[0-9]+)\s+on cpu)?.*"
	reline3 = "CPU states:\s*([0-9.]+)% idle,\s*([0-9.]+)% user,\s*([0-9.]+)% kernel,\s*([0-9.]+)% iowait,\s*([0-9.]+)% swap"
	#reline4 = "Memory:\s*(?P<mem_real>\w+)\s*real,\s*(?P<mem_free>\w+)\s*free,(?:\s*(?P<mem_swapuse>\w+)\s*swap in use,)?\s*(?P<mem_swapfree>\w+)\s*swap free"

	# line 1
	inx = re.search( reline1, line )
	if inx == None:
	    log.log( "<system>system._getSystemstate() error parsing line1 'top' output.", 5 )
	    utils.safe_pclose( rawList )
	    return None
	## Handled by _getuptime() now
	#lastpid = int(inx.group(1))
	#loadavg1 = float(inx.group(1))
	#loadavg5 = float(inx.group(2))
	#loadavg15 = float(inx.group(3))
	#time = inx.group(4)

	# line 2
	line = rawList.readline()
	inx = re.search( reline2, line )
	if inx == None:
	    log.log( "<system>system._getSystemstate(): error parsing line2 'top' output.", 5 )
	    utils.safe_pclose( rawList )
	    return None
	processes = int(inx.group(1))
	try:
	    sleeping = int(inx.group('sleeping'))
	except:
	    sleeping = 0
	try:
	    zombie = int(inx.group('zombie'))
	except:
	    zombie = 0
	try:
	    running = int(inx.group('running'))
	except:
	    running = 0
	try:
	    stopped = int(inx.group('stopped'))
	except:
	    stopped = 0
	try:
	    oncpu = int(inx.group('oncpu'))
	except:
	    oncpu = 0

	# line 3
	line = rawList.readline()
	inx = re.search( reline3, line )
	if inx == None:
	    log.log( "<system>system._getSystemstate(): error parsing line3 'top' output.", 5 )
	    utils.safe_pclose( rawList )
	    return None
	cpu_idle = float(inx.group(1))
	cpu_user = float(inx.group(2))
	cpu_kernel = float(inx.group(3))
	cpu_iowait = float(inx.group(4))
	cpu_swap = float(inx.group(5))

	utils.safe_pclose( rawList )

	datahash['processes'] = processes
	datahash['sleeping'] = sleeping
	datahash['zombie'] = zombie
	datahash['running'] = running
	datahash['stopped'] = stopped
	datahash['oncpu'] = oncpu

	datahash['cpu_idle'] = cpu_idle
	datahash['cpu_user'] = cpu_user
	datahash['cpu_kernel'] = cpu_kernel
	datahash['cpu_iowait'] = cpu_iowait
	datahash['cpu_swap'] = cpu_swap

        return datahash


##
## END - system.py
##
