#!/opt/local/bin/python 
## 
## File		: directive.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 971205 
## 
## Description	: 
##
## $Id$
##
##

import os
import string
import regex
import sys
import socket
import action
import definition
import utils
import log

# Define exceptions
ParseFailure = 'ParseFailure'

# Rules holds all the directives in a hash where the value of each key is the
# list of rules relating to that key.
class Rules:
    def __init__(self):
	self.hash = {}

    # Overload '+', eg: rules + directive_rule
    def __add__(self, new):
	try:
	    tl = self.hash[new.type]

	except KeyError:
	    self.hash[new.type] = []
	    tl = []

	tl.append(new)

	self.hash[new.type] = tl
	return(self)

    # Overload '[]', eg: fs_directive_list = rules['FS']
    def __getitem__(self, key):
	try:
	    return self.hash[key]
	except KeyError:
	    return None

    def keys(self):
	return self.hash.keys()
    
    def delete(self, directive):
	del self.hash[directive]

    def __str__(self):
	#str = ""
	#for r in self.hash.keys():
	#    str = str + "%s\n" % self.hash[r]
	#return str
	return "%s" % self.hash


##
## The base directive class.  Derive all directives from this base class.
##
class Directive:
    def __init__(self, toklist):
	# Check toklist for valid tokens
	if len(toklist) < 3:		# need at least 3 tokens
	    raise ParseFailure, "Directive expected at least 3 tokens, found %d" % len(toklist)
	if toklist[-1] != ':':		# last token should be a ':'
	    raise ParseFailure, "Directive expected ':' but didn't find one"

	self.basetype = 'Directive'	# the object can know its own basetype
	self.type = toklist[0]		# the directive type of this instance

	self.Action = action.action()	# create new action instance
	self.Action.actionList = ''	# each directive will have an action
	self.Action.varDict = {}	# dictionary of variables used for emails etc

	# Set up informational variables - these are common to all Directives
	#  %h = hostname
	self.Action.varDict['h'] = log.hostname

	#  %sys = command from a system() action
	#     TODO
	self.Action.varDict['sys'] = '[sys not yet defined]'

	#  %act = show list of actions taken preceded by "The following actions
	#         were taken:" if any were taken
	self.Action.varDict['act'] = '[act not yet defined]'

	#  %actnm = show list of actions taken (excluding email()'s) preceded by
	#         "The following actions were taken:" if any were taken
	self.Action.varDict['actnm'] = '[actnm not yet defined]'


    # Perform actions for a directive
    def doAction(self, Config):
	# split comma-seperated list of actions
	print ">>> 1 actionList:",self.actionList
	#actionList = utils.trickySplit( self.actionList, ',' )
	actionList = self.actionList
	print ">>> 2 actionList:",actionList

	# Replace Action definitions with the corresponding actions
	#actionList = definition.parseList( actionList, ADict )

	# Put quotes around arguments so we can use eval()
	#actionList = utils.quoteArgs( actionList )

	# Set the 'action' variables with the expanded action list
	self.Action.varDict['act'] = 'The following actions are being taken:\n'
	self.Action.varDict['actnm'] = 'The following (non-email) actions are being taken:\n'
	#TODO:
	#for a in actionList:
	#    self.Action.varDict['act'] = self.Action.varDict['act'] + '\t' + a + '\n'
	#    if a[:5] != 'email':
	#	self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '\t' + a + '\n'

	# Perform each action
	for a in actionList:
	    print ">>>> a:",a
	    sre = regex.compile( "\([A-Za-z0-9_]+\)(\([A-Za-z0-9_.]+\),?\([0-9]?\))" )
	    inx = sre.search( a )
	    if inx == -1:
		#raise SyntaxError, "actionList regex error"
		# Assume we have a simple action call (rather than a
		# notification definition.
		eval( 'self.Action.'+a )
	    else:
		notif = sre.group(1)
		msg = sre.group(2)
		level = sre.group(3)
		if level == None:
		    level = 0

		#print ">>>> notif:",notif
		#print ">>>> msg:",msg
		#print ">>>> level:",level

		afunc = Config.NDict[notif].levels[level]
		#print ">>>> afunc:",afunc

		self.Action.notif = notif
		self.Action.msg = msg
		self.Action.level = level
		self.Action.MDict = Config.MDict #TODO: move to init() ?

		aList = utils.trickySplit( afunc[0], ',' )
		# Put quotes around arguments so we can use eval()
		aList = utils.quoteArgs( aList )
		for aa in aList:
		    #try:
			# Call the action
			log.log( "<directive>Directive, calling action '%s'" % (aa), 9 )
			print "<directive>Directive, calling action '%s'" % (aa)
			eval( 'self.Action.'+aa )
		    #except AttributeError:
			# Not an action function ... error...
		#	log.log( "<directive>Directive, Error, 'action.%s' is not a defined action, config line follows,\n%s\n" % (a,self.raw), 2 )


    ##
    ## parseAction(toklist)
    ##  Parses token list and returns a list of action call strings
    ##
    def parseAction(self, toklist):
	actstr = ""
	for t in toklist:
	    if t != '\012':
		actstr = actstr + t
	actlist = utils.trickySplit( actstr, ',' )
	return actlist


##
## RULE-BASED COMMANDS
##
class FS(Directive):
    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )
	self.filesystem = string.join(toklist[1:-1], '')	# the filesystyem to check


    def tokenparser(self, toklist, toktypes, indent):

	self.rule = utils.stripquote(toklist[0])	# the rule
	self.actionList = self.parseAction(toklist[1:])

	# Set any FS-specific variables
	#  fsf = filesystem
	#  fsrule = rule
	self.Action.varDict['fsf'] = self.filesystem
	self.Action.varDict['fsrule'] = self.rule

	print "<FS> filesystem: '%s' rule: '%s' action: '%s'" % (self.filesystem, self.rule, self.actionList)
	log.log( "<FS> filesystem: '%s' rule: '%s' action: '%s'" % (self.filesystem, self.rule, self.actionList), 8 )


    def docheck(self, Config):
	log.log( "<directive>FS(), docheck(), fs '%s', rule '%s'" % (self.filesystem,self.rule), 7 )
	df = dlist[self.filesystem]
	if df == None:
	    log.log( "<directive>FS(), Error, no df with filesystem '%s'" % (self.filesystem), 2 )
	    return

	dfenv = {}			# environment for df rules execution
	dfenv['used'] = string.atoi(df.getUsed())
	dfenv['avail'] = string.atoi(df.getAvail())
	dfenv['capac'] = string.atoi(df.getPctused())
	# TODO : calculate deltas from history...
	dfenv['useddelta'] = string.atoi(df.getUsedDelta())
	dfenv['availdelta'] = string.atoi(df.getAvailDelta())
	dfenv['capacdelta'] = string.atoi(df.getPctusedDelta())

	self.parseRule()

	#print "used='%d', avail='%d', capac='%d', useddelta='%d', availdelta='%d', capacdelta='%d'" % (dfenv['used'],dfenv['avail'],dfenv['capac'],dfenv['useddelta'],dfenv['availdelta'],dfenv['capacdelta'])

	result = eval( self.rule, dfenv )

	if result != 0:
	    # assign variables
	    self.Action.varDict['fsused'] = df.getUsed()
	    self.Action.varDict['fsavail'] = df.getAvail()
	    self.Action.varDict['fscapac'] = df.getPctused()
	    self.Action.varDict['fssize'] = df.getSize()
	    self.Action.varDict['fsdf'] = "%s%s" % (dlist.dfheader,df)

	    # get '%fsls' details for this filesystem
    	    fsls = os.popen("ls -l %s" % (df.mountpt), 'r')
 
	    fsls_output = ""
    	    for line in fsls.readlines():
		fsls_output = fsls_output + line
	    
	    fsls.close()
	    self.Action.varDict['fsls'] = fsls_output
	


    	    log.log( "<directive>FS(), rule '%s' was false, calling doAction()" % (self.rule), 6 )
    	    self.doAction(Config)

    # Parse the rule line and replace/remove certain characters
    def parseRule(self):
	parsed = ""

	skipnext = 0			# flag to skip next character/s

	for i in range(len(self.rule)):
	    if skipnext > 0:
		skipnext = skipnext - 1
		continue

	    c = self.rule[i]

	    if c == '%':	# throw away '%'s - don't need em
		continue
	    elif c == '|':	# replace '|'s with 'or'
		parsed = parsed + ' or '
		continue
	    elif c == '&':	# replace '&'s with 'and'
		parsed = parsed + ' and '
		continue
	    elif i == len(self.rule)-1:	# break out of 'switch' if c is last character
		pass
	    elif ( string.lower(c) + string.lower(self.rule[i+1]) ) == 'mb':
		parsed = parsed + '000'
		skipnext = 1
		continue
	    elif ( string.lower(c) + string.lower(self.rule[i+1]) ) == 'gb':
		parsed = parsed + '000000'
		skipnext = 1
		continue
	    
	    parsed = parsed + c

	self.rule = parsed



class PID(Directive):
    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )
	self.pidfile = string.join(toklist[1:-1], '')	# the pid file to check for
	self.ruleDict = { 'EX' : None,
		          'PR' : None }


    def tokenparser(self, toklist, toktypes, indent):

	# Expect first token to be rule - one of self.ruleDict
	if toklist[0] not in self.ruleDict.keys():
	    raise ParseFailure, "PID found unexpected rule '%s'" % toklist[0]

	self.rule = toklist[0]			# the rule (EX or PR)
	self.actionList = self.parseAction(toklist[1:])

	# Set any PID-specific variables
	#  %pidf = the PID-file
	self.Action.varDict['pidf'] = self.pidfile

	print "<PID> pidfile: '%s' rule: '%s' action: '%s'" % (self.pidfile, self.rule, self.actionList)
	log.log( "<PID> pidfile: '%s' rule: '%s' action: '%s'" % (self.pidfile, self.rule, self.actionList), 8 )


    def docheck(self, Config):
	log.log( "<directive>PID(), docheck(), pidfile '%s', rule '%s'" % (self.pidfile,self.rule), 7 )
	if self.rule == "EX":
	    # Check if pidfile exists
	    try:
		pidfile = open( self.pidfile, 'r' )
	    except IOError:
		# pidfile not found
		log.log( "<directive>PID(), EX, pidfile '%s' not found" % (self.pidfile), 6 )
		self.doAction(Config)
	    else:
		log.log( "<directive>PID(), EX, pidfile '%s' found" % (self.pidfile), 8 )
		pidfile.close()

	elif self.rule == "PR":
	    # check if process pid found in pidfile is running - no alert if pidfile not found
	    try:
		pidfile = open( self.pidfile, 'r' )
	    except IOError:
		# pidfile not found
		log.log( "<directive>PID(), PR, pidfile '%s' not found" % (self.pidfile), 6 )
	    else:
		log.log( "<directive>PID(), PR, pidfile '%s' found" % (self.pidfile), 8 )
		pid = pidfile.readline()
		pidfile.close()
		pid = string.strip(pid)
		# strip '\n' from pid string if necessary
		if pid[-1:] == '\n':
		    pid = pid[:-1]

		# Get rid of any other junk after pid
		pid = string.split(pid)[0]

		self.Action.varDict['pid'] = pid

		# Search for pid from process list
		if plist.pidExists( pid ) == 0:
		    # there is no process with pid == pid
    		    log.log( "<directive>PID(), PR, pid %s not in process list" % (pid), 6 )
		    self.doAction(Config)
		else:
    		    log.log( "<directive>PID(), PR, pid %s is in process list" % (pid), 8 )


	else:
	    # invalid rule
	    log.log( "<directive>PID(), Error, '%s' is not a valid PID rule, config line follows,\n%s\n" % (self.rule,self.raw), 2 )


class PROC(Directive):
    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )
	self.name = toklist[1]			# the daemon to check for
	self.daemon = toklist[1]		# the daemon to check for
	self.ruleDict = { 'NR' : self.NR,
		          'R'  : self.R }


    def tokenparser(self, toklist, toktypes, indent):

	# Expect first token to be rule - one of self.ruleDict
	if toklist[0] not in self.ruleDict.keys():
	    raise ParseFailure, "PROC found unexpected rule '%s'" % toklist[0]

	self.rule = self.ruleDict[toklist[0]]	# Set the rule
	self.actionList = self.parseAction(toklist[1:])

	# Set any PROC-specific variables
	#  %dproc = the process name
	self.Action.varDict['dproc'] = self.daemon
	#  %pid = pid of process (ie: if found running for R rule)
	self.Action.varDict['pid'] = '[pid not yet defined]'

	print "<PROC> daemon: '%s' rule: '%s' action: '%s'" % (self.daemon, self.rule, self.actionList)
	log.log( "<PROC> daemon: '%s' rule: '%s' action: '%s'" % (self.daemon, self.rule, self.actionList), 8 )


    def docheck(self, Config):
	log.log( "<directive>PROC(), docheck(), daemon '%s', rule '%s'" % (self.daemon,self.rule), 7 )
	self.rule(Config)

    def NR(self,Config):
	if plist.procExists( self.daemon ) == 0:
	    log.log( "<directive>NR(PROC) daemon not running, '%s'" % (self.daemon), 6 )
	    self.doAction(Config)

    def R(self,Config):
	if plist.procExists( self.daemon ) > 0:
	    log.log( "<directive>R(PROC) daemon is running, '%s'" % (self.daemon), 6 )
	    # Set %pid variable.
	    self.Action.varDict['pid'] = plist[self.daemon].pid
	    self.doAction(Config)


class SP(Directive):
    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )

	# Must be 5 tokens to make up: ['SP', 'proto', '/', 'port', ':']
	if len(toklist) < 5:
	    raise ParseError, "SP proto/port not specified correctly"
	if toklist[2] != '/':
	    raise ParseError, "SP proto/port not specified correctly"

	self.proto = toklist[1]		# the proto to check
	self.port_n = toklist[3]	# the port to check


    def tokenparser(self, toklist, toktypes, indent):

	self.addr   = toklist[0]			# the addr to check
	self.actionList = self.parseAction(toklist[1:])

	# lets try resolving this service port to a number
	try:
	    self.port = socket.getservbyname(self.port_n, self.proto)
	    # print p
	except socket.error:
	    self.port = self.port_n

	self.Action.varDict['port'] = self.port_n
	self.Action.varDict['addr'] = self.addr
	self.Action.varDict['prot'] = self.proto

	print "<Directive>SP, proto '%s', port '%s', bind addr '%s', action '%s'" % (self.proto, self.port, self.addr, self.actionList)
	log.log( "<Directive>SP, proto '%s', port '%s', bind addr '%s', action '%s'" % (self.proto, self.port, self.addr, self.actionList), 8 )


    def docheck(self, Config):
	log.log( "<directive>SP(), docheck(), proto '%s', port '%s', addr '%s'" % (self.proto,self.port_n,self.addr), 7 )

	ret = nlist.portExists(self.proto, self.port, self.addr) != None
	if ret != 0:
	    log.log( "<directive>SP(), port %s/%s listener found bound to %s" % (self.proto , self.port_n, self.addr), 8 )
	else:
	    self.doAction(Config)
	    log.log( "<directive>SP(), port %s/%s no listener found bound to %s" % (self.proto , self.port_n, self.addr), 6 )


class COM(Directive):
    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )
	self.command = utils.stripquote(toklist[1])	# the command


    def tokenparser(self, toklist, toktypes, indent):
	self.rule = utils.stripquote(toklist[0])	# the rule
	self.actionList = self.parseAction(toklist[1:])	# the action

	# Set any PID-specific variables
	#  %com = the command
	#  %rule = the rule
	self.Action.varDict['com'] = self.command
	self.Action.varDict['rule'] = self.rule

	print "<COM> command: '%s' rule: '%s' action: '%s'" % (self.command, self.rule, self.actionList)
	log.log( "<COM> command: '%s' rule: '%s' action: '%s'" % (self.command, self.rule, self.actionList), 8 )


    def docheck(self, Config):
	log.log( "<directive>COM(), docheck(), command '%s', rule '%s'" % (self.command,self.rule), 7 )
	tmpprefix = "/var/tmp/com%d" % os.getpid()
	cmd = "%s >%s.out 2>%s.err" % (self.command, tmpprefix, tmpprefix )
	log.log( "<directive>COM.docheck(), calling system('%s')" % (cmd), 8 )
	retval = os.system( cmd )
	try:
	    outf = open( tmpprefix + ".out", 'r' )
	except IOError:
	    # stdout tmp file not found
	    log.log( "<directive>COM.docheck(), Error, could not open '%s'" % (tmpprefix + ".out"), 2 )
	else:
	    out = outf.readline()
	    outf.close()
	    os.remove( tmpprefix + ".out" )
	    out = string.strip(out)
	    if out[-1:] == '\n':
		out = out[:-1]

	try:
	    errf = open( tmpprefix + ".err", 'r' )
	except IOError:
	    # stderr tmp file not found
	    log.log( "<directive>COM.docheck(), Error, could not open '%s'" % (tmpprefix + ".err"), 2 )
	else:
	    err = errf.readline()
	    errf.close()
	    os.remove( tmpprefix + ".err" )
	    err = string.strip(err)
	    if err[-1:] == '\n':
		err = err[:-1]

        log.log( "<directive>COM.docheck(), retval=%d" % retval, 9 )
	log.log( "<directive>COM.docheck(), stdout='%s'" % out, 9 )
	log.log( "<directive>COM.docheck(), stderr='%s'" % err, 9 )

	# save values in variable dictionary
	self.Action.varDict['out'] = out
	self.Action.varDict['err'] = err
	self.Action.varDict['ret'] = retval

        comenv = {}                      # environment for com rules execution
        comenv['out'] = out
        comenv['err'] = err
        comenv['ret'] = retval
	result = eval( self.rule, comenv )
        log.log( "<directive>COM.docheck(), eval:'%s', result='%s'" % (self.rule,result), 9 )
	if result != 0:
	    self.doAction(Config)


##
## END - directive.py
##
