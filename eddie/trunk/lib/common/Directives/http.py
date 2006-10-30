
'''
File		: http.py 

Start Date	: 20020504

Description	: Directives for performing HTTP-related checks

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 2002-2005'

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
import httplib
import re
import time
import sys
import socket
# Imports: Eddie
import directive
import log


##
## Directives ##
##


class HTTP(directive.Directive):
    """Uses httplib module to make a HTTP (or HTTPS) connection and request
    an object.  The elapsed connection time is recorded, and all related
    connection variables are made available, such as response code and
    returned message body, as well as error information if the connection
    failed.

    SSL-support must be compiled into Python for HTTPS connections.

    The POST method is not yet supported. (TODO)
    """

    def __init__(self, toklist):
	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	"""Parse directive arguments.
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
	url_re = "https?://(?P<hostname>[a-zA-Z0-9.-]+)(:(?P<port>[0-9]+))?(?P<file>/.*)?"
	inx = re.match(url_re, self.args.url)
	if inx == None:
	    log.log( "<http>HTTP.tokenparser(): not a valid URL '%s'" % (self.args.url), 1 )
	    raise directive.ParseFailure, "not a valid URL '%s'" % (self.args.url)

	self.hostname = inx.group('hostname')
	self.port = inx.group('port')
	if self.port == None:
	    if self.ssl:
		self.port = 443
	    else:
		self.port = 80
	else:
	    try:
		self.port = int(self.port)
	    except ValueError, msg:
		raise directive.ParseFailure, "%s: port invalid for URL %s, %s" %(self.ID,self.args.url,msg)

	self.file = inx.group('file')
	if self.file == None:
	    self.file = '/'

	# cmiles 2004-07-13: option to set the timeout for the socket when making the HTTP request
	try:
	    self.args.request_timeout
        except AttributeError:
	    self.request_timeout = None		# no timeout specified by default
	else:
	    try:
		self.request_timeout = float(self.args.request_timeout)
	    except ValueError, msg:
		raise directive.ParseFailure, "%s: request_timeout (%s) is not a valid floating-point number" %(self.ID,self.args.request_timeout)
	    if self.request_timeout < 0.0:
		raise directive.ParseFailure, "%s: request_timeout (%s) cannot be negative" %(self.ID,self.args.request_timeout)

	# Set variables for Actions to use
	self.defaultVarDict['url'] = self.args.url
	self.defaultVarDict['rule'] = self.args.rule
	self.defaultVarDict['hostname'] = self.hostname
	self.defaultVarDict['port'] = self.port
	self.defaultVarDict['file'] = self.file
	self.defaultVarDict['request_timeout'] = self.request_timeout

	# define the unique ID
        if self.ID == None:
	    self.ID = '%s.FILE.%s' % (log.hostname, self.args.url)
	self.state.ID = self.ID

	log.log( "<http>HTTP.tokenparser(): ID '%s' URL '%s' parsed" % (self.ID, self.args.url), 8 )


    def getData(self):
	"""Called by Directive docheck() method to fetch the data required for
	evaluating the directive rule.

	Data:
	    failed	(boolean) - true if connection failed (socket error usually)
	    time	  (float) - total elapsed time of connection
	    time_resolve  (float) - elapsed time to resolve hostname  to IP
	    time_connect  (float) - elapsed time to connect to server
	    time_request  (float) - elapsed time to send HTTP/S request to server
	    time_response (float) - elapsed time to retrieve the server response (and close connection)
	    timedout	(boolean) - true if request timed out

	    if failed:
		exception (string) - exception type
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

	# cmiles 2004-07-05: modified to record elapsed time of each section of the HTTP(S)
	#	connection: IP resolution, connection, sending request, receiving response

	# Initialize the data
	data = {}
	data['failed'] = 0
	data['exception'] = ""
	data['errno'] = ""
	data['errstr'] = ""
	data['time'] = ""
	data['time_resolve'] = ""
	data['time_connect'] = ""
	data['time_request'] = ""
	data['time_response'] = ""
	data['timedout'] = 0		# boolean; is true if received socket.timeout exception
	data['ip'] = ""
	data['status'] = ""

	e = None

	# Resolve the hostname to IP address (and time it)
	log.log( "<http>HTTP.getData(): Resolving %s"%(self.hostname), 7 )
	time_resolve_start = time.time()
	try:
	    ip = socket.gethostbyname( self.hostname )
	except:
	    time_resolve_end = time.time()
	    e = sys.exc_info()
	    data['exception'] = e[0]
	    data['errno'] = e[1][0]
	    data['errstr'] = e[1][1]
	    data['time_resolve'] = time_resolve_end - time_resolve_start
	    data['time'] = data['time_resolve']
	    data['failed'] = 1
	    log.log( "<http>HTTP.getData(): Resolving %s failed, exception=%s, errno=%s, errstr=%s"%(self.hostname,data['exception'],data['errno'],data['errstr']), 7 )
	    return data

	time_resolve_end = time.time()
	data['time_resolve'] = time_resolve_end - time_resolve_start
	data['ip'] = ip
	log.log( "<http>HTTP.getData(): Resolved %s to: %s, time=%f"%(self.hostname,ip,data['time_resolve']), 7 )

	time_start = time_resolve_start
	time_end = time_resolve_end

	# Initialize httplib - use IP address to avoid any more DNS lookups
	if self.ssl:
	    try:
		conn = httplib.HTTPSConnection( ip, self.port )
	    except AttributeError:
		log.log( "<http>HTTP.getData(): cannot open HTTPS connection, SSL module not available", 3 )
		raise directive.DirectiveError, "cannot open HTTPS connection, SSL module not available"
	else:
	    conn = httplib.HTTPConnection( ip, self.port )

	# Uncomment this to send httplib debug output to stdout
	#conn.set_debuglevel(1)

	# Create the HTTP/HTTPS connection (and time it)
	log.log( "<http>HTTP.getData(): Connecting to: %s:%d (%s)"%(ip,self.port,self.hostname), 7 )
	time_connect_start = time.time()
	try:
	    conn.connect()
	except AttributeError, err:
	    raise directive.DirectiveError, "cannot open HTTP(S) connection, %s" % str(err)
		
	except:
	    time_connect_end = time.time()
	    e = sys.exc_info()
	    data['exception'] = e[0]
	    data['errno'] = e[1][0]
	    try:
		data['errstr'] = e[1][1]
	    except IndexError:
	    	data['errstr'] = str(e[0])
	    data['time_connect'] = time_connect_end - time_connect_start
	    data['time'] = time_connect_end - time_start
	    data['failed'] = 1
	    log.log( "<http>HTTP.getData(): Connection to %s failed, exception=%s, errno=%s, errstr=%s"%(self.hostname,data['exception'],data['errno'],data['errstr']), 7 )
	    return data

	time_connect_end = time.time()
	data['time_connect'] = time_connect_end - time_connect_start
	log.log( "<http>HTTP.getData(): Connected to: %s, time=%f"%(self.hostname,data['time_connect']), 7 )

	# Send user-agent to be a good netizen
	# Set hostname so HTTP/1.1 works properly (we connect to the IP address above)
	extra_headers = { 'User-Agent': 'EDDIE-Tool/%s'%(log.version),
			       'Host' : self.hostname 
			}

	# Send request to server
	log.log( "<http>HTTP.getData(): Sending request: %s"%(self.file), 7 )
	# cmiles 2004-07-13: set a socket timeout if one is specified
	if self.request_timeout != None:
	    try:
		conn.sock.settimeout( self.request_timeout )
	    except AttributeError, msg:
		log.log( "<http>HTTP.getData(): request_timeout not set as socket.settimeout() not supported, %s"%(msg), 5 )
	    else:
		log.log( "<http>HTTP.getData(): socket timeout set to %f"%(self.request_timeout), 8 )
	time_request_start = time.time()
	try:
	    conn.request( "GET", self.file, None, extra_headers )
	except:
	    time_request_end = time.time()
	    e = sys.exc_info()
	    data['exception'] = e[0]
	    # cmiles 2004-07-13: check for socket.timeout exception (but only if Python >= 2.3)
	    if (sys.version_info[0] > 2 or (sys.version_info[0] == 2 and sys.version_info[1] >= 3)) and data['exception'] == socket.timeout:
		data['errno'] = 0
		data['errstr'] = str(e[1])
		data['timedout'] = 1
	    else:
		data['errno'] = e[1][0]
		data['errstr'] = e[1][1]
	    data['time_request'] = time_request_end - time_request_start
	    data['time'] = time_request_end - time_start
	    data['failed'] = 2
	    log.log( "<http>HTTP.getData(): Request failed, exception=%s, errno=%s, errstr=%s"%(data['exception'],data['errno'],data['errstr']), 7 )
	    conn.close()
	    return data

	time_request_end = time.time()
	data['time_request'] = time_request_end - time_request_start
	log.log( "<http>HTTP.getData(): Request sent, time=%f"%(data['time_request']), 7 )

	time_end = time_request_end

	# Get response from server
	log.log( "<http>HTTP.getData(): Waiting to receive response", 7 )
	time_response_start = time.time()
	try:
	    r = conn.getresponse()
	except:
	    time_response_end = time.time()
	    e = sys.exc_info()
	    data['exception'] = e[0]
	    # cmiles 2004-07-19: check for socket.timeout exception (but only if Python >= 2.3)
	    if (sys.version_info[0] > 2 or (sys.version_info[0] == 2 and sys.version_info[1] >= 3)) and data['exception'] == socket.timeout:
		data['errno'] = 0
		data['errstr'] = str(e[1])
		data['timedout'] = 1
	    else:
		data['errno'] = e[1][0]
		try:
		    if len( e[1] ) > 1:
			data['errstr'] = e[1][1]
		    else:
			data['errstr'] = str(e[1])
		except AttributeError:
		    data['errstr'] = str(e)

	    data['time_response'] = time_response_end - time_response_start
	    data['time'] = time_response_end - time_start
	    data['failed'] = 3
	    log.log( "<http>HTTP.getData(): Receive response failed, exception=%s, errno=%s, errstr=%s"%(data['exception'],data['errno'],data['errstr']), 7 )
	    conn.close()
	    return data

	try:	# cmiles 2003-04-02: httplib can fail when reading body sometimes
	    data['body'] = r.read()
	except:
	    e = sys.exc_info()
	    # cmiles 2004-07-19: check for socket.timeout exception (but only if Python >= 2.3)
	    if (sys.version_info[0] > 2 or (sys.version_info[0] == 2 and sys.version_info[1] >= 3)) and e[0] == socket.timeout:
		log.log( "<http>HTTP.getData(): response read failed with timeout, exception=%s, errstr=%s"%(e[0],str(e[1])), 7 )
	    else:
		# cmiles 2004-07-19: some Exceptions were breaking string substitution
		#log.log( "<http>HTTP.getData(): response read failed, exception=%s, errno=%s, errstr=%s"%(e[0],e[1][0],e[1][1]), 7 )
		log.log( "<http>HTTP.getData(): response read failed, exception=%s, errstr=%s"%(e[0],e[1]), 7 )
	    data['body'] = "<read failed>"

	data['status'] = r.status
	data['reason'] = r.reason
	data['length'] = r.length
	data['version'] = r.version
	data['header'] = str(r.msg)

	conn.close()

	# cmiles - 2003-04-02: moved time_end from before getresponse() to after close()
	time_response_end = time.time()
	data['time_response'] = time_response_end - time_response_start
	data['time'] = time_response_end - time_start

	log.log( "<http>HTTP.getData(): Response received, status=%s, reason=%s, time=%f, total elapsed time=%f"%(data['status'],data['reason'],data['time_response'],data['time']), 7 )

	# Set an ok if status is 2xx or 3xx
	if r.status >= 200 and r.status < 400:
	    data['ok'] = 1
	else:
	    data['ok'] = 0

	return data


##
## END - http.py
##
