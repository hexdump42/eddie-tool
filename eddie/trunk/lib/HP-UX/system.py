
'''
File                : system.py

Start Date        : 19990520

Description        :
  This is an Eddie data collector.  It collects System data and statistics on
  an HP-UX system.
  The following statistics are currently collected and made available to
  directives that request it (e.g., SYS):

  (See system class doc info below.)

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 1999-2005'

__author__ = 'Chris Miles; Rod Telford'

__license__ = '''
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
'''



# Python modules
import string, re
# Eddie modules
import datacollect, log, utils


class system(datacollect.DataCollect):
    """Gathers system statistics.

        Calls the following external commands to get stats from:
        /usr/bin/vmstat -s: tested on HPUX 11.00
        /usr/bin/uptime: tested on HPUX 11.00

        The names of all the stats collected by the system class are:

            System stats from '/usr/bin/uptime':
                uptime          - (string)
                users           - (int)
                loadavg1        - (float)
                loadavg5        - (float)
                loadavg15       - (float)

            System counters from '/usr/bin/vmstat -s' (see vmstat(1)):
                ctr_swap_ins                                    - (long)
                ctr_swap_outs                                   - (long)
                ctr_pages_swapped_in                            - (long)
                ctr_pages_swapped_out                           - (long)
                ctr_total_address_trans_faults_taken            - (long)
                ctr_page_ins                                    - (long)
                ctr_page_outs                                   - (long)
                ctr_pages_paged_in                              - (long)
                ctr_pages_paged_out                             - (long)
                ctr_reclaims_from_free_list                     - (long)
                ctr_total_page_reclaims                         - (long)
                ctr_intransit_blocking_page_faults              - (long)
                ctr_zero_fill_pages_created                     - (long)
                ctr_zero_fill_page_faults                       - (long)
                ctr_executable_fill_pages_created               - (long)
                ctr_executable_fill_page_faults                 - (long)
                ctr_swap_text_pages_found_in_free_list          - (long)
                ctr_inode_text_pages_found_in_free_list         - (long)
                ctr_revolutions_of_the_clock_hand               - (long)
                ctr_pages_scanned_for_page_out                  - (long)
                ctr_pages_freed_by_the_clock_daemon             - (long)
                ctr_cpu_context_switches                        - (long)
                ctr_device_interrupts                           - (long)
                ctr_traps                                       - (long)
                ctr_system_calls                                - (long)
                ctr_Page_Select_Size_Successes_for_Page_size_4K - (long)
                ctr_Page_Select_Size_Successes_for_Page_size_16K - (long)
                ctr_Page_Select_Size_Successes_for_Page_size_64K - (long)
                ctr_Page_Select_Size_Successes_for_Page_size_256K - (long)
                ctr_Page_Select_Size_Failures_for_Page_size_16K - (long)
                ctr_Page_Select_Size_Failures_for_Page_size_64K - (long)
                ctr_Page_Select_Size_Failures_for_Page_size_256K - (long)
                ctr_Page_Allocate_Successes_for_Page_size_4K    - (long)
                ctr_Page_Allocate_Successes_for_Page_size_16K   - (long)
                ctr_Page_Allocate_Successes_for_Page_size_64K   - (long)
                ctr_Page_Allocate_Successes_for_Page_size_256K  - (long)
                ctr_Page_Allocate_Successes_for_Page_size_64M   - (long)
                ctr_Page_Demotions_for_Page_size_16K            - (long)
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

        self.data.datahash = {}                # dict of system data

        vmstat_dict = self._getvmstat()
        if vmstat_dict:
            self.data.datahash.update(vmstat_dict)

        uptime_dict = self._getuptime()
        if uptime_dict:
            self.data.datahash.update(uptime_dict)

        log.log( "<system>system.collectData(): new system list created", 7 )


    def _getvmstat(self):
        """Get system statistics from the 'vmstat -s' call."""

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
            elif string.find( l, 'reclaims from free list' ) != -1:
                vmstat_dict['ctr_reclaims_from_free_list'] = long(string.split(l)[0])
            elif string.find( l, 'total page reclaims' ) != -1:
                vmstat_dict['ctr_total_page_reclaims'] = long(string.split(l)[0])
            elif string.find( l, 'intransit blocking page faults' ) != -1:
                vmstat_dict['ctr_intransit_blocking_page_faults'] = long(string.split(l)[0])
            elif string.find( l, 'zero fill pages created' ) != -1:
                vmstat_dict['ctr_zero_fill_pages_created'] = long(string.split(l)[0])
            elif string.find( l, 'zero fill page faults' ) != -1:
                vmstat_dict['ctr_zero_fill_page_faults'] = long(string.split(l)[0])
            elif string.find( l, 'executable fill pages created' ) != -1:
                vmstat_dict['ctr_executable_fill_pages_created'] = long(string.split(l)[0])
            elif string.find( l, 'executable fill page faults' ) != -1:
                vmstat_dict['ctr_executable_fill_page_faults'] = long(string.split(l)[0])
            elif string.find( l, 'swap text pages found in free list' ) != -1:
                vmstat_dict['ctr_swap_text_pages_found_in_free_list'] = long(string.split(l)[0])
            elif string.find( l, 'inode text pages found in free list' ) != -1:
                vmstat_dict['ctr_inode_text_pages_found_in_free_list'] = long(string.split(l)[0])
            elif string.find( l, 'revolutions of the clock hand' ) != -1:
                vmstat_dict['ctr_revolutions_of_the_clock_hand'] = long(string.split(l)[0])
            elif string.find( l, 'pages scanned for page out' ) != -1:
                vmstat_dict['ctr_pages_scanned_for_page_out'] = long(string.split(l)[0])
            elif string.find( l, 'pages freed by the clock daemon' ) != -1:
                vmstat_dict['ctr_pages_freed_by_the_clock_daemon'] = long(string.split(l)[0])
            elif string.find( l, 'cpu context switches' ) != -1:
                vmstat_dict['ctr_cpu_context_switches'] = long(string.split(l)[0])
            elif string.find( l, 'device interrupts' ) != -1:
                vmstat_dict['ctr_device_interrupts'] = long(string.split(l)[0])
            elif string.find( l, 'traps' ) != -1:
                vmstat_dict['ctr_traps'] = long(string.split(l)[0])
            elif string.find( l, 'system calls' ) != -1:
                vmstat_dict['ctr_system_calls'] = long(string.split(l)[0])
            elif string.find( l, 'Page Select Size Successes for Page size 4K' ) != -1:
                vmstat_dict['ctr_Page_Select_Size_Successes_for_Page_size_4K'] = long(string.split(l)[0])
            elif string.find( l, 'Page Select Size Successes for Page size 16K' ) != -1:
                vmstat_dict['ctr_Page_Select_Size_Successes_for_Page_size_16K'] = long(string.split(l)[0])
            elif string.find( l, 'Page Select Size Successes for Page size 64K' ) != -1:
                vmstat_dict['ctr_Page_Select_Size_Successes_for_Page_size_64K'] = long(string.split(l)[0])
            elif string.find( l, 'Page Select Size Successes for Page size 256K' ) != -1:
                vmstat_dict['ctr_Page_Select_Size_Successes_for_Page_size_256K'] = long(string.split(l)[0])
            elif string.find( l, 'Page Select Size Failures for Page size 16K' ) != -1:
                vmstat_dict['ctr_Page_Select_Size_Failures_for_Page_size_16K'] = long(string.split(l)[0])
            elif string.find( l, 'Page Select Size Failures for Page size 64K' ) != -1:
                vmstat_dict['ctr_Page_Select_Size_Failures_for_Page_size_64K'] = long(string.split(l)[0])
            elif string.find( l, 'Page Select Size Failures for Page size 256K' ) != -1:
                vmstat_dict['ctr_Page_Select_Size_Failures_for_Page_size_256K'] = long(string.split(l)[0])
            elif string.find( l, 'Page Allocate Successes for Page size 4K' ) != -1:
                vmstat_dict['ctr_Page_Allocate_Successes_for_Page_size_4K'] = long(string.split(l)[0])
            elif string.find( l, 'Page Allocate Successes for Page size 16K' ) != -1:
                vmstat_dict['ctr_Page_Allocate_Successes_for_Page_size_16K'] = long(string.split(l)[0])
            elif string.find( l, 'Page Allocate Successes for Page size 64K' ) != -1:
                vmstat_dict['ctr_Page_Allocate_Successes_for_Page_size_64K'] = long(string.split(l)[0])
            elif string.find( l, 'Page Allocate Successes for Page size 256K' ) != -1:
                vmstat_dict['ctr_Page_Allocate_Successes_for_Page_size_256K'] = long(string.split(l)[0])
            elif string.find( l, 'Page Allocate Successes for Page size 64M' ) != -1:
                vmstat_dict['ctr_Page_Allocate_Successes_for_Page_size_64M'] = long(string.split(l)[0])
            elif string.find( l, 'Page Demotions for Page size 16K' ) != -1:
                vmstat_dict['ctr_Page_Demotions_for_Page_size_16K'] = long(string.split(l)[0])

        return vmstat_dict


    def _getuptime(self):
        """Get system statistics from the output of the 'uptime' command."""

        uptime_cmd = "/usr/bin/uptime"

        (retval, output) = utils.safe_getstatusoutput( uptime_cmd )

        if retval != 0:
            log.log( "<system>system._getuptime(): error calling '%s'"%(uptime_cmd), 5 )
            return None

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


##
## END - system.py
##
