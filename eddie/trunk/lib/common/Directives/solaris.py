## 
## File		: solaris.py 
## 
## Author       : Chris Miles  <cmiles@codefx.com.au>
## 
## Date		: 20000615
## 
## Description	: Directives for standard Solaris checks
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
import sys, os, time, re
# Imports: Eddie
import log, directive, utils




class CRON(directive.Directive):
    """An Eddie directive for checking that cron is working.
	A cron job should be setup to touch the test file at least as often
	as the CRON check will be performed.  This directive simply checks
	that the file has been touched (modified) within the last 15 minutes,
	implying that cron is running properly.

	Eg:
	CRON: file="/tmp/cron.touch" rule="!alive" action="email('alert', 'cron alive check failed on %(h)s')"
    """

    def __init__(self, toklist, toktypes):
	apply( directive.Directive.__init__, (self, toklist, toktypes) )


    def tokenparser(self, toklist, toktypes, indent):
	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.file		# test file touched by cronjob
	except AttributeError:
	    raise directive.ParseFailure, "Test File not specified"
	try:
	    self.args.rule		# the rule
	except AttributeError:
	    raise directive.ParseFailure, "Rule not specified"

	# Set any FS-specific variables
	#  rule = rule
	self.Action.varDict['rule'] = self.args.rule

	# define the unique ID
        if self.ID == None:
	    self.ID = '%s.CRON.%s' % (log.hostname,self.args.rule)
	self.state.ID = self.ID

	log.log( "<solaris>CRON.tokenparser(): ID '%s' rule '%s' action '%s'" % (self.ID, self.args.rule, self.args.actionList), 8 )


    def docheck(self, Config):
	log.log( "<solaris>CRON.docheck(): rule '%s'" % (self.args.rule), 7 )

	from stat import *				# for ST_MTIME
	try:
	    mtime = os.stat( self.args.file )[ST_MTIME]
	except OSError, detail:
    	    log.log( "<solaris>CRON.docheck(): stat had error %d, '%s'" % (detail[0], detail[1]), 6 )
	    return

	import time
	now = time.time()

	if now - mtime > 60 * 15:
	    # if file not touched within the last 15 minutes (safety factor
	    # assuming checks and touches every 10 minutes) then fail check

	    self.state.statefail()	# update state info for check failed

	    # assign variables
	    self.Action.varDict['cronfile'] = self.args.file
	    self.Action.varDict['cronfilemtime'] = str(mtime)

    	    log.log( "<solaris>CRON.docheck(): check failed, calling doAction()", 6 )
    	    self.doAction(Config)

	else:
	    self.state.stateok(Config)	# update state info for check passed

        self.putInQueue( Config.q )     # put self back in the Queue




class METASTAT(directive.Directive):
    """Solaris Disksuite checks for bad metadevices/disks.
	This directive only currently checks for any devices that require
	'Maintenance' from the metastat output.
	TODO: parse metastat output better and report the actual device
	that is having the problem.

	Eg:
	METASTAT: action="email('alert', 'A metadevice requires maintenance on %(h)s.')"
    """

    def __init__(self, toklist, toktypes):
	apply( directive.Directive.__init__, (self, toklist, toktypes) )


    def tokenparser(self, toklist, toktypes, indent):
	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	## nothing but action so far! (Already tested in Directive.tokenparser())


	# Set any FS-specific variables
	#  rule = rule

	# define the unique ID
        if self.ID == None:
	    self.ID = '%s.METASTAT' % (log.hostname)
	self.state.ID = self.ID

	log.log( "<solaris>METASTAT.tokenparser(): ID '%s' action '%s'" % (self.ID, self.args.actionList), 8 )


    def docheck(self, Config):
	log.log( "<solaris>METASTAT.docheck(): ", 7 )
	metastat = "/usr/opt/SUNWmd/sbin/metastat"

	try:
	    os.stat( metastat )
	except:
	    log.log( "<solaris>METASTAT.docheck(): %s not found, directive cancelled" % (metastat), 4 )
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

		self.state.statefail()	# update state info for check failed

		# assign variables
		self.Action.varDict['metastatmaintcnt'] = int(result)

		log.log( "<solaris>METASTAT.docheck(): check failed, calling doAction()", 6 )
		self.doAction(Config)

	    else:
		self.state.stateok(Config)	# update state info for check passed

            self.putInQueue( Config.q )     # put self back in the Queue


class PRTDIAG(directive.Directive):
    """Solaris checks using prtdiag output.
	Currently only supports AMBIENT and CPU temperatures.
	TODO: parse rest of prtdiag.

	Eg:
	PRTDIAG: rule="temp_ambient > 40"
                 action="email('alert', 'Ambient temperature on %(h)s is %(PRTDIAG_temp_ambient)s.')"
    """

    def __init__(self, toklist, toktypes):
	apply( directive.Directive.__init__, (self, toklist, toktypes) )


    def tokenparser(self, toklist, toktypes, indent):
	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.rule		# the rule
	except AttributeError:
	    raise directive.ParseFailure, "Rule not specified"

	# Set any PRTDIAG-specific variables
	self.Action.varDict['rule'] = self.args.rule

	# define the unique ID
        if self.ID == None:
	    self.ID = '%s.PRTDIAG' % (log.hostname)
	self.state.ID = self.ID

	log.log( "<solaris>PRTDIAG.tokenparser(): ID '%s' rule '%s' action '%s'" % (self.ID, self.args.rule, self.args.actionList), 8 )


    def docheck(self, Config):
	log.log( "<solaris>PRTDIAG.docheck(): ", 7 )

	# Determine system type and parse system-specific output
	cmd = "/usr/bin/uname -i"
	(retval, output) = utils.safe_getstatusoutput( cmd )
	if output == "SUNW,Ultra-4":
	    prtdiag_dict = self.parse_prtdiag_u450()
	elif output == "SUNW,Ultra-250":
	    prtdiag_dict = self.parse_prtdiag_u250()
	else:
	    log.log( "<solaris>PRTDIAG.docheck(): system type %s not supported yet, directive cancelled" % (output), 4 )

	if prtdiag_dict == None:	# there was an error, just exit
	    return

	rulesenv = {}
	rulesenv.update(prtdiag_dict)

	# Evaluate rule
	result = eval( self.args.rule, rulesenv )

	if result:
	    self.state.statefail()	# update state info for check failed

	    # assign variables
	    for i in prtdiag_dict.keys():
		self.Action.varDict['PRTDIAG_%s'%(i)] = prtdiag_dict[i]

	    log.log( "<solaris>PRTDIAG.docheck(): check failed, calling doAction()", 6 )
	    self.doAction(Config)

	else:
	    self.state.stateok(Config)	# update state info for check passed

	self.putInQueue( Config.q )     # put self back in the Queue


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
		


##
## END - solaris.py
##
