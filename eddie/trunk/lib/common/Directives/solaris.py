## 
## File		: solaris.py 
## 
## Author       : Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 20000615
## 
## Description	: Directives for standard Solaris checks
##
## $Id$
##
##


# Imports: Python
import sys, os, commands, time
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

    def __init__(self, toklist):
	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.file		# test file touched by cronjob
	except AttributeError:
	    raise ParseFailure, "Test File not specified"
	try:
	    self.args.rule		# the rule
	except AttributeError:
	    raise ParseFailure, "Rule not specified"

	# Set any FS-specific variables
	#  rule = rule
	self.Action.varDict['rule'] = self.args.rule

	# define the unique ID
	self.ID = '%s.CRON.%s' % (log.hostname,self.args.rule)

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
	    self.state.stateok()	# update state info for check passed

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

    def __init__(self, toklist):
	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):
	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	## nothing but action so far! (Already tested in Directive.tokenparser())


	# Set any FS-specific variables
	#  rule = rule

	# define the unique ID
	self.ID = '%s.METASTAT' % (log.hostname)

	log.log( "<solaris>METASTAT.tokenparser(): ID '%s' action '%s'" % (self.ID, self.args.actionList), 8 )


    def docheck(self, Config):
	log.log( "<solaris>METASTAT.docheck(): ", 7 )
	metastat = "/usr/opt/SUNWmd/sbin/metastat"

	try:
	    os.stat( metastat )
	except:
	    log.log( "<solaris>METASTAT.docheck(): %s not found, skipping check" % (metastat), 7 )
	else:
	    # metastat exists, so check for anything requiring Maintenance

	    cmd = "%s | /usr/bin/grep -i maint | /usr/bin/wc -l" % (metastat)
	    result = commands.getoutput( cmd )
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
		self.state.stateok()	# update state info for check passed

        self.putInQueue( Config.q )     # put self back in the Queue


##
## END - solaris.py
##
