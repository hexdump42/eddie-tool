#!/opt/local/bin/python 
## 
## File		: directive.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 971205 
## 
## Description	: 
##
## $Id$
##
##

import os
import string
import regex
import sys
import action
import definition
import utils

# Define exceptions
ParseFailure = 'ParseFailure'

# Rules holds all the directives in a hash where the value of each key is the
# list of rules relating to that key.
class Rules:
    def __init__(self):
	self.hash = {}

    # Overload '+', eg: rules + directive_rule
    def __add__(self, new):
	try:
	    tl = self.hash[new.type]

	except KeyError:
	    self.hash[new.type] = []
	    tl = []

	tl.append(new)

	self.hash[new.type] = tl
	return(self)

    # Overload '[]', eg: fs_directive_list = rules['FS']
    def __getitem__(self, key):
	try:
	    return self.hash[key]
	except KeyError:
	    return None

    def keylist(self):
	return self.hash.keys()
    
    def delete(self, directive):
	del self.hash[directive]

##
## The base directive class.  Derive all directives from this base class.
##
class Directive:
    def __init__(self, *arg):
	self.raw = arg[0]			# the raw line as read from config file
	self.basetype = 'Directive'		# the object can know its own basetype
	self.type = string.split(self.raw)[0]	# the directive type of this instance
	self.regexp = ''			# the regexp to split the raw line into fields
	self.action = ''			# each directive will have an action

    # Parses raw line with directive-defined regexp and returns tuple of
    # regex groups.
    def parseRaw(self):
	sre = regex.compile( self.regexp )
	inx = sre.search( self.raw )
	if inx == -1:
	    # probably make an exception here.....
	    raise ParseFailure, "Error while parsing line: "+self.raw
	fieldlist = ()
	i=1
	while( sre.group(i) != None ):
	    fieldlist = fieldlist + (sre.group(i),)
	    i = i + 1
	return fieldlist

    # Perform actions for a directive
    def doAction(self):
	# split comma-seperated list of actions
	actionList = utils.trickySplit( self.action, ',' )

	# Replace Action definitions with the corresponding actions
	actionList = definition.parseList( actionList, ADict )

	# Put quotes around arguments so we can use eval()
	actionList = utils.quoteArgs( actionList )

	# Perform each action
	for a in actionList:
	    try:
		# Call the action
		eval( 'action.'+a )
	    except AttributeError:
		# Not an action function ... error...
		print "'%s' is not a defined action.  Config line follows:\n%s\n" % (a,self.raw)



##
## RULE-BASED COMMANDS
##
class FS(Directive):
    def docheck():
	print "FS directive doing checking......"



class PID(Directive):
    def __init__(self, *arg):
	apply( Directive.__init__, (self,) + arg )
	self.regexp = 'PID[\t \n]+\([a-zA-Z0-9_/\.]+\)[\t \n]+\([a-zA-Z0-9_]+\)[\t \n]+\(.*\)'
	fields = self.parseRaw()
	self.pidfile = fields[0]		# the pid file to check for
	self.rule = fields[1]			# the rule (EX or PR)
	self.action = fields[2]			# the action
	#print "<PID> pidfile: '%s' rule: '%s' action: '%s'" % (self.pidfile, self.rule, self.action)

    def docheck(self):
	print "PID directive doing checking......"


class D(Directive):
    def __init__(self, *arg):
	apply( Directive.__init__, (self,) + arg )
	self.regexp = 'D[\t \n]+\([a-zA-Z0-9_]+\)[\t \n]+\([a-zA-Z0-9_]+\)[\t \n]+\(.*\)'
	fields = self.parseRaw()
	self.daemon = fields[0]			# the daemon to check for
	self.rule = fields[1]			# the rule (NR or R)
	self.action = fields[2]			# the action
	
	self.ruleDict = { 'NR' : self.NR,
	                  'R'  : self.R	}
	#print "<D> daemon: '%s' rule: '%s' action: '%s'" % (self.daemon, self.rule, self.action)

    def docheck(self):
	#print "D directive doing checking...... daemon: %s rule: '%s' action: '%s'" % (self.daemon,self.rule,self.action)
	self.ruleDict[ self.rule ]()

    def NR(self):
	if plist.procExists( self.daemon ) == 0:
	    print " <D>",self.daemon,"is NOT running."
	    self.doAction()

    def R(self):
	if plist.procExists( self.daemon ) > 0:
	    print " <D>",self.daemon,"is running."
	    self.doAction()


class SP(Directive):
    def __init__(self, *arg):
	apply( Directive.__init__, (self,) + arg )
	self.regexp = 'SP[\t \n]+\([a-zA-Z0-9_/]+\)[\t \n]+\(.*\)'
	fields = self.parseRaw()
	self.port = fields[0]			# the port to check
	self.action = fields[1]			# the action
	#print "<SP> port: '%s' action: '%s'" % (self.port, self.action)

    def docheck(self):
	print "SP directive doing checking......"



##
## END - directive.py
##
