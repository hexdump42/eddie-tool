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
import sys, os, commands, time
# Imports: Eddie
import log, directive, utils


# Define exceptions
ParseFailure = 'ParseFailure'



class IPF(directive.Directive):
    """Eddie directive for performing ipfilter checks.
	Syntax:
	    IPF: rule="<rule>" action="<actions>"
	Examples:
	    IPF: rule="ipfstat == None" action="email('alert', 'ipfstat is empty')"
	    IPF: rule="len(ipfstatin) == 0" action="email('alert', 'ipfstat has no input rules for %(h)s')"
    """

    def __init__(self, toklist):
	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.rule
	except AttributeError:
	    raise ParseFailure, "Rule not specified"

	# Set any FS-specific variables
	#  rule = rule
	self.Action.varDict['rule'] = self.args.rule

	# define the unique ID
	self.ID = '%s.IPF.%s' % (log.hostname,self.args.rule)

	log.log( "<ipf>IPF.tokenparser(): ID '%s' rule '%s' action '%s'" % (self.ID, self.args.rule, self.args.actionList), 8 )


    def docheck(self, Config):
	log.log( "<ipf>IPF.docheck(): rule '%s'" % (self.args.rule), 7 )

	# locations to find ipfstat command
	ipfstatcmds = [ "/sbin/ipfstat", "/opt/local/sbin/ipfstat" ]
	ipfstatcmd = None

	for i in ipfstatcmds:
            try:
	        os.stat( i )
		ipfstatcmd = i
		break
	    except os.error, detail:
		log.log( "<ipf>IPF.docheck(): ipfstat not found, stat returned error %d, '%s'" % (detail[0], detail[1]), 8)

	if ipfstatcmd == None:
	    # no ipfstat
	    ipfstat = None
	    ipfstatin = None
	    ipfstatout = None
	else:
	    (r, ipfstat) = commands.getstatusoutput(ipfstatcmd)
	    if r != 0:
		# ipfstat call failed
		log.log( "<ipf>IPF.docheck(): %s call failed, returned %d, '%s'" % (ipfstatcmd, r, ipfstat), 3)

	    (r, ipfstatin) = commands.getstatusoutput(ipfstatcmd+" -ih")
	    if r != 0:
		# ipfstat -ih call failed
		log.log( "<ipf>IPF.docheck(): %s -ih call failed, returned %d, '%s'" % (ipfstatcmd, r, ipfstatin), 3)

	    (r, ipfstatout) = commands.getstatusoutput(ipfstatcmd+" -oh")
	    if r != 0:
		# ipfstat -oh call failed
		log.log( "<ipf>IPF.docheck(): %s -oh call failed, returned %d, '%s'" % (ipfstatcmd, r, ipfstatout), 3)

	rulesenv = {}			# environment for rules execution
	rulesenv['ipfstat'] = str(ipfstat)
	rulesenv['ipfstatin'] = str(ipfstatin)
	rulesenv['ipfstatout'] = str(ipfstatout)

	result = eval( self.args.rule, rulesenv )

	if result == 0:
	    self.state.stateok()	# update state info for check passed

	else:
	    self.state.statefail()	# update state info for check failed

	    # assign variables
	    self.Action.varDict['ipfstat'] = str(ipfstat)
	    self.Action.varDict['ipfstatin'] = str(ipfstatin)
	    self.Action.varDict['ipfstatout'] = str(ipfstatout)

    	    log.log( "<ipf>IPF.docheck(): rule '%s' was false, calling doAction()" % (self.args.rule), 6 )
    	    self.doAction(Config)

        self.putInQueue( Config.q )     # put self back in the Queue



##
## END - ipf.py
##
