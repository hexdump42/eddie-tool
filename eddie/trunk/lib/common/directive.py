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


# Imports: Python
import os, string, re, sys, socket, time, threading
# Imports: Eddie
import action, definition, utils, log, ack


# Define exceptions
ParseFailure = 'ParseFailure'


class State:
    """Object to track the state of a directive."""

    def __init__(self):
	self.ID = None			# each directive has a unique ID
	self.lastfailtime = None	# last time a failure was detected
	self.faildetecttime = None	# first time failure was detected for current problem
	self.ack = ack.ack()		# ack object to track acknowledgements
	self.status = "ok"		# status of most recent check: "ok" or "fail"

    def ack(self, user=None, details=None):
	"""Record a user acknowledgement for current problem."""

	self.ack.set(user, details)		# set the acknowledgement


    def statefail(self):
	"""Update state info for check failure."""

	timenow = time.localtime(time.time())

	if self.status == "ok":
	    # if this is not a repeated failure then record the time of this
	    # first failure detection
	    self.faildetecttime = timenow

	self.status = "fail"
	self.lastfailtime = timenow

	log.log( "<directive>State.statefail(), ID '%s' status '%s' lastfailtime %s faildetecttime %s"%(self.ID, self.status, self.lastfailtime, self.faildetecttime), 6 )

	#TODO: Post an EVENT about this failure...
	#      EVENTS are either: new failure/problem detected
	#                     or: repeating failure


    def stateok(self):
	"""Update state info for check succeeding."""

	if self.status != "ok":
	    log.log( "<directive>State.stateok(), State changed to OK.  ID '%s'."%(self.ID), 6 )
	    #TODO: Post an EVENT about problem being resolved
	    pass

	self.status = "ok"

	log.log( "<directive>State.stateok(), ID '%s' status '%s'"%(self.ID, self.status), 8 )


    def age(self):
	"""Length of time since problem first found and problem last detected.
	   (ie: faildetecttime and lastfailtime).  Returned as time 9-tuple."""

	t1 = time.mktime(self.faildetecttime)
	t2 = time.mktime(self.lastfailtime)

	td = t2 -t1

	t0 = time.gmtime(0)			# time base (ie: 1/1/1970)
	t9 = time.gmtime(td)			# time diff from time base as 9-tuple
	tdiff = [0, 0, 0, 0, 0, 0, 0, 0, 0]	# 9-tuple for time diff from 0

	for i in range(len(t0)):
	    tdiff[i] = t9[i] - t0[i]

	return tdiff



class Rules:
    """Rules holds all the directives in a hash where the value of each key is the
       list of rules relating to that key.
    """

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



class Directive:
    """The base directive class.  Derive all directives from this base class."""

    def __init__(self, toklist):
	# Check toklist for valid tokens
	if len(toklist) < 2:		# need at least 2 tokens
	    raise ParseFailure, "Directive expected at least 2 tokens, found %d" % len(toklist)
	if len(toklist) > 3:		# no more than 3 tokens
	    raise ParseFailure, "Directive expected no more than 3 tokens, found %d" % len(toklist)
	if toklist[-1] != ':':		# last token should be a ':'
	    raise ParseFailure, "Directive expected ':' but didn't find one"

	self.ID = None			# No ID by default
	if len(toklist) == 3:
	    self.ID = toklist[1]	# grab ID if given

	self.basetype = 'Directive'	# the object can know its own basetype
	self.type = toklist[0]		# the directive type of this instance

	self.Action = action.action()	# create new action instance
	self.Action.varDict = {}	# dictionary of variables used for emails etc

	self.actionList = []		# each directive will have a list of actions

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

	# directives keep state information about themselves
	self.state = State()


    def __str__( self ):
	return "<%s Directive %s>" % (self.type, self.ID)


    def tokenparser(self, toklist, toktypes, indent):
	"""Parse named arguments for directives.  All valid named
	arguments are saved in the objects as self.argname, eg: self.rule
	It is up to each directive to check the validity of the arguments.
	Each directive should first call this function with:
	    apply( Directive.tokenparser, (self, toklist, toktypes, indent) )
	Note: toktypes and indent are not used by this function and can
	be None.
	"""

	tokdict=self.parseArgs(toklist)
	for t in tokdict.keys():
	    if t == 'action':	# special handler for actions
		self.actionList = self.parseAction( tokdict[t] )
	    else:
		try:
		    exec( "self.%s = tokdict[t]" % (t) )
		except:
		    raise ParseFailure, "Error parsing argument '%s'" % (t)

	# test for actionList which is always required
	try:
	    self.actionList
	except AttributeError:
	    raise ParseFailure, "Action not specified"

	# convert scanperiod to integer seconds if not already
	try:
	    if type(self.scanperiod) != type(1):
		self.scanperiod = utils.val2secs( self.scanperiod )
	except AttributeError:
	    pass	# scanperiod isn't setup, which is fine


    def doAction(self, Config):
    	"""Perform actions for a directive."""

	# record action information
	self.lastactiontime = time.localtime(time.time())


	actionList = self.actionList

	# Replace Action definitions with the corresponding actions
	#actionList = definition.parseList( actionList, ADict )

	# Put quotes around arguments so we can use eval()
	#actionList = utils.quoteArgs( actionList )

	# Set the 'action' variables with the expanded action list
	self.Action.varDict['act'] = 'The following actions were attempted:\n'
	self.Action.varDict['actnm'] = 'The following (non-email) actions were attempted:\n'
	#TODO:
	#for a in actionList:
	#    self.Action.varDict['act'] = self.Action.varDict['act'] + '\t' + a + '\n'
	#    if a[:5] != 'email':
	#	self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '\t' + a + '\n'

	self.Action.state = self.state
	self.Action.aliasDict = Config.aliasDict

	# Perform each action
	ret = None
	self.Action.actionReports = {}		# dict of actions and their return status
	for a in actionList:
	    sre = re.compile( "([A-Za-z0-9_]+)\(([A-Za-z0-9_.]+),?([0-9]?)\)" )
	    inx = sre.search( a )
	    if inx == None:
		#raise SyntaxError, "actionList regex error"
		# Assume we have a simple action call (rather than a
		# notification definition.
		self.Action.msg = None
		#print "calling: self.Action."+a
		ret = eval( 'self.Action.'+a )
		self.Action.actionReports[a] = ret
		if ret == None:
		    self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s\n' % a
		elif ret == 0:
		    self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s - Successful\n' % a
		else:
		    self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s - FAILED, return code %d\n' % (a, ret)

	    else:
		notif = inx.group(1)
		msg = inx.group(2)
		level = inx.group(3)
		if level == None or level == '':
		    level = '0'

		#print ">>>> notif:",notif
		#print ">>>> msg:",msg
		#print ">>>> level:",level

		try:
		    afunc = Config.NDict[notif].levels[level]
		except KeyError:
		    #print "Eddie: Error in directive.py line 148: Config.NDict[notif].levels[level] - level=%d" % level
		    log.log( "<directive>doAction(), Error in directive.py line 148: Config.NDict[notif].levels[level] - level=%s" % level, 1 )
		else:
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
			    ret = eval( 'self.Action.'+aa )
			    self.Action.actionReports[aa] = ret
			    if ret == None:
				self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s\n' % aa
			    elif ret == 0:
				self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s - Successful\n' % aa
			    else:
				self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s - FAILED, return code %d\n' % (aa, ret)

			#except AttributeError:
			    # Not an action function ... error...
		    #	log.log( "<directive>Directive, Error, 'action.%s' is not a defined action, config line follows,\n%s\n" % (a,self.raw), 2 )
	#print "actionReports:",self.Action.actionReports


    def parseAction(self, toklist):
        """Parses token list and returns a list of action call strings."""

	actstr = ""
	for t in toklist:
	    if t != '\012':
		actstr = actstr + t
	actlist = utils.trickySplit( actstr, ',' )
	return actlist


    def parseArgs( self, toklist ):
	"""Return dictionary of directive arguments."""

	argdict = {}

	listsize = len(toklist)
	i = 0
	while i < listsize:
	    try:
		if toklist[i] == '\012':
		    # skip carriage returns - we can ignore them
		    i = i + 1

		elif toklist[i+1] == '=':
		    argdict[toklist[i]] = utils.stripquote(toklist[i+2])
		    i = i + 3

		else:
		    log.log( "<directive>parseArgs(), unknown directive token '%s'" % (toklist[i]), 3)
		    raise ParseFailure, "unknown directive token '%s'" %(toklist[i])
	    except KeyError:
		log.log( "<directive>parseArgs(), error parsing directive arguments at i=%d" % (i), 2)
		raise ParseFailure, "Error parsing directive arguments"

	return argdict





##
## RULE-BASED COMMANDS
##
class FS(Directive):
    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	apply( Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.fs
	except AttributeError:
	    raise ParseFailure, "Filesystem not specified"
	try:
	    self.rule
	except AttributeError:
	    raise ParseFailure, "Rule not specified"

	# Set any FS-specific variables
	#  fsf = fs
	#  fsrule = rule
	self.Action.varDict['fsf'] = self.fs
	self.Action.varDict['fsrule'] = self.rule

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.FS.%s' % (log.hostname,self.fs)
	self.state.ID = self.ID

	log.log( "<Directive>FS, ID '%s' fs '%s' rule '%s' action '%s'" % (self.state.ID, self.fs, self.rule, self.actionList), 8 )


    def docheck(self, Config):
	log.log( "<directive>FS(), docheck(), fs '%s', rule '%s'" % (self.fs,self.rule), 7 )
	df = dlist[self.fs]
	if df == None:
	    log.log( "<directive>FS(), Error, no df with fs '%s'" % (self.fs), 2 )
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

	if result == 0:
	    self.state.stateok()	# update state info for check passed

	else:
	    self.state.statefail()	# update state info for check failed

	    # assign variables
	    self.Action.varDict['fsused'] = df.getUsed()
	    self.Action.varDict['fsavail'] = df.getAvail()
	    self.Action.varDict['fscapac'] = df.getPctused()
	    self.Action.varDict['fssize'] = df.getSize()
	    self.Action.varDict['fsdf'] = "%s%s" % (dlist.dfheader,df)

	    # get '%fsls' details for this filesystem
    	    #fsls = os.popen("ls -l %s" % (df.mountpt), 'r')
    	    fsls = utils.safe_popen("ls -l %s" % (df.mountpt), 'r')
 
	    fsls_output = ""
    	    for line in fsls.readlines():
		fsls_output = fsls_output + line
	    
	    #fsls.close()
	    utils.safe_pclose( fsls )

	    self.Action.varDict['fsls'] = fsls_output
	
    	    log.log( "<directive>FS(), rule '%s' was false, calling doAction()" % (self.rule), 6 )
    	    self.doAction(Config)

	Config.q.put( (self,time.time()+self.scanperiod) )	# put self back in the Queue


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

	self.ruleDict = { 'EX' : None,
		          'PR' : None }


    def tokenparser(self, toklist, toktypes, indent):
	apply( Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.pid
	except AttributeError:
	    raise ParseFailure, "Pid not specified"
	try:
	    self.rule
	except AttributeError:
	    raise ParseFailure, "Rule not specified"

	# Expect first token to be rule - one of self.ruleDict
	if self.rule not in self.ruleDict.keys():
	    raise ParseFailure, "PID found unexpected rule '%s'" % self.rule

	# Set any PID-specific variables
	#  %pidf = the PID-file
	self.Action.varDict['pidf'] = self.pid

	# define the unique ID
	self.state.ID = '%s.PID.%s.%s' % (log.hostname,self.pid,self.rule)

	log.log( "<Directive>PID, ID '%s' pid '%s' rule '%s' action '%s'" % (self.state.ID, self.pid, self.rule, self.actionList), 8 )


    def docheck(self, Config):
	log.log( "<directive>PID(), docheck(), pid '%s', rule '%s'" % (self.pid,self.rule), 7 )
	if self.rule == "EX":
	    # Check if pidfile exists
	    try:
		pidfile = open( self.pid, 'r' )
	    except IOError:
		# pidfile not found
		log.log( "<directive>PID(), EX, pidfile '%s' not found" % (self.pid), 6 )
		self.state.statefail()	# update state info for check failed
		self.doAction(Config)
	    else:
		log.log( "<directive>PID(), EX, pidfile '%s' found" % (self.pid), 8 )
		self.state.stateok()		# update state info for check passed
		pidfile.close()

	elif self.rule == "PR":
	    # check if process pid found in pidfile is running - no alert if pidfile not found
	    try:
		pidfile = open( self.pid, 'r' )
	    except IOError:
		# pidfile not found
		log.log( "<directive>PID(), PR, pidfile '%s' not found" % (self.pid), 6 )
	    else:
		log.log( "<directive>PID(), PR, pidfile '%s' found" % (self.pid), 8 )
		pid = pidfile.readline()
		pidfile.close()
		pid = string.strip(pid)
		# strip '\n' from pid string if necessary
		if pid[-1:] == '\n':
		    pid = pid[:-1]

		# Get rid of any other junk after pid
		pid = string.split(pid)[0]

		pid = int(pid)		# want it as an integer

		self.Action.varDict['pid'] = pid

		# Search for pid from process list
		if plist.pidExists( pid ) == 0:
		    # pid not found - to make sure, let's sleep a bit then check again
		    log.log( "<directive>PID(), PR, pid %s not in process list - sleeping and checking again..." % (pid), 7 )
		    time.sleep( 30 )
		    plist.refresh()		# force refresh of proc list
		    if plist.pidExists( pid ) == 0:
			# there is no process with pid == pid
			log.log( "<directive>PID(), PR, pid %s not in process list" % (pid), 6 )
			self.state.statefail()	# update state info for check failed
			self.doAction(Config)
		    else:
			log.log( "<directive>PID(), PR, pid %s is in process list" % (pid), 7 )
			self.state.stateok()		# update state info for check passed

	    Config.q.put( (self,time.time()+self.scanperiod) )	# put self back in the Queue

	else:
	    # invalid rule
	    log.log( "<directive>PID, Error, '%s' is not a valid PID rule, config line follows,\n%s\n" % (self.rule,self.raw), 2 )


class PROC(Directive):
    """Process checks."""

    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )
	self.ruleDict = { 'NR' : self.NR,
		          'R'  : self.R,
			  'check' : self.check }


    def tokenparser(self, toklist, toktypes, indent):
	"""Parse tokenized input."""

	apply( Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.procname
	except AttributeError:
	    raise ParseFailure, "Process name not specified"
	try:
	    self.rule
	except AttributeError:
	    raise ParseFailure, "Rule name not specified"

	# Expect first token to be rule
	if self.rule in self.ruleDict.keys():
	    # - either one of self.ruleDict
	    self.rule = self.ruleDict[self.rule]       # Rule is a function
	elif type(self.rule) == type('STRING'):
	    # - or a string containing a special check
	    self.rule = self.ruleDict['check']
	    self.checkstring = utils.stripquote(self.rule)
	else:
	    raise ParseFailure, "PROC found unexpected rule '%s'" % self.rule

	# Set any PROC-specific variables
	#  %procp = the process name
	self.Action.varDict['procp'] = self.procname
	#  %procpid = pid of process (ie: if found running for R rule)
	self.Action.varDict['procpid'] = '[pid not yet defined]'

	# define the unique ID
	self.state.ID = '%s.PROC.%s.%s' % (log.hostname,self.procname,toklist[0])

	log.log( "<Directive>PROC, ID '%s' procname '%s' rule '%s' action '%s'" % (self.state.ID, self.procname, self.rule, self.actionList), 8 )


    def docheck(self, Config):
	"""Perform specified check."""

	log.log( "<directive>PROC(), docheck(), procname '%s', rule '%s'" % (self.procname,self.rule), 7 )
	self.rule(Config)

	Config.q.put( (self,time.time()+self.scanperiod) )	# put self back in the Queue


    def NR(self,Config):
	"""Call action if process is found to be NOT running."""

	if plist.procExists( self.procname ) == 0:
	    # process not running - let's sleep a bit then check again to make sure
	    log.log( "<directive>NR(PROC) procname not running, '%s' - sleeping before recheck..." % (self.procname), 7 )
	    time.sleep( 30 )
	    plist.refresh()		# force refresh of proc list
	    if plist.procExists( self.procname ) == 0:
		log.log( "<directive>NR(PROC) procname not running, '%s'" % (self.procname), 6 )
		self.state.statefail()	# update state info for check failed
		self.doAction(Config)
		return

	self.state.stateok()	# update state info for check passed


    def R(self,Config):
	"""Call action if process is found to BE running."""

	if plist.procExists( self.procname ) > 0:
	    log.log( "<directive>R(PROC) procname is running, '%s'" % (self.procname), 6 )
	    # Set %procpid variable.
	    self.Action.varDict['procpid'] = plist[self.procname].pid
	    self.state.statefail()	# update state info for check failed
	    self.doAction(Config)

	else:
	    self.state.stateok()	# update state info for check passed


    def check(self,Config):
	"""Executes a check string supplied by user."""

	for p in plist.getList():
	    if p.procname == self.procname:
		try:
		    procenv = p.procinfo()		# get dictionary of process details
		except AttributeError:
		    log.log( "<directive>PROC.check() warning, no process '%s'." % (self.procname), 8 )
		    return

		result = eval( self.checkstring, procenv )

		if result != 0:
		    # build varDict from procenv
		    for i in procenv.keys():
			self.Action.varDict['proc%s'%(i)] = procenv[i]
		    self.state.statefail()	# update state info for check failed
		    self.doAction(Config)

		else:
		    self.state.stateok()	# update state info for check passed



class SP(Directive):
    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	apply( Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.port
	except AttributeError:
	    raise ParseFailure, "Port not specified"
	try:
	    self.protocol
	except AttributeError:
	    raise ParseFailure, "Protocol not specified"
	try:
	    self.bindaddr
	except AttributeError:
	    raise ParseFailure, "Bind address not specified"

	self.port_n = self.port		# remember port name

	# lets try resolving this service port to a number
	try:
	    self.port = socket.getservbyname(self.port_n, self.protocol)
	except socket.error:
	    self.port = self.port_n

	self.Action.varDict['spport'] = self.port_n
	self.Action.varDict['spaddr'] = self.bindaddr
	self.Action.varDict['spprot'] = self.protocol

	# define the unique ID
	self.state.ID = '%s.SP.%s/%s.%s' % (log.hostname,self.protocol,self.port_n,self.bindaddr)

	log.log( "<Directive>SP, ID '%s' protocol '%s', port '%s', bind addr '%s', action '%s'" % (self.state.ID, self.protocol, self.port, self.bindaddr, self.actionList), 8 )


    def docheck(self, Config):
	log.log( "<directive>SP(), docheck(), protocol '%s', port '%s', addr '%s'" % (self.protocol,self.port_n,self.bindaddr), 7 )

	ret = nlist.portExists(self.protocol, self.port, self.bindaddr) != None
	if ret != 0:
	    log.log( "<directive>SP(), port %s/%s listener found bound to %s" % (self.protocol , self.port_n, self.bindaddr), 8 )
	    self.state.stateok()	# update state info for check passed
	else:
	    log.log( "<directive>SP(), port %s/%s no listener found bound to %s - sleeping before recheck..." % (self.protocol , self.port_n, self.bindaddr), 7 )
	    time.sleep( 30 )
	    nlist.refresh()		# force refresh of network stats

	    ret = nlist.portExists(self.protocol, self.port, self.bindaddr) != None
	    if ret != 0:
		log.log( "<directive>SP(), port %s/%s listener found bound to %s" % (self.protocol , self.port_n, self.bindaddr), 7 )
		self.state.stateok()	# update state info for check passed
	    else:
		log.log( "<directive>SP(), port %s/%s no listener found bound to %s" % (self.protocol , self.port_n, self.bindaddr), 6 )
		self.state.statefail()	# update state info for check failed
		self.doAction(Config)

	Config.q.put( (self,time.time()+self.scanperiod) )	# put self back in the Queue


COMsemaphore = threading.Semaphore()

class COM(Directive):
    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	apply( Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.cmd
	except AttributeError:
	    raise ParseFailure, "Command (cmd) not specified"
	try:
	    self.rule
	except AttributeError:
	    raise ParseFailure, "Rule not specified"

	# Set any COM-specific variables
	#  %com = the command
	#  %rule = the rule
	self.Action.varDict['COMcmd'] = self.cmd
	self.Action.varDict['COMrule'] = self.rule

	# define the unique ID
	self.state.ID = '%s.COM.%s.%s' % (log.hostname,self.cmd,self.rule)

	log.log( "<directive>COM, ID '%s' cmd '%s' rule '%s' action '%s'" % (self.state.ID, self.cmd, self.rule, self.actionList), 8 )


    def docheck(self, Config):
	log.log( "<directive>COM.docheck(), cmd '%s', rule '%s'" % (self.cmd,self.rule), 7 )
	log.log( "<directive>COM.docheck(), acquiring semaphore lock for cmd '%s'" % (self.cmd), 8 )
	COMsemaphore.acquire()
	log.log( "<directive>COM.docheck(), semaphore acquired for cmd '%s'" % (self.cmd), 8 )
	tmpprefix = "/var/tmp/com%d" % os.getpid()
	cmd = "{ %s ; } >%s.out 2>%s.err" % (self.cmd, tmpprefix, tmpprefix )
	log.log( "<directive>COM.docheck(), calling system('%s')" % (cmd), 8 )
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
	    log.log( "<directive>COM.docheck(), Error, could not open '%s'" % (tmpprefix + ".out"), 2 )
	else:
	    out = outf.read()
	    outf.close()
	    os.remove( tmpprefix + ".out" )
	    out = string.strip(out)
	    if out[-1:] == '\n':
		out = out[:-1]

        err = ""
	try:
	    errf = open( tmpprefix + ".err", 'r' )
	except IOError:
	    # stderr tmp file not found
	    log.log( "<directive>COM.docheck(), Error, could not open '%s'" % (tmpprefix + ".err"), 2 )
	else:
	    err = errf.read()
	    errf.close()
	    os.remove( tmpprefix + ".err" )
	    err = string.strip(err)
	    if err[-1:] == '\n':
		err = err[:-1]

	COMsemaphore.release()
	log.log( "<directive>COM.docheck(), released semaphore lock for cmd '%s'" % (self.cmd), 8 )

        log.log( "<directive>COM.docheck(), retval=%d" % retval, 8 )
        log.log( "<directive>COM.docheck(), signum=%s" % signum, 8 )
	log.log( "<directive>COM.docheck(), stdout='%s'" % out, 8 )
	log.log( "<directive>COM.docheck(), stderr='%s'" % err, 8 )

	# save values in variable dictionary
	self.Action.varDict['comout'] = out
	self.Action.varDict['comerr'] = err
	self.Action.varDict['comret'] = retval

        comenv = {}                      # environment for com rules execution
        comenv['out'] = out
        comenv['err'] = err
        comenv['ret'] = retval
	result=None
	try:
	    result = eval( self.rule, comenv )
	except:
	    log.log( "<directive>COM.docheck() : an error occured with rule '%s' exception type: '%s' exception value: '%s' - env was: %s"%(self.rule,sys.exc_type,sys.exc_value,comenv), 3 )
	    return

        log.log( "<directive>COM.docheck(), eval:'%s', result='%s'" % (self.rule,result), 9 )
	if result != 0:
	    self.state.statefail()	# update state info for check failed
	    self.doAction(Config)
	else:
	    self.state.stateok()	# update state info for check passed

	Config.q.put( (self,time.time()+self.scanperiod) )	# put self back in the Queue


class PORT(Directive):
    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	apply( Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.host
	except AttributeError:
	    raise ParseFailure, "Host not specified"
	try:
	    self.port
	except AttributeError:
	    raise ParseFailure, "Port not specified"
	try:
	    self.port = int(self.port)
	except ValueError:
	    raise ParseFailure, "Port is not an integer: %s" % (self.port)
	try:
	    self.send
	except AttributeError:
	    raise ParseFailure, "Send string not specified"
	try:
	    self.expect
	except AttributeError:
	    raise ParseFailure, "Expect string not specified"

	# Set any PORT-specific variables
	#  %porthost = the host
	#  %portport = the port
	#  %portsend = the send string
	#  %portexpect = the expect string
	#  %portrecv = the string received from port connection (at check time)
	self.Action.varDict['porthost'] = self.host
	self.Action.varDict['portport'] = self.port
	self.Action.varDict['portsend'] = self.send
	self.Action.varDict['portexpect'] = self.expect
	self.Action.varDict['portrecv'] = ''

	# define the unique ID
	self.state.ID = '%s.PORT.%s.%d' % (log.hostname,self.host,self.port)

	log.log( "<Directive>PORT, ID '%s' host '%s' port '%d' send '%s' expect '%s'" % (self.state.ID, self.host, self.port, self.send, self.expect), 8 )


    def docheck(self, Config):
	log.log( "<directive>PORT.docheck(), host '%s', port '%d', send '%s', expect '%s'" % (self.host,self.port,self.send,self.expect), 7 )

	self.Action.varDict['portrecv'] = ''

        if not self.isalive(host=self.host,port=self.port,send=self.send,expect=self.expect):
	    log.log( "<directive>PORT.docheck(), isalive() failed.", 7 )
	    self.state.statefail()	# update state info for check failed
            self.doAction(Config)
	else:
	    self.state.stateok()	# update state info for check passed

	Config.q.put( (self,time.time()+self.scanperiod) )	# put self back in the Queue


    def isalive(self,host,port,send="",expect=""):
        """ Connects to host:port, sends send,
            receives input, compares it to expect
            and returns TRUE or FALSE accordingly """
        #print "Trying to connect to %s:%d send:'%s' exp:'%s'" % (host,port,send,expect)   #DEBUG
        try:
            try:
                s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                s.connect(host,port)
                if expect == "":
                    s.close()
                    return 1    # port connection ok
                else:
                    exec( "send='%s'" % send )
		    sendlist = string.split(send, '\n')		# split each line
		    # send each line - only compare last output received
		    for line in sendlist:
			log.log( "<directive>PORT.isalive(): sending '%s'" % (line), 7 )
			s.send(line+'\n')
			data=s.recv(1024)
			log.log( "<directive>PORT.isalive(): received '%s'" % (data), 7 )

                    self.Action.varDict['portrecv'] = data

                    if data==expect or re.search( '.*' + expect + '.*', data, ) != None:
                        s.close()
                        return 1
                    else:
                        return 0
            finally:
                try:
                    s.close()
                except: 
                    pass
        except:
            return 0

	return 0



class IF(Directive):
    """Network Interface directive."""

    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )

        self.ruleDict = { 'NE' : self.NE,
			  'EX' : self.EX,
			  'check' : self.check }



    def tokenparser(self, toklist, toktypes, indent):
	"""Parse rest of rule (after ':')."""
	apply( Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.name
	except AttributeError:
	    raise ParseFailure, "Interface name not specified"
	try:
	    self.rule
	except AttributeError:
	    raise ParseFailure, "Rule not specified"

	self.checkstring = ""

	# Expect first token to be rule
        if self.rule in self.ruleDict.keys():
            # - either one of self.ruleDict
            self.rule = self.ruleDict[self.rule]       # Set the rule
        elif type(self.rule) == type('STRING'):
            # - or a string containing a special check
            self.rule = self.ruleDict['check']
            self.checkstring = utils.stripquote(self.rule)
        else:
            raise ParseFailure, "IF found unexpected rule '%s'" % self.rule

	self.Action.varDict['ifname'] = self.name
	self.Action.varDict['ifrule'] = self.rule
	self.Action.varDict['ifcheckstring'] = self.checkstring

	# define the unique ID
	self.state.ID = '%s.IF.%s.%s' % (log.hostname,self.name,self.rule)

	log.log( "<Directive>IF, ID '%s' name '%s', rule '%s', checkstring '%s', action '%s'" % (self.state.ID, self.name, self.rule, self.checkstring, self.actionList), 8 )


    def docheck(self, Config):
	"""Perform the check."""

	log.log( "<directive>IF(), docheck(), name '%s', check '%s', checkstring '%s'" % (self.name,self.check,self.checkstring), 7 )

	self.rule(Config)

	Config.q.put( (self,time.time()+self.scanperiod) )	# put self back in the Queue


    def NE(self, Config):
	"""Check that an interface currently does not exist."""

	if nlist.getInterface(self.name) == None:
	    # interface doesn't exist
	    log.log( "<directive>IF.NE() interface '%s' does not exist" % (self.name), 6 )
	    self.state.statefail()	# update state info for check failed
	    self.doAction(Config)
	else:
	    self.state.stateok()	# update state info for check passed


    def EX(self, Config):
	"""Check that an interface currently exists."""

	if nlist.getInterface(self.name) != None:
	    # interface exists
	    log.log( "<directive>IF.EX() interface '%s' exists" % (self.name), 6 )
	    self.state.statefail()	# update state info for check failed
	    self.doAction(Config)
	else:
	    self.state.stateok()	# update state info for check passed


    def check(self, Config):
	"""Execute a check supplied by the user as a string."""

	i = nlist.getInterface(self.name)
	if i == None:
	    log.log( "<directive>IF.check() warning, no interface '%s'." % (self.name), 7 )
	    return		# ignore if this interface doesn't exist

	ifenv = i.ifinfo()	# get dictionary of interface details

	result = eval( self.checkstring, ifenv )

	if result != 0:
	    # build varDict from ifenv
	    for i in ifenv.keys():
		self.Action.varDict['if%s'%(i)] = ifenv[i]
	    self.state.statefail()	# update state info for check failed
	    self.doAction(Config)
	else:
	    self.state.stateok()	# update state info for check passed


class NET(Directive):
    """Network Statistics directive."""

    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )

	self.rule = ''


    def tokenparser(self, toklist, toktypes, indent):
	"""Parse rest of rule (after ':')."""
	apply( Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.rule
	except AttributeError:
	    raise ParseFailure, "Rule not specified"

	# Rule should be a string
        if type(self.rule) != type('STRING'):
	    raise ParseFailure, "NET parse error, rule is not string."

	self.Action.varDict['netrule'] = self.rule

	# define the unique ID
	self.state.ID = '%s.NET.%s' % (log.hostname,self.rule)

	log.log( "<Directive>NET, ID '%s' rule '%s', action '%s'" % (self.state.ID, self.rule, self.actionList), 8 )


    def docheck(self, Config):
	"""Perform the check."""

	log.log( "<directive>NET(), docheck(), rule '%s'" % (self.rule), 7 )

	netenv = nlist.statstable.getHash()	# get dictionary of network stats

	result = eval( self.rule, netenv )

	if result != 0:
	    # build varDict from netenv
	    for i in netenv.keys():
		self.Action.varDict['net%s'%(i)] = netenv[i]
	    self.state.statefail()	# update state info for check failed
	    self.doAction(Config)
	else:
	    self.state.stateok()	# update state info for check passed

	Config.q.put( (self,time.time()+self.scanperiod) )	# put self back in the Queue



class SYS(Directive):
    """System Statistics directive."""

    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )

	self.rule = ''


    def tokenparser(self, toklist, toktypes, indent):
	"""Parse rest of rule (after ':')."""
	apply( Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.rule
	except AttributeError:
	    raise ParseFailure, "Rule not specified"

	# Rule should be a string
        if type(self.rule) != type('STRING'):
	    raise ParseFailure, "SYS parse error, rule is not string."

	self.Action.varDict['sysrule'] = self.rule

	# define the unique ID
	self.state.ID = '%s.SYS.%s' % (log.hostname,self.rule)

	log.log( "<Directive>SYS, ID '%s' rule '%s' action '%s'" % (self.state.ID, self.rule, self.actionList), 8 )


    def docheck(self, Config):
	"""Perform the check."""

	log.log( "<directive>SYS(), docheck(), rule '%s'" % (self.rule), 7 )

	sysenv = system.getHash()		# get dictionary of system stats

	try:
	    result = eval( self.rule, sysenv )
	except SyntaxError:
	    log.log( "<directive>SYS(), docheck(), SyntaxError evaluating rule '%s'" % (self.rule), 3 )
	    return


	if result != 0:
	    # build varDict from sysenv
	    for i in sysenv.keys():
		self.Action.varDict['sys%s'%(i)] = sysenv[i]
	    self.state.statefail()	# update state info for check failed
	    self.doAction(Config)
	else:
	    self.state.stateok()	# update state info for check passed

	Config.q.put( (self,time.time()+self.scanperiod) )	# put self back in the Queue



class STORE(Directive):
    """Store selected host data."""

    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )

	self.rule = ''


    def tokenparser(self, toklist, toktypes, indent):
	"""Parse rest of rule (after ':')."""
	apply( Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.rule
	except AttributeError:
	    raise ParseFailure, "Rule not specified"

	# Rule should be a string
        if type(self.rule) != type('STRING'):
	    raise ParseFailure, "STORE parse error, rule is not string."

	self.Action.varDict['storerule'] = self.rule

	# define the unique ID
	self.state.ID = '%s.FS.%s' % (log.hostname,self.rule)

	log.log( "<Directive>STORE, ID '%s' rule '%s' action '%s'" % (self.state.ID, self.rule, self.actionList), 8 )


    def docheck(self, Config):
	"""Perform the check.  In this case, the 'check' is automatically true (we always want to store)."""

	self.state.stateok()	# update state info for check passed
	log.log( "<directive>STORE(), docheck(), rule '%s'" % (self.rule), 7 )

	datahash = None

	# Get data as directed by rule.
	# * this is hard-coded to a few different 'rules' atm.  This should be
	# cleaned up later to handle any type of rule (TODO)

	if self.rule[:6] == 'system':
	    datahash = system.getHash()			# get dictionary of system stats
	elif self.rule[:7] == 'netstat':
	    #datahash = nlist.statstable.getHash()		# get dictionary of network stats
	    datahash = nlist.getNetworkStats()			# get dictionary of network stats
	elif self.rule[:4] == 'proc':
	    datahash = plist.allprocs()				# get dictionary of process details
	elif self.rule[:2] == 'if':
	    datahash = nlist.getAllInterfaces()			# get dictionary of interface details
	elif self.rule[:6] == 'iostat':
	    datahash = iostat.getHash()			# get dictionary of iostat data

	if datahash == None:
	    log.log( "<directive>STORE(), docheck(), rule '%s' is invalid." % (self.rule), 3 )
	    return

	# Create a new hash with 'data.' prepended to each key (as required by estored).
# Don't do this anymore.
#	storeenv = {}
#	for i in datahash.keys():
#	    storeenv['data.'+i] = datahash[i]

	self.Action.storedict = datahash
	self.doAction(Config)

	Config.q.put( (self,time.time()+self.scanperiod) )	# put self back in the Queue



##
## END - directive.py
##
