
'''
File		: proc.py 

Start Date	: 20041206 

Description	:
  This is an Eddie data collector.  It collects process information on
  a FreeBSD system.

  The following statistics are currently collected and made available to
  directives that request it (e.g., PROC):

  TODO...

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 2004-2005'

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



# Python modules
import string
import sys
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
        """
        Search the process list and return the number of occurrences
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

	self.data.datahash = {}		# dict of processes keyed by pid
	self.data.proclist = []		# list of processes
	self.data.nameHash = {}		# dict of processes keyed by process name

	#rawList = utils.safe_popen('/usr/bin/ps -e -o "s user ruser group rgroup uid ruid gid rgid pid ppid pgid sid pri opri pcpu pmem vsz rss osz time etime stime f c tty addr nice class wchan fname comm args"', 'r')
	rawList = utils.safe_popen('/bin/ps -axwww -o "state user ruser uid ruid rgid pid ppid pgid pri pcpu pmem vsz rss time f tty nice wchan ucomm command"', 'r')
	rawList.readline()		# skip header
 
	for line in rawList.readlines():
	    try:
		p = proc(line)
	    except:
		e = sys.exc_info()
		log.log( "<proc>procList.collectData(): exception parsing proc: %s, %s; line: %s" % (e[0],e[1],line), 5 )
	    else:
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

	self.state =   fields[ 0]       # state of the process
	self.user =    fields[ 1]       # effective user ID of the process
	self.ruser =   fields[ 2]       # real user ID of the process
	self.uid = int(fields[ 3])      # effective user ID number of the process as a decimal integer
	self.ruid =int(fields[ 4])      # real user ID number of the process as a decimal integer
	self.rgid =int(fields[ 5])      # real group ID number of the process as a decimal integer
	self.pid = int(fields[ 6])      # decimal value of the process ID
	self.ppid =int(fields[ 7])      # decimal value of the parent process ID
	self.pgid =int(fields[ 8])      # decimal value of the process group ID
	self.pri = int(fields[ 9])      # priority of the process
	self.pcpu =float(fields[10])    # ratio of CPU time used recently to CPU time available in the same period, expressed as a percentage
	self.pmem =float(fields[11])       # ratio of the process's resident set size to the physical memory on the machine, expressed as a percentage
	self.vsz = int(fields[12])      # size of the process in (virtual) memory in kilobytes as a decimal integer
	self.rss = int(fields[13])      # resident set size of the process, in kilobytes as a decimal integer
	self.time =    fields[14]       # cumulative CPU time of the process in the form: [dd-]hh:mm:ss
	self.f =       fields[15]       # flags (hexadecimal and additive) associated with the process
	self.tty =     fields[16]       # name of the controlling terminal of the process (if any)

	if self.state == 'Z':
	    # Zombied (or <defunct>) processes don't show any more information
	    self.nice =    ""
	    self.wchan =   ""
	    self.comm =    "<defunct>"
	    self.args =    "<defunct>"
	    self.procname = "<defunct>"
	else:
	    self.nice =    fields[17]       # decimal value of the system scheduling priority of the process
	    self.wchan =   fields[18]       # address of an event for which the process is sleeping (if -, the process is running)
	    self.comm =    fields[19]       # name of the command being executed (argv[0] value) as a string
	    self.args =    string.join(fields[20:], " ")      # command with all its arguments as a string

	    # Actual 'command' name with no path or interpreter - Eddie will mainly use this
	    self.procname = string.split(self.comm, '/')[-1]
	    if self.procname in interpreters:
		# this command is an interpreter (eg: 'perl', 'python', etc)
		# let's set procname to the name of the script (if there is a script)
		if len(fields) > 21:
		    i = 21
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

	return( '%s\t%s\t%s\t%s\t%s\t%s' % (self.pid, u, c, t, self.pcpu, self.state) )


    def procinfo(self):
	"""
        Return process details as a dictionary.
        """

	info = {}
	info["state"] = self.state
	info["user"] = self.user
	info["ruser"] = self.ruser
	info["uid"] = self.uid
	info["ruid"] = self.ruid
	info["rgid"] = self.rgid
	info["pid"] = self.pid
	info["ppid"] = self.ppid
	info["pgid"] = self.pgid
	info["pri"] = self.pri
	info["pcpu"] = self.pcpu
	info["pmem"] = self.pmem
	info["vsz"] = self.vsz
	info["rss"] = self.rss
	info["time"] = self.time
	info['timesec'] = self.timeconv(self.time)
	info["f"] = self.f
	info["tty"] = self.tty
	info["nice"] = self.nice
	info["wchan"] = self.wchan
	info["comm"] = self.comm
	info["args"] = self.args
	info["procname"] = self.procname

	return info


##
## END - proc.py
##
