## 
## File		: directive.py 
## 
## Author       : Rod Telford  <rtelford@codefx.com.au>
##                Chris Miles  <cmiles@codefx.com.au>
## 
## Date		: 971205 
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
import os, string, re, sys, socket, time, threading, traceback
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
	self.checkcount = 0		# count number of checks/re-checks


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

	self.checkcount = self.checkcount + 1

	log.log( "<directive>State.statefail(), ID '%s' status '%s' checkcount %d lastfailtime %s faildetecttime %s"%(self.ID, self.status, self.checkcount, self.lastfailtime, self.faildetecttime), 6 )

	#TODO: Post an EVENT about this failure...
	#      EVENTS are either: new failure/problem detected
	#                     or: repeating failure


    def stateok(self, thisdirective, Config):
	"""Update state info for check succeeding."""

	if self.status != "ok":
	    log.log( "<directive>State.stateok(), State changed to OK.  ID '%s'."%(self.ID), 6 )
	    #TODO: Post an EVENT about problem being resolved
            thisdirective.doOkAct(Config)

	self.status = "ok"

	self.checkcount = 0	# reset check counter

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



class Args:
    """Container for holding directive arguments."""

    def __init__(self):
	"""Nothing to do really."""
	pass



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
	    self.ID = utils.stripquote(toklist[1])	# grab ID if given

	self.basetype = 'Directive'	# the object can know its own basetype
	self.type = toklist[0]		# the directive type of this instance

	self.hastokenparser = 1		# tell parser this object has a separate tokenparser()

	self.Action = action.action()	# create new action instance
	self.Action.varDict = {}	# dictionary of variables used for emails etc

	self.args = Args()		# Container for arguments
	self.args.actionList = []	# each directive will have a list of actions
	self.args.actokList = []	# each directive will have a list of actions

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

	self.requeueTime = None	# specific requeue time can be specified

	self.args.numchecks = 1	# perform only 1 check at a time by default
	self.args.checkwait = 0	# time to wait in between multiple checks
	self.args.template = None	# no template by default


    def __str__( self ):
	#return "<%s Directive %s>" % (self.type, self.ID)
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
				#print 'self.args.%s = tpldirective.args.%s' % (t,t)
				#print 'self.args.%s'%t,
				#exec( "print self.args.%s" % (t) )

	    elif t == 'act2ok':	# special handler for actions
                self.args.actokList = self.parseAction( tokdict[t] )

	    elif t == 'action':	# special handler for actions
		self.args.actionList = self.parseAction( tokdict[t] )

	    else:
		try:
		    exec( "self.args.%s = tokdict[t]" % (t) )
		except:
		    raise ParseFailure, "Error parsing argument '%s'" % (t)

	# test for actionList which is always required
	# (except if directive a template only)
	try:
	    self.args.actionList
	except AttributeError:
	    if self.args.template != 'self':
		raise ParseFailure, "Action not specified"


	try:
	    self.args.scanperiod
	    # convert scanperiod to integer seconds if not already
	    if type(self.args.scanperiod) != type(1):
		self.args.scanperiod = utils.val2secs( self.args.scanperiod )
	    self.scanperiod = self.args.scanperiod	# set the scanperiod
	except:
	    pass

	# test numchecks argument is integer and >= 0
	if type(self.args.numchecks) != type(1):
	    try:
		self.args.numchecks = int(self.args.numchecks)
	    except ValueError:
		raise ParseFailure, "numchecks argument is not integer '%s'"%(self.args.numchecks)
	if self.args.numchecks < 0:
	    raise ParseFailure, "numchecks argument must be > 0 '%s'"%(self.args.numchecks)

	# convert scanperiod to integer seconds if not already
	try:
	    if type(self.args.checkwait) != type(1):
		self.args.checkwait = utils.val2secs( self.args.checkwait )
	except:
	    raise ParseFailure, "checkwait argument has incorrect value '%s'"%(self.args.checkwait)

	if self.args.template == 'self':
	    # jump out of token parsing if this is a template only
	    raise 'Template'



    def doAction(self, Config):
    	"""Perform actions for a directive."""

	if self.state.checkcount < self.args.numchecks:
	    # need to wait before re-checking
	    # when put back in queue only wait checkwait seconds
	    self.requeueTime = time.time()+self.args.checkwait
	    log.log( "<directive>doAction(), scheduling for recheck in %d seconds" % self.args.checkwait, 7 )
	    return
	else:
	    self.state.checkcount = 0	# performing action so reset counter
  

	# record action information
	self.lastactiontime = time.localtime(time.time())


	actionList = self.args.actionList

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
		try:
		    ret = eval( 'self.Action.'+a )
		except:
		    e = sys.exc_info()
		    tb = traceback.format_list( traceback.extract_tb( e[2] ) )
		    log.log( "<directive>doAction(), Error evaluating self.Action.%s: %s, %s, %s" % (a, e[0], e[1], tb), 2 )
		    return
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
		    log.log( "<directive>doAction(), Error in directive.py line 371: Config.NDict[notif].levels[level], level=%s" % level, 1 )
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
			    try:
				ret = eval( 'self.Action.'+aa )
			    except:
				e = sys.exc_info()
				tb = traceback.format_list( traceback.extract_tb( e[2] ) )
				log.log( "<directive>doAction(), Error evaluating self.Action.%s: %s, %s, %s" % (aa, e[0], e[1], tb), 2 )
				return
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

    def doOkAct(self, Config):
    	"""Perform actions for a directive."""

        #print ">>>> ", self
        #print ">>>> ", self.args
	actionList = self.args.actokList
        #print ">>>> actionList: ", self.args.actokList
        #print ">>>> actionList: ", actionList

	# Set the 'action' variables with the expanded action list
	self.Action.varDict['act'] = 'The following actions were attempted:\n'
	self.Action.varDict['actnm'] = 'The following (non-email) actions were attempted:\n'

	self.Action.state = self.state
	self.Action.aliasDict = Config.aliasDict

	# Perform each action
	ret = None
	self.Action.actionReports = {}		# dict of actions and their return status
	for a in actionList:
	    sre = re.compile( "([A-Za-z0-9_]+)\(([A-Za-z0-9_.]+),?([0-9]?)\)" )
	    inx = sre.search( a )

            notif = inx.group(1)
            msg = inx.group(2)
            level = inx.group(3)
            if level == None or level == '':
                level = '0'

	    # print ">>>> notif:",notif
            # print ">>>> msg:",msg
            # print ">>>> level:",level

            try:
                afunc = Config.NDict[notif].levels[level]
            except KeyError:
                log.log( "<directive>doAction(), Error in directive.py line 371: Config.NDict[notif].levels[level], level=%s" % level, 1 )
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
		    # Call the action
		    log.log( "<directive>Directive, calling action '%s'" % (aa), 9 )
		    try:
		        ret = eval( 'self.Action.'+aa )
		    except:
		        e = sys.exc_info()
			tb = traceback.format_list( traceback.extract_tb( e[2] ) )
		        log.log( "<directive>doAction(), Error evaluating self.Action.%s: %s, %s, %s" % (aa, e[0], e[1], tb), 2 )
			return

		    self.Action.actionReports[aa] = ret
		    if ret == None:
			self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s\n' % aa

	            elif ret == 0:
			self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s - Successful\n' % aa
		    else:
			self.Action.varDict['actnm'] = self.Action.varDict['actnm'] + '    %s - FAILED, return code %d\n' % (aa, ret)


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


    def putInQueue( self, q ):
	"""Put this directive back into the scheduler queue."""

	if self.requeueTime:
	    # a specific requeueTime has been requested
	    q.put( (self,self.requeueTime) )
	    self.requeueTime = None
	    log.log( "<directive>putInQueue(), %s re-queued by requeueTime" % (self), 8)

	else:
	    # reschedule in scanperiod seconds
	    q.put( (self,time.time()+self.scanperiod) )
	    log.log( "<directive>putInQueue(), %s re-queued by scanperiod (%d secs)" % (self,self.scanperiod), 8)


    def safeCheck( self, Config ):
	"""This function is called to start a new checking thread for a directive.
	   It wraps the directive's self.docheck() in try/except so any un-caught
	   exceptions can be captured and the thread exited nicely.
	"""

	log.log( "<Directive>safeCheck(), ID '%s', calling self.docheck()" % (self.state.ID), 9 )

	try:
	    self.docheck( Config )
	except:
	    e = sys.exc_info()
	    tb = traceback.format_list( traceback.extract_tb( e[2] ) )
	    log.log( "<Directive>safeCheck(), ID '%s', Uncaught exception: %s, %s, %s" % (self.state.ID, e[0], e[1], tb), 3 )
	    return

	log.log( "<Directive>safeCheck(), ID '%s', self.docheck() returned successfully" % (self.state.ID), 9 )


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
	    self.args.fs
	except AttributeError:
	    raise ParseFailure, "Filesystem not specified"
	try:
	    self.args.rule
	except AttributeError:
	    raise ParseFailure, "Rule not specified"

	# Set any FS-specific variables
	#  fsf = fs
	#  fsrule = rule
	self.Action.varDict['fsf'] = self.args.fs
	self.Action.varDict['fsrule'] = self.args.rule

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.FS.%s' % (log.hostname,self.args.fs)
	self.state.ID = self.ID

	log.log( "<Directive>FS, ID '%s' fs '%s' rule '%s' action '%s'" % (self.state.ID, self.args.fs, self.args.rule, self.args.actionList), 8 )


    def docheck(self, Config):
	log.log( "<directive>FS(), docheck(), fs '%s', rule '%s'" % (self.args.fs,self.args.rule), 7 )

	if self.state.checkcount > 0:
	    dlist.refresh()	# force refresh of list if re-checking

	df = dlist[self.args.fs]
	if df == None:
	    log.log( "<directive>FS(), Error, no df with fs '%s'" % (self.args.fs), 2 )
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

	result = eval( self.args.rule, dfenv )

	# assign variables
	self.Action.varDict['fsused'] = df.getUsed()
	self.Action.varDict['fsavail'] = df.getAvail()
	self.Action.varDict['fscapac'] = df.getPctused()
	self.Action.varDict['fssize'] = df.getSize()
	self.Action.varDict['fsdf'] = "%s%s" % (dlist.dfheader,df)

	if result == 0:
	    self.state.stateok(self, Config)	# update state info for check passed

	else:
	    self.state.statefail()	# update state info for check failed

	    # get '%fsls' details for this filesystem
    	    #fsls = os.popen("ls -l %s" % (df.mountpt), 'r')
    	    fsls = utils.safe_popen("ls -l %s" % (df.mountpt), 'r')
 
	    fsls_output = ""
    	    for line in fsls.readlines():
		fsls_output = fsls_output + line
	    
	    #fsls.close()
	    utils.safe_pclose( fsls )

	    self.Action.varDict['fsls'] = fsls_output
	
    	    log.log( "<directive>FS(), rule '%s' was false, calling doAction()" % (self.args.rule), 6 )
    	    self.doAction(Config)

	self.putInQueue( Config.q )	# put self back in the Queue


    # Parse the rule line and replace/remove certain characters
    def parseRule(self):
	parsed = ""

	skipnext = 0			# flag to skip next character/s

	for i in range(len(self.args.rule)):
	    if skipnext > 0:
		skipnext = skipnext - 1
		continue

	    c = self.args.rule[i]

	    if c == '%':	# throw away '%'s - don't need em
		continue
	    elif c == '|':	# replace '|'s with 'or'
		parsed = parsed + ' or '
		continue
	    elif c == '&':	# replace '&'s with 'and'
		parsed = parsed + ' and '
		continue
	    elif i == len(self.args.rule)-1:	# break out of 'switch' if c is last character
		pass
	    elif ( string.lower(c) + string.lower(self.args.rule[i+1]) ) == 'mb':
		parsed = parsed + '000'
		skipnext = 1
		continue
	    elif ( string.lower(c) + string.lower(self.args.rule[i+1]) ) == 'gb':
		parsed = parsed + '000000'
		skipnext = 1
		continue
	    
	    parsed = parsed + c

	self.args.rule = parsed



class PID(Directive):
    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )

	self.ruleDict = { 'EX' : None,
		          'PR' : None }


    def tokenparser(self, toklist, toktypes, indent):
	apply( Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.pid
	except AttributeError:
	    raise ParseFailure, "Pid not specified"
	try:
	    self.args.rule
	except AttributeError:
	    raise ParseFailure, "Rule not specified"

	# Expect first token to be rule - one of self.ruleDict
	if self.args.rule not in self.ruleDict.keys():
	    raise ParseFailure, "PID found unexpected rule '%s'" % self.args.rule

	# Set any PID-specific variables
	#  %pidf = the PID-file
	self.Action.varDict['pidf'] = self.args.pid

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.PID.%s.%s' % (log.hostname,self.args.pid,self.args.rule)
	self.state.ID = self.ID

	log.log( "<Directive>PID, ID '%s' pid '%s' rule '%s' action '%s'" % (self.state.ID, self.args.pid, self.args.rule, self.args.actionList), 8 )


    def docheck(self, Config):
	log.log( "<directive>PID(), docheck(), pid '%s', rule '%s'" % (self.args.pid,self.args.rule), 7 )

	if self.args.rule == "EX":
	    # Check if pidfile exists
	    try:
		pidfile = open( self.args.pid, 'r' )
	    except IOError:
		# pidfile not found
		log.log( "<directive>PID(), EX, pidfile '%s' not found" % (self.args.pid), 6 )
		self.state.statefail()	# update state info for check failed
		self.doAction(Config)
	    else:
		log.log( "<directive>PID(), EX, pidfile '%s' found" % (self.args.pid), 8 )
		self.state.stateok(self, Config)		# update state info for check passed
		pidfile.close()

	elif self.args.rule == "PR":
	    # check if process pid found in pidfile is running - no alert if pidfile not found
	    try:
		pidfile = open( self.args.pid, 'r' )
	    except IOError:
		# pidfile not found
		log.log( "<directive>PID(), PR, pidfile '%s' not found" % (self.args.pid), 6 )
	    else:
		log.log( "<directive>PID(), PR, pidfile '%s' found" % (self.args.pid), 8 )
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
		    # there is no process with pid == pid
		    log.log( "<directive>PID(), PR, pid %s not in process list" % (pid), 6 )
		    self.state.statefail()	# update state info for check failed
		    self.doAction(Config)
		else:
		    log.log( "<directive>PID(), PR, pid %s is in process list" % (pid), 7 )
		    self.state.stateok(self, Config)		# update state info for check passed


	else:
	    # invalid rule
	    log.log( "<directive>PID, Error, '%s' is not a valid PID rule, config line follows,\n%s\n" % (self.args.rule,self.raw), 2 )
	    return

	self.putInQueue( Config.q )	# put self back in the Queue


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
	    self.args.procname
	except AttributeError:
	    raise ParseFailure, "Process name not specified"
	try:
	    self.args.rule
	except AttributeError:
	    raise ParseFailure, "Rule name not specified"

	# Expect first token to be rule
	if self.args.rule in self.ruleDict.keys():
	    # - either one of self.ruleDict
	    self.args.rule = self.ruleDict[self.args.rule]       # Rule is a function
	elif type(self.args.rule) == type('STRING'):
	    # - or a string containing a special check
	    self.checkstring = utils.stripquote(self.args.rule)
	    self.args.rule = self.ruleDict['check']
	else:
	    raise ParseFailure, "PROC found unexpected rule '%s'" % self.args.rule

	# Set any PROC-specific variables
	#  %procp = the process name
	self.Action.varDict['procp'] = self.args.procname
	#  %procpid = pid of process (ie: if found running for R rule)
	self.Action.varDict['procpid'] = '[pid not yet defined]'

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.PROC.%s' % (log.hostname,self.args.procname)
	self.state.ID = self.ID

	log.log( "<Directive>PROC, ID '%s' procname '%s' rule '%s' action '%s'" % (self.state.ID, self.args.procname, self.args.rule, self.args.actionList), 8 )


    def docheck(self, Config):
	"""Perform specified check."""

	log.log( "<directive>PROC(), docheck(), procname '%s', rule '%s'" % (self.args.procname,self.args.rule), 7 )
	self.args.rule(Config)

	self.putInQueue( Config.q )	# put self back in the Queue


    def NR(self,Config):
	"""Call action if process is found to be NOT running."""

	if self.state.checkcount > 0:
	    plist.refresh()	# force refresh of list if re-checking

	if plist.procExists( self.args.procname ) == 0:
	    log.log( "<directive>NR(PROC) procname not running, '%s'" % (self.args.procname), 6 )
	    self.state.statefail()	# update state info for check failed
	    self.doAction(Config)
	    return

	self.state.stateok(self, Config)	# update state info for check passed


    def R(self,Config):
	"""Call action if process is found to BE running."""

	if plist.procExists( self.procname ) > 0:
	    log.log( "<directive>R(PROC) procname is running, '%s'" % (self.args.procname), 6 )
	    # Set %procpid variable.
	    self.Action.varDict['procpid'] = plist[self.args.procname].pid
	    self.state.statefail()	# update state info for check failed
	    self.doAction(Config)

	else:
	    self.state.stateok(self, Config)	# update state info for check passed


    def check(self,Config):
	"""Executes a check string supplied by user."""

	for p in plist.getList():
	    if p.procname == self.args.procname:
		try:
		    procenv = p.procinfo()		# get dictionary of process details
		except AttributeError:
		    log.log( "<directive>PROC.check() warning, no process '%s'." % (self.args.procname), 8 )
		    return

		result = eval( self.checkstring, procenv )

		# build varDict from procenv
		for i in procenv.keys():
		    self.Action.varDict['proc%s'%(i)] = procenv[i]

		if result != 0:
		    self.state.statefail()	# update state info for check failed
		    self.doAction(Config)

		else:
		    self.state.stateok(self, Config)	# update state info for check passed



class SP(Directive):
    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	apply( Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.port
	except AttributeError:
	    raise ParseFailure, "Port not specified"
	try:
	    self.args.protocol
	except AttributeError:
	    raise ParseFailure, "Protocol not specified"
	try:
	    self.args.bindaddr
	except AttributeError:
	    raise ParseFailure, "Bind address not specified"

	self.port_n = self.args.port		# remember port name

	# lets try resolving this service port to a number
	try:
	    self.port = socket.getservbyname(self.port_n, self.args.protocol)
	except socket.error:
	    self.port = self.port_n

	self.Action.varDict['spport'] = self.port_n
	self.Action.varDict['spaddr'] = self.args.bindaddr
	self.Action.varDict['spprot'] = self.args.protocol

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.SP.%s/%s.%s' % (log.hostname,self.args.protocol,self.port_n,self.args.bindaddr)
	self.state.ID = self.ID

	log.log( "<Directive>SP, ID '%s' protocol '%s', port '%s', bind addr '%s', action '%s'" % (self.state.ID, self.args.protocol, self.port, self.args.bindaddr, self.args.actionList), 8 )


    def docheck(self, Config):
	log.log( "<directive>SP(), docheck(), protocol '%s', port '%s', addr '%s'" % (self.args.protocol,self.port_n,self.args.bindaddr), 7 )

	if self.state.checkcount > 0:
	    nlist.refresh()	# force refresh of list if re-checking

	ret = nlist.portExists(self.args.protocol, self.port, self.args.bindaddr) != None
	if ret != 0:
	    log.log( "<directive>SP(), port %s/%s listener found bound to %s" % (self.args.protocol , self.port_n, self.args.bindaddr), 8 )
	    self.state.stateok(self, Config)	# update state info for check passed
	else:
	    log.log( "<directive>SP(), port %s/%s no listener found bound to %s" % (self.args.protocol , self.port_n, self.args.bindaddr), 6 )
	    self.state.statefail()	# update state info for check failed
	    self.doAction(Config)

	self.putInQueue( Config.q )	# put self back in the Queue


COMsemaphore = threading.Semaphore()

class COM(Directive):
    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	apply( Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.cmd
	except AttributeError:
	    raise ParseFailure, "Command (cmd) not specified"
	try:
	    self.args.rule
	except AttributeError:
	    raise ParseFailure, "Rule not specified"

	# Set any COM-specific variables
	#  %com = the command
	#  %rule = the rule
	self.Action.varDict['COMcmd'] = self.args.cmd
	self.Action.varDict['COMrule'] = self.args.rule

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.COM.%s.%s' % (log.hostname,self.args.cmd,self.args.rule)
	self.state.ID = self.ID

	log.log( "<directive>COM, ID '%s' cmd '%s' rule '%s' action '%s'" % (self.state.ID, self.args.cmd, self.args.rule, self.args.actionList), 8 )


    def docheck(self, Config):
	log.log( "<directive>COM.docheck(), cmd '%s', rule '%s'" % (self.args.cmd,self.args.rule), 7 )
	log.log( "<directive>COM.docheck(), acquiring semaphore lock for cmd '%s'" % (self.args.cmd), 8 )
	COMsemaphore.acquire()
	log.log( "<directive>COM.docheck(), semaphore acquired for cmd '%s'" % (self.args.cmd), 8 )
	tmpprefix = "/var/tmp/com%d" % os.getpid()
	cmd = "{ %s ; } >%s.out 2>%s.err" % (self.args.cmd, tmpprefix, tmpprefix )
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
	log.log( "<directive>COM.docheck(), released semaphore lock for cmd '%s'" % (self.args.cmd), 8 )

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
	    result = eval( self.args.rule, comenv )
	except:
	    log.log( "<directive>COM.docheck() : an error occured with rule '%s' exception type: '%s' exception value: '%s' - env was: %s"%(self.args.rule,sys.exc_type,sys.exc_value,comenv), 3 )
	    return

        log.log( "<directive>COM.docheck(), eval:'%s', result='%s'" % (self.args.rule,result), 9 )
	if result != 0:
	    self.state.statefail()	# update state info for check failed
	    self.doAction(Config)
	else:
	    self.state.stateok(self, Config)	# update state info for check passed

	self.putInQueue( Config.q )	# put self back in the Queue


class PORT(Directive):
    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	apply( Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.host
	except AttributeError:
	    raise ParseFailure, "Host not specified"
	try:
	    self.args.port
	except AttributeError:
	    raise ParseFailure, "Port not specified"
	try:
	    self.args.port = int(self.args.port)
	except ValueError:
	    raise ParseFailure, "Port is not an integer: %s" % (self.args.port)
	try:
	    self.args.send
	except AttributeError:
	    raise ParseFailure, "Send string not specified"
	try:
	    self.args.expect
	except AttributeError:
	    raise ParseFailure, "Expect string not specified"

	# Set any PORT-specific variables
	#  %porthost = the host
	#  %portport = the port
	#  %portsend = the send string
	#  %portexpect = the expect string
	#  %portrecv = the string received from port connection (at check time)
	self.Action.varDict['porthost'] = self.args.host
	self.Action.varDict['portport'] = self.args.port
	self.Action.varDict['portsend'] = self.args.send
	self.Action.varDict['portexpect'] = self.args.expect
	self.Action.varDict['portrecv'] = ''

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.PORT.%s.%d' % (log.hostname,self.args.host,self.args.port)
	self.state.ID = self.ID

	log.log( "<Directive>PORT, ID '%s' host '%s' port '%d' send '%s' expect '%s'" % (self.state.ID, self.args.host, self.args.port, self.args.send, self.args.expect), 8 )


    def docheck(self, Config):
	log.log( "<directive>PORT.docheck(), host '%s', port '%d', send '%s', expect '%s'" % (self.args.host,self.args.port,self.args.send,self.args.expect), 7 )

	self.Action.varDict['portrecv'] = ''

        if not self.isalive(host=self.args.host,port=self.args.port,send=self.args.send,expect=self.args.expect):
	    log.log( "<directive>PORT.docheck(), isalive() failed.", 7 )
	    self.state.statefail()	# update state info for check failed
            self.doAction(Config)
	else:
	    self.state.stateok(self, Config)	# update state info for check passed

	self.putInQueue( Config.q )	# put self back in the Queue


    def isalive(self,host,port,send="",expect=""):
        """ Connects to host:port, sends send,
            receives input, compares it to expect
            and returns TRUE or FALSE accordingly """
        #print "Trying to connect to %s:%d send:'%s' exp:'%s'" % (host,port,send,expect)   #DEBUG
        try:
	    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            try:
		s.connect( (host,port) )

                if expect == "":
                    s.close()
                    return 1    # port connection ok
                else:
                    exec( "send='%s'" % send )
		    sendlist = string.split(send, '\n')		# split each line
		    # send each line - only compare last output received
		    for line in sendlist:
			log.log( "<directive>PORT.isalive(): sending '%s'" % (line), 8 )
			s.send(line+'\n')
			data=''
			data=s.recv(1024)
			log.log( "<directive>PORT.isalive(): received '%s'" % (data), 8 )

                    self.Action.varDict['portrecv'] = data

                    if data==expect or re.search( '.*' + expect + '.*', data, ) != None:
                        s.close()
                        return 1
                    else:
                        return 0
            except socket.error:
		e = sys.exc_info()
		if e[1][0] == 146:		# Connection Refused
		    log.log( "<Directive>PORT.isalive(), ID '%s', Connection refused" % (self.state.ID), 5 )
		    return 0
		else:
		    s.close()
		    tb = traceback.format_list( traceback.extract_tb( e[2] ) )
		    log.log( "<Directive>PORT.isalive(), ID '%s', Uncaught: %s, %s, %s" % (self.state.ID, e[0], e[1], tb), 3 )
        except:
	    e = sys.exc_info()
	    tb = traceback.format_list( traceback.extract_tb( e[2] ) )
	    log.log( "<Directive>PORT.isalive(), ID '%s', Uncaught exception: %s, %s, %s" % (self.state.ID, e[0], e[1], tb), 3 )

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
	    self.args.name
	except AttributeError:
	    raise ParseFailure, "Interface name not specified"
	try:
	    self.args.rule
	except AttributeError:
	    raise ParseFailure, "Rule not specified"

	self.checkstring = ""

	# Expect first token to be rule
        if self.args.rule in self.ruleDict.keys():
            # - either one of self.ruleDict
            self.rule = self.ruleDict[self.args.rule]       # Set the rule
        elif type(self.args.rule) == type('STRING'):
            # - or a string containing a special check
            self.checkstring = utils.stripquote(self.args.rule)
            self.rule = self.ruleDict['check']
        else:
            raise ParseFailure, "IF found unexpected rule '%s'" % self.rule

	self.Action.varDict['ifname'] = self.args.name
	self.Action.varDict['ifrule'] = self.rule
	self.Action.varDict['ifcheckstring'] = self.checkstring

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.IF.%s.%s' % (log.hostname,self.args.name,self.rule)
	self.state.ID = self.ID

	log.log( "<Directive>IF, ID '%s' name '%s', rule '%s', checkstring '%s', action '%s'" % (self.state.ID, self.args.name, self.rule, self.checkstring, self.args.actionList), 8 )


    def docheck(self, Config):
	"""Perform the check."""

	log.log( "<directive>IF(), docheck(), name '%s', check '%s', checkstring '%s'" % (self.args.name,self.check,self.checkstring), 7 )

	self.rule(Config)

	self.putInQueue( Config.q )	# put self back in the Queue


    def NE(self, Config):
	"""Check that an interface currently does not exist."""

	if self.state.checkcount > 0:
	    nlist.refresh()	# force refresh of list if re-checking

	if nlist.getInterface(self.args.name) == None:
	    # interface doesn't exist
	    log.log( "<directive>IF.NE() interface '%s' does not exist" % (self.args.name), 6 )
	    self.state.statefail()	# update state info for check failed
	    self.doAction(Config)
	else:
	    self.state.stateok(self, Config)	# update state info for check passed


    def EX(self, Config):
	"""Check that an interface currently exists."""

	if self.state.checkcount > 0:
	    nlist.refresh()	# force refresh of list if re-checking

	if nlist.getInterface(self.args.name) != None:
	    # interface exists
	    log.log( "<directive>IF.EX() interface '%s' exists" % (self.args.name), 6 )
	    self.state.statefail()	# update state info for check failed
	    self.doAction(Config)
	else:
	    self.state.stateok(self, Config)	# update state info for check passed


    def check(self, Config):
	"""Execute a check supplied by the user as a string."""

	if self.state.checkcount > 0:
	    nlist.refresh()	# force refresh of list if re-checking

	i = nlist.getInterface(self.args.name)
	if i == None:
	    log.log( "<directive>IF.check() warning, no interface '%s'." % (self.args.name), 7 )
	    return		# ignore if this interface doesn't exist

	ifenv = i.ifinfo()	# get dictionary of interface details

	result = eval( self.checkstring, ifenv )

	# build varDict from ifenv
	for i in ifenv.keys():
	    self.Action.varDict['if%s'%(i)] = ifenv[i]

	if result != 0:
	    self.state.statefail()	# update state info for check failed
	    self.doAction(Config)
	else:
	    self.state.stateok(self, Config)	# update state info for check passed


class NET(Directive):
    """Network Statistics directive."""

    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	"""Parse rest of rule (after ':')."""
	apply( Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.rule
	except AttributeError:
	    raise ParseFailure, "Rule not specified"

	# Rule should be a string
        if type(self.args.rule) != type('STRING'):
	    raise ParseFailure, "NET parse error, rule is not string."

	self.Action.varDict['netrule'] = self.args.rule

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.NET.%s' % (log.hostname,self.args.rule)
	self.state.ID = self.ID

	log.log( "<Directive>NET, ID '%s' rule '%s', action '%s'" % (self.state.ID, self.args.rule, self.args.actionList), 8 )


    def docheck(self, Config):
	"""Perform the check."""

	log.log( "<directive>NET(), docheck(), rule '%s'" % (self.args.rule), 7 )

	if self.state.checkcount > 0:
	    nlist.refresh()	# force refresh of list if re-checking

	netenv = nlist.statstable.getHash()	# get dictionary of network stats

	result = eval( self.args.rule, netenv )

	# build varDict from netenv
	for i in netenv.keys():
	    self.Action.varDict['net%s'%(i)] = netenv[i]

	if result != 0:
	    self.state.statefail()	# update state info for check failed
	    self.doAction(Config)
	else:
	    self.state.stateok(self, Config)	# update state info for check passed

	self.putInQueue( Config.q )	# put self back in the Queue



class SYS(Directive):
    """System Statistics directive."""

    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )



    def tokenparser(self, toklist, toktypes, indent):
	"""Parse rest of rule (after ':')."""
	apply( Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.rule
	except AttributeError:
	    raise ParseFailure, "Rule not specified"

	# Rule should be a string
        if type(self.args.rule) != type('STRING'):
	    raise ParseFailure, "SYS parse error, rule is not string."

	self.Action.varDict['sysrule'] = self.args.rule

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.SYS.%s' % (log.hostname,self.args.rule)
	self.state.ID = self.ID

	log.log( "<Directive>SYS, ID '%s' rule '%s' action '%s'" % (self.state.ID, self.args.rule, self.args.actionList), 8 )


    def docheck(self, Config):
	"""Perform the check."""

	log.log( "<directive>SYS(), docheck(), rule '%s'" % (self.args.rule), 7 )

	if self.state.checkcount > 0:
	    system.refresh()	# force refresh of data if re-checking

	sysenv = system.getHash()		# get dictionary of system stats

	try:
	    result = eval( self.args.rule, sysenv )
	except SyntaxError:
	    log.log( "<directive>SYS(), docheck(), SyntaxError evaluating rule '%s'" % (self.args.rule), 3 )
	    return

	# build varDict from sysenv
	for i in sysenv.keys():
	    self.Action.varDict['sys%s'%(i)] = sysenv[i]

	if result != 0:
	    self.state.statefail()	# update state info for check failed
	    self.doAction(Config)
	else:
	    self.state.stateok(self, Config)	# update state info for check passed

	self.putInQueue( Config.q )	# put self back in the Queue



class STORE(Directive):
    """Store selected host data."""

    def __init__(self, toklist):
	apply( Directive.__init__, (self, toklist) )



    def tokenparser(self, toklist, toktypes, indent):
	"""Parse rest of rule (after ':')."""
	apply( Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.rule
	except AttributeError:
	    raise ParseFailure, "Rule not specified"

	# Rule should be a string
        if type(self.args.rule) != type('STRING'):
	    raise ParseFailure, "STORE parse error, rule is not string."

	self.Action.varDict['storerule'] = self.args.rule

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.STORE.%s' % (log.hostname,self.args.rule)
	self.state.ID = self.ID

	log.log( "<Directive>STORE, ID '%s' rule '%s' action '%s'" % (self.state.ID, self.args.rule, self.args.actionList), 8 )


    def docheck(self, Config):
	"""Perform the check.  In this case, the 'check' is automatically true (we always want to store)."""

	log.log( "<directive>STORE(), docheck(), rule '%s'" % (self.args.rule), 7 )

	datahash = None

	# Get data as directed by rule.
	# * this is hard-coded to a few different 'rules' atm.  This should be
	# cleaned up later to handle any type of rule (TODO)

	if self.args.rule[:6] == 'system':
	    datahash = system.getHash()			# get dictionary of system stats
	elif self.args.rule[:7] == 'netstat':
	    #datahash = nlist.statstable.getHash()		# get dictionary of network stats
	    datahash = nlist.getNetworkStats()			# get dictionary of network stats
	elif self.args.rule[:4] == 'proc':
	    datahash = plist.allprocs()				# get dictionary of process details
	elif self.args.rule[:2] == 'if':
	    datahash = nlist.getAllInterfaces()			# get dictionary of interface details
	elif self.args.rule[:6] == 'iostat':
	    datahash = iostat.getHash()			# get dictionary of iostat data

	if datahash == None:
	    log.log( "<directive>STORE(), docheck(), rule '%s' is invalid." % (self.args.rule), 3 )
	    return

	# Create a new hash with 'data.' prepended to each key (as required by estored).
# Don't do this anymore.
#	storeenv = {}
#	for i in datahash.keys():
#	    storeenv['data.'+i] = datahash[i]

	self.Action.storedict = datahash

	self.state.statefail()	# state should be fail before doAction() called
	self.doAction(Config)
	self.state.stateok(self, Config)	# reset state

	self.putInQueue( Config.q )	# put self back in the Queue



##
## END - directive.py
##
