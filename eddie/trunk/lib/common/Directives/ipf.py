## 
## File		: ipf.py 
## 
## Author       : Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 20000613
## 
## Description	: Directives for ipfilter checks
##
## $Id$
##
##


# Imports: Python
import sys
print "ipf sys.path:",sys.path
import commands
# Imports: Eddie
import log, directive


# Define exceptions
ParseFailure = 'ParseFailure'



class IPF(directive.Directive):
    def __init__(self, toklist):
	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):

	self.rule = utils.stripquote(toklist[0])	# the rule
	self.actionList = self.parseAction(toklist[1:])

	# Set any FS-specific variables
	#  rule = rule
	self.Action.varDict['rule'] = self.rule

	# define the unique ID
	self.ID = '%s.FS.%s.%s' % (log.hostname,self.rule)

	log.log( "<ipf.py>IPF, ID '%s' rule '%s' action '%s'" % (self.ID, self.rule, self.actionList), 8 )


    def docheck(self, Config):
	log.log( "<ipf.py>IPF, docheck(): rule '%s'" % (self.rule), 7 )

	# define the ipfstat command with full path
	ipfstatcmd = "/opt/local/sbin/ipfstat"

	try:
	    os.stat( ipfstatcmd )
	except os.error, detail:
	    # no ipfstat
	    ipfstat = None
	    log.log( "<ipf.py>IPF, docheck(): ipfstat not found, stat returned error %d, '%s'" % (detail[0], detail[1]), 8)
	else:
	    (r, ipfstat) = commands.getstatusoutput("/opt/local/sbin/ipfstat")
	    if r != 0:
		# ipfstat call failed
		log.log( "<ipf.py>IPF, docheck(): ipfstat call failed, returned %d, '%s'" % (r, ipfstat), 3)

	print "ipfstat:",ipfstat

	rulesenv = {}			# environment for rules execution
	rulesenv['ipfstat'] = str(ipfstat)

	###self.parseRule()

	result = eval( self.rule, rulesenv )

	if result == 0:
	    self.stateok()	# update state info for check passed

	else:
	    self.statefail()	# update state info for check failed

	    # assign variables
	    self.Action.varDict['ipfstat'] = str(ipfstat)

    	    log.log( "<ipf.py>IPF, docheck(): rule '%s' was false, calling doAction()" % (self.rule), 6 )
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





##
## END - ipf.py
##
