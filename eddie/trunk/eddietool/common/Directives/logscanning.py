
'''
File                : logscanning.py 

Start Date        : 20010529

Description        : Directives for scanning logfiles

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 2001-2005'

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



# Imports: Python
import sys
import os
import string
import re
# Imports: Eddie
from eddietool.common import directive, log


##
## Directives
##

class LOGSCAN(directive.Directive):
    """LOGSCAN directive.  Scan a file looking for regex matches.

    Sample rule:
       LOGSCAN messages: file="/var/log/messages"
                         regex=".*error.*"
                         rule='matchedcount > 0'
                         action="email('alert', 'Log matched %(matchedcount)d lines', '%(lines)s')"

    Optional arguments:
        negate=true                # only lines NOT matching regex will cause action
        rule=<rule string>        # defaults to 'matchedcount > 0' if not specified
    """

    def __init__(self, toklist):
        apply( directive.Directive.__init__, (self, toklist) )

        self.filepos = 0        # position in file saved between checks
        self.filestat = None        # stat of log file
        self.reglist = []
        self.regfile = None

    def tokenparser(self, toklist, toktypes, indent):
        """Parse directive arguments.
        """

        apply( directive.Directive.tokenparser, (self, toklist, toktypes, indent) )

        # test required arguments
        try:
            self.args.file                # filename
        except AttributeError:
            raise directive.ParseFailure, "Filename not specified"

        if not hasattr(self.args, 'regex') and not hasattr(self.args, 'regfile'):
            raise directive.ParseFailure, "Regex or regfile required"

        if hasattr(self.args, 'regfile'):
            self.defaultVarDict['regfile'] = self.args.regfile
            self.regfile = self.args.regfile
            try:
                f = open(self.args.regfile)
                data = f.readlines()
                f.close()
            except IOError, err:
                    raise directive.DirectiveError, "Couldn't process %s: %s" % (self.args.regfile, str(err))

            for i in data:
                    self.reglist.append(re.compile(i.strip()))

        if hasattr(self.args, 'regex'):
            self.reglist = [re.compile(self.args.regex)]
            self.defaultVarDict['regex'] = self.args.regex

        try:
            self.args.negate                # whether to negate rule
            if self.args.negate == '1' or self.args.negate == 'true' or self.args.negate == 'on':
                self.args.negate = 1
            elif self.args.negate == '0' or self.args.negate == 'false' or self.args.negate == 'off':
                self.args.negate = 0
            else:
                raise directive.ParseFailure, "Unknown argument '%s' to negate option" % (self.args.negate)
        except AttributeError:
            self.args.negate = 0

        # Default rule for this directive
        try:
            self.args.rule
        except AttributeError:
            self.args.rule = "matchedcount > 0"                # default rule

        # Set variables for Actions to use
        self.defaultVarDict['file'] = self.args.file
        self.defaultVarDict['negate'] = self.args.negate
        self.defaultVarDict['rule'] = self.args.rule

        # define the unique ID
        if self.ID == None:
            if self.regfile:
                self.ID = '%s.LOGSCAN.%s.%s' % (log.hostname,self.args.file,self.args.regfile)
            else:
                self.ID = '%s.LOGSCAN.%s.%s' % (log.hostname,self.args.file,self.args.regex)
        self.state.ID = self.ID

        if self.regfile:
            log.log( "<logscanning>LOGSCAN.tokenparser(): ID '%s' file '%s' regfile '%s' reglist %d records" % (self.ID, self.args.file, self.args.regfile, len(self.reglist)), 7 )
        else:
            log.log( "<logscanning>LOGSCAN.tokenparser(): ID '%s' file '%s' regex '%s'" % (self.ID, self.args.file, self.args.regex), 7 )


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
        data['unmatchedcount'] = 0
        data['matchedcount'] = 0

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
                if s[6] < self.filestat[6] or s[1] != self.filestat[1]:
                    # file has been truncated or inode number changed: read from start of file
                    self.filestat = s
                    self.filepos = 0

                matchedlines = []

                try:
                    fp = open( self.args.file, 'r' )
                except IOError:
                    e = sys.exc_info()
                    log.log( "<logscanning>LOGSCAN.docheck(): ID '%s' IOError opening file '%s': %s, %s" % (self.ID, self.args.file, e[0], e[1]), 5 )
                    raise directive.DirectiveError, "IOError opening file '%s': %s, %s" % (self.args.file, e[0], e[1])

                else:
                    if self.filepos > 0:
                        fp.seek(self.filepos)        # jump to last position in file
                        line = fp.readline()

                    else:
                        line = fp.readline()

                    while len(line) > 0:
                        data['linecount'] = data['linecount'] + 1
                        matched = 0
                        for i in self.reglist:
                            inx = i.search( line )
                            if inx:
                                data['matchedcount'] = data['matchedcount'] + 1
                                matched = 1
                                if not self.args.negate:
                                    matchedlines.append( line )
                                break
                        if not matched:
                            data['unmatchedcount'] = data['unmatchedcount'] + 1
                            if self.args.negate:
                                matchedlines.append( line )

                        line = fp.readline()

                    # remember position of EOF so we can jump here next time
                    self.filepos = fp.tell()

                    fp.close()
                    matchedcount = len(matchedlines)

                    # assign variables
                    data['lines'] = string.join(matchedlines, "")

        return data

##
## END - logscanning.py
##
