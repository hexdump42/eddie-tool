
'''
File            : parseConfig.py 

Start Date      : 19971204 

Description     : Parses Eddie configuration files

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 1997-2005'

__author__ = 'Chris Miles; Rod Telford'

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


# Python specific modules
import sys, os, string, tokenize
# Eddie specific modules
import config, log, utils


#### Exceptions ####

class ConfigError(Exception):
    pass



#### Classes ####

class State:
    """Keep state of tokenization as config is being parsed."""

    def __init__(self, Config):
        self.groupStack = utils.Stack()        # Stack to store groups on temporarily
        self.direcStack = utils.Stack()        # Stack to store direcs on temporarily
        self.direcStack.push(Config)
        self.Config = Config

        self.indent = 0                # Indentation level
        self.direc = None        # current directive

        self.reset()


    # Reset state
    def reset(self):
        self.toklist = []        # clear token list
        self.toktypes = []        # clear token types list
        self.direcmode = 0        # whether currently parsing directive arguments
        self.direcindent = 0        # indent level of directive definition
        self.direcargs = []        # current directive arguments
        self.directypes = []        # current directive arguments (types)
        self.notfirstdirecline = 0        # first directive line marker


    def tokeneater(self, ttype, token, (srow, scol), (erow, ecol), line):
        """Eddie's token eater!
           Parses the tokens given to it (from tokenize.tokenize()) and uses them
           to create the configuration information."""

        try:
            #DEBUG
            #print " "
            #print "direcmode:",self.direcmode
            #print "direcindent:",self.direcindent
            #print "indent:",self.indent
            #print "notfirstdirecline:",self.notfirstdirecline

            # The type of token
            toktype = tokenize.tok_name[ttype]

            #DEBUG:
            #print "%d,%d-%d,%d:\t%s\t%s" % \
            #    (srow, scol, erow, ecol, toktype, repr(token))

            # Don't care about single CRs (empty lines) so skip over them
            if token == '\012' and len(self.toklist) == 0:
                return

            # Handle indentation/dedentations...
            if toktype == "INDENT":
                self.indent = self.indent + 1
                if self.direcmode == 0:                        # if not waiting for directive args:
                    self.direcStack.push(self.direc)                # keep track of direc's
                    self.reset()                                # reset state   
                return

            if toktype == "DEDENT":
                self.indent = self.indent - 1
                if self.indent < 0:                        # this should not happen...
                    raise config.ParseFailure, "Indentation error."
                if self.direcmode == 0:                        # if not waiting for directive args:
                    self.prevdirec = self.direcStack.pop()        # Restore previous direc
                    if self.prevdirec.type == 'Config':
                        self.Config = self.groupStack.pop()
                    self.direc = self.prevdirec
                    self.reset()                                # reset state

                elif self.indent <= self.direcindent:        # got all directive arguments
                    # Now allow the directive to parse the tokens
                    try:
                        self.direc.Config = self.Config
                        self.direc.tokenparser(self.direcargs, self.directypes, self.indent)
                    except 'Template':
                        log.log( "<parseConfig>tokeneater(), directive is a Template, args: %s" % (dir(self.direc.args)), 8 )

                    if self.indent < self.direcindent:        # back to previous directive level
                        self.prevdirec = self.direcStack.pop()
                        self.direc = self.prevdirec

                    self.reset()                        # reset state

                return

            if toktype == "ERRORTOKEN":
                # Raise a ParseFailure for ERRORTOKEN
                raise config.ParseFailure, "Illegal characters in config."

            if toktype == "NAME":
                # Assign 'None' values properly
                if token == "None":
                    token = None

                # Substitute ALIAS variables if possible
                elif self.Config.aliasDict.has_key(token):
                    aval = self.Config.aliasDict[token]

                    # replace token with value and fix toklist
                    if type(aval) == type("string"):
                        aval = '"%s"'%(aval)
                    log.log( "<parseConfig>tokeneater(), ALIAS substituted %s for %s" % (aval,token), 8 )
                    token = aval

            if toktype != "COMMENT" and token != "\012":
                # If token not a comment, newline, indent or dedent then add to our list of
                # tokens.
                self.toklist.append(token)
                self.toktypes.append(toktype)

            # DEBUG
            #print "toklist:",self.toklist

            if self.direcmode > 0 and token=='\012':
                #self.direcargs = self.direcargs + self.toklist
                self.direcargs.append( self.toklist )
                #self.directypes = self.directypes + self.toktypes
                self.directypes.append( self.toktypes )
                self.toklist = []                # clear token list
                self.toktypes = []                # clear token types list
                self.notfirstdirecline = 1        # passed first directive line
                return

            # If waiting for directive arguments, and indent level is same as directive
            # indent level, and this not first directive line, directive must be ready
            # for creation...
            if self.direcmode > 0 and self.indent == self.direcindent and self.notfirstdirecline == 1:
                try:
                    self.direc.Config = self.Config
                    self.direc.tokenparser(self.direcargs, self.directypes, self.indent)
                except 'Template':
                    log.log( "<parseConfig>tokeneater(), directive is a Template, args: %s" % (dir(self.direc.args)), 8 )

                savetoklist = self.toklist        # save token list - not parsed yet
                savetoktypes = self.toktypes        # save token types
                self.reset()                        # reset state
                self.toklist = savetoklist        # restore token list
                self.toktypes = savetoktypes        # restore token types
                return


            # Only continue if the last token is a ':' or CR
            if len(self.toklist) < 1 or (self.direcmode > 0 and token != '\012') or (self.direcmode == 0 and token != ':' and token != '\012'):
                return

            # If the only token is a CR, throw it away and continue
#            if len(self.toklist) == 1 and self.toklist[0] == '\012':
#                self.reset()
#                return

            # See if we can do anything with the current list of tokens.

            if self.toklist[0] == 'INCLUDE':
                # recursively read the INCLUDEd file
                file = utils.stripquote(self.toklist[1])
                log.log( "<parseConfig>tokeneater(), reading INCLUDEd file '%s'" % file, 8 )

                newstate = State(self.Config)
                newstate.filename = file

                # Start parsing the INCLUDEd file.
                if file[0] ==  '/':
                    readFile(file, newstate)
                else:
                    readFile(os.path.join(self.dir, file), newstate)

                # Reset state and token lists
                self.reset()                # reset state
                return

            elif self.toklist[0] in ('group', 'Group', 'GROUP'):
                # Create new rule group
                newgrp = self.Config.newgroup(self.toklist, self.toktypes, self.Config)
                self.reset()                # reset state
                self.direc = newgrp
                self.groupStack.push(self.Config)
                self.Config = newgrp
                return

            elif config.keywords.has_key(self.toklist[0]):
                # Create a new object (not a Directive)
                direc = config.keywords[self.toklist[0]](self.toklist,self.toktypes)
                self.direc = direc

                if direc == None:
                    raise ParseFailure, "Object creation failed."

                # tell object who its parent is
                self.prevdirec = self.direcStack.top()
                self.direc.parent = self.prevdirec

                self.reset()                # reset state

                try:
                    if direc.hastokenparser:
                        # some objects must wait for more multi-line arguments
                        self.direcmode = 1
                        self.direcindent = self.indent
                except:
                    pass

                # 'give' object to parent
                self.prevdirec = self.direcStack.top()
                self.prevdirec.give(direc)
                self.direc.scanperiod = config.scanperiod        # set default scanperiod

                return

            elif config.directives.has_key(self.toklist[0]):
                # Create new directive
                direc = config.directives[self.toklist[0]](self.toklist)
                self.direc = direc

                if direc == None:
                    raise ParseFailure, "Directive creation failed."

                # tell directive who its parent is
                self.prevdirec = self.direcStack.top()
                self.direc.parent = self.prevdirec

                self.reset()                # reset state

                try:
                    if direc.hastokenparser:
                        # some objects must wait for more multi-line arguments
                        self.direcmode = 1
                        self.direcindent = self.indent
                except:
                    pass

                # 'give' object to parent
                self.prevdirec = self.direcStack.top()
                self.prevdirec.give(direc)
                self.direc.scanperiod = config.scanperiod        # set default scanperiod

                return


            else:
                raise config.ParseFailure("Syntax error")
                self.reset()                # reset state

        except config.ParseFailure, msg:
            parseFailure( msg, (srow, scol), (erow, ecol), line, self.filename )
            log.sendadminlog()
            sys.exit(-1)


def parseFailure( msg, (srow, scol), (erow, ecol), line, filename ):
    """
    parseFailure( message, (start-row, start-col), (end-row, end-col), linestr, filename )
     Display error message caused by a parsing failure while parsing the
     config file.

    Returns: nothing
    """

    print "Parse Failure:",msg
    print "  File: '%s'" % (filename),
    if srow == erow:
        print " line: %d" % (srow),
    else:
        print " lines: %d-%d" % (srow,erow)

    if scol == ecol:
        print " col: %d" % (scol),
    else:
        print " col: %d-%d" % (scol,ecol),

    print "  line follows:"

    if len(line) > 0 and line[-1] == '\n':
        line = line[:-1]                        # strip newline from end
    print line                                        # print line
    print " " * (scol-1) + "^" * (ecol-scol+1)        # print pointer to error

    log.log( "<parseConfig>parseFailure(), '%s' File:%s row:%d Line:\n%s" % (msg, filename, srow, line), 1 )



def readConf(file, Config):
    """
    readConf( filename, Config-object )
     Parse config file 'filename' and create configuration information
     stored in a Config object.

    Returns: nothing
    """

    # Instantiate a State object to track the current state of tokenization.
    state = State(Config)
    state.filename = file

    # build a list of configfiles
    global configfiles
    configfiles = []

    # Start reading the config file
    readFile(file, state)

    #DEBUG: view the config!
    #print "------------------Config Follows------------------"
    #print Config

    #print "DEBUG: configfiles:",configfiles

    # Store a dictionary of config files and their corresponding mtimes
    for f in configfiles:
        Config.configfiles[f] = os.stat(f)[8]


def readFile(file, state):
    """
    readFile( filename, State-object)
     Open the config file 'filename' and pass file descriptor to the tokenizer.

    Returns: nothing
    """

    # Get the directory name of the current config file
    #state.dir = file[:string.rfind(file, '/')]+'/'
    state.dir = os.path.dirname( file )

    try:
        conf = open(file, 'r')
    except IOError, e:
        msg = "Error opening file '%s': %s" % (file, str(e))
        sys.stderr.write(msg + '\n')
        log.log( msg, 4 )
        raise ConfigError(msg)

    # add this filename to the list of config files
    configfiles.append(file)

    # Let tokenize.tokenize() parse the file into tokens which it will pass to
    # state.tokeneater() which will parse the tokens and create something
    # meaningful.
    try:
        tokenize.tokenize(conf.readline, state.tokeneater)
    except tokenize.TokenError, msg:
        raise config.ParseFailure, "Syntax error, %s"%(msg)

    conf.close()



###
### END parseConfig.py
###
