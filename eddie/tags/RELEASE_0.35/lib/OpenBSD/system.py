## 
## File		: system.py
## 
## Author       : Chris Miles <chris@psychofx.com>
##              : John McInnes <john@dissension.net>
## 
## Start Date	: 20021202
## 
## Description	: Collect current snapshot of system state for OpenBSD
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
  an OpenBSD system.
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
                ctr_pages_managed                               - (long)
                ctr_pages_free                                  - (long)
                ctr_pages_active                                - (long)
                ctr_pages_inactive                              - (long)
                ctr_pages_being_paged_out                       - (long)
                ctr_pages_wired                                 - (long)
                ctr_pages_reserved for pagedaemon               - (long)
                ctr_pages_reserved_for_kernel                   - (long)
                ctr_swap_pages                                  - (long)
                ctr_swap_pages_in_use                           - (long)
                ctr_total_anons_in_system                       - (long)
                ctr_free_anons                                  - (long)
                ctr_page_faults                                 - (long)
                ctr_traps                                       - (long)
                ctr_interrupts                                  - (long)
                ctr_cpu_context_switches                        - (long)
                ctr_software_interrupts                         - (long)
                ctr_system_calls                                - (long)
                ctr_page_ins_                                   - (long)
                ctr_swap_ins                                    - (long)
                ctr_swap_outs                                   - (long)
                ctr_forks                                       - (long)
                ctr_forks_where_vmspace_is_shared               - (long)
                ctr_number_of_times_the_pagedaemon_woke_up      - (long)
                ctr_revolutions_of_the_clock_hand               - (long)
                ctr_pages_freed_by_pagedaemon                   - (long)
                ctr_pages_scanned_by_pagedaemon                 - (long)
                ctr_pages_reactivated_by_pagedaemon             - (long)
                ctr_busy_pages_found_by_pagedaemon              - (long)
                ctr_total_name_lookups                          - (long)
                ctr_select collisions                           - (long)
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
            if string.find( l, 'pages managed' ) != -1:
                vmstat_dict['ctr_pages_managed'] = long(string.split(l)[0])
            elif string.find( l, 'pages free' ) != -1:
                vmstat_dict['ctr_pages_free'] = long(string.split(l)[0])
            elif string.find( l, 'pages active' ) != -1:
                vmstat_dict['ctr_pages_active'] = long(string.split(l)[0])
            elif string.find( l, 'pages inactive' ) != -1:
                vmstat_dict['ctr_pages_inactive'] = long(string.split(l)[0])
            elif string.find( l, 'pages being paged out' ) != -1:
                vmstat_dict['ctr_pages_being_paged_out'] = long(string.split(l)[0])
            elif string.find( l, 'pages wired' ) != -1:
                vmstat_dict['ctr_pages_wired'] = long(string.split(l)[0])
            elif string.find( l, 'pages reserved for pagedaemon' ) != -1:
                vmstat_dict['ctr_pages_reserved_for_pagedaemon'] = long(string.split(l)[0])
            elif string.find( l, 'pages reserved for kernel' ) != -1:
                vmstat_dict['ctr_pages_reserved_for_kernel'] = long(string.split(l)[0])
            elif string.find( l, 'swap pages' ) != -1:
                vmstat_dict['ctr_swap_pages'] = long(string.split(l)[0])
            elif string.find( l, 'swap pages in use' ) != -1:
                vmstat_dict['ctr_swap_pages_in_use'] = long(string.split(l)[0])
            elif string.find( l, 'total anon\'s in system' ) != -1:
                vmstat_dict['ctr_total_anons_in_system'] = long(string.split(l)[0])
            elif string.find( l, 'free anon\'s' ) != -1:
                vmstat_dict['ctr_free_anons'] = long(string.split(l)[0])
            elif string.find( l, 'page faults' ) != -1:
                vmstat_dict['ctr_page_faults'] = long(string.split(l)[0])
            elif string.find( l, 'traps' ) != -1:
                vmstat_dict['ctr_traps'] = long(string.split(l)[0])
            elif string.find( l, 'interrupts' ) != -1:
                vmstat_dict['ctr_interrupts'] = long(string.split(l)[0])
            elif string.find( l, 'cpu context switches' ) != -1:
                vmstat_dict['ctr_cpu_context_switches'] = long(string.split(l)[0])
            elif string.find( l, 'software interrupts' ) != -1:
                vmstat_dict['ctr_software_interrupts'] = long(string.split(l)[0])
            elif string.find( l, 'syscalls' ) != -1:
                vmstat_dict['ctr_system_calls'] = long(string.split(l)[0])
            elif string.find( l, 'pagein operations' ) != -1:
                vmstat_dict['ctr_page_ins'] = long(string.split(l)[0])
            elif string.find( l, 'swap ins' ) != -1:
                vmstat_dict['ctr_swap_ins'] = long(string.split(l)[0])
            elif string.find( l, 'swap outs' ) != -1:
                vmstat_dict['ctr_swap_outs'] = long(string.split(l)[0])
            elif string.find( l, 'forks' ) != -1:
                vmstat_dict['ctr_forks'] = long(string.split(l)[0])
            elif string.find( l, 'forks where vmspace is shared' ) != -1:
                vmstat_dict['ctr_forks_where_vmspace_is_shared'] = long(string.split(l)[0])
            elif string.find( l, 'number of times the pagedeamon woke up' ) != -1:
                vmstat_dict['ctr_number_of_times_the_pagedaemon_woke_up'] = long(string.split(l)[0])
            elif string.find( l, 'revolutions of the clock hand' ) != -1:
                vmstat_dict['ctr_revolutions_of_the_clock_hand'] = long(string.split(l)[0])
            elif string.find( l, 'pages freed by pagedaemon' ) != -1:
                vmstat_dict['ctr_pages_freed_by_pagedaemon'] = long(string.split(l)[0])
            elif string.find( l, 'pages scanned by pagedaemon' ) != -1:
                vmstat_dict['ctr_pages_scanned_by_pagedaemon'] = long(string.split(l)[0])
            elif string.find( l, 'pages reactivated by pagedaemon' ) != -1:
                vmstat_dict['ctr_pages_reactiviated_by_pagedaemon'] = long(string.split(l)[0])
            elif string.find( l, 'busy pages found by pagedaemon' ) != -1:
                vmstat_dict['ctr_busy_pages_found_by_pagedaemon'] = long(string.split(l)[0])
            elif string.find( l, 'total name lookups' ) != -1:
                vmstat_dict['ctr_total_name_lookups'] = long(string.split(l)[0])
            elif string.find( l, 'select collisions' ) != -1:
                vmstat_dict['ctr_select_collisions'] = long(string.split(l)[0])

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


##
## END - system.py
##
