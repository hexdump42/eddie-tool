## 
## File		: ipf.py 
## 
## Author       : Chris Miles  <chris@psychofx.com>
## 
## Start Date	: 20000613
## 
## Description	: Directives for ipfilter checks
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
import sys, os, time
# Imports: Eddie
import log, directive, utils


##
## Directives
##

class IPF(directive.Directive):
    """
    Eddie directive for performing ipfilter checks.
	Syntax:
	    IPF <name>: rule="<rule>"
	                action="<actions>"
	Examples:
	    IPF empty:   rule="ipfstat == None"
	                 action="email('alert', 'ipfstat is empty')"
	    IPF norules: rule="len(ipfstatin) == 0"
	                 action="email('alert', 'ipfstat has no input rules for %(h)s')"
    """

    def __init__(self, toklist):
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

	# Set any FS-specific variables
	#  rule = rule
	self.defaultVarDict['rule'] = self.args.rule

	# define the unique ID
        if self.ID == None:
	    self.ID = '%s.IPF.%s' % (log.hostname,self.args.rule)
	self.state.ID = self.ID

	log.log( "<ipf>IPF.tokenparser(): ID '%s' rule '%s'" % (self.ID, self.args.rule), 8 )


    def getData(self):
	"""
	Called by Directive docheck() method to fetch the data required for
	evaluating the directive rule.
	"""

	# locations to find ipfstat command
	ipfstatcmds = [ "/sbin/ipfstat", "/opt/local/sbin/ipfstat" ]
	ipfstatcmd = None

	for i in ipfstatcmds:
            try:
	        os.stat( i )
		ipfstatcmd = i
		log.log( "<ipf>IPF.getData(): ipfstat found at %s" % (i), 7 )
		break
	    except os.error, detail:
		log.log( "<ipf>IPF.getData(): ipfstat not found at %s, stat returned error %d, '%s'" % (i, detail[0], detail[1]), 9 )

	if ipfstatcmd == None:
	    # no ipfstat
	    log.log( "<ipf>IPF.getData(): ipfstat command not found, directive cannot continue", 4 )
	    raise directive.DirectiveError, "ipfstat command not found, directive cannot continue"

	else:
	    (r, ipfstat) = utils.safe_getstatusoutput(ipfstatcmd)
	    if r != 0:
		# ipfstat call failed
		log.log( "<ipf>IPF.getData(): %s call failed, returned %d, '%s'" % (ipfstatcmd, r, ipfstat), 5)

	    (r, ipfstatin) = utils.safe_getstatusoutput(ipfstatcmd+" -ih")
	    if r != 0:
		# ipfstat -ih call failed
		log.log( "<ipf>IPF.getData(): %s -ih call failed, returned %d, '%s'" % (ipfstatcmd, r, ipfstatin), 5)

	    (r, ipfstatout) = utils.safe_getstatusoutput(ipfstatcmd+" -oh")
	    if r != 0:
		# ipfstat -oh call failed
		log.log( "<ipf>IPF.getData(): %s -oh call failed, returned %d, '%s'" % (ipfstatcmd, r, ipfstatout), 5)

	data = {}
	data['ipfstat'] = str(ipfstat)
	data['ipfstatin'] = str(ipfstatin)
	data['ipfstatout'] = str(ipfstatout)

	return data



##
## END - ipf.py
##
