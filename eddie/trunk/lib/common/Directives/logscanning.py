## 
## File		: logscanning.py 
## 
## Author       : Chris Miles  <chris@psychofx.com>
## 
## Start Date	: 20010529
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
import sys
import os
import string
import re
# Imports: Eddie
import directive
import log


##
## Directives
##

class LOGSCAN(directive.Directive):
    """LOGSCAN directive.  Scan a file looking for regex matches.

    Sample rule:
       LOGSCAN messages: file="/var/log/messages"
                         regex=".*error.*"
			 rule='linecount > 0'
                         action="email('alert', 'Log matched %(linecount)d lines', '%(lines)s')"

    Optional arguments:
	negate=true		# only lines NOT matching regex will cause action
	rule=<rule string>	# defaults to 'linecount > 0' if not specified
    """

    def __init__(self, toklist):
	apply( directive.Directive.__init__, (self, toklist) )

	self.filepos = 0	# position in file saved between checks
	self.filestat = None	# stat of log file


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

	# Default rule for this directive
	try:
	    self.args.rule
	except AttributeError:
	    self.args.rule = "linecount > 0"		# default rule

	# Set variables for Actions to use
	self.defaultVarDict['file'] = self.args.file
	self.defaultVarDict['regex'] = self.args.regex
	self.defaultVarDict['negate'] = self.args.negate
	self.defaultVarDict['rule'] = self.args.rule

	# define the unique ID
        if self.ID == None:
	    self.ID = '%s.LOGSCAN.%s.%s' % (log.hostname,self.args.file,self.args.regex)
	self.state.ID = self.ID

	log.log( "<logscanning>LOGSCAN.tokenparser(): ID '%s' file '%s' regex '%s'" % (self.ID, self.args.file, self.args.regex), 8 )


    def getData(self):
	"""Called by Directive docheck() method to fetch the data required for
	evaluating the directive rule.

	The check is to read the specified file and save any lines
        which match the given regular expression.  Only lines which
        are new to the file since the last check are examined.
	"""

	data = {}
	data['lines'] = ""
	data['linecount'] = 0

	try:
	    s = os.stat( self.args.file )
	except OSError, err:
	    log.log( "<logscanning>LOGSCAN.docheck(): ID '%s' OSError stat-ing file '%s': %s" % (self.ID, self.args.file, err), 5 )
	    raise directive.DirectiveError, "OSError stat-ing file '%s': %s" % (self.args.file, err)

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
		    log.log( "<logscanning>LOGSCAN.docheck(): ID '%s' IOError opening file '%s': %s, %s" % (self.ID, self.args.file, e[0], e[1]), 5 )
		    raise directive.DirectiveError, "IOError opening file '%s': %s, %s" % (self.args.file, e[0], e[1])

		else:
		    if self.filepos > 0:
			fp.seek(self.filepos)	# jump to last position in file
			line = fp.readline()

		    else:
			line = fp.readline()

		    while len(line) > 0:
			inx = sre.search( line )
			if (inx and not self.args.negate) or (not inx and self.args.negate):
			    matchedlines.append( line )
			line = fp.readline()

		    # remember position of EOF so we can jump here next time
		    self.filepos = fp.tell()

		    fp.close()
		    matchedcount = len(matchedlines)

		    # assign variables
		    data['lines'] = string.join(matchedlines, "")
		    data['linecount'] = matchedcount

	return data



##
## END - logscanning.py
##
