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

import os
import string
import regex

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
	self.raw = arg[0]
	self.type = string.split(self.raw)[0]

    def getRaw(self):
	return self.raw

##
## COMMANDS
##
class SCANPERIOD(Directive):
    # remove docheck()
    def docheck(self):
	print "SCANPERIOD - this shouldn't have docheck()"
    
    def setConfig( self, line ):
	print "SCANPERIOD:setConfig( "+line+" )"

class INCLUDE(Directive):
    pass

##
## MESSAGE DIRECTIVE
##
class M(Directive):
    def __init__(self, *arg):
	self.raw = arg[0]

	# get the object type and the name of this message
	lines = string.split(self.raw, "\n")
	fl = string.split(lines[0])
	self.type = fl[0]
	self.name = fl[1]

	# define regexp for extracting the subject for the email
	sre = regex.compile("\"\(.*\)\"")
	inx  = sre.search(lines[0])
	self.subject = sre.group(1)

	# now get the message body
	lines.remove(lines[0])
	self.message = string.join(lines, "\n")

    def docheck(self):
	print "M directive doing checking......"

    def send(self, email):
	print "sending message to", email


##
## RULE-BASED COMMANDS
##
class FS(Directive):
    def docheck():
	print "FS directive doing checking......"


class A(Directive):
    def docheck(self):
	print "A directive doing checking......"


class PID(Directive):
    def docheck(self):
	print "PID directive doing checking......"


class D(Directive):
    def docheck(self):
	print "D directive doing checking......"


class SP(Directive):
    def docheck(self):
	print "SP directive doing checking......"


class R(Directive):
    def docheck(self):
	print "R directive doing checking......"


##
## END - directive.py
##
