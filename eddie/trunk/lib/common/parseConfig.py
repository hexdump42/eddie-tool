#!/opt/local/bin/python 
## 
## File         : parseConfig.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date         : 971204 
## 
## Description  : Parses Eddie configuration files
##
## $Id$
##

# Python specific modules
import os, string, regex, tokenize
# Eddie specific modules
import directive, definition, config, log, utils

#
# State of tokenization
#
class State:
    def __init__(self, Config):
	self.reset()
	self.groupStack = utils.Stack()	# Stack to store groups on temporarily
	self.direcStack = utils.Stack()	# Stack to store direcs on temporarily
	self.direcStack.push(Config)
	self.Config = Config

	self.indent = 0		# Indentation level
	self.direc = None	# current directive


    # Reset state
    def reset(self):
	#self.state = None	# clear current config state
	self.toklist = []	# clear token list
	self.toktypes = []	# clear token types list


    # Eddie's token eater!
    # - Parses the tokens given to it (from tokenize.tokenize()) and uses them
    #   to create the configuration information.
    #
    def tokeneater(self, type, token, (srow, scol), (erow, ecol), line):
	# The type of token
	toktype = tokenize.tok_name[type]

	#DEBUG:
	#print "%d,%d-%d,%d:\t%s\t%s" % \
	#    (srow, scol, erow, ecol, toktype, repr(token))

	# Handle indentation/dedentations...
	if toktype == "INDENT":
	    self.indent = self.indent + 1
	    self.direcStack.push(self.direc)	# Keep track of direc's
	    self.reset()		# reset state
	    return
	elif toktype == "DEDENT":
	    self.indent = self.indent - 1
	    if self.indent < 0:
		print "INDENT ERROR!!!! TODO"
		raise 'Indent Error...'
	    self.prevdirec = self.direcStack.pop()	# Restore previous direc
	    if self.direc.type == 'Config':
		self.Config = self.groupStack.pop()
	    #elif self.prevdirec != self.direc:
		#print "@@@@@ Giving direc to:",self.prevdirec
		#self.prevdirec.give(self.direc)

	    self.direc = self.prevdirec
	    self.reset()		# reset state
	    return
	elif toktype == "ERRORTOKEN" and token == '$':
	    # Special case for '$' symbols which the standard Python parser
	    # tokenizes as an error token but we will actually use it to
	    # indicate a variable-name following it.
	    self.toklist.append(token)
	    self.toktypes.append("DOLLAR")	# make up new token type !
	elif toktype == "ERRORTOKEN" and (token == ' ' or token == '\011'):
	    # ERRORTOKEN's which are spaces or tabs can be ignored for now.
	    # They are probably found before a '$'...
	    return
	elif toktype == "ERRORTOKEN":
	    # Raise a ParseFailure for any other ERRORTOKEN
	    raise config.ParseFailure, "ERRORTOKEN found."
	elif toktype != "COMMENT":
	    # If token not a comment, indent or dedent then add to our list of
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
	# Only continue if the last token is a ':' or CR
	if len(self.toklist) < 1 or (self.toklist[-1] != ':' and self.toklist[-1] != '\012'):
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
#	    except config.ParseFailure:
#		print "PARSEFAILURE from newgroup() !!! TODO"
	    else:
		self.reset()		# reset state
		self.direc = newgrp
		self.groupStack.push(self.Config)
		self.Config = newgrp
	    return

	elif config.keywords.has_key(self.toklist[0]):
	    try:
		print "!!! creating new directive:",self.toklist[0]
		direc = config.keywords[self.toklist[0]](self.toklist)
	    except config.ParseNotcomplete:
		pass
#	    except config.ParseFailure:
#		print "PARSEFAILURE !!! TODO"
	    else:
		if direc != None:
		    self.prevdirec = self.direcStack.top()
		    self.prevdirec.give(direc)

		self.reset()		# reset state
		self.direc = direc	# current directive
	    return

	elif self.direc != None:
	    print "...passing toklist to tokenparser() of:",self.direc
	    self.direc.tokenparser(self.toklist, self.toktypes, self.indent)
	    self.reset()		# reset state
	    return

	else:
	    raise "PARSE FAILURE! toklist: %s" % toklist
	    self.reset()		# reset state


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

    # Start reading the config file
    readFile(file, state)

    #DEBUG: view the config!
    print "------------------Config Follows------------------"
    print Config

    #DEBUG: exit
    #import sys
    #sys.exit(-1)


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

    # Let tokenize.tokenize() parse the file into tokens which it will pass to
    # state.tokeneater() which will parse the tokens and create something
    # meaningful.
    tokenize.tokenize(conf.readline, state.tokeneater)


# find any DEF's in line (ie: $SPAZ) and replace with definition
#def parseDefs(line, defDict):
#    defsrch = regex.compile( "\$\([A-Za-z0-9_]+\)" )
#
#    pos = defsrch.search( line, 0 )
#    while pos != -1 and pos < len(line):
#	var = defsrch.group(0)[1:]		# get var name and strip '$'
#
#	try:
#	    replace = defDict[var]
#	except KeyError:
#	    replace = None
#	
#	if replace != None:
#	    line = line[:pos] + replace + line[pos+len(var)+1:]
#
#	pos = defsrch.search( line, pos+1 )
#
#    return line


###
### END parseConfig.py
###
