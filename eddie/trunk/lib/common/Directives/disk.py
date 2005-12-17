
'''
File		: disk.py 

Start Date	: 20041005 

Description	: Disk directives

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 2004-2005'

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



##
## Imports: Python
##

##
## Imports: Eddie
##
import directive
import log
import utils


##
## Directives
##

class DISK(directive.Directive):
    """DISK provides access to data & stats for disk devices.

    It requires the 'DiskStatistics' class from the 'diskdevice' data-collection module.

    Example:

	# /dev/md/dsk/d20 == /var
	DISK md20_thruput:
	    device='md20'
	    scanperiod='5m'
	    rule='1'        # always perform action
	    action='elvinrrd("disk-%(h)s_%(device)s", "rbytes=%(nread)s", "wbytes=%(nwritten)s")'
    """

    def __init__(self, toklist):
	# FS requires the DiskStatistics collector object from the diskdevice module
	self.need_collectors = ( ('diskdevice','DiskStatistics'), )		# (module, collector-class) required

	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	"""Parse directive arguments."""

	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.device
	except AttributeError:
	    raise directive.ParseFailure, "Device not specified"
	try:
	    self.args.rule
	except AttributeError:
	    raise directive.ParseFailure, "Rule not specified"

	# Set any directive-specific variables
	self.defaultVarDict['device'] = self.args.device
	self.defaultVarDict['rule'] = self.args.rule

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.DISK.%s' % (log.hostname,self.args.device)
	self.state.ID = self.ID

	log.log( "<disk>DISK.tokenparser(): ID '%s' device '%s' rule '%s'" % (self.state.ID, self.args.device, self.args.rule), 8 )


    def getData(self):
	"""Called by Directive docheck() method to fetch the data required for
	evaluating the directive rule.
	"""

	disk = self.data_collectors['diskdevice.DiskStatistics'][self.args.device]
	if disk == None:
	    log.log( "<disk>DISK.docheck(): Error, device not found '%s'" % (self.args.device), 4 )
	    return None
	else:
	    return disk.getHash()



class TAPE(directive.Directive):
    """TAPE provides access to data & stats for tape devices.

    It requires the 'TapeStatistics' class from the 'diskdevice' data-collection module.

    Example:

        # st65 == TAPE
        TAPE st65_thruput:
            device='st65'
            scanperiod='5m'
            rule='1'        # always perform action
            action='elvinrrd("tape-%(h)s_%(device)s", "rbytes=%(nread)s", "wbytes=%(nwritten)s")'
    """

    def __init__(self, toklist):
	# FS requires the TapeStatistics collector object from the diskdevice module
	self.need_collectors = ( ('diskdevice','TapeStatistics'), )		# (module, collector-class) required

	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	"""Parse directive arguments."""

	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.device
	except AttributeError:
	    raise directive.ParseFailure, "Device not specified"
	try:
	    self.args.rule
	except AttributeError:
	    raise directive.ParseFailure, "Rule not specified"

	# Set any directive-specific variables
	self.defaultVarDict['device'] = self.args.device
	self.defaultVarDict['rule'] = self.args.rule

	# define the unique ID
	if self.ID == None:
	    self.ID = '%s.TAPE.%s' % (log.hostname,self.args.device)
	self.state.ID = self.ID

	log.log( "<disk>TAPE.tokenparser(): ID '%s' device '%s' rule '%s'" % (self.state.ID, self.args.device, self.args.rule), 8 )


    def getData(self):
	"""Called by Directive docheck() method to fetch the data required for
	evaluating the directive rule.
	"""

	tape = self.data_collectors['diskdevice.TapeStatistics'][self.args.device]
	if tape == None:
	    log.log( "<disk>TAPE.docheck(): Error, device not found '%s'" % (self.args.device), 4 )
	    return None
	else:
	    return tape.getHash()


##
## END - disk.py
##
