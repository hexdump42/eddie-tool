## 
## File		: http.py 
## 
## Author       : Chris Miles  <chris@psychofx.com>
## 
## Start Date	: 20020504
## 
## Description	: Directives for performing HTTP-related checks
##
## $Id$
##
##
########################################################################
## (C) Chris Miles 2002
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
import httplib, re, time, sys, string
# Imports: Eddie
import directive, log


##
## Directives ##
##


class HTTP(directive.Directive):
    """
    Uses httplib module to make a HTTP (or HTTPS) connection and request
    an object.  The elapsed connection time is recorded, and all related
    connection variables are made available, such as response code and
    returned message body, as well as error information if the connection
    failed.

    SSL-support must be compiled into Python for HTTPS connections.

    The POST method is not yet supported.
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
	    self.args.url		# filename
        except AttributeError:
            raise directive.ParseFailure, "url argument missing for HTTP directive %s" %(self.ID)
	try:
	    self.args.rule		# rule to test
        except AttributeError:
            raise directive.ParseFailure, "rule argument missing for HTTP directive %s" %(self.ID)

	# Set flag if SSL connection required
	if self.args.url[:5] == 'https':
	    self.ssl = 1
	else:
	    self.ssl = 0

	# Parse URL
	url_re = "https?://(?P<hostname>[a-zA-Z0-9.-]+)(?P<file>/.*)?"
	inx = re.match(url_re, self.args.url)
	if inx == None:
	    log.log( "<http>HTTP.tokenparser(): not a valid URL '%s'" % (self.args.url), 1 )
	    raise directive.ParseFailure, "not a valid URL '%s'" % (self.args.url)
	self.hostname = inx.group('hostname')
	self.file = inx.group('file')
	if self.file == None:
	    self.file = '/'

	# Set variables for Actions to use
	self.defaultVarDict['url'] = self.args.url
	self.defaultVarDict['rule'] = self.args.rule
	self.defaultVarDict['hostname'] = self.hostname
	self.defaultVarDict['file'] = self.file

	# define the unique ID
        if self.ID == None:
	    self.ID = '%s.FILE.%s' % (log.hostname, self.args.url)
	self.state.ID = self.ID

	log.log( "<http>HTTP.tokenparser(): ID '%s' URL '%s' parsed" % (self.ID, self.args.url), 8 )


    def getData(self):
	"""
	Called by Directive docheck() method to fetch the data required for
	evaluating the directive rule.

	Data:
	    failed	(boolean) - true if connection failed (socket error usually)
	    time	(float)   - elapsed time of connection

	    if failed:
		errno	(integer) - error code of failure
		errstr	(string)  - error message

	    if not failed:
		status	(integer) - HTTP status (e.g., 200, 404, etc)
		reason	(string)  - HTTP status message (e.g., "OK", "Not Found", etc)
		ok	(boolean) - true if status is 2xx or 3xx
		length	(integer) - length of body
		version	(integer) - HTTP version used
		header	(string)  - the response header
		body	(string)  - contains HTTP message body
	"""

	# Initialize the data
	data = {}
	data['failed'] = 0

	if self.ssl:
	    try:
		conn = httplib.HTTPSConnection( self.hostname )
	    except AttributeError:
		log.log( "<http>HTTP.getData(): cannot open HTTPS connection, SSL module not available", 3 )
		raise directive.DirectiveError, "cannot open HTTPS connection, SSL module not available"
	else:
	    conn = httplib.HTTPConnection( self.hostname )

	extra_headers = { 'User-Agent': 'EDDIE-Tool/%s'%(log.version) }

	time_start = time.time()
	try:
	    conn.request( "GET", self.file, None, extra_headers )
	except:
	    time_end = time.time()
	    e = sys.exc_info()
	    data['exception'] = e[0]
	    data['errno'] = e[1][0]
	    data['errstr'] = e[1][1]
	    data['time'] = time_end - time_start
	    data['failed'] = 1
	    return data

	time_end = time.time()
	data['time'] = time_end - time_start

	try:
	    r = conn.getresponse()
	except:
	    e = sys.exc_info()
	    data['exception'] = e[0]
	    data['errno'] = e[1][0]
	    data['errstr'] = e[1][1]
	    data['failed'] = 1
	    conn.close()
	    return data

	data['status'] = r.status
	data['reason'] = r.reason
	data['length'] = r.length
	data['version'] = r.version
	data['header'] = str(r.msg)
	data['body'] = r.read()

	conn.close()

	# Set an ok if status is 2xx or 3xx
	if r.status >= 200 and r.status < 400:
	    data['ok'] = 1
	else:
	    data['ok'] = 0

	return data


##
## END - http.py
##
