## 
## File		: system.py
## 
## Author       : Chris Miles <chris@psychofx.com>
## 
## Start Date	: 20041206
## 
## Description	: Collect current snapshot of system state for FreeBSD
##
## $Id$
##
########################################################################
## (C) Chris Miles 2004
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
  a FreeBSD system.
  The following statistics are currently collected and made available to
  directives that request it (e.g., SYS):

  (See system class doc info below.)
"""


# Python modules
import string
import re
# Eddie modules
import datacollect
import log
import utils


class system(datacollect.DataCollect):
    """Gathers system statistics.

        Calls the following external commands to get stats from:
        /usr/bin/vmstat -s
        /usr/bin/uptime

        The names of all the stats collected by the system class are:

            System stats from '/usr/bin/uptime':
                uptime          - (string)
                users           - (int)
                loadavg1        - (float)
                loadavg5        - (float)
                loadavg15       - (float)

            System counters from '/usr/bin/vmstat -s' (see vmstat(1)):
                ctr_cpu_context_switches                  - (long)
                ctr_device_interrupts                     - (long)
                ctr_software_interrupts                   - (long)
                ctr_traps                                 - (long)
                ctr_system_calls                          - (long)
                ctr_swap_pager_pageins                    - (long)
                ctr_swap_pager_pages_paged_in             - (long)
                ctr_swap_pager_pageouts                   - (long)
                ctr_swap_pager_pages_paged_out            - (long)
                ctr_vnode_pager_pageins                   - (long)
                ctr_vnode_pager_pages_paged_in            - (long)
                ctr_vnode_pager_pageouts                  - (long)
                ctr_vnode_pager_pages_paged_out           - (long)
                ctr_page_daemon_wakeups                   - (long)
                ctr_pages_examined_by_the_page_daemon     - (long)
                ctr_pages_reactivated                     - (long)
                ctr_copyonwrite_faults                    - (long)
                ctr_copyonwrite_optimized_faults          - (long)
                ctr_zero_fill_pages_zeroed                - (long)
                ctr_zero_fill_pages_prezeroed             - (long)
                ctr_intransit_blocking_page_faults        - (long)
                ctr_pages_freed                           - (long)
                ctr_pages_freed_by_daemon                 - (long)
                ctr_pages_freed_by_exiting_processes      - (long)
                ctr_pages_freed_by_exiting_processes      - (long)
                ctr_total_name_lookups                    - (long)
    """

    def __init__(self):
	apply( datacollect.DataCollect.__init__, (self,) )



    ##################################################################
    # Public, thread-safe, methods



    ##################################################################
    # Private methods.  No thread safety if not using public methods.

    def collectData(self):
        """Collect system statistics data.
        """

	self.data.datahash = {}		# dict of system data

        vmstat_dict = self._getvmstat()
        if vmstat_dict:
            self.data.datahash.update(vmstat_dict)

        uptime_dict = self._getuptime()
        if uptime_dict:
            self.data.datahash.update(uptime_dict)

        swapinfo_dict = self._getswapinfo()
        if swapinfo_dict:
            self.data.datahash.update(swapinfo_dict)

	log.log( "<system>system.collectData(): new system list created", 7 )


    def _getvmstat(self):
        """Get system statistics from the 'vmstat -s' call.
	"""

        vmstat_cmd = "/usr/bin/vmstat -s"

        (retval, output) = utils.safe_getstatusoutput( vmstat_cmd )

        if retval != 0:
            log.log( "<system>system._getvmstat(): error calling '%s'"%(vmstat_cmd), 5 )
            return None

        vmstat_dict = {}

        for l in string.split( output, '\n' ):
            if string.find( l, 'cpu context switches' ) != -1:
                vmstat_dict['ctr_cpu_context_switches'] = long(string.split(l)[0])
            elif string.find( l, 'device interrupts' ) != -1:
                vmstat_dict['ctr_device_interrupts'] = long(string.split(l)[0])
            elif string.find( l, 'software interrupts' ) != -1:
                vmstat_dict['ctr_software_interrupts'] = long(string.split(l)[0])
            elif string.find( l, 'traps' ) != -1:
                vmstat_dict['ctr_traps'] = long(string.split(l)[0])
            elif string.find( l, 'system calls' ) != -1:
                vmstat_dict['ctr_system_calls'] = long(string.split(l)[0])
            elif string.find( l, 'swap pager pageins' ) != -1:
                vmstat_dict['ctr_swap_pager_pageins'] = long(string.split(l)[0])
            elif string.find( l, 'swap pager pages paged in' ) != -1:
                vmstat_dict['ctr_swap_pager_pages_paged_in'] = long(string.split(l)[0])
            elif string.find( l, 'swap pager pageouts' ) != -1:
                vmstat_dict['ctr_swap_pager_pageouts'] = long(string.split(l)[0])
            elif string.find( l, 'swap pager pages paged out' ) != -1:
                vmstat_dict['ctr_swap_pager_pages_paged_out'] = long(string.split(l)[0])
            elif string.find( l, 'vnode pager pageins' ) != -1:
                vmstat_dict['ctr_vnode_pager_pageins'] = long(string.split(l)[0])
            elif string.find( l, 'vnode pager pages paged in' ) != -1:
                vmstat_dict['ctr_vnode_pager_pages_paged_in'] = long(string.split(l)[0])
            elif string.find( l, 'vnode pager pageouts' ) != -1:
                vmstat_dict['ctr_vnode_pager_pageouts'] = long(string.split(l)[0])
            elif string.find( l, 'vnode pager pages paged out' ) != -1:
                vmstat_dict['ctr_vnode_pager_pages_paged_out'] = long(string.split(l)[0])
            elif string.find( l, 'page daemon wakeups' ) != -1:
                vmstat_dict['ctr_page_daemon_wakeups'] = long(string.split(l)[0])
            elif string.find( l, 'pages examined by the page daemon' ) != -1:
                vmstat_dict['ctr_pages_examined_by_the_page_daemon'] = long(string.split(l)[0])
            elif string.find( l, 'pages reactivated' ) != -1:
                vmstat_dict['ctr_pages_reactivated'] = long(string.split(l)[0])
            elif string.find( l, 'copy-on-write faults' ) != -1:
                vmstat_dict['ctr_copyonwrite_faults'] = long(string.split(l)[0])
            elif string.find( l, 'copy-on-write optimized faults' ) != -1:
                vmstat_dict['ctr_copyonwrite_optimized_faults'] = long(string.split(l)[0])
            elif string.find( l, 'zero fill pages zeroed' ) != -1:
                vmstat_dict['ctr_zero_fill_pages_zeroed'] = long(string.split(l)[0])
            elif string.find( l, 'zero fill pages prezeroed' ) != -1:
                vmstat_dict['ctr_zero_fill_pages_prezeroed'] = long(string.split(l)[0])
            elif string.find( l, 'intransit blocking page faults' ) != -1:
                vmstat_dict['ctr_intransit_blocking_page_faults'] = long(string.split(l)[0])
            elif string.find( l, 'pages freed' ) != -1:
                vmstat_dict['ctr_pages_freed'] = long(string.split(l)[0])
            elif string.find( l, 'pages freed by daemon' ) != -1:
                vmstat_dict['ctr_pages_freed_by_daemon'] = long(string.split(l)[0])
            elif string.find( l, 'pages freed by exiting processes' ) != -1:
                vmstat_dict['ctr_pages_freed_by_exiting_processes'] = long(string.split(l)[0])
            elif string.find( l, 'pages freed by exiting processes' ) != -1:
                vmstat_dict['ctr_pages_freed_by_exiting_processes'] = long(string.split(l)[0])
            elif string.find( l, 'total name lookups' ) != -1:
                vmstat_dict['ctr_total_name_lookups'] = long(string.split(l)[0])

        return vmstat_dict


    def _getuptime(self):
        """Get system statistics from the output of the 'uptime' command.
	"""

        uptime_cmd = "/usr/bin/uptime"

        (retval, output) = utils.safe_getstatusoutput( uptime_cmd )

        if retval != 0:
            log.log( "<system>system._getuptime(): error calling '%s'"%(uptime_cmd), 5 )
            return None

        uptime_re = ".+up (?P<uptime>.+),\s*(?P<users>[0-9]+) users?,\s+load averages:\s+(?P<loadavg1>[0-9.]+),\s*(?P<loadavg5>[0-9.]+),\s*(?P<loadavg15>[0-9.]+)"
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


    def _getswapinfo(self):
        """Get swap usage statistics from the output of 'pstat -sk'.
	"""

        swapinfo_cmd = "/usr/sbin/pstat -sk"

        (retval, output) = utils.safe_getstatusoutput( swapinfo_cmd )

        if retval != 0:
            log.log( "<system>system._getswapinfo(): error calling '%s'"%(swapinfo_cmd), 5 )
            return None

	swapinfo_dict = {}

	# Parse the output and record the swap usage info of the last
	# line.  If there's only a single swap device, this will be the
	# total usage.  If there are 2 or more swap devices, the last
	# line will be a grand total.
	# TODO: record stats for all swap devices individually
        l = string.split( output, '\n' )[-1]

	if l[:5] == 'Total':	# how many fields to expect
	    fieldnum = 5
	else:
	    fieldnum = 6

	fields = l.split()
	if len(fields) != fieldnum:
	    log.log( "<system>system._getswapinfo(): could not parse '%s' output line '%s'"%(swapinfo_cmd,l), 5 )
	    return None

	swapinfo_dict['swap_device'] = fields[0]	# either the swap device or "Total"
	swapinfo_dict['swap_size'] = fields[1]
	swapinfo_dict['swap_used'] = fields[2]
	swapinfo_dict['swap_available'] = fields[3]
	# ignore fields[4] (capacity %)
	# ignore fields[5] (Type, but only for a device line)

	return swapinfo_dict


##
## END - system.py
##
