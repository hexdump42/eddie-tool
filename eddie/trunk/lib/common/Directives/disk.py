## 
## File		: disk.py 
## 
## Author       : Chris Miles  <chris@psychofx.com>
## 
## Start Date	: 20041005 
## 
## Description	: Disk directives
##
## $Id$
##
##
########################################################################
## (C) Chris Miles 2004
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
	# FS requires the DiskStatistics collector object from the df module
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


##
## END - disk.py
##
