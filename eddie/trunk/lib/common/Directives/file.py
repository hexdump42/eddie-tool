## 
## File		: file.py 
## 
## Author       : Chris Miles  <chris@psychofx.com>
## 
## Start Date	: 20010716
## 
## Description	: Directives for monitoring files
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
import string, os
# Imports: Eddie
import log, directive



## Directives ##


class FILE(directive.Directive):
    """FILE directive.  Examine a file statistics and perform checks on those statistics.
       Stats from previous check are kept so comparisons can be made from one scanperiod
       to the next (eg: rule='md5 != lastmd5').

       Sample rule:
       FILE passwd: file="/etc/passwd"
                    rule="size == 0"
                    action="email('alert', 'ALERT: /etc/passwd is 0 bytes')"

       Optional arguments:
	None
    """

    def __init__(self, toklist, toktypes):
	apply( directive.Directive.__init__, (self, toklist, toktypes) )

	self.lastmode = None	# keep copy of stats from last check


    def tokenparser(self, toklist, toktypes, indent):
	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.file		# filename
        except AttributeError:
            raise directive.ParseFailure, "Filename not specified"
	try:
	    self.args.rule		# rule to test
        except AttributeError:
            raise directive.ParseFailure, "Rule not specified"

	# Set variables for Actions to use
	self.Action.varDict['filefile'] = self.args.file
	self.Action.varDict['filerule'] = self.args.rule

	# define the unique ID
        if self.ID == None:
	    self.ID = '%s.FILE.%s.%s' % (log.hostname,self.args.file,self.args.rule)
	self.state.ID = self.ID

	log.log( "<file>FILE.tokenparser(): ID '%s' file '%s' rule '%s'" % (self.ID, self.args.file, self.args.rule), 8 )


    def docheck(self, Config):
	"""Stat the file and evaluate the given rule as a Python expression.
	"""

	log.log( "<file>FILE.docheck(): ID '%s' file '%s' rule '%s'" % (self.ID, self.args.file, self.args.rule), 7 )

	try:
	    s = os.stat( self.args.file )
	except OSError, err:
	    log.log( "<file>FILE.docheck(): ID '%s' OSError stat-ing file '%s': %s" % (self.ID, self.args.file, err), 4 )
	    # directive not re-scheduled

	else:
	    # Setup rule environment
	    rulesenv = {}
	    rulesenv['mode'] = s[0]
	    rulesenv['ino'] = s[1]
	    rulesenv['dev'] = s[2]
	    rulesenv['nlink'] = s[3]
	    rulesenv['uid'] = s[4]
	    rulesenv['gid'] = s[5]
	    rulesenv['size'] = s[6]
	    rulesenv['atime'] = s[7]
	    rulesenv['mtime'] = s[8]
	    rulesenv['ctime'] = s[9]
	    rulesenv['md5'] = ''

	    # md5 the file too if necessary and if md5 module available
	    if string.find(self.args.rule, 'md5') != -1:
		# rule contains 'md5', so we need to calculate it
		try:
		    import md5
		except ImportError, err:
		    # no md5 module - log error and don't re-schedule
		    log.log( "<file>FILE.docheck(): ID '%s' ImportError, md5 module needed but not available" % (self.ID, self.args.file, err), 4 )
		else:
		    fp = open(self.args.file)
		    m = md5.md5(string.join(fp.readlines(), '')).hexdigest()
		    fp.close()
		    log.log( "<file>FILE.docheck(): ID '%s' md5='%s'" % (self.ID, m), 9 )
		    rulesenv['md5'] = m

	    if self.lastmode == None:
		# if no lastxxx variables set, set them to same as current
		self.lastmode = rulesenv['mode']
		self.lastino = rulesenv['ino']
		self.lastdev = rulesenv['dev']
		self.lastnlink = rulesenv['nlink']
		self.lastuid = rulesenv['uid']
		self.lastgid = rulesenv['gid']
		self.lastsize = rulesenv['size']
		self.lastatime = rulesenv['atime']
		self.lastmtime = rulesenv['mtime']
		self.lastctime = rulesenv['ctime']
		self.lastmd5 = rulesenv['md5']

	    rulesenv['lastmode'] = self.lastmode
	    rulesenv['lastino'] = self.lastino
	    rulesenv['lastdev'] = self.lastdev
	    rulesenv['lastnlink'] = self.lastnlink
	    rulesenv['lastuid'] = self.lastuid
	    rulesenv['lastgid'] = self.lastgid
	    rulesenv['lastsize'] = self.lastsize
	    rulesenv['lastatime'] = self.lastatime
	    rulesenv['lastmtime'] = self.lastmtime
	    rulesenv['lastctime'] = self.lastctime
	    rulesenv['lastmd5'] = self.lastmd5

	    # Evaluate rule
	    result = eval( self.args.rule, rulesenv )

	    # assign variables for Actions
	    self.Action.varDict['filemode'] = rulesenv['mode']
	    self.Action.varDict['fileino'] = rulesenv['ino']
	    self.Action.varDict['filedev'] = rulesenv['dev']
	    self.Action.varDict['filenlink'] = rulesenv['nlink']
	    self.Action.varDict['fileuid'] = rulesenv['uid']
	    self.Action.varDict['filegid'] = rulesenv['gid']
	    self.Action.varDict['filesize'] = rulesenv['size']
	    self.Action.varDict['fileatime'] = rulesenv['atime']
	    self.Action.varDict['filemtime'] = rulesenv['mtime']
	    self.Action.varDict['filectime'] = rulesenv['ctime']
	    self.Action.varDict['filemd5'] = rulesenv['md5']
	    self.Action.varDict['filelastmode'] = rulesenv['lastmode']
	    self.Action.varDict['filelastino'] = rulesenv['lastino']
	    self.Action.varDict['filelastdev'] = rulesenv['lastdev']
	    self.Action.varDict['filelastnlink'] = rulesenv['lastnlink']
	    self.Action.varDict['filelastuid'] = rulesenv['lastuid']
	    self.Action.varDict['filelastgid'] = rulesenv['lastgid']
	    self.Action.varDict['filelastsize'] = rulesenv['lastsize']
	    self.Action.varDict['filelastatime'] = rulesenv['lastatime']
	    self.Action.varDict['filelastmtime'] = rulesenv['lastmtime']
	    self.Action.varDict['filelastctime'] = rulesenv['lastctime']
	    self.Action.varDict['filelastmd5'] = rulesenv['lastmd5']

	    log.log( "<logscanning>LOGSCAN.docheck(): ID '%s' rule result=%d" % (self.ID, result), 7 )

	    if result == 0:
		self.state.stateok(Config)	# reset state info
	    else:
		self.state.statefail()	# set state to fail before calling doAction()
		self.doAction(Config)

	    # save variables for next time
	    self.lastmode = rulesenv['mode']
	    self.lastino = rulesenv['ino']
	    self.lastdev = rulesenv['dev']
	    self.lastnlink = rulesenv['nlink']
	    self.lastuid = rulesenv['uid']
	    self.lastgid = rulesenv['gid']
	    self.lastsize = rulesenv['size']
	    self.lastatime = rulesenv['atime']
	    self.lastmtime = rulesenv['mtime']
	    self.lastctime = rulesenv['ctime']
	    self.lastmd5 = rulesenv['md5']

	    self.putInQueue( Config.q )     # put self back in the Queue



##
## END - file.py
##
