## 
## File		: directive.py 
## 
## Author       : Rod Telford  <rtelford@psychofx.com>
##                Chris Miles  <chris@psychofx.com>
## 
## Start Date	: 19971205 
## 
## Description	: 
##
## $Id$
##
##
########################################################################
## (C) Chris Miles 2001
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


# Imports: Python
import os, string, re, sys, socket, time, threading, traceback, errno
# Imports: Eddie
import action, definition, utils, log, ack, datacollect


##
## Define exceptions
##

# ParseFailure: a problem occured parsing the directive definition or the
#   directive arguments.  Config parsing will halt and an error will be
#   printed, pointing out the config line where parsing stopped.
ParseFailure = 'ParseFailure'

# DirectiveError: a critical error was caught while executing the directive.
#   The directive will not be re-scheduled for future execution.
DirectiveError = 'DirectiveError'


##
## Directive management objects
##

class State:
    """
    Object to track the state of a directive.
    """

    def __init__(self, thisdirective):
	self.ID = None			# each directive has a unique ID
	self.lastfailtime = None	# last time a failure was detected
	self.faildetecttime = None	# first time failure was detected for current problem
	self.ack = ack.ack()		# ack object to track acknowledgements
	self.checkcount = 0		# count number of checks/re-checks
	self.thisdirective = thisdirective	# pointer to the directive this object belongs to

	# Status can be:
	#  ok          - no problem
	#  failinitial - possible failure state (might need more rechecks, for example)
	#  fail        - check has failed
	self.status = "ok"		# status of most recent check


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

	    self.status = "failinitial"

	self.checkcount = self.checkcount + 1

	if self.checkcount >= self.thisdirective.args.numchecks:
	    # Only put in "fail" state when all rechecks have failed
	    # otherwise the state is left in "failinitial" state
	    self.status = "fail"

	self.lastfailtime = timenow

	log.log( "<directive>State.statefail(): ID '%s' status '%s' checkcount %d lastfailtime %s faildetecttime %s"%(self.ID, self.status, self.checkcount, self.lastfailtime, self.faildetecttime), 7 )

	#TODO: Post an EVENT about this failure...
	#      EVENTS are either: new failure/problem detected
	#                     or: repeating failure


    def stateok(self, Config):
	"""Update state info for check succeeding.
	Perform actions depending on previous state."""

	if self.status == "fail":
	    # This is a state change from "fail" to "ok".
	    # This is when the 'act2ok' actions should be performed.
	    #
	    # (If state was "failinitial" then check never really failed
	    #  properly so allow change back to "ok" silently.)

	    # Mark the lastfailtime as now, as state has been failed up until
	    # this point in time.
	    timenow = time.localtime(time.time())
	    self.lastfailtime = timenow

	    log.log( "<directive>State.stateok(): State changed to OK.  ID '%s'."%(self.ID), 7 )

	    if 'act2okList' in dir(self.thisdirective.args):
		self.thisdirective.performAction(Config,self.thisdirective.args.act2okList)

	    #TODO: Post an EVENT about problem being resolved

	else:
	    # If state wasn't previously failed then it is still ok.
	    # This is when the 'actelse' actions should be performed.
	    if 'actelseList' in dir(self.thisdirective.args):
		self.thisdirective.performAction(Config,self.thisdirective.args.actelseList)

	self.status = "ok"

	self.checkcount = 0	# reset check counter

	log.log( "<directive>State.stateok(): ID '%s' status '%s'"%(self.ID, self.status), 7 )


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
    """
    Rules holds all the directives in a hash where the value of each key is the
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



class Args:
    """Container for holding directive arguments."""

    def __init__(self):
	"""Nothing to do really."""
	pass



class Directive:
    """
    The base directive class.  All directives are derived from this base class.
    """

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
	    self.ID = utils.stripquote(toklist[1])	# grab ID if given

	self.basetype = 'Directive'	# the object can know its own basetype
	self.type = toklist[0]		# the directive type of this instance

	self.request_collector()	# request data collector reference

	self.hastokenparser = 1		# tell parser this object has a separate tokenparser()

	self.Action = action.action()	# create new action instance
	self.defaultVarDict = {}	# dictionary of variables used by action strings

	self.args = Args()		# Container for arguments
	#self.args.actionList = []	# each directive will have a list of actions
	#self.args.act2okList = []	# a list of actions for failed state changing to ok
	#self.args.actelseList = []	# a list of actions for state remaining ok

	# Set up informational variables - these are common to all Directives
	#  %(hostname)s = hostname
	#  %(h)s = hostname		(shorthand for '%(hostname)s')
	self.defaultVarDict['hostname'] = log.hostname
	self.defaultVarDict['h'] = log.hostname

	# Create initial variable dictionary
	self.Action.varDict = {}

	# Set default output displayed on console connections
	self.console_output = '%(state)s'

	# directives keep state information about themselves
	self.state = State(self)

	self.requeueTime = None	# specific requeue time can be specified

	self.args.numchecks = 1	# perform only 1 check at a time by default
	self.args.checkwait = 0	# time to wait in between multiple checks
	self.args.template = None	# no template by default


    def request_collector(self):
	"""
	If data collector(s) required, get reference(s) to it(them).
	If data collectors don't exist, the directive cannot be created.

	Data collectors are requested by creating a list of (module, collector)
	pairs in self.need_collectors.
	"""

	self.data_collectors = {}	# dictionary of data collector references

	# If need_collectors is not defined, then no collectors are required,
	# just return to continue setting up directive
	try:
	    self.need_collectors
	except:
	    return 1		# ok

	for i in self.need_collectors:
	    (module, collector) = i

	    try:
		self.data_collectors["%s.%s"%(module,collector)] = data_modules.request( module, collector )
	    except data_modules.DataModuleError:
		e = sys.exc_info()
		log.log( "<directive>Directive.request_collector(): error requesting %s.%s, %s %s" % (module,collector,e[0],e[1]), 1 )
		raise ParseFailure, "Error requesting collector %s.%s for directive %s:\n%s\n%s" % (module,collector,self.ID,e[0],e[1])

	return 1		# ok


    def __str__( self ):
	return "%s.%s" % (self.type, self.ID)


    def getDirective( self, ID, Config ):
	for d in Config.ruleList.keys():
	    list = Config.ruleList[d]
	    if list != None:
		for i in list:
		    if i.ID == ID:
			return i

	for c in Config.groups:
	    self.getDirective( ID, c.ruleList )

	return None


    def tokenparser(self, toklist, toktypes, indent):
	"""
	Parse named arguments for directives.  All valid named
	arguments are saved in the objects as self.args.argname,
	eg: self.args.rule

	It is up to each directive to check the validity of the arguments.
	Each directive should first call this function with:
	    apply( Directive.tokenparser, (self, toklist, toktypes, indent) )

	Note: toktypes and indent are not used by this function and can
	be None.
	"""

	tokdict=self.parseArgs(toklist)
	for t in tokdict.keys():
	    if t == 'template':	# special handler for templates
		self.args.template = tokdict[t]	# template name
		if self.args.template != 'self':
		    tpldirective = self.getDirective(self.args.template, self.Config)
		    if tpldirective == None:
			raise ParseFailure, "template '%s' not found." % (self.args.template)
		    else:
			# copy template directive arguments
			for t in dir(tpldirective.args):
			    if t != 'template':
				exec( 'self.args.%s = tpldirective.args.%s' % (t,t) )
				#exec( "print 'self.args.%s =', self.args.%s" % (t,t) )

	    # Use action parser for any of the action lists
	    elif t == 'act2ok':
                self.args.act2okList = self.parseAction( tokdict[t] )
	    elif t == 'actelse':
		self.args.actelseList = self.parseAction( tokdict[t] )
	    elif t == 'action':
		self.args.actionList = self.parseAction( tokdict[t] )

	    else:
		try:
		    exec( "self.args.%s = tokdict[t]" % (t) )
		except:
		    raise ParseFailure, "Error parsing argument '%s'" % (t)

	# Parse rest of directive arguments

	try:
	    self.args.scanperiod
	except AttributeError:
	    pass
	else:
	    # convert scanperiod to integer seconds if not already
	    if type(self.args.scanperiod) != type(1):
		self.args.scanperiod = utils.val2secs( self.args.scanperiod )
		if self.args.scanperiod == None:
		    raise ParseFailure, "Invalid scanperiod: '%s'"%(self.args.scanperiod)
	    self.scanperiod = self.args.scanperiod	# set the scanperiod

	# test numchecks argument is integer and >= 0
	if type(self.args.numchecks) != type(1):
	    try:
		self.args.numchecks = int(self.args.numchecks)
	    except ValueError:
		raise ParseFailure, "numchecks argument is not integer: '%s'"%(self.args.numchecks)
	if self.args.numchecks < 0:
	    raise ParseFailure, "numchecks argument must be > 0: '%s'"%(self.args.numchecks)

	# convert checkwait to integer seconds if not already
	try:
	    if type(self.args.checkwait) != type(1):
		self.args.checkwait = utils.val2secs( self.args.checkwait )
	except:
	    raise ParseFailure, "checkwait argument has incorrect value '%s'"%(self.args.checkwait)

	# Set console_output if possible
	try:
	    self.console_output = self.args.console
	except AttributeError:
	    pass	# console argument not set, so leave as default

	# Set history if possible
	try:
	    self.history_size = int(self.args.history)
	except AttributeError:
	    pass	# history argument not set, so leave as default
	except ValueError:
	    raise ParseFailure, "history must be an integer: '%s'"%(self.args.history)
	else:
	    # TODO
	    pass
#	    for i in self.data_collectors.keys():
#		self.data_collectors[i].history.setHistory(self.history_size)

	# Assign Notification object actions if any
	for n in self.parent.NDict.keys():
	    execstr = "self.Action.%s = self.parent.NDict[n].doAction" % (n)
	    exec( execstr )

	# Set any default action variables
	if 'rule' in dir(self.args):
	    self.defaultVarDict['rule'] = str(self.args.rule)

	if self.args.template == 'self':
	    # jump out of token parsing if this is a template only
	    raise 'Template'


    def evalAction(self, actioncall):
	"""
	Evaluate the given action call.
	"""

	log.log( "<directive>Directive.evalAction(): calling action '%s'" % (actioncall), 9 )

	# Evaluate action in environment with alias-dictionary to auto
	# substitute any aliases
	actionEnv = {}				# setup action environment
	actionEnv.update(self.Action.aliasDict)	# add all aliases

	if self.Action.msg:
	    # Get M group needed for this action
	    msgtree = string.split( self.Action.msg, '.' )
	    M = self.Action.MDict[msgtree[0]]
	    for m in msgtree[1:]:
		M = M[m]

	    #DEBUG
	    #print "self.Action.msg:",self.Action.msg
	    #print "self.Action.level:",self.Action.level
	    #print "self.Action.MDict:",self.Action.MDict
	    #print "self.Action.MDict:proc:",self.Action.MDict['proc']
	    #print "M:",M

	    actionEnv.update(M.MDict)			# add MSGs

	actionEnv['_Action'] = self.Action		# add Action object
	acall = "_Action.%s" % (actioncall)		# the string to be evaluated

	evalenv = {}
	evalenv.update(actionEnv)			# copy actionEnv for eval()
	try:
	    ret = eval( acall, {"__builtins__": {}}, evalenv )		# Call the Action
	except:
	    # Handle any action evaluation exceptions neatly
	    e = sys.exc_info()
	    tb = traceback.format_list( traceback.extract_tb( e[2] ) )
	    log.log( "<directive>Directive.evalAction(): Error evaluating %s: %s, %s, %s; actionEnv=%s" % (acall, e[0], e[1], tb, actionEnv), 5 )
	    return

	# Update the action reports
	self.Action.actionReports[actioncall] = ret
	if ret == None:
	    self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s\n' % (actioncall)
	elif ret == 0:
	    self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s - Successful\n' % (actioncall)
	else:
	    self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s - FAILED, return code %d\n' % (actioncall, ret)


    def performAction(self, Config, actionList):

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
		# Assume we have a simple action call (rather than a
		# notification definition.
		self.Action.msg = None
		self.evalAction( a )

	    else:
		# Using a Notification object
		notif = inx.group(1)
		msg = inx.group(2)
		level = inx.group(3)
		if level == None or level == '':
		    level = '0'

		#print ">>>> notif:",notif
		#print ">>>> msg:",msg
		#print ">>>> level:",level

		try:
		    # Get the actions to execute from the given Level of the N object
		    afunc = Config.NDict[notif].levels[level]
		except KeyError:
		    log.log( "<directive>Directive.performAction(): Error in directive.py line 431: Config.NDict[notif].levels[level], level=%s" % level, 5 )
		else:
		    self.Action.notif = notif
		    self.Action.msg = msg
		    self.Action.level = level
		    self.Action.MDict = Config.MDict #TODO: move to init() ?

		    aList = utils.trickySplit( afunc[0], ',' )
		    # Put quotes around arguments so we can use eval()
		    #aList = utils.quoteArgs( aList )
		    for aa in aList:
			self.evalAction( aa )



    def doAction(self, Config, actionList=None):
    	"""Perform actions for a directive."""

	if self.state.checkcount < self.args.numchecks:
	    # need to wait before re-checking
	    # when put back in queue only wait checkwait seconds
	    self.requeueTime = time.time()+self.args.checkwait
	    log.log( "<directive>doAction(): scheduling for recheck in %d seconds" % self.args.checkwait, 6 )
	    return
	else:
	    self.state.checkcount = 0	# performing action so reset counter
  

	# record action information
	self.lastactiontime = time.localtime(time.time())

	# Make sure there are some actions to perform
	# (they are not always necessary)
	if 'actionList' in dir(self.args):
	    self.performAction(Config, self.args.actionList)


    def parseAction(self, toklist):
        """Parses token list and returns a list of action call strings."""

	actstr = ""
	for t in toklist:
	    if t != '\012':
		actstr = actstr + t
	actlist = utils.trickySplit( actstr, ',' )
	return actlist


    def parseArgs( self, toklist ):
	"""
	Return dictionary of directive arguments.

	toklist is a list of directive argument lines.
	Each line is a list of basic tokens.
	Argument lines must be of the form: <name>=<value>
	  where <name> is a 'word' and <value> is something like a string,
	  int, float, function call, etc.
	"""

	argdict = {}

	for argline in toklist:
	    if len(argline) < 3 or argline[1] != '=':
		log.log( "<directive>Directive.parseArgs(): invalid directive argument '%s'" % (string.join(argline)), 1)
		raise ParseFailure, "invalid directive argument '%s'" %(string.join(argline))

	    argdict[argline[0]] = utils.stripquote(string.join(argline[2:],""))

	return argdict


    def putInQueue( self, q ):
	"""Put this directive back into the scheduler queue."""

	if self.requeueTime:
	    # a specific requeueTime has been requested
	    q.put( (self,self.requeueTime) )
	    self.requeueTime = None
	    log.log( "<directive>Directive.putInQueue(): %s re-queued by requeueTime" % (self), 7)

	else:
	    # reschedule in scanperiod seconds
	    q.put( (self,time.time()+self.scanperiod) )
	    log.log( "<directive>Directive.putInQueue(): %s re-queued by scanperiod (%d secs)" % (self,self.scanperiod), 7)


    def safeCheck( self, Config ):
	"""
	This function is called to start a new checking thread for a directive.
	It wraps the directive's self.docheck() in try/except so any un-caught
	exceptions can be captured (and logged) and the thread exited nicely.
	"""

	log.log( "<directive>Directive.safeCheck(): ID '%s', calling self.docheck()" % (self.state.ID), 7 )

	self.last_check_time = time.localtime(time.time())	# note time of last check

	try:
	    self.docheck( Config )
	except:
	    e = sys.exc_info()
	    tb = traceback.format_list( traceback.extract_tb( e[2] ) )
	    log.log( "<directive>Directive.safeCheck(): ID '%s', Uncaught exception: %s, %s, %s" % (self.state.ID, e[0], e[1], tb), 3 )
	    return

	log.log( "<directive>Directive.safeCheck(): ID '%s', self.docheck() returned successfully" % (self.state.ID), 7 )


    def docheck(self, Config):
	"""
	Common Directive method to start executing the directive-specific check
	(or directive function, which may not necessarily "check" something)
	by calling the sub-class method self.getData() to fetch the necessary
	data which is then used as the environment to execute the directive
	rule in.
	
	If the rule evaluates to "true" (not 0 or None) the check is
	considered to have failed and the actions will be called.

	getData() should return a dictionary of variables to be used in the
	rule evaluation environment. The variables will also be added to the
	action variables list to be used in action strings.

	If getData() returns the None object, no check is to be performed in
	this instance, but directive will be re-scheduled.

	If getData() raises directive.DirectiveError, it is considered to have
	hit a critical error and the message will be logged and the directive
	discarded (not re-scheduled).
	"""

	if self.state.checkcount > 0:
	    for i in self.data_collectors.keys():
		self.data_collectors[i].refresh()	# force refresh of data if re-checking

	# self.getData() must be supplied by Directive sub-class.
	# It must fetch the required data (if any) somehow...
	# All fetched data should be returned in a dictionary.
	try:
	    data = self.getData()
	except DirectiveError, err:
	    # Critical directive error, log message and end directive thread.
	    # (Directive will not be re-scheduled.)
    	    log.log( "<directive>Directive.docheck(): directive %s error, %s, not re-scheduled" % (self.ID,err), 4 )
	    return

	# TODO save historical data
	# TODO add historical data to data dict....

	# If data returned as None, do not perform a check but still
	# re-schedule directive.
	if data == None:
	    self.putInQueue( Config.q )	# put self back in the Queue
	    return

	try:
	    #result = eval( self.args.rule, {"__builtins__": {}}, data )
	    result = eval( self.args.rule, {}, data )
	except SyntaxError, details:
	    # Syntax error evaluating rule. Log and end thread without
	    # submitting broken directive back into queue.
    	    log.log( "<directive>Directive.docheck(): SyntaxError evaluating rule '%s'" % (self.args.rule), 4 )
	    return

	# Create action string substitution variables.
	# These are a dictionary of data-collection variables along with any
	# extra variables added specifically by the Directive itself.
	self.Action.varDict = {}
	self.Action.varDict.update(self.defaultVarDict)
	for i in data.keys():
	    self.Action.varDict.update(data)
	self.addVariables()

	if result == 0:
	    self.state.stateok(Config)	# update state info for check passed

	else:
	    self.state.statefail()	# update state info for check failed

    	    log.log( "<directive>Directive.docheck(): directive %s rule failed, calling doAction()" % (self.ID), 7 )
    	    self.doAction(Config)

	self.postAction( data )		# perform any post-action processing

	self.putInQueue( Config.q )	# put self back in the Queue


    def addVariables(self):
	"""
	Add any directive-specific variables to the action variables
	dictionary.

	This function must be overloaded by the Directive sub-class, if
	required.
	By default it does nothing (simply an empty place-holder).
	"""

	pass


    def postAction(self, data):
	"""
	Perform any directive-specific post-action processing.
	It is passed the data dictionary.

	This function must be overloaded by the Directive sub-class, if
	required.
	By default it does nothing (simply an empty place-holder).
	"""

	pass


    def console_str(self):
	"""Return the string that is to be output on console connections."""

	if self.console_output == None:
	    return None

	## Setup variables available to console_output string
	vars = {}

	# add all the action variables
	vars.update(self.Action.varDict)

	# add the current state
	vars['state'] = self.state.status

	# add time of last check
	try:
	    t = self.last_check_time
	    vars['lastchecktime'] = "%04d/%02d/%02d %d:%02d:%02d" % (t[0], t[1], t[2], t[3], t[4], t[5])
	except AttributeError:
	    vars['lastchecktime'] = "<not yet run>"

	# add the lastfailtime and faildetecttime
	if self.state.status == "fail":
	    t = self.state.faildetecttime
	    vars['problemfirstdetect'] = "First detected: %04d/%02d/%02d %d:%02d:%02d" % (t[0], t[1], t[2], t[3], t[4], t[5])
	    t = self.state.lastfailtime
	    vars['problemlastfail'] = "Last detected: %04d/%02d/%02d %d:%02d:%02d" % (t[0], t[1], t[2], t[3], t[4], t[5])
	else:
	    vars['problemfirstdetect'] = ""
	    vars['problemlastfail'] = ""


	# create console string by substituting variables
	cstr = self.console_output % vars
	return cstr



##
## END - directive.py
##
