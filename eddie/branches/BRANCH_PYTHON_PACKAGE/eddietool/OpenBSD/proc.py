
'''
File                : proc.py 

Start Date        : 20040522 

Description        :
  This is an Eddie data collector.  It collects process information on
  an OpenBSD system.

  The following statistics are currently collected and made available to
  directives that request it (e.g., PROC):

  TODO...

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 2004-2005'

__author__ = 'Chris Miles; John McInnes'

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
# Eddie modules
import datacollect
import log
import utils


# List of interpreters - default empty
interpreters = []

class procList(datacollect.DataCollect):
    """Class procList, holds a list of running processes and related information.
    """

    def __init__(self):
        apply( datacollect.DataCollect.__init__, (self,) )


    ##################################################################
    # Public, thread-safe, methods

    def procExists(self, procname):
        """Search the process list and return the number of occurrences
        of procname.
        """

        proclist = self.getList( 'proclist' )   # safely get copy of process list

        count = 0               # count number of occurrences of 'procname'
        for i in proclist:
            command = string.split(i.comm, '/')[-1]
            if command == procname or i.procname == procname:
                count = count + 1

        return count


    def pidExists(self, pid):
        """Return true (1) if a process with 'pid' exists,
        or false (0) otherwise.
        """

        prochash = self.getHash( 'datahash' )   # safely get copy of process dict

        try:
            prochash[pid]
            return 1
        except KeyError:
            return 0


    def __getitem__(self, name):
        """Overload '[]' to return corresponding process object for given
        process name.
        """

        processes = self.getHash( 'nameHash' )  # safely get copy of process name dictionary

        try:
            r = processes[name]
        except KeyError:
            r = None            # no such process called 'name'

        return r


    def allprocs(self):
        """Return dictionary of all processes (which are dictionaries of each
        process' details).
        """

        processes = self.getHash( 'nameHash' )  # safely get copy of process name dictionary

        allprocs = {}

        for p in processes.keys():
            allprocs[p] = processes[p].procinfo()

        return allprocs


    ##################################################################
    # Private methods.  No thread safety if not using public methods.

    def collectData(self):
        """Collect process list.
        """

        self.data.datahash = {}                # dict of processes keyed by pid
        self.data.proclist = []                # list of processes
        self.data.nameHash = {}                # dict of processes keyed by process name

        # gather data from "ps"
        rawList = utils.safe_popen('ps -o ppid,nice,ruid,rgid,gid -auxww', 'r')
        rawList.readline()                # skip header
 
        for line in rawList.readlines():
            p = proc(line)
            self.data.proclist.append(p)
            self.data.datahash[p.pid] = p
            self.data.nameHash[p.procname] = p

        utils.safe_pclose( rawList )

        log.log( "<proc>procList.collectData(): new proc list created", 7 )



class proc:
    """Class proc : holds information about a single process.
    """

    def __init__(self, rawline):

        fields = string.split(rawline)

        # fields as defined from "ps -o ppid,nice,ruid,rgid,gid -auxww"
        self.ppid =        int(fields[ 0])        # parent process id
        self.nice =        fields[ 1]        # nice value
        self.ruid =        fields[ 2]        # real user id
        self.rgid =        fields[ 3]        # real group id
        self.gid =        fields[ 4]        # group id
        self.uid =        fields[ 5]        # username or uid
        self.pid =        int(fields[ 6])        # pid
        self.pcpu =        float(fields[ 7])        # cpu
        self.pmem =        float(fields[ 8])        # mem
        self.sz =        int(fields[ 9])        # size
        self.rsz =        int(fields[10])        # resident size
        self.tty =        fields[11]        # terminal
        self.s =        fields[12]        # state
        self.stime =        fields[13]        # start time
        self.time =        fields[14]        # cpu time
        self.comdname =        fields[15]        # process name (no arguments)
        self.comm =        fields[15]        # process name (no arguments)
        self.comd =        string.join(fields[16:], " ")        # command with all its arguments as a string
        lastfield = 15

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


    def timeconv(self,str):
        """Convert something vaguely in the format [dd-]hh:mm:ss.ms into
        something usable - ie pure seconds.
        """

        s=0
        t=string.split(str,"-")
        if len(t)>1:
            s=s+86400*int(t[0])        
            str=t[1]
        else:
            str=t[0]
        t=string.split(str,":")
        s=s+float(t[-1])
        s=s+60*int(t[-2])
        if len(t)==3:
            s=s+3600*int(t[0])
            return s


    def __str__(self):
        # display process details (OLD, doesn't show many details)
        c = string.ljust(self.procname, 20)
        u = string.ljust(self.comm, 20)
        t = string.ljust(self.time, 10)

        return( '%s\t%s\t%s\t%s\t%s\t%s' % (self.pid, u, c, t, self.pcpu, self.s) )


    def procinfo(self):
        """Return process details as a dictionary.
        """

        info = {}
        for k in ('ppid', 'nice', 'ruid', 'rgid', 'uid', 'pid', 'gid', 'pcpu', 'pmem', 'sz', 'vsz:sz', 'rsz', 'rss:rsz', 'tty', 's', 'stime', 'time', 'comdname', 'comd', 'comm:comd', 'procname'):
            ks = k.split(':', 2)
            ks.append(ks[0])
            info[ks[0]] = eval("self.%s" % (ks[1]))

        return info


##
## END - proc.py
##
