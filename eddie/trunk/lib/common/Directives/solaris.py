## 
## File		: solaris.py 
## 
## Author       : Chris Miles  <cmiles@codefx.com.au>
## 
## Start Date	: 20000615
## 
## Description	: Directives for Solaris-specific checks
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
import os, re
# Imports: Eddie
import log, directive, utils


##
## Directives
##


class METASTAT(directive.Directive):
    """
    Solaris Disksuite checks for bad metadevices/disks.
    This directive only currently checks for any devices that require
    'Maintenance' from the metastat output.

    TODO: parse metastat output better and report the actual device
    that is having the problem.

    Example:
	METASTAT maint: rule='need_maintenance'
	                action="email('alert', 'A metadevice requires maintenance on %(h)s.')"
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

	# Set any directive-specific variables
	self.defaultVarDict['rule'] = self.args.rule

	# define the unique ID
        if self.ID == None:
	    self.ID = '%s.METASTAT' % (log.hostname)
	self.state.ID = self.ID

	log.log( "<solaris>METASTAT.tokenparser(): ID '%s' rule '%s'" % (self.ID, self.args.rule), 8 )


    def getData(self):
	"""
	Called by Directive docheck() method to fetch the data required for
	evaluating the directive rule.
	"""

        # where to find the metastat command
	metastat_list = [ "/usr/opt/SUNWmd/sbin/metastat", "/usr/sbin/metastat" ]

	metastat = None

        for m in metastat_list:
	    try:
	        os.stat( m )
		metastat = m
	    except:
		pass

	if metastat == None:
	    log.log( "<solaris>METASTAT.getData(): metastat not found at %s, directive cancelled" % (metastat_list), 4 )
	    raise directive.DirectiveError, "metastat not found at %s, directive cancelled" % (metastat_list)

	else:
	    # metastat exists, so check for anything requiring Maintenance

	    cmd = "%s | /usr/bin/grep -i maint | /usr/bin/wc -l" % (metastat)
	    (retval, result) = utils.safe_getstatusoutput( cmd )
	    try:
		r = int(result)
	    except ValueError:
		r = 0

	    if r > 0:
		# something requires Maintenance
		data['need_maintenance'] = 1	# true
	    else:
		data['need_maintenance'] = 0	# false

	return data




class PRTDIAG(directive.Directive):
    """
    Solaris checks using prtdiag output.
    Currently only supports AMBIENT and CPU temperatures.

    TODO: parse rest of prtdiag.

    Example:
	PRTDIAG: rule="temp_ambient > 40"
                 action="email('alert', 'Ambient temperature on %(h)s is %(temp_ambient)s.')"
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
	    self.args.rule		# the rule
	except AttributeError:
	    raise directive.ParseFailure, "Rule not specified"

	# Set any PRTDIAG-specific variables
	self.defaultVarDict['rule'] = self.args.rule

	# define the unique ID
        if self.ID == None:
	    self.ID = '%s.PRTDIAG' % (log.hostname)
	self.state.ID = self.ID

	log.log( "<solaris>PRTDIAG.tokenparser(): ID '%s' rule '%s'" % (self.ID, self.args.rule), 8 )


    def getData(self):
        prtdiag = None

	# Determine system type and parse system-specific output
	cmd = "/usr/bin/uname -i"
	(retval, output) = utils.safe_getstatusoutput( cmd )
	if output == "SUNW,Ultra-4":
	    prtdiag_dict = self.parse_prtdiag_u450()
	elif output == "SUNW,Ultra-250":
	    prtdiag_dict = self.parse_prtdiag_u250()
	elif output == "SUNW,Sun-Fire-280R":
	    prtdiag_dict = self.parse_prtdiag_u280r()
	elif output == "SUNW,Ultra-Enterprise":
	    prtdiag_dict = self.parse_prtdiag_Enterprise()
	else:
	    log.log( "<solaris>PRTDIAG.getData(): system type %s not supported yet, directive cancelled" % (output), 4 )
	    raise directive.DirectiveError, "system type %s not supported yet, directive cancelled" % (output)

	if prtdiag_dict == None:	# there was an error, just exit
	    log.log( "<solaris>PRTDIAG.getData(): prtdiag returned no data, directive cancelled", 4 )
	    raise directive.DirectiveError, "prtdiag returned no data, directive cancelled"

	data = prtdiag_dict

	return data


    def parse_prtdiag_u450(self):
	"""Parse prtdiag for a U450."""

	prtdiag = "/usr/platform/sun4u/sbin/prtdiag"

	try:
	    os.stat( prtdiag )
	except:
	    log.log( "<solaris>PRTDIAG.parse_prtdiag_u450(): %s not found, directive cancelled" % (prtdiag), 4 )
	    return None

	cmd = "%s -v" % (prtdiag)
	(retval, output) = utils.safe_getstatusoutput( cmd )

	# Initialise prtdiag dictionary of values
	prtdiag_dict = {}
	prtdiag_dict['temp_ambient'] = None
	prtdiag_dict['temp_cpu0'] = None
	prtdiag_dict['temp_cpu1'] = None
	prtdiag_dict['temp_cpu2'] = None
	prtdiag_dict['temp_cpu3'] = None
	prtdiag_dict['temp_supply0'] = None
	prtdiag_dict['temp_supply1'] = None
	prtdiag_dict['temp_supply2'] = None

	for l in output.split('\n'):
	    inx = re.search("^AMBIENT\s+([0-9]+)", l)
	    if inx:	# AMBIENT temp
		prtdiag_dict['temp_ambient'] = int(inx.group(1))
		continue

	    inx = re.search("^CPU\s+([0-9])\s+([0-9]+)", l)
	    if inx:	# CPU temps
		prtdiag_dict['temp_cpu%s'%(inx.group(1))] = int(inx.group(2))
		continue

	    inx = re.search("([0-9])\s+[0-9]+ W\s+([0-9]+)\s+\w+", l)
	    if inx:	# Power Supply temps
		prtdiag_dict['temp_supply%s'%(inx.group(1))] = int(inx.group(2))
		continue

	return prtdiag_dict
		

    def parse_prtdiag_u250(self):
	"""Parse prtdiag for a U250."""

	prtdiag = "/usr/platform/sun4u/sbin/prtdiag"

	try:
	    os.stat( prtdiag )
	except:
	    log.log( "<solaris>PRTDIAG.parse_prtdiag_u250(): %s not found, directive cancelled" % (prtdiag), 4 )
	    return None

	cmd = "%s -v" % (prtdiag)
	(retval, output) = utils.safe_getstatusoutput( cmd )

	# Initialise prtdiag dictionary of values
	prtdiag_dict = {}
	prtdiag_dict['temp_cpu0'] = None
	prtdiag_dict['temp_cpu1'] = None
	prtdiag_dict['temp_mb0'] = None
	prtdiag_dict['temp_mb1'] = None
	prtdiag_dict['temp_pdb'] = None
	prtdiag_dict['temp_scsi'] = None

	for l in output.split('\n'):
	    inx = re.search("CPU([0-9])\s+([0-9]+)", l)
	    if inx:	# CPU temps
		prtdiag_dict['temp_cpu%s'%(inx.group(1))] = int(inx.group(2))
		continue

	    inx = re.search("MB([0-9])\s+([0-9]+)", l)
	    if inx:	# Motherboard (?) temps
		prtdiag_dict['temp_mb%s'%(inx.group(1))] = int(inx.group(2))
		continue

	    inx = re.search("PDB\s+([0-9]+)", l)
	    if inx:	# PDB ?? temps
		prtdiag_dict['temp_pdb'] = int(inx.group(1))
		continue

	    inx = re.search("SCSI\s+([0-9]+)", l)
	    if inx:	# SCSI ?? temps
		prtdiag_dict['temp_scsi'] = int(inx.group(1))
		continue

	return prtdiag_dict
		

    def parse_prtdiag_u280r(self):
	"""Parse prtdiag for a U280R."""

	prtdiag = "/usr/platform/sun4u/sbin/prtdiag"

	try:
	    os.stat( prtdiag )
	except:
	    log.log( "<solaris>PRTDIAG.parse_prtdiag_u280r(): %s not found, directive cancelled" % (prtdiag), 4 )
	    return None

	cmd = "%s -v" % (prtdiag)
	(retval, output) = utils.safe_getstatusoutput( cmd )

	# Initialise prtdiag dictionary of values
	prtdiag_dict = {}
	prtdiag_dict['temp_cpu0'] = None
	prtdiag_dict['temp_cpu1'] = None

	inx = re.search( "cpu([0-9])\s+([0-9])\s*-+\s*([0-9]+)\s+([0-9]+)", output)
	if inx:	# CPU temps
	    prtdiag_dict['temp_cpu%s'%(inx.group(1))] = int(inx.group(3))
	    prtdiag_dict['temp_cpu%s'%(inx.group(2))] = int(inx.group(4))

	return prtdiag_dict


    def parse_prtdiag_Enterprise(self):
	"""Parse prtdiag for an Enterprise class Sun server (E3500, E6500, etc)."""

	prtdiag = "/usr/platform/sun4u/sbin/prtdiag"

	try:
	    os.stat( prtdiag )
	except:
	    log.log( "<solaris>PRTDIAG.parse_prtdiag_Enterprise(): %s not found, directive cancelled" % (prtdiag), 4 )
	    return None

	cmd = "%s -v" % (prtdiag)
	(retval, output) = utils.safe_getstatusoutput( cmd )

	# Initialise prtdiag dictionary of values
	prtdiag_dict = {}
	prtdiag_dict['temp_brd0'] = None
	prtdiag_dict['temp_brd1'] = None
	prtdiag_dict['temp_brd2'] = None
	prtdiag_dict['temp_brd3'] = None
	prtdiag_dict['temp_brd4'] = None
	prtdiag_dict['temp_brd5'] = None
	prtdiag_dict['temp_brd6'] = None
	prtdiag_dict['temp_brd7'] = None
	prtdiag_dict['temp_brd8'] = None
	prtdiag_dict['temp_brd9'] = None
	prtdiag_dict['temp_brd10'] = None
	prtdiag_dict['temp_brd11'] = None
	prtdiag_dict['temp_brd12'] = None
	prtdiag_dict['temp_brd13'] = None
	prtdiag_dict['temp_brd14'] = None
	prtdiag_dict['temp_brd15'] = None
	prtdiag_dict['temp_clk'] = None

	outlist = output.split('\n')
	for i in range(0, len(outlist)):
	    if outlist[i][:19] == "System Temperatures":
		i = i + 4
		while 1:
		    if len(outlist[i]) <= 1:
			break			# finish temp parsing
		    l = outlist[i].split()
		    if l[0] == "CLK":
			prtdiag_dict['temp_clk'] = int(l[2])
		    else:
			prtdiag_dict['temp_brd%s'%l[0]] = int(l[2])
		    i = i + 1
		break

	return prtdiag_dict
		

##
## END - solaris.py
##
