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
import sys, os, commands
# Imports: Eddie
import log, directive, utils




class CRON(directive.Directive):
    def __init__(self, toklist):
	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):

	self.touchfile = utils.stripquote(toklist[0])	# test file touched by cronjob
	self.rule = utils.stripquote(toklist[1])	# the rule
	self.actionList = self.parseAction(toklist[2:])

	# Set any FS-specific variables
	#  rule = rule
	self.Action.varDict['rule'] = self.rule

	# define the unique ID
	self.ID = '%s.CRON.%s' % (log.hostname,self.rule)

	log.log( "<solaris.py>CRON.tokenparser(): ID '%s' rule '%s' action '%s'" % (self.ID, self.rule, self.actionList), 8 )


    def docheck(self, Config):
	log.log( "<solaris.py>CRON.docheck(): rule '%s'" % (self.rule), 7 )

	from stat import *				# for ST_MTIME
	try:
	    mtime = os.stat( self.touchfile )[ST_MTIME]
	except OSError, detail:
    	    log.log( "<solaris.py>CRON.docheck(): stat had error %d, '%s'" % (detail[0], detail[1]), 6 )
	    return

	import time
	now = time.time()

	if now - mtime > 60 * 15:
	    # if file not touched within the last 15 minutes (safety factor
	    # assuming checks and touches every 10 minutes) then fail check

	    self.statefail()	# update state info for check failed

	    # assign variables
	    self.Action.varDict['crontouchfile'] = self.touchfile
	    self.Action.varDict['crontouchfilemtime'] = str(mtime)

    	    log.log( "<solaris.py>CRON.docheck(): check failed, calling doAction()", 6 )
    	    self.doAction(Config)

	else:
	    self.stateok()	# update state info for check passed


class METASTAT(directive.Directive):
    """Solaris Disksuite checks for bad metadevices/disks."""

    def __init__(self, toklist):
	apply( directive.Directive.__init__, (self, toklist) )


    def tokenparser(self, toklist, toktypes, indent):

	self.actionList = self.parseAction(toklist[0:])

	# Set any FS-specific variables
	#  rule = rule

	# define the unique ID
	self.ID = '%s.METASTAT' % (log.hostname)

	log.log( "<solaris.py>METASTAT.tokenparser(): ID '%s' action '%s'" % (self.ID, self.actionList), 8 )


    def docheck(self, Config):
	log.log( "<solaris.py>METASTAT.docheck(): ", 7 )
	metastat = "/usr/opt/SUNWmd/sbin/metastat"

	try:
	    os.stat( metastat )
	except:
	    log.log( "<solaris.py>METASTAT.docheck(): %s not found, skipping check" % (metastat), 7 )
	else:
	    # metastat exists, so check for anything requiring Maintenance

	    cmd = "%s | /usr/bin/grep -i maint | /usr/bin/wc -l" % (metastat)
	    result = commands.getoutput( cmd )
	    if int(result) > 0:
		# something requires Maintenance

		self.statefail()	# update state info for check failed

		# assign variables
		self.Action.varDict['metastatmaintcnt'] = int(result)

		log.log( "<solaris.py>METASTAT.docheck(): check failed, calling doAction()", 6 )
		self.doAction(Config)

	    else:
		self.stateok()	# update state info for check passed


##
## END - solaris.py
##
