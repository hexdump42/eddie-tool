#!/opt/local/bin/python 
## 
## File		: definition.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 971215
## 
## Description	: 
##
## $Id$
##
##

import string
import regex
import utils

# Define exceptions
ParseFailure = 'ParseFailure'


##
## The Message class that acts as a dictionary...
##
class MsgDict:
    def __init__(self):
	self.hash = {}		# Dictionary of M objects keyed by name

    # Overload '+', eg: rules + directive_rule
    def __add__(self, new):
	self.hash[new.name] = new	# Add M object to dictionary
	return(self)

    # Overload '[]', eg: returns corresponding message for M-name
    def __getitem__(self, name):
	try:
	    return self.hash[name].message
	except KeyError:
	    return None

    def subj(self, name):
	try:
	    return self.hash[name].subject
	except KeyError:
	    return None

    def keys(self):
	return self.hash.keys()
    
    def delete(self, name):
	del self.hash[name]


##
## The base definition class.  Derive all definition-types from this base class.
##
class Definition:
    def __init__(self, *arg):
	self.raw = arg[0]			# the raw line as read from config file
	self.basetype = 'Definition'		# the object can know its own basetype
	self.type = string.split(self.raw)[0]	# the definition type of this instance
	self.regexp = ''			# the regexp to split the raw line into fields

    def getRaw(self):
	return self.raw

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

## -- DEFINITIONS --

##
## MESSAGE DEFINITION
##
class M(Definition):
    def __init__(self, *arg):
	apply( Definition.__init__, (self,) + arg )
	self.regexp = 'M[\t ]+\([a-zA-Z0-9_/\.]+\)[\t ]+\"\(.*\)\"[\t \n]+\([^\005]*\)'
	fields = self.parseRaw()
	self.name = fields[0]
	self.subject = fields[1]
	self.message = fields[2]

    def send(self, email):
	print "sending message to", email

##
## DEF DEFINITION - defines general definitions, access with $defn_name
##
class DEF(Definition):
    def __init__(self, *arg):
	apply( Definition.__init__, (self,) + arg )
	self.regexp = 'DEF[\t ]+\([a-zA-Z0-9_]+\)[\t ]*=[\t ]*\(.*\)[\t \n]*$'
	fields = self.parseRaw()
	self.name = fields[0]		# the name of this DEFinition
	self.text = fields[1]		# the text that is assigned to it


##
## A DEFINITION - defines Actions
class A(Definition):
    def __init__(self, *arg):
	apply( Definition.__init__, (self,) + arg )
	self.regexp = 'A[\t ]+\([a-zA-Z0-9_]+\)[\t ]+\(.*\)'
	fields = self.parseRaw()
	self.name = fields[0]		# the name of this Action
	self.text = fields[1]		# the text that is assigned to it


##
## parseList( list, dict ) - cycles thru list, if any entries are keys in dict, replaces
##   entry with value from dict.
def parseList( list, dict ):
    newlist = []
    for l in list:
	try:
	    # is l a key in dict ?  if yes, it is added
	    tmp = dict[l]
	    tmplist = utils.trickySplit( tmp, ',' )
	    tmplist = parseList( tmplist, dict )
	    for i in tmplist:
		newlist.append(i)
	except KeyError:
	    # if no, just add l
	    newlist.append(l)
    return newlist


##
## parseM( text, dict ) - if text is in dict (assumed to be of type MsgDict)
##   then (subj,body) list is returned, else empty list is returned.
def parseM( text, dict ):
    try:
	# is text a key in dict ?
	body = dict[text]
    except KeyError:
	# if no, return empty list
	return ()
    if body == None:
	# not in dictionary, return empty list
	return ()
    return (dict.subj(text), body)


##
## END - definition.py
##
