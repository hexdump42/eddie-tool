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
import sys, os, commands
# Imports: Eddie
import log, directive, utils


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
	self.ID = '%s.IPF.%s' % (log.hostname,self.rule)

	log.log( "<ipf.py>IPF.tokenparser(): ID '%s' rule '%s' action '%s'" % (self.ID, self.rule, self.actionList), 8 )


    def docheck(self, Config):
	log.log( "<ipf.py>IPF.docheck(): rule '%s'" % (self.rule), 7 )

	# locations to find ipfstat command
	ipfstatcmds = [ "/sbin/ipfstat", "/opt/local/sbin/ipfstat" ]
	ipfstatcmd = None

	for i in ipfstatcmds:
            try:
	        os.stat( i )
		ipfstatcmd = i
		break
	    except os.error, detail:
		log.log( "<ipf.py>IPF.docheck(): ipfstat not found, stat returned error %d, '%s'" % (detail[0], detail[1]), 8)

	if ipfstatcmd == None:
	    # no ipfstat
	    ipfstat = None
	    ipfstatin = None
	    ipfstatout = None
	else:
	    (r, ipfstat) = commands.getstatusoutput(ipfstatcmd)
	    if r != 0:
		# ipfstat call failed
		log.log( "<ipf.py>IPF.docheck(): %s call failed, returned %d, '%s'" % (ipfstatcmd, r, ipfstat), 3)

	    (r, ipfstatin) = commands.getstatusoutput(ipfstatcmd+" -ih")
	    if r != 0:
		# ipfstat -ih call failed
		log.log( "<ipf.py>IPF.docheck(): %s -ih call failed, returned %d, '%s'" % (ipfstatcmd, r, ipfstatin), 3)

	    (r, ipfstatout) = commands.getstatusoutput(ipfstatcmd+" -oh")
	    if r != 0:
		# ipfstat -oh call failed
		log.log( "<ipf.py>IPF.docheck(): %s -oh call failed, returned %d, '%s'" % (ipfstatcmd, r, ipfstatout), 3)

	rulesenv = {}			# environment for rules execution
	rulesenv['ipfstat'] = str(ipfstat)
	rulesenv['ipfstatin'] = str(ipfstatin)
	rulesenv['ipfstatout'] = str(ipfstatout)

	###self.parseRule()

	result = eval( self.rule, rulesenv )

	if result == 0:
	    self.state.stateok()	# update state info for check passed

	else:
	    self.state.statefail()	# update state info for check failed

	    # assign variables
	    self.Action.varDict['ipfstat'] = str(ipfstat)
	    self.Action.varDict['ipfstatin'] = str(ipfstatin)
	    self.Action.varDict['ipfstatout'] = str(ipfstatout)

    	    log.log( "<ipf.py>IPF.docheck(): rule '%s' was false, calling doAction()" % (self.rule), 6 )
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
