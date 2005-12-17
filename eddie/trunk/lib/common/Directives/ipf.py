
'''
File		: ipf.py 

Start Date	: 20000613

Description	: Directives for ipfilter checks

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 2000-2005'

__author__ = 'Chris Miles'

__license__ = '''
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
'''



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
