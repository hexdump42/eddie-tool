## 
## File		: common.py 
## 
## Author       : Chris Miles  <chris@psychofx.com>
## 
## Start Date	: 20020418 
## 
## Description	: Common Directive definitions
##
## $Id$
##
##
########################################################################
## (C) Chris Miles 2002-2004
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


##
## Imports: Python
##
import os
import string
import sys
import socket
import time
import threading
import traceback
import errno

##
## Imports: Eddie
##
import directive
import log
import utils


##
## Directives
##

class FS(directive.Directive):
    """
    FS allows filesystem checks to be performed.

    It requires the 'dfList' class from the 'df' data-collection module.
    """

    def __init__(self, toklist):
	# FS requires the dfList collector object from the df module
	self.need_collectors = ( ('df','dfList'), )		# (module, collector-class) required

	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	"""
	Parse directive arguments.
	"""

	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.fs
	except AttributeError:
	    raise directive.ParseFailure, "Filesystem not specified"
	try:
	    self.args.rule
	except AttributeError:
	    raise directive.ParseFailure, "Rule not specified"

	# Set any directive-specific variables
	self.defaultVarDict['rule'] = self.args.rule

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.FS.%s' % (log.hostname,self.args.fs)
	self.state.ID = self.ID

	log.log( "<directive>FS.tokenparser(): ID '%s' fs '%s' rule '%s'" % (self.state.ID, self.args.fs, self.args.rule), 8 )


    def getData(self):
	"""
	Called by Directive docheck() method to fetch the data required for
	evaluating the directive rule.
	"""

	try:
	    df = self.data_collectors['df.dfList'][self.args.fs]
	except KeyError:
	    log.log( "<directive>FS.docheck(): Error, filesystem not found '%s'" % (self.args.fs), 4 )
	    return None

	if df == None:
	    log.log( "<directive>FS.docheck(): Error, filesystem not found '%s'" % (self.args.fs), 4 )
	    return None
	else:
	    return df.getHash()


    def addVariables(self):
	"""
	Add directive-specific action variables.
	"""

	self.Action.varDict['df'] = str( self.data_collectors['df.dfList'][self.args.fs] )



class PID(directive.Directive):
    """
    PID allows simple pid-file checks to be performed.

    It requires the 'procList' class from the 'proc' data-collection module.
    """

    def __init__(self, toklist):
	# PID requires the procList collector object from the proc module
	self.need_collectors = ( ('proc','procList'), )		# (module, collector-class) required
	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.pidfile
	except AttributeError:
	    raise directive.ParseFailure, "pidfile argument not specified"
	try:
	    self.args.rule
	except AttributeError:
	    raise directive.ParseFailure, "Rule not specified"

	# Set any PID-specific variables
	#  %pidf = the PID-file
	self.defaultVarDict['pidfile'] = self.args.pidfile
	self.defaultVarDict['rule'] = self.args.rule

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.PID.%s.%s' % (log.hostname,self.args.pidfile,self.args.rule)
	self.state.ID = self.ID

	log.log( "<directive>PID.tokenparser(): ID '%s' pid '%s' rule '%s'" % (self.state.ID, self.args.pidfile, self.args.rule), 8 )


    def getData(self):
	"""
	Called by Directive docheck() method to fetch the data required for
	evaluating the directive rule.
	"""

	data = {}

	# Check if pidfile exists
	try:
	    pidfile = open( self.args.pidfile, 'r' )
	except IOError:
	    # pidfile not found
	    data['exists'] = 0		# false
	else:
	    data['exists'] = 1		# true
	    pid = pidfile.readline()
	    pidfile.close()
	    pid = string.strip(pid)
	    pid = string.split(pid)[0]	    # Get rid of any other junk after pid
	    pid = int(pid)			# want it as an integer
	    data['pid'] = pid

	    # Search for pid in process list
	    if self.data_collectors['proc.procList'].pidExists( pid ) == 0:
		# there is no process with pid == pid
		data['running'] = 0	# false
		log.log( "<directive>PID.getData(): pid %s not in process list" % (pid), 7 )
	    else:
		data['running'] = 1	# true
		log.log( "<directive>PID.getData(): pid %s is in process list" % (pid), 7 )

	return data


class PROC(directive.Directive):
    """
    PROC allows process-level checks to be performed.

    It requires the 'procList' class from the 'proc' data-collection module.
    """

    def __init__(self, toklist):
	# PROC requires the procList collector object from the proc module
	self.need_collectors = ( ('proc','procList'), )		# (module, collector-class) required

	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	"""Parse tokenized input."""

	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.name
	except AttributeError:
	    raise directive.ParseFailure, "Process name not specified"
	try:
	    self.args.rule
	except AttributeError:
	    raise directive.ParseFailure, "Rule not specified"

	# Set any PROC-specific action variables
	#  proc_check_name = the process name being checked
	self.defaultVarDict['name'] = self.args.name

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.PROC.%s' % (log.hostname,self.args.name)
	self.state.ID = self.ID

	log.log( "<directive>PROC.tokenparser(): ID '%s' name '%s' rule '%s'" % (self.state.ID, self.args.name, self.args.rule), 8 )


    def getData(self):
	"""
	Called by Directive docheck() method to fetch the data required for
	evaluating the directive rule.
	"""

	data = {}

	proc = self.data_collectors['proc.procList'][self.args.name]
	if proc == None:
	    log.log( "<directive>PROC.getData(): process not in process table, '%s'" % (self.args.name), 7 )
	    data['exists'] = 0		# false
	else:
	    log.log( "<directive>PROC.getData(): process is in process table, '%s'" % (self.args.name), 7 )
	    data['exists'] = 1		# true
	    data.update(proc.procinfo())

	return data


class SP(directive.Directive):
    """
    SP allows service port checks to be performed.

    It requires the 'TCPtable' class from the 'netstat' data-collection module.
    """

    def __init__(self, toklist):
	# SP requires the TCPtable and UDPtable collectors from the netstat module
	self.need_collectors = ( ('netstat','TCPtable'), ('netstat','UDPtable') )

	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.port
	except AttributeError:
	    raise directive.ParseFailure, "Port not specified"
	try:
	    self.args.protocol
	except AttributeError:
	    raise directive.ParseFailure, "Protocol not specified"
	try:
	    self.args.bindaddr
	except AttributeError:
	    raise directive.ParseFailure, "Bind address not specified"
	try:
	    self.args.rule
	except AttributeError:
	    raise directive.ParseFailure, "Rule not specified"

	# CM 2004-05-16: allow '*' as alias for wildcard address '0.0.0.0'
	if self.args.bindaddr == '*':
	    self.args.bindaddr = '0.0.0.0'

	self.port_n = self.args.port		# remember port name

	# lets try resolving this service port to a number
	try:
	    self.port = socket.getservbyname(self.port_n, self.args.protocol)
	except socket.error:
	    self.port = self.port_n

	self.defaultVarDict['port'] = self.port_n
	self.defaultVarDict['bindaddr'] = self.args.bindaddr
	self.defaultVarDict['protocol'] = self.args.protocol

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.SP.%s/%s.%s' % (log.hostname,self.args.protocol,self.port_n,self.args.bindaddr)
	self.state.ID = self.ID

	log.log( "<directive>SP.tokenparser(): ID '%s' protocol '%s', port '%s', bind addr '%s'" % (self.state.ID, self.args.protocol, self.port, self.args.bindaddr), 8 )


    def getData(self):

	if self.args.protocol == 'tcp' or  self.args.protocol == 'TCP':
	    connections = self.data_collectors['netstat.TCPtable'].getHash()
	elif self.args.protocol == 'udp' or  self.args.protocol == 'UDP':
	    connections = self.data_collectors['netstat.UDPtable'].getHash()
	else:
	    log.log( "<directive>SP.getData(): protocol '%s' illegal" % (self.args.protocol), 8 )
	    raise directive.DirectiveError, "protocol '%s' illegal" % (self.args.protocol)

	if len(connections)==0:
	    log.log( "<directive>SP.getData(): Zero connections for protocol '%s'" % (self.args.protocol), 6 )
	    return None

	key = "%s:%s" % (self.args.bindaddr, self.port)

	data = {}
	data['exists'] = key in connections.keys()	# true or false

	return data



class COM(directive.Directive):
    """
    COM allows simply system commands to be executed and the results/output
    to be checked.

    It requires no data-collection modules.
    """

    def __init__(self, toklist):
	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.cmd
	except AttributeError:
	    raise directive.ParseFailure, "Command (cmd) not specified"
	try:
	    self.args.rule
	except AttributeError:
	    raise directive.ParseFailure, "Rule not specified"

	# Set any COM-specific variables
	#  cmd = the command
	self.defaultVarDict['cmd'] = self.args.cmd

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.COM.%s.%s' % (log.hostname,self.args.cmd,self.args.rule)
	self.state.ID = self.ID

	log.log( "<directive>COM.tokenparser(): ID '%s' cmd '%s' rule '%s'" % (self.state.ID, self.args.cmd, self.args.rule), 8 )


    def getData(self):
	log.log( "<directive>COM.getData(): acquiring systemcall_semaphore for cmd '%s'" % (self.args.cmd), 9 )
	utils.systemcall_semaphore.acquire()
	log.log( "<directive>COM.getData(): systemcall_semaphore acquired for cmd '%s'" % (self.args.cmd), 9 )
	tmpprefix = "/var/tmp/com%d" % os.getpid()
	cmd = "{ %s ; } >%s.out 2>%s.err" % (self.args.cmd, tmpprefix, tmpprefix )
	log.log( "<directive>COM.getData(): calling system('%s')" % (cmd), 7 )
	retval = os.system( cmd )
	signum = None
	if (retval & 0xff) == 0:
	    # call terminated from standard exit()
	    retval = retval >> 8
	elif (retval & 0xff00) == 0:
	    # call terminated due to a signal
	    signum = retval & 0xff
	elif (retval & 0xff) == 0177:
	    # child process stopped with WSTOPFLG (0177) set
	    signum = retval & 0xff00

        out = ""
	try:
	    outf = open( tmpprefix + ".out", 'r' )
	except IOError:
	    # stdout tmp file not found
	    log.log( "<directive>COM.docheck(): Error, could not open '%s'" % (tmpprefix + ".out"), 4 )
	else:
	    out = outf.read()
	    outf.close()
	    os.remove( tmpprefix + ".out" )
	    out = string.strip(out)

        err = ""
	try:
	    errf = open( tmpprefix + ".err", 'r' )
	except IOError:
	    # stderr tmp file not found
	    log.log( "<directive>COM.docheck(): Error, could not open '%s'" % (tmpprefix + ".err"), 4 )
	else:
	    err = errf.read()
	    errf.close()
	    os.remove( tmpprefix + ".err" )
	    err = string.strip(err)

	utils.systemcall_semaphore.release()
	log.log( "<directive>COM.getData(): released systemcall_semaphore for cmd '%s'" % (self.args.cmd), 9 )

        log.log( "<directive>COM.getData(): retval=%d" % retval, 7 )
        log.log( "<directive>COM.getData(): signum=%s" % signum, 9 )
	log.log( "<directive>COM.getData(): stdout='%s'" % out, 9 )
	log.log( "<directive>COM.getData(): stderr='%s'" % err, 9 )

        data = {}                      # environment for com rules execution
        data['out'] = out
        data['err'] = err
        data['ret'] = retval
        data['signum'] = signum

	# Split output to assist rules
	outsplit = string.split(out)
	for i in range(0, len(outsplit)):
	    data['outfield%d'%(i+1)] = outsplit[i]

	# If no output, set outfield1 anyway so rule strings don't break
	if len(outsplit) == 0:
	    data['outfield1'] = ""

	return data



class PORT(directive.Directive):
    """
    PORT allows remote TCP checks to be performed.

    It requires no data-collection modules.
    """

    def __init__(self, toklist):
	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.host
	except AttributeError:
	    raise directive.ParseFailure, "Host not specified"
	try:
	    self.args.port
	except AttributeError:
	    raise directive.ParseFailure, "Port not specified"
	try:
	    self.args.port = int(self.args.port)
	except ValueError:
	    raise directive.ParseFailure, "Port is not an integer: %s" % (self.args.port)
##	send is optional
	try:
	    self.args.send
	except AttributeError:
	    self.args.send = ""		# default to not send
##	expect is optional
#	try:
#	    self.args.expect
#	except AttributeError:
#	    raise directive.ParseFailure, "Expect string not specified"
	try:
	    self.args.rule
	except AttributeError:
	    raise directive.ParseFailure, "Rule not specified"

	# Set any PORT-specific variables
	#  host = the host
	#  port = the port
	#  send = the send string
	#  expect = the expect string
	self.defaultVarDict['host'] = self.args.host
	self.defaultVarDict['port'] = self.args.port
	self.defaultVarDict['rule'] = self.args.rule
	self.defaultVarDict['send'] = self.args.send
	if 'expect' in dir(self.args):
	    self.defaultVarDict['expect'] = self.args.expect

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.PORT.%s.%d' % (log.hostname,self.args.host,self.args.port)
	self.state.ID = self.ID

	log.log( "<directive>PORT.tokenparser(): ID '%s' host '%s' port %d" % (self.state.ID, self.args.host, self.args.port), 8 )


    def getData(self):
	"""
	Called by Directive docheck() method to fetch the data required for
	evaluating the directive rule.
	"""

	(connected, recv_string, connect_time, error, errorstr) = \
	    self.tcp_test(host=self.args.host, port=self.args.port, send=self.args.send)

	data = {}
	data['alive'] = connected	# true/false (1/0)
	data['recv'] = recv_string	# data received from connection
	data['connect_time'] = connect_time	# time for socket connect
	data['error'] = error		# error code if connect failed
	data['errorstr'] = errorstr	# error text for above

	if 'expect' in dir(self.args):
	    if recv_string and self.args.expect:
		if string.find( recv_string, self.args.expect ) != -1:
		    data['matched'] = 1	# true
		else:
		    data['matched'] = 0	# false
	    else:
		data['matched'] = 0	# false
	else:
	    data['matched'] = 0

	return data


    def tcp_test(self, host, port, send=""):
        """
	Opens a connection to 'host' tcp port 'port' to test the connection.
	If 'send' is not an empty string, it will be sent to the remote host
	and any response stored in recv_string.
	
	Returns the tuple:
	 (connected, recv_string, connect_time, error, errorstr)
	 - connected: true (1) or false (0) based on a successful connection or
	   not.
	 - recv_string: contains the data received from the remote host.
	 - connect_time: the total amount of time the between establishing the
	   connection and closing the connection.
	 - error: the error code from a failed connection.
	 - errorstr: plain text description of the above error.
	"""

	# Defaults
	connected = 0
	recv_string = None
	connect_time = 0.0
	error = None
	errorstr = ""

        try:
	    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            try:
		time_start = time.time()
		s.connect( (host,port) )
		connected = 1    # port connection ok

                if send != "":
                    exec( "send='%s'" % send )
		    sendlist = string.split(send, '\n')		# split each line
		    # send each line - only capture last output received
		    for line in sendlist:
			log.log( "<directive>PORT.tcp_test(): sending '%s'" % (line), 9 )
			s.send(line+'\n')

		recv_string = s.recv(1024)	# receive max 1024 bytes
		s.close()
		time_finish = time.time()

		connect_time = time_finish - time_start

            except socket.error:
		e = sys.exc_info()
		s.close()
		try:
		    error = errno.errorcode[e[1][0]]
		except KeyError:
		    error = str(e[1][0])
		errorstr = e[1][1]
		log.log( "<directive>PORT.tcp_test(): socket.error: %s, %s" % (e[0], e[1]), 7 )

        except:
	    e = sys.exc_info()
	    tb = traceback.format_list( traceback.extract_tb( e[2] ) )
	    log.log( "<directive>PORT.tcp_test(): ID '%s', Uncaught exception: %s, %s, %s" % (self.state.ID, e[0], e[1], tb), 3 )

	return (connected, recv_string, connect_time, error, errorstr)



class IF(directive.Directive):
    """
    IF allows network interface checks to be performed.

    It requires the 'IntTable' class from the 'netstat' data-collection module.
    """

    def __init__(self, toklist):
	# IF requires the IntTable collector object from the netstat module
	self.need_collectors = ( ('netstat','IntTable'), )	# (module, collector-class) required

	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	"""Parse rest of rule (after ':')."""
	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.name
	except AttributeError:
	    raise directive.ParseFailure, "Interface name not specified"
	try:
	    self.args.rule
	except AttributeError:
	    raise directive.ParseFailure, "Rule not specified"

	self.defaultVarDict['name'] = self.args.name

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.IF.%s.%s' % (log.hostname,self.args.name,self.rule)
	self.state.ID = self.ID

	log.log( "<directive>IF.tokenparser(): ID '%s' name '%s', rule '%s'" % (self.state.ID, self.args.name, self.args.rule), 8 )


    def getData(self):
	"""
	Called by Directive docheck() method to fetch the data required for
	evaluating the directive rule.
	"""

	data = {}

	try:
	    i = self.data_collectors['netstat.IntTable'].getHash()[self.args.name]
	except KeyError:
	    data['exists'] = 0		# false
	else:
	    data['exists'] = 1		# true
	    data.update(i.ifinfo())	# get interface statistics

	return data



class NET(directive.Directive):
    """
    NET allows network statistics checks to be performed.

    It requires the 'stats_ctrs' class from the 'netstat' data-collection module.
    """

    def __init__(self, toklist):
	# NET requires the stats_ctrs collector object from the netstat module
	self.need_collectors = ( ('netstat','stats_ctrs'), )	# (module, collector-class) required

	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	"""
	Parse directive arguments.
	"""

	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.rule
	except AttributeError:
	    raise directive.ParseFailure, "Rule not specified"

	# Rule should be a string
        if type(self.args.rule) != type('STRING'):
	    raise directive.ParseFailure, "NET parse error, rule is not string."

	self.defaultVarDict['rule'] = self.args.rule

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.NET.%s' % (log.hostname,self.args.rule)
	self.state.ID = self.ID

	log.log( "<directive>NET.tokenparser(): ID '%s' rule '%s'" % (self.state.ID, self.args.rule), 8 )


    def getData(self):
	"""
	Called by Directive docheck() method to fetch the data required for
	evaluating the directive rule.
	"""

	# get dictionary of network statistics
	data = self.data_collectors['netstat.stats_ctrs'].getHash()
	return data



class SYS(directive.Directive):
    """
    SYS allows system performance checks to be performed.

    It requires the 'system' class from the 'system' data-collection module.
    """

    def __init__(self, toklist):
	# SYS requires the system collector object from the system module
	self.need_collectors = ( ('system','system'), )	# (module, collector-class) required

	apply( directive.Directive.__init__, (self, toklist) )



    def tokenparser(self, toklist, toktypes, indent):
	"""Parse rest of rule (after ':')."""
	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.rule
	except AttributeError:
	    raise directive.ParseFailure, "Rule not specified"

	# Rule should be a string
        if type(self.args.rule) != type('STRING'):
	    raise directive.ParseFailure, "SYS parse error, rule is not string."

	self.defaultVarDict['rule'] = self.args.rule

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.SYS.%s' % (log.hostname,self.args.rule)
	self.state.ID = self.ID

	log.log( "<directive>SYS.tokenparser(): ID '%s' rule '%s'" % (self.state.ID, self.args.rule), 8 )


    def getData(self):
	"""
	Called by Directive docheck() method to fetch the data required for
	evaluating the directive rule.
	"""

	# get dictionary of system stats
	data = self.data_collectors['system.system'].getHash()
	return data



class STORE(directive.Directive):
    """
    STORE provides a facility to store data.
    Currently it is used with the elvindb() action.

    It requires as many data collectors as required to store the data.

    This directive still needs a lot of work.

    NOTE: This directive may be made redundant when support for any standard
     directive to call the elvindb() action is sorted out.
    """

    def __init__(self, toklist):
	self.need_collectors = ( ('system','system'), ('netstat','stats_ctrs'), ('proc','procList') )		# (module, collector-class) required
	apply( directive.Directive.__init__, (self, toklist) )



    def tokenparser(self, toklist, toktypes, indent):
	"""
	Parse directive arguments.
	"""

	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.rule
	except AttributeError:
	    raise directive.ParseFailure, "Rule not specified"

	# Rule should be a string
        if type(self.args.rule) != type('STRING'):
	    raise directive.ParseFailure, "STORE parse error, rule is not string."

	self.defaultVarDict['rule'] = self.args.rule

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.STORE.%s' % (log.hostname,self.args.rule)
	self.state.ID = self.ID

	log.log( "<directive>STORE.tokenparser(): ID '%s' rule '%s'" % (self.state.ID, self.args.rule), 8 )


    def getData(self):
	"""
	Called by Directive docheck() method to fetch the data required for
	evaluating the directive rule.
	"""

	datahash = None

	# Get data as directed by rule.
	# * this is hard-coded to a few different 'rules' atm.  This should be
	# cleaned up later to handle any type of rule (TODO)

	if self.args.rule[:6] == 'system':
	    datahash = self.data_collectors['system.system'].getHash()		# get dictionary of system stats
	elif self.args.rule[:7] == 'netstat':
	    datahash = self.data_collectors['netstat.stats_ctrs'].getHash() # get dictionary of network stats
	elif self.args.rule[:4] == 'proc':
	    datahash = self.data_collectors['proc.procList'].allprocs()	# get dictionary of process details
	elif self.args.rule[:2] == 'if':
	    datahash = self.data_collectors['netstat.netstat'].getAllInterfaces() # get dictionary of interface details
	elif self.args.rule[:6] == 'iostat':
	    datahash = iostat.getHash()				# get dictionary of iostat data

	if datahash == None:
	    log.log( "<directive>STORE.getData(): rule '%s' is invalid." % (self.args.rule), 4 )
	    return None

	return datahash


##
## END - common.py
##
