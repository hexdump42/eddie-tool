
'''
File                : proc.py 

Start Date        : 20010709

Description        :
  Library of classes that deal with a machine's process table

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 2001-2005'

__author__ = 'Chris Miles'

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


# Python imports
import os, string, time, threading

# Eddie imports
from eddietool.common import log, utils


# List of interpreters - default empty
interpreters = []

class procList:
    """Class procList - holds a list of running processes and related information."""

    # refresh_rate : amount of time current process list will be cached before
    #                refreshing with new process list (in seconds)
    refresh_rate = 60

    def __init__(self):
        self.refresh_time = 0        # process list must be refreshed at first request

        self.semaphore = threading.Semaphore()  # must be thread-friendly now


    ##################################################################
    # Public, thread-safe, methods

    def refresh(self):
        """Force a refresh of the process list."""

        self.semaphore.acquire()
        self._refresh()
        self.semaphore.release()


    def procExists(self, procname):
        """Searches the 'ps' dictionary and returns number of occurrences
        of procname."""

        self.semaphore.acquire()
        self._checkCache()        # refresh process data if necessary

        count = 0                # count number of occurrences of 'procname'
        for i in self.list:
            command = i.comdname
            if command == procname or i.procname == procname:
                count = count + 1

        self.semaphore.release()

        return count


    def pidExists(self, pid):
        """Searches the 'ps' dictionary and returns number of occurrences
        of pid (should be 0 or 1 for any sane system...)"""

        self.semaphore.acquire()
        self._checkCache()        # refresh process data if necessary

        count = 0                # count number of occurrences of 'pid'
        for i in self.list:
            if i.pid == pid:
                count = count + 1

        self.semaphore.release()

        return count


    def getList(self):
        """Return copy of process list."""

        return self.list


    def __getitem__(self, name):
        """Overload '[]', eg: returns corresponding proc object for given
        process name."""

        self.semaphore.acquire()
        self._checkCache()        # refresh process data if necessary

        try:
            r = self.nameHash[name]
        except KeyError:
            r = None

        self.semaphore.release()

        return r


    def allprocs(self):
        """Return dictionary of all processes (which are dictionaries of each process' details."""

        self.semaphore.acquire()
        self._checkCache()        # refresh process data if necessary

        allprocs = {}

        for p in self.nameHash.keys():
            allprocs[p] = self.nameHash[p].procinfo()

        self.semaphore.release()

        return allprocs


    def __str__(self):

        # note: don't do cache check - assume we want to display current data

        #rv = 'PID     USER            COMMAND                 TIME            CPU     STATUS\n'
        rv = ''

        self.semaphore.acquire()
         for item in self.list:
             rv = rv + str(item) + '\n'
        self.semaphore.release()

        return(rv)


    ##################################################################
    # Private methods.  No thread safety if not using public methods.

    def _refresh(self):
        """Refresh the process list"""

        self._getProcList()

        # new refresh time is current time + refresh rate (seconds)
        self.refresh_time = time.time() + self.refresh_rate


    def _checkCache(self):
        """Check if cached procList data is invalid, ie: refresh_time has
        been exceeded."""

        if time.time() > self.refresh_time:
            log.log( "<proc>procList._checkCache(): refreshing procList", 7 )
            self._refresh()
        else:
            log.log( "<proc>procList._checkCache(): using cached procList", 7 )


    def _getProcList(self):
        self.hash = {}                # dict of processes keyed by pid
        self.list = []                # list of processes
        self.nameHash = {}        # dict of processes keyed by process name
         
        rawList = utils.safe_popen('ps -elf', 'r')
        rawList.readline()
 
        for line in rawList.readlines():
            p = proc(line)
            self.list.append(p)
            self.hash[p.pid] = p
            #self.nameHash[string.split(p.comm, '/')[-1]] = p
            self.nameHash[p.procname] = p

        utils.safe_pclose( rawList )

        log.log( "<proc>procList._procList(): new proc list created", 7 )



##
## Class proc : holds a process record
##
class proc:
    def __init__(self, rawline):

        fields = string.split(rawline)

        # fields as defined from "ps -elf"
        self.f =        int(fields[ 0])
        self.s =        fields[ 1]
        self.uid =        fields[ 2]        # real user ID of the process (text or decimal)
        self.pid =        int(fields[ 3])        # process ID
        self.ppid =        int(fields[ 4])        # parent process ID
        self.c =        int(fields[ 5])
        self.pri =        int(fields[ 6])        # real priority
        self.ni =        int(fields[ 7])        # nice priority
        self.addr =        fields[ 8]
        self.sz =        int(fields[ 9])        # memory size
        self.wchan =        fields[10]
        self.stime =        fields[11]        # start time
        if string.find(self.stime, ':') == -1:        # stime is "Month Day" format
            self.stime = self.stime + " " + fields[12]
            self.tty =        fields[13]        # terminal
            self.time =        fields[14]        # cpu time
            self.comdname =        fields[15]        # process name (no arguments)
            self.comd =        string.join(fields[15:], " ")        # command with all its arguments as a string
            lastfield = 15
        else:
            self.tty =        fields[12]        # terminal
            self.time =        fields[13]        # cpu time
            self.comdname =        fields[14]        # process name (no arguments)
            self.comd =        string.join(fields[14:], " ")        # command with all its arguments as a string
            lastfield = 14

        # Actual 'command' name with no path or interpreter - Eddie will mainly use this
        self.procname = string.split(self.comdname, '/')[-1]
        if self.procname in interpreters:
            # this command is an interpreter (eg: 'perl', 'python', etc)
            # let's set procname to the name of the script (if there is a script)
            if len(fields) > lastfield + 1:
                i = lastfield + 1
                self.procname = string.split(fields[i], '/')[-1]
                # ignore arguments (strings starting with '-')
                try:
                    while self.procname[0] == '-':
                        i = i + 1
                        self.procname = string.split(fields[i], '/')[-1]
                except IndexError:
                    # can't determine procname.....
                    self.procname = ''


    def __str__(self):
        # display process details (OLD, doesn't show many details)
        c = string.ljust(self.procname, 20)
        u = string.ljust(self.comm, 20)
        t = string.ljust(self.time, 10)

        #return( '%s\t%s\t%s\t%s\t%s\t%s' % (self.pid, u, c, t, self.percent, self.status ) )
        return( '%s\t%s\t%s\t%s\t%s\t%s' % (self.pid, u, c, t, self.pcpu, self.s) )


    def procinfo(self):
        """Return process details as a dictionary."""

        info = {}
        info['f'] = self.f
        info['s'] = self.s
        info['uid'] = self.uid
        info['pid'] = self.pid
        info['ppid'] = self.ppid
        info['c'] = self.c
        info['pri'] = self.pri
        info['ni'] = self.ni
        info['addr'] = self.addr
        info['sz'] = self.sz
        info['wchan'] = self.wchan
        info['stime'] = self.stime
        info['tty'] = self.tty
        info['time'] = self.time
        info['comdname'] = self.comdname
        info['comd'] = self.comd
        info['procname'] = self.procname

        return info


##
## END - proc.py
##
