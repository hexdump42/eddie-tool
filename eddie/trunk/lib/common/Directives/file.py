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
## (C) Chris Miles 2001-2005
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


"""
Implements the FILE directive for Eddie.
FILE provides a mechanism to monitor files, testing for changes to
files.

doctest:

>>> f = FILE( ('FILE', 'filetest', ':' ) )
>>> f
filetest
>>> f.tokenparser( (('file', '=', "'file.py'"), ('rule','=',"'exists'"), ('scanperiod', '=', 1)), None, None )
>>> f
filetest
>>> f.args.file
'file.py'
>>> f.args.rule
'exists'

"""


# Imports: Python
import string
import os
import time
import sys

sys.path.append('..')	# for Eddie common modules

# Imports: Eddie
import log
import directive


##
## Directives ##
##


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

    def __init__(self, toklist):
	apply( directive.Directive.__init__, (self, toklist) )

	self.lastmode = None	# keep copy of stats from last check


    def tokenparser(self, toklist, toktypes, indent):
	"""Parse directive arguments.
	"""

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
	self.defaultVarDict['file'] = self.args.file
	self.defaultVarDict['rule'] = self.args.rule

	# define the unique ID
        if self.ID == None:
	    self.ID = '%s.FILE.%s.%s' % (log.hostname,self.args.file,self.args.rule)
	self.state.ID = self.ID

	log.log( "<file>FILE.tokenparser(): ID '%s' file '%s' rule '%s'" % (self.ID, self.args.file, self.args.rule), 8 )


    def getData(self):
	"""Called by Directive docheck() method to fetch the data required for
	evaluating the directive rule.
	"""

	# Initialize the data
	data = {}
	data['exists'] = None
	data['mode'] = None
	data['ino'] = None
	data['dev'] = None
	data['nlink'] = None
	data['uid'] = None
	data['gid'] = None
	data['size'] = None
	data['atime'] = None
	data['mtime'] = None
	data['ctime'] = None
	data['md5'] = None
	data['perm'] = None
	data['sticky'] = None
	data['type'] = None
	data['issocket'] = None
	data['issymlink'] = None
	data['isfile'] = None
	data['isblockdevice'] = None
	data['isdir'] = None
	data['ischardevice'] = None
	data['isfifo'] = None
	data['now'] = None

	data['lastmode'] = None
	data['lastino'] = None
	data['lastdev'] = None
	data['lastnlink'] = None
	data['lastuid'] = None
	data['lastgid'] = None
	data['lastsize'] = None
	data['lastatime'] = None
	data['lastmtime'] = None
	data['lastctime'] = None
	data['lastmd5'] = None
	data['lastperm'] = None
	data['laststicky'] = None
	data['lasttype'] = None
	data['lastissocket'] = None
	data['lastissymlink'] = None
	data['lastisfile'] = None
	data['lastisblockdevice'] = None
	data['lastisdir'] = None
	data['lastischardevice'] = None
	data['lastisfifo'] = None

	data['now'] = time.time()	# get current time for comparing with file times

	if os.path.exists( self.args.file ):
	    data['exists'] = 1		# true
	else:
	    data['exists'] = 0		# false
	    return data			# cannot check anything else

	try:
	    s = os.stat( self.args.file )
	except IOError, err:
	    log.log( "<file>FILE.getData(): ID '%s' IOError stat-ing file '%s': %s" % (self.ID, self.args.file, err), 4 )
	    raise directive.DirectiveError, "IOError stat-ing file '%s': %s" % (self.args.file, err)
	else:
	    data['mode'] = s[0]
	    data['ino'] = s[1]
	    data['dev'] = s[2]
	    data['nlink'] = s[3]
	    data['uid'] = s[4]
	    data['gid'] = s[5]
	    data['size'] = s[6]
	    data['atime'] = s[7]
	    data['mtime'] = s[8]
	    data['ctime'] = s[9]
	    data['md5'] = ''
	    data['perm'] = s[0] & 0777		# extract permission bits only
	    data['sticky'] = (s[0] & 07000) >>9	# extract sticky/setuid/setgid bits only
	    data['type'] = (s[0] & 0170000) >>12 # extract file type bits only
	    # shorthand isfile booleans
	    data['issocket'] = data['type'] & 014 == 014
	    data['issymlink'] = data['type'] & 012 == 012
	    data['isfile'] = data['type'] & 010 == 010
	    data['isblockdevice'] = data['type'] & 006 == 006
	    data['isdir'] = data['type'] & 004 == 004
	    data['ischardevice'] = data['type'] & 002 == 002
	    data['isfifo'] = data['type'] & 001 == 001

	    # md5 the file too if necessary and if md5 module available
	    if string.find(self.args.rule, 'md5') != -1:
		# rule contains 'md5', so we need to calculate it
		try:
		    import md5
		except ImportError, err:
		    # no md5 module - log error and don't re-schedule
		    log.log( "<file>FILE.getData(): ID '%s' ImportError, md5 module needed but not available" % (self.ID), 4 )
		    raise directive.DirectiveError, "ImportError, md5 module needed but not available"
		else:
		    try:
			fp = open(self.args.file)
		    except IOError, err:
			log.log( "<file>FILE.getData(): ID '%s' IOError reading file '%s': %s" % (self.ID, self.args.file, err), 4 )
			raise directive.DirectiveError, "IOError reading file '%s': %s" % (self.args.file, err)

		    m = md5.md5(fp.read()).hexdigest()
		    fp.close()
		    log.log( "<file>FILE.getData(): ID '%s' md5='%s'" % (self.ID, m), 9 )
		    data['md5'] = m

	    if self.lastmode == None:
		# if no lastxxx variables set, set them to same as current
		self.lastmode = data['mode']
		self.lastino = data['ino']
		self.lastdev = data['dev']
		self.lastnlink = data['nlink']
		self.lastuid = data['uid']
		self.lastgid = data['gid']
		self.lastsize = data['size']
		self.lastatime = data['atime']
		self.lastmtime = data['mtime']
		self.lastctime = data['ctime']
		self.lastmd5 = data['md5']
		self.lastperm = data['perm']
		self.laststicky = data['sticky']
		self.lasttype = data['type']
		self.lastissocket = data['issocket']
		self.lastissymlink = data['issymlink']
		self.lastisfile = data['isfile']
		self.lastisblockdevice = data['isblockdevice']
		self.lastisdir = data['isdir']
		self.lastischardevice = data['ischardevice']
		self.lastisfifo = data['isfifo']

	    data['lastmode'] = self.lastmode
	    data['lastino'] = self.lastino
	    data['lastdev'] = self.lastdev
	    data['lastnlink'] = self.lastnlink
	    data['lastuid'] = self.lastuid
	    data['lastgid'] = self.lastgid
	    data['lastsize'] = self.lastsize
	    data['lastatime'] = self.lastatime
	    data['lastmtime'] = self.lastmtime
	    data['lastctime'] = self.lastctime
	    data['lastmd5'] = self.lastmd5
	    data['lastperm'] = self.lastperm
	    data['laststicky'] = self.laststicky
	    data['lasttype'] = self.lasttype
	    data['lastissocket'] = self.lastissocket
	    data['lastissymlink'] = self.lastissymlink
	    data['lastisfile'] = self.lastisfile
	    data['lastisblockdevice'] = self.lastisblockdevice
	    data['lastisdir'] = self.lastisdir
	    data['lastischardevice'] = self.lastischardevice
	    data['lastisfifo'] = self.lastisfifo

	    return data


    def postAction(self, data):
	"""Work that needs to be done after the actions are called.
	"""

	# save variables for next time (if they were collected)
	if 'mode' in data.keys():
	    self.lastmode = data['mode']
	    self.lastino = data['ino']
	    self.lastdev = data['dev']
	    self.lastnlink = data['nlink']
	    self.lastuid = data['uid']
	    self.lastgid = data['gid']
	    self.lastsize = data['size']
	    self.lastatime = data['atime']
	    self.lastmtime = data['mtime']
	    self.lastctime = data['ctime']
	    self.lastmd5 = data['md5']
	    self.lastperm = data['perm']
	    self.laststicky = data['sticky']
	    self.lasttype = data['type']
	    self.lastissocket = data['issocket']
	    self.lastissymlink = data['issymlink']
	    self.lastisfile = data['isfile']
	    self.lastisblockdevice = data['isblockdevice']
	    self.lastisdir = data['isdir']
	    self.lastischardevice = data['ischardevice']
	    self.lastisfifo = data['isfifo']


## doctest:
def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()


##
## END - file.py
##
