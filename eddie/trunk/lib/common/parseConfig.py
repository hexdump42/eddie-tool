## 
## File         : parseConfig.py 
## 
## Author       : Rod Telford  <rtelford@codefx.com.au>
##                Chris Miles  <cmiles@codefx.com.au>
## 
## Date         : 971204 
## 
## Description  : Parses Eddie configuration files
##
## $Id$
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

# Python specific modules
import sys, os, string, tokenize
# Eddie specific modules
import config, log, utils

#
# State of tokenization
#
class State:
    def __init__(self, Config):
	self.groupStack = utils.Stack()	# Stack to store groups on temporarily
	self.direcStack = utils.Stack()	# Stack to store direcs on temporarily
	self.direcStack.push(Config)
	self.Config = Config

	self.indent = 0		# Indentation level
	self.direc = None	# current directive

	self.reset()


    # Reset state
    def reset(self):
	#self.state = None	# clear current config state
	self.toklist = []	# clear token list
	self.toktypes = []	# clear token types list
	self.direcmode = 0	# whether currently parsing directive arguments
	self.direcindent = 0	# indent level of directive definition
	self.direcargs = []	# current directive arguments
	self.directypes = []	# current directive arguments (types)
	self.notfirstdirecline = 0	# first directive line marker


    # Eddie's token eater!
    # - Parses the tokens given to it (from tokenize.tokenize()) and uses them
    #   to create the configuration information.
    #
    def tokeneater(self, type, token, (srow, scol), (erow, ecol), line):
	try:
	    #print " "
	    #print "direcmode:",self.direcmode
	    #print "direcindent:",self.direcindent
	    #print "indent:",self.indent
	    #print "notfirstdirecline:",self.notfirstdirecline

	    # The type of token
	    toktype = tokenize.tok_name[type]

	    #DEBUG:
	    #print "%d,%d-%d,%d:\t%s\t%s" % \
	    #    (srow, scol, erow, ecol, toktype, repr(token))

	    # Don't care about single CRs
	    if token == '\012' and len(self.toklist) == 0:
		return

	    # Handle indentation/dedentations...
	    if toktype == "INDENT":
		self.indent = self.indent + 1
		if self.direcmode == 0:		# if not waiting for directive args
		    self.direcStack.push(self.direc)        # Keep track of direc's
		    self.reset()            # reset state   
		return

	    elif toktype == "DEDENT":
		self.indent = self.indent - 1
		if self.indent < 0:
		    print "INDENT ERROR!!!! TODO"
		    raise 'Indent Error...'
		if self.direcmode == 0:		# if not waiting for directive args
		    self.prevdirec = self.direcStack.pop()  # Restore previous direc
		    if self.prevdirec.type == 'Config':
			self.Config = self.groupStack.pop()
		    self.direc = self.prevdirec
		    self.reset()            # reset state

		elif self.indent <= self.direcindent:	# got all directive arguments
		    #print "!! BACK TO DIREC INDENT - TOKENPARSING NOW"
		    try:
			self.direc.Config = self.Config
			self.direc.tokenparser(self.direcargs, self.directypes, self.indent)
		    except 'Template':
			log.log( "<parseConfig>tokeneater(), directive is a Template, args: %s" % (dir(self.direc.args)), 8 )
		    self.prevdirec = self.direcStack.top()
		    self.direc.parent = self.prevdirec	# show directive its parent
		    #print "!!  self.direc.parent=",self.direc.parent

		    if self.indent < self.direcindent:	# back to previous directive level
			self.prevdirec = self.direcStack.pop()
			self.direc = self.prevdirec

		    self.reset()		# reset state
		#print "!!!! self.direcStack:",self.direcStack

		return

	    elif toktype == "ERRORTOKEN" and token == '$':
		# Special case for '$' symbols which the standard Python parser
		# tokenizes as an error token but we will actually use it to
		# indicate a variable-name following it.
		# !! This functionality should disappear as it breaks the Python-like flow !!
		self.toklist.append(token)
		self.toktypes.append("DOLLAR")	# make up new token type !
	    elif toktype == "ERRORTOKEN" and (token == ' ' or token == '\011'):
		# ERRORTOKEN's which are spaces or tabs can be ignored for now.
		# They are probably found before a '$'...
		return
	    elif toktype == "ERRORTOKEN":
		# Raise a ParseFailure for any other ERRORTOKEN
		raise config.ParseFailure, "Illegal characters in config."
	    elif toktype != "COMMENT" and token != "\012":
		# If token not a comment, newline, indent or dedent then add to our list of
		# tokens.
		self.toklist.append(token)
		self.toktypes.append(toktype)

	    # Substitute $VAR variables for DEF's
	    if len(self.toklist) > 1 and self.toktypes[-2] == "DOLLAR":
		if toktype != "NAME":
		    # '$' must be followed by a "NAME" toktype
		    raise config.ParseFailure, "'$' followed by illegal characters."
		else:
		    # Replace last two tokens with variable substitution
		    try:
			del self.toklist[-2:]
			self.toklist.append(self.Config.defDict[token])
		    except KeyError:
			raise config.ParseFailure, "Variable substitution error for $%s" % token
		    del self.toktypes[-2:]
		    self.toktypes.append("NAME")

	    # DEBUG
	    #print "toklist:",self.toklist

	    #if self.direcmode > 0 and token=='\012' and self.indent == self.direcindent and toktype == "NAME":
	    if self.direcmode > 0 and token=='\012':
		self.direcargs = self.direcargs + self.toklist
		self.directypes = self.directypes + self.toktypes
		#print "**direcargs:",self.direcargs
		self.toklist = []	# clear token list
		self.toktypes = []	# clear token types list
		self.notfirstdirecline = 1	# passed first directive line
		return

	    # If waiting for directive arguments, and indent level is same as directive
	    # indent level, and this not first directive line, directive must be ready
	    # for creation...
	    if self.direcmode > 0 and self.indent == self.direcindent and self.notfirstdirecline == 1:
		#print "!! BACK TO DIREC INDENT AND NOT FIRSTLINE - TOKENPARSING NOW"
		try:
		    self.direc.Config = self.Config
		    self.direc.tokenparser(self.direcargs, self.directypes, self.indent)
		except 'Template':
		    log.log( "<parseConfig>tokeneater(), directive is a Template, args: %s" % (dir(self.direc.args)), 8 )
		self.prevdirec = self.direcStack.top()
		self.direc.parent = self.prevdirec	# show directive its parent
		#print "!!  self.direc.parent=",self.direc.parent

		savetoklist = self.toklist	# save token list - not parsed yet
		savetoktypes = self.toktypes	# save token types
		self.reset()			# reset state
		self.toklist = savetoklist	# restore token list
		self.toktypes = savetoktypes	# restore token types
		return


	    # Only continue if the last token is a ':' or CR
	    #if len(self.toklist) < 1 or self.direcmode > 0 or (self.toklist[-1] != ':' and self.toklist[-1] != '\012'):
	    if len(self.toklist) < 1 or (self.direcmode > 0 and token != '\012') or (self.direcmode == 0 and token != ':' and token != '\012'):
		return

	    # If the only token is a CR, throw it away and continue
	    if len(self.toklist) == 1 and self.toklist[0] == '\012':
		self.reset()
		return

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
		    readFile(self.dir+file, newstate)

		# Reset state and token lists
		self.reset()		# reset state
		return

	    elif self.toklist[0] in ('group', 'Group', 'GROUP'):
		# Create new rule group
		try:
		    newgrp = self.Config.newgroup(self.toklist, self.toktypes, self.Config)
		except config.ParseNotcomplete:
		    pass
		else:
		    self.reset()		# reset state
		    self.direc = newgrp
		    self.groupStack.push(self.Config)
		    self.Config = newgrp
		return

	    elif config.keywords.has_key(self.toklist[0]):
		#print " -> toklist:",self.toklist
		direc = config.keywords[self.toklist[0]](self.toklist)
		self.direc = direc

		if direc == None:
		    raise ParseFailure, "Directive creation failed."

		self.reset()		# reset state

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
		self.direc.scanperiod = config.scanperiod	# set default scanperiod

		return

	    else:
		raise "PARSE FAILURE! toklist: %s" % self.toklist
		self.reset()		# reset state

	except config.ParseFailure, msg:
	    parseFailure( msg, (srow, scol), (erow, ecol), line, self.filename )
	    #print "PARSEFAILURE: ",msg,(srow, scol), (erow, ecol), line
	    ## TODO: probably should return to top level properly...?
            log.sendadminlog()
	    sys.exit(-1)


###
### parseFailure( message, (start-row, start-col), (end-row, end-col), linestr, filename )
###  Display error message caused by a parsing failure while parsing the
###  config file.
###
### Returns: nothing
###
def parseFailure( msg, (srow, scol), (erow, ecol), line, filename ):
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

    if line[-1] == '\n':
	line = line[:-1]
    print line
    print " " * (scol-1) + "^" * (ecol-scol+1)

    log.log( "<parseConfig>parseFailure(), '%s' File:%s row:%d Line:\n%s" % (msg, filename, srow, line), 1 )



###
### readConf( filename, Config-object )
###  Parse config file 'filename' and create configuration information
###  stored in a Config object.
###
### Returns: nothing
###
def readConf(file, Config):

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


###
### readFile( filename, State-object)
###  Open the config file 'filename' and pass file descriptor to the tokenizer.
###
### Returns: nothing
###
def readFile(file, state):

    # Get the directory name of the current config file
    state.dir = file[:string.rfind(file, '/')]+'/'

    try:
    	conf = open(file, 'r')
    except IOError:
	print "Error opening file '%s'" % file;
	log.log( "<parseConfig>readFile(), Error, Cannot open '%s' - skipping" % (file), 2 )
	return

    # add this filename to the list of config files
    configfiles.append(file)

    # Let tokenize.tokenize() parse the file into tokens which it will pass to
    # state.tokeneater() which will parse the tokens and create something
    # meaningful.
    tokenize.tokenize(conf.readline, state.tokeneater)

    conf.close()



###
### END parseConfig.py
###
