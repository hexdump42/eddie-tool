
'''
File                : system.py

Start Date        : 19990520

Description        :
  This is an Eddie data collector.  It collects System data and statistics
  on a Solaris system.

  Data collectors provided by this module:
    - system: collects system stats.  See the class doc below for details
      of exactly which statistics are gathered and what they are called in
      the EDDIE environment.

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
import string
import re

# Eddie modules
from eddietool.common import datacollect, log, utils


class system(datacollect.DataCollect):
    """
    Gathers system statistics.

    Calls the following external commands to get stats from:
    /usr/bin/vmstat -s: standard with Solaris 2.5.1 and greater
    /usr/bin/uptime: standard with Solaris 2.5.1 and greater

    The names of all the stats collected by the system class are:

    System stats from '/usr/bin/uptime':
        uptime                - time since last boot (string)
        users                - number of logged on users (int)
        loadavg1        - 1 minute load average (float)
        loadavg5        - 5 minute load average (float)
        loadavg15        - 15 minute load average (float)

    System counters from '/usr/bin/vmstat -s' (see vmstat(1M)):
        ctr_swap_ins                                - (long)
        ctr_swap_outs                                - (long)
        ctr_pages_swapped_in                        - (long)
        ctr_pages_swapped_out                        - (long)
        ctr_total_address_trans_faults_taken        - (long)
        ctr_page_ins                                - (long)
        ctr_page_outs                                - (long)
        ctr_pages_paged_in                        - (long)
        ctr_pages_paged_out                        - (long)
        ctr_total_reclaims                        - (long)
        ctr_reclaims_from_free_list                - (long)
        ctr_micro_hat_faults                        - (long)
        ctr_minor_as_faults                        - (long)
        ctr_major_faults                        - (long)
        ctr_copyonwrite_faults                        - (long)
        ctr_zero_fill_page_faults                - (long)
        ctr_pages_examined_by_the_clock_daemon        - (long)
        ctr_revolutions_of_the_clock_hand        - (long)
        ctr_pages_freed_by_the_clock_daemon        - (long)
        ctr_forks                                - (long)
        ctr_vforks                                - (long)
        ctr_execs                                - (long)
        ctr_cpu_context_switches                - (long)
        ctr_device_interrupts                        - (long)
        ctr_traps                                - (long)
        ctr_system_calls                        - (long)
        ctr_total_name_lookups                        - (long)
        ctr_toolong                                - (long)
        ctr_user_cpu                                - (long)
        ctr_system_cpu                                - (long)
        ctr_idle_cpu                                - (long)
        ctr_wait_cpu                                - (long)

    Process/memory stats from '/usr/bin/vmstat' (see vmstat(1M)):
        procs_running        - number of processes running (int)
        procs_blocked        - number of processes blocked (int)
        procs_waiting        - number of processes waiting (int)
        mem_swapfree        - amount of free swap (bytes) (int)
        mem_free        - amount of free RAM (bytes) (int)
        page_reclaims        - page reclaims (int)
        minor_faults        - minor faults (int)
        kb_paged_in        - kilobytes paged in (int)
        kb_paged_out        - kilobytes paged out (int)
        kb_freed        - kilobytes freed (int)
        kb_deficit        - anticipated short-term memory shortfall (Kbytes) (int)
        scan_rate        - pages scanned by clock algorithm (int)
        device_interrupts - (non clock) device interrupts (int)
        system_calls        - system calls (int)
        cpu_context_switches - CPU context switches (int)
        cpu_user        - percentage of cpu in user mode (float)
        cpu_system        - percentage of cpu in kernel mode (float)
        cpu_idle        - percentage of cpu in idle thread (float)
    """

    def __init__(self):
        apply( datacollect.DataCollect.__init__, (self,) )



    ##################################################################
    # Public, thread-safe, methods

    # none special to this class


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

        vmstat2_dict = self._getvmstat2()
        if vmstat2_dict:
            self.data.datahash.update(vmstat2_dict)

        uptime_dict = self._getuptime()
        if uptime_dict:
            self.data.datahash.update(uptime_dict)


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

        # uptime_re matches standard /usr/bin/uptime output such as:
        #   2:06pm  up 490 day(s), 10:46,  4 users,  load average: 0.62, 0.59, 0.71
        uptime_re = ".+up (?P<uptime>.+),\s*(?P<users>[0-9]+) users?,\s+ load average:\s+(?P<loadavg1>[0-9.]+),\s*(?P<loadavg5>[0-9.]+),\s*(?P<loadavg15>[0-9.]+)"
        inx = re.compile( uptime_re )
        sre = inx.search( output )
        if sre:
            uptime_dict = sre.groupdict()
        else:
            # chris 20040923: Sometimes the "day(s)" section is missing (usually if
            # wtmpx rotated more often than the system boot, thus losing the last
            # 'reboot' entry) # so try a second regexp for output such as:
            #  2:05pm  5 users,  load average: 1.78, 5.57, 5.39
            uptime2_re = ".+[0-9:apm]+\s*(?P<users>[0-9]+) users?,\s+ load average:\s+(?P<loadavg1>[0-9.]+),\s*(?P<loadavg5>[0-9.]+),\s*(?P<loadavg15>[0-9.]+)"
            inx = re.compile( uptime2_re )
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
        This should work for Solaris 2.5.1/2.6/2.7/2.8."""

        vmstat_cmd = "/usr/bin/vmstat 1 2 | /usr/bin/tail -1"

        (retval, output) = utils.safe_getstatusoutput( vmstat_cmd )

        if retval != 0:
            log.log( "<system>system._getvmstat2(): error calling '%s'"%(vmstat_cmd), 5 )
            return None

        v_split = string.split( output )
        if len(v_split) != 22:
            log.log( "<system>system._getvmstat2(): vmstat output invalid, '%s'"%(output), 5 )
            return None

        vmstat_dict = {}
        try:
            vmstat_dict['procs_running'] = int(v_split[0])
            vmstat_dict['procs_blocked'] = int(v_split[1])
            vmstat_dict['procs_waiting'] = int(v_split[2])
            vmstat_dict['mem_swapfree'] = int(v_split[3]) * 1024    # bytes
            vmstat_dict['mem_free'] = int(v_split[4]) * 1024    # bytes
            vmstat_dict['page_reclaims'] = int(v_split[5])
            vmstat_dict['minor_faults'] = int(v_split[6])
            vmstat_dict['kb_paged_in'] = int(v_split[7])
            vmstat_dict['kb_paged_out'] = int(v_split[8])
            vmstat_dict['kb_freed'] = int(v_split[9])
            vmstat_dict['kb_deficit'] = int(v_split[10])
            vmstat_dict['scan_rate'] = int(v_split[11])
            #vmstat_dict['disk1'] = int(v_split[12]) # disk stats not used
            #vmstat_dict['disk2'] = int(v_split[13])
            #vmstat_dict['disk3'] = int(v_split[14])
            #vmstat_dict['disk4'] = int(v_split[15])
            vmstat_dict['device_interrupts'] = int(v_split[16])
            vmstat_dict['system_calls'] = int(v_split[17])
            vmstat_dict['cpu_context_switches'] = int(v_split[18])
            vmstat_dict['cpu_user'] = float(v_split[19])
            vmstat_dict['cpu_system'] = float(v_split[20])
            vmstat_dict['cpu_idle'] = float(v_split[21])
        except ValueError:
            log.log( "<system>system._getvmstat2(): could not parse vmstat output '%s'"%(output), 5 )
            return None

        return vmstat_dict



##
## END - system.py
##
