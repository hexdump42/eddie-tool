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

    def keylist(self):
	return self.hash.keys()
    
    def delete(self, directive):
	del self.hash[directive]

##
## The base directive class.  Derive all directives from this base class.
##
class Directive:
    def __init__(self, *arg):
	self.raw = arg[0]			# the raw line as read from config file
	self.basetype = 'Directive'		# the object can know its own basetype
	self.type = string.split(self.raw)[0]	# the directive type of this instance
	self.regexp = ''			# the regexp to split the raw line into fields
	self.action = ''			# each directive will have an action
	self.varDict = {}			# dictionary of variables used for emails etc

	# Set up informational variables - these are common to all Directives
	#  %h = hostname
	#    TODO: Is there a simpler Python-way of getting hostname ??
	#    TODO: Get the hostname at program startup, not here...
	tmp = os.popen('uname -n', 'r')
	hostname = tmp.readline()
	self.varDict['h'] = hostname[:-1]	# strip \n off end
	tmp.close()

	#  %sys = command from a system() action
	#     TODO
	self.varDict['sys'] = '[sys not yet defined]'

	#  %act = show list of actions taken preceded by "The following actions
	#         were taken:" if any were taken
	self.varDict['act'] = '[act not yet defined]'

	#  %actnm = show list of actions taken (excluding email()'s) preceded by
	#         "The following actions were taken:" if any were taken
	self.varDict['actnm'] = '[actnm not yet defined]'


    # Parses raw line with directive-defined regexp and returns tuple of
    # regex groups.
    def parseRaw(self):
	sre = regex.compile( self.regexp )
	inx = sre.search( self.raw )
	if inx == -1:
	    # probably make an exception here.....
	    raise ParseFailure, "Error while parsing line: "+self.raw
	fieldlist = ()
	i=1
	while( sre.group(i) != None ):
	    fieldlist = fieldlist + (sre.group(i),)
	    i = i + 1
	return fieldlist

    # Perform actions for a directive
    def doAction(self):
	# split comma-seperated list of actions
	actionList = utils.trickySplit( self.action, ',' )

	# Replace Action definitions with the corresponding actions
	actionList = definition.parseList( actionList, ADict )

	# Put quotes around arguments so we can use eval()
	actionList = utils.quoteArgs( actionList )

	# Set the 'action' variables with the expanded action list
	self.varDict['act'] = 'The following actions are being taken:\n'
	self.varDict['actnm'] = 'The following (non-email) actions are being taken:\n'
	for a in actionList:
	    self.varDict['act'] = self.varDict['act'] + '\t' + a + '\n'
	    if a[:5] != 'email':
		self.varDict['actnm'] = self.varDict['actnm'] + '\t' + a + '\n'

	# Setup current varDict in action module
	action.varDict = self.varDict

	# Perform each action
	for a in actionList:
	    try:
		# Call the action
		log.log( "<directive>Directive, calling action '%s'" % (a), 8 )
		eval( 'action.'+a )
	    except AttributeError:
		# Not an action function ... error...
		log.log( "<directive>Directive, Error, 'action.%s' is not a defined action, config line follows,\n%s\n" % (a,self.raw), 2 )



##
## RULE-BASED COMMANDS
##
class FS(Directive):
    def __init__(self, *arg):
	apply( Directive.__init__, (self,) + arg )
	#self.regexp = 'FS[\t \n]+\([a-zA-Z0-9_/\.-]+\)[\t \n]+\([a-zA-Z0-9_><=&\|%^!-]+|[\"\'][a-zA-Z0-9_><=&\|%^!\t -]+[\"\']\)[\t \n]+\(.*\)'
	self.regexp = 'FS[\t \n]+\([a-zA-Z0-9_/\.-]+\)[\t \n]+\([a-zA-Z0-9_$><=&\|%^!-]+\|["\'][a-zA-Z0-9_$><=&\|%^! \t-]+["\']\)[\t \n]+\(.*\)'
	fields = self.parseRaw()
	self.filesystem = fields[0]		# the filesystyem to check
	self.rule = utils.stripquote(fields[1])	# the rules
	self.action = fields[2]			# the action
	print "<FS> filesystem: '%s' rule: '%s' action: '%s'" % (self.filesystem, self.rule, self.action)

	# Set any FS-specific variables
	#  fsf = filesystem
	#  fsrule = rule
	self.varDict['fsf'] = self.filesystem
	self.varDict['fsrule'] = self.rule

    def docheck(self):
	print "FS directive doing checking......"
	df = dlist[self.filesystem]
	if df == None:
	    log.log( "<directive>FS(), Error, no df with filesystem '%s'" % (self.filesystem), 2 )
	    return

	print "df = ",df

	dfenv = {}			# environment for df rules execution
	dfenv['used'] = string.atoi(df.getUsed())
	dfenv['avail'] = string.atoi(df.getAvail())
	dfenv['capac'] = string.atoi(df.getPctused())
	# TODO : calculate deltas from history...
	dfenv['useddelta'] = 0
	dfenv['availdelta'] = 0
	dfenv['capacdelta'] = 0

	self.parseRule()

	print "used='%d', avail='%d', capac='%d'" % (dfenv['used'],dfenv['avail'],dfenv['capac'])

	result = eval( self.rule, dfenv )

	print "DEBUG FS: result of eval( %s ) = %d" % ( self.rule, result )

	if result != 0:
	    # assign variables
	    self.varDict['fsused'] = df.getUsed()
	    self.varDict['fsavail'] = df.getAvail()
	    self.varDict['fscapac'] = df.getPctused()
	    self.varDict['fssize'] = df.getSize()
	    self.varDict['fsdf'] = "%s" % df

    	    log.log( "<directive>FS(), rule '%s' was false, calling doAction()" % (self.rule), 6 )
    	    self.doAction()

    # Parse the rule line and replace/remove certain characters
    def parseRule(self):
	parsed = ""

	print "DEBUG: self.rule = '%s'" % self.rule

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

	print "DEBUG: parsed   = '%s'" % parsed

	self.rule = parsed



class PID(Directive):
    def __init__(self, *arg):
	apply( Directive.__init__, (self,) + arg )
	self.regexp = 'PID[\t \n]+\([a-zA-Z0-9_/\.]+\)[\t \n]+\([a-zA-Z0-9_]+\)[\t \n]+\(.*\)'
	fields = self.parseRaw()
	self.pidfile = fields[0]		# the pid file to check for
	self.rule = fields[1]			# the rule (EX or PR)
	self.action = fields[2]			# the action
	#print "<PID> pidfile: '%s' rule: '%s' action: '%s'" % (self.pidfile, self.rule, self.action)

	# Set any PID-specific variables
	#  %pidf = the PID-file
	self.varDict['pidf'] = self.pidfile

    def docheck(self):
	if self.rule == "EX":
	    # Check if pidfile exists
	    try:
		pidfile = open( self.pidfile, 'r' )
	    except IOError:
		# pidfile not found
		log.log( "<directive>PID(), EX, pidfile '%s' not found" % (self.pidfile), 6 )
		self.doAction()
	    else:
		log.log( "<directive>PID(), EX, pidfile '%s' found" % (self.pidfile), 6 )
		pidfile.close()

	elif self.rule == "PR":
	    # check if process pid found in pidfile is running - no alert if pidfile not found
	    try:
		pidfile = open( self.pidfile, 'r' )
	    except IOError:
		# pidfile not found
		log.log( "<directive>PID(), PR, pidfile '%s' not found" % (self.pidfile), 6 )
	    else:
		log.log( "<directive>PID(), PR, pidfile '%s' found" % (self.pidfile), 6 )
		pid = pidfile.readline()
		pidfile.close()
		pid = string.strip(pid)
		# strip '\n' from pid string if necessary
		if pid[-1:] == '\n':
		    pid = pid[:-1]

		self.varDict['pid'] = pid

		# Search for pid from process list
		if plist.pidExists( pid ) == 0:
		    # there is no process with pid == pid
    		    log.log( "<directive>PID(), PR, pid %s not in process list" % (pid), 6 )
		    self.doAction()
		else:
    		    log.log( "<directive>PID(), PR, pid %s is in process list" % (pid), 6 )


	else:
	    # invalid rule
	    log.log( "<directive>PID(), Error, '%s' is not a valid PID rule, config line follows,\n%s\n" % (self.rule,self.raw), 2 )


class D(Directive):
    def __init__(self, *arg):
	apply( Directive.__init__, (self,) + arg )
	self.regexp = 'D[\t \n]+\([a-zA-Z0-9_]+\)[\t \n]+\([a-zA-Z0-9_]+\)[\t \n]+\(.*\)'
	fields = self.parseRaw()
	self.daemon = fields[0]			# the daemon to check for
	self.rule = fields[1]			# the rule (NR or R)
	self.action = fields[2]			# the action
	
	self.ruleDict = { 'NR' : self.NR,
	                  'R'  : self.R	}
	#print "<D> daemon: '%s' rule: '%s' action: '%s'" % (self.daemon, self.rule, self.action)

	# Set any D-specific variables
	#  %dproc = the process name
	self.varDict['dproc'] = self.daemon
	#  %pid = pid of process (ie: if found running for R rule)
	self.varDict['pid'] = '[pid not yet defined]'

    def docheck(self):
	log.log( "<directive>docheck(D), daemon '%s', rule '%s', action '%s'" % (self.daemon,self.rule,self.action), 8 )
	self.ruleDict[ self.rule ]()

    def NR(self):
	if plist.procExists( self.daemon ) == 0:
	    log.log( "<directive>NR(D) daemon not running, '%s'" % (self.daemon), 6 )
	    self.doAction()

    def R(self):
	if plist.procExists( self.daemon ) > 0:
	    log.log( "<directive>R(D) daemon is running, '%s'" % (self.daemon), 6 )
	    # Set %pid variable.
	    self.varDict['pid'] = plist[self.daemon].pid
	    self.doAction()


class SP(Directive):
    def __init__(self, *arg):
	apply( Directive.__init__, (self,) + arg )
	self.regexp = 'SP[\t \n]+\([a-zA-Z0-9_/]+\)[\t \n]+\(.*\)'
	fields = self.parseRaw()
	self.port = fields[0]			# the port to check
	self.action = fields[1]			# the action
	log.log( "<Directive>SP, port '%s', action '%s'" % (self.port, self.action), 8 )

    def docheck(self):
	print "SP directive doing checking......"



##
## END - directive.py
##
