## 
## File		: logscanning.py 
## 
## Author       : Chris Miles  <cmiles@codefx.com.au>
## 
## Date		: 20010529
## 
## Description	: Directives for scanning logfiles
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
import re, string, os
# Imports: Eddie
import log, directive



## Directives ##


class LOGSCAN(directive.Directive):
    """LOGSCAN directive.  Scan a file looking for regex matches.

       Sample rule:
       LOGSCAN messages: file="/var/log/messages"
                         regex=".*error.*"
                         action="email('alert', 'Log match', '%(logscanmatch)s')"

       Optional arguments:
	negate=true	# only lines NOT matching regex will cause action
    """

    def __init__(self, toklist, toktypes):
	apply( directive.Directive.__init__, (self, toklist, toktypes) )

	self.filepos = 0	# position in file saved between checks
	self.filestat = None	# stat of log file


    def tokenparser(self, toklist, toktypes, indent):
	apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

	# test required arguments
	try:
	    self.args.file		# filename
        except AttributeError:
            raise directive.ParseFailure, "Filename not specified"
	try:
	    self.args.regex		# regular expression
        except AttributeError:
            raise directive.ParseFailure, "Regex not specified"

	try:
	    self.args.negate		# whether to negate rule
	    if self.args.negate == '1' or self.args.negate == 'true' or self.args.negate == 'on':
		self.args.negate = 1
	    elif self.args.negate == '0' or self.args.negate == 'false' or self.args.negate == 'off':
		self.args.negate = 0
	    else:
		raise directive.ParseFailure, "Unknown argument '%s' to negate option" % (self.args.negate)
        except AttributeError:
            self.args.negate=0

	# Set variables for Actions to use
	self.Action.varDict['logscanfile'] = self.args.file
	self.Action.varDict['logscanregex'] = self.args.regex
	self.Action.varDict['logscannegate'] = self.args.negate

	# define the unique ID
        if self.ID == None:
	    self.ID = '%s.LOGSCAN.%s.%s' % (log.hostname,self.args.file,self.args.regex)
	self.state.ID = self.ID

	log.log( "<logscanning>LOGSCAN.tokenparser(): ID '%s' file '%s' regex '%s'" % (self.ID, self.args.file, self.args.regex), 8 )


    def docheck(self, Config):
	"""The check is to read the specified file and save any lines
        which match the given regular expression.  Only lines which
        are new to the file since the last check are examined.
	"""

	log.log( "<logscanning>LOGSCAN.docheck(): ID '%s' file '%s' regex '%s'" % (self.ID, self.args.file, self.args.regex), 7 )

	try:
	    s = os.stat( self.args.file )
	except OSError, err:
	    log.log( "<logscanning>LOGSCAN.docheck(): ID '%s' OSError stat-ing file '%s': %s" % (self.ID, self.args.file, err), 3 )
	else:
	    if self.filestat == None:
		# Haven't read file before so jump to EOF and save state
		# for next check
		self.filestat = s
		self.filepos = s[6]

	    else:
		if s[6] < self.filestat[6]:
		    # file has been truncated, read from start of file
		    self.filestat = s
		    self.filepos = 0

		sre = re.compile( self.args.regex )
		matchedlines = []

		try:
		    fp = open( self.args.file, 'r' )
		except IOError:
		    e = sys.exc_info()
		    log.log( "<logscanning>LOGSCAN.docheck(): ID '%s' IOError opening file '%s': %s, %s" % (self.ID, self.args.file, e[0], e[1]), 3 )

		else:
		    if self.filepos > 0:
			fp.seek(self.filepos)	# jump to last position in file
			line = fp.readline()
#			if len(line) == 0:		# already at EOF
#			    fp.seek(0)		# jump to start-of-file
#			    line = fp.readline()

		    else:
			line = fp.readline()

		    while len(line) > 0:
			inx = sre.match( line )
			if (inx and not self.args.negate) or (not inx and self.args.negate):
			    matchedlines.append( line )
			line = fp.readline()

		    # remember position of EOF so we can jump here next time
		    self.filepos = fp.tell()

		    fp.close()
		    matchedcount = len(matchedlines)

		    # assign variables
		    self.Action.varDict['logscanlines'] = string.join(matchedlines, "")
		    self.Action.varDict['logscanlinecount'] = matchedcount

		    log.log( "<logscanning>LOGSCAN.docheck(): matchedlinecount=%d" % (matchedcount), 8 )

		    if matchedcount > 0:
			self.state.statefail()	# set state to fail before calling doAction()
			self.doAction(Config)
		    else:
			self.state.stateok(Config)	# reset state info

        self.putInQueue( Config.q )     # put self back in the Queue



##
## END - logscanning.py
##
