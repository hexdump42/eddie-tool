## 
## File		: radius.py 
## 
## Author       : Chris Miles  <chris@psychofx.com>
## 
## Start Date	: 20001016
## 
## Description	: Directives for Radius authentication & accounting checks
##
## Requires     : radcm.py
##
## $Id$
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
import sys, os, time, string
# Imports: Eddie
import log, directive, utils
# Imports: Misc
import radcm


##
## Directives
##

class RADIUS(directive.Directive):
    """
    RADIUS directive.  Perform a Radius authentication and return
    results.  Rules can be specified to test the results.

    Rule format:
       RADIUS: server='hostname[:port]'
               secret='secret'
	       user='username'
	       password='password'
	       rule='rule'
	       action='<actions>'
    Example:
       RADIUS: server='radius.domain.name:1645'
               secret='s3cr3t'
	       user='bob@domain.name'
	       password='b0bm@t3'
	       rule='not passed'
	       action='email("alert", "radius FAILED to %(host)s:%(port)d")'
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
	    self.args.server		# hostname[:port]
	except AttributeError:
	    raise directive.ParseFailure, "Server not specified"
	try:
	    self.args.secret		# secret
	except AttributeError:
	    raise directive.ParseFailure, "Secret not specified"
	try:
	    self.args.user		# username
	except AttributeError:
	    raise directive.ParseFailure, "Username not specified"
	try:
	    self.args.password		# password
	except AttributeError:
	    raise directive.ParseFailure, "Password not specified"

	# rule argument is optional...
	try:
	    self.args.rule		# rule
	except AttributeError:
	    self.args.rule = 1		# always true if no supplied rule

	if ':' in self.args.server:
	    (self.host, self.port) = string.split( self.args.server, ':' )
	    self.port = int(self.port)
	else:
	    self.host = self.args.server
	    self.port = 1645


	# Set any directive-specific variables
	self.defaultVarDict['server'] = self.host
	self.defaultVarDict['port'] = self.port
	self.defaultVarDict['secret'] = self.args.secret
	self.defaultVarDict['username'] = self.args.user
	self.defaultVarDict['password'] = self.args.password
	self.Action.varDict['rule'] = self.args.rule

	# define the unique ID
        if self.ID == None:
	    self.ID = '%s.RADIUS.%s.%d.%s' % (log.hostname,self.host,self.port,self.args.user)
	self.state.ID = self.ID

	log.log( "<radius>RADIUS.tokenparser(): ID '%s' host '%s' port %d secret '%s' user '%s'" % (self.ID, self.host, self.port, self.args.secret, self.args.user), 8 )


    def getData(self):
	"""
	Perform a Radius authentication and return results.
	"""

	timing = None

	# create pop3 connection object
	r = radcm.Radius( self.host, self.args.secret, self.port  )
	tstart = time.time()
	try:
	    passed = r.authenticate(self.args.user,self.args.password)
	except radcm.NoResponse:
	    passed = 0
	tend = time.time()
	timing = tend - tstart

	# Values are set to None if there was some problem performing the
	# commands.
	if timing == None:
	    timing = 0
	    log.log( "<radius>RADIUS.getData(): timing could not be measured, setting to 0", 5 )

	log.log( "<radius>RADIUS.getData(): timing=%s passed=%s" % (timing,passed), 7 )

	# assign variables
	data = {}
	data['timing'] = timing
	data['passed'] = passed

	return data


##
## END - radius.py
##
