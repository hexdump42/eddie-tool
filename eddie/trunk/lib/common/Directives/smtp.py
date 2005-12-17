
'''
File		: smtp.py 

Start Date	: 20040616

Description	: Directives for smtp checks

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 2004-2005'

__author__ = 'Dougal Scott'

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
import socket
import time
# Imports: Eddie
import log
import directive


# Define exceptions
SMTPerror = "SMTPerror"


class smtpclient:
    def __init__(self, host, port=25):
	if host == "":
	    raise SMTPerror, "host not given"

	if type(port) != type(1):
	    raise SMTPerror, "port must be integer"

	self.host = host
	self.port = port
	self.connected = 0


    def connect(self):
	self.smtpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	tstart = time.time()
	try:
	    self.smtpsock.connect( (self.host,self.port) )
	except socket.error, detail:
	    log.log( "<smtp>smtp.connect(): exception, %d, '%s'" % (detail[0], detail[1]), 5 )
	    return 0

	data = self.smtpsock.recv(1024)
	tend = time.time()

	if data[:4] != "220 ":
	    return 0

	self.connected = 1
	self.timing = tend - tstart
	return 1


    def close(self):
	if self.connected == 0:
	    raise SMTPerror, "no connection to close"

	self.smtpsock.close()
	self.connected = 0


##
## Directives
##

class SMTP(directive.Directive):
    """SMTP directive.  Make a smtp connection and time how
       long it takes to connect.

       Sample rule:
       SMTP: server='hostname:port' action="<actions>"
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
	    self.args.server		# hostname:port
        except AttributeError:
            raise directive.ParseFailure, "SMTP Server not specified"
	try:
	    self.args.rule
	except AttributeError:
	    raise directive.ParseFailure, "Rule not specified"

	if ':' in self.args.server:
	    (self.host, self.port) = self.args.server.split(':')
	    self.port = int(self.port)
	else:
	    self.host = self.args.server
	    self.port = 25


	# Set variables for Actions to use
	self.defaultVarDict['server'] = self.host
	self.defaultVarDict['port'] = self.port

	# define the unique ID
        if self.ID == None:
	    self.ID = '%s.SMTP.%s.%d' % (log.hostname,self.host,self.port)
	self.state.ID = self.ID

	log.log( "<smtp>SMTP.tokenparser(): ID '%s' host '%s' port %d" % (self.ID, self.host, self.port), 8 )


    def getData(self):
	"""
	The 'check' in this case is to login to the smtp server and
	perform a few actions, recording the timing of each action.
	"""

	data = {}

	connecttime = None

	# create smtp connection object
	p = smtpclient( self.host, self.port )
	if p.connect():
	    data['connected'] = 1
	    connecttime = p.timing
	    p.close()
	else:
	    data['connected'] = 0

	# assign variables
	data['connecttime'] = connecttime

	log.log( "<smtp>SMTP.getData(): connecttime=%s" % connecttime, 7 )

        return data

##
## END - smtp.py
##
