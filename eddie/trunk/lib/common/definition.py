## 
## File		: definition.py 
## 
## Author       : Rod Telford  <rtelford@codefx.com.au>
##                Chris Miles  <cmiles@codefx.com.au>
## 
## Date		: 971215
## 
## Description	: 
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

# Python specific modules
import string

# Eddie specific modules
import utils, log


# Define exceptions
ParseFailure = 'ParseFailure'
#ParseNotcomplete = 'ParseNotcomplete'



class MsgDict:
    """The Message dictionary class."""

    def __init__(self):
	self.hash = {}		# Dictionary of M objects keyed by name


    def __add__(self, new):
	"""Overload '+', eg: rules + directive_rule"""

	self.hash[new.name] = new	# Add M object to dictionary
	return(self)


    def __setitem__(self, name, new):
	"""Overload '[]' for setting."""

	self.hash[name] = new		# Add M object to dictionary
	return(self)


    def __getitem__(self, name):
	"""Overload '[]', eg: returns corresponding object for name."""
	try:
	    return self.hash[name]
	except KeyError:
	    return None


    def __str__(self):
	return "%s" % self.hash


    def keys(self):
	return self.hash.keys()


    def delete(self, name):
	del self.hash[name]


    # update this dictionary with adict as per dict.update() method
    def update(self, adict):
	#self.hash.update(adict)
	#..update() not working ?!??!
	for a in adict.keys():
	    self.hash[a] = adict[a]


class Definition:
    """The base definition class.  Derive all definition-types from
       this base class.
    """

    def __init__(self, list):
	self.basetype = 'Definition'	# the object can know its own basetype
	self.type = list[0]		# the definition type of this instance
	self.hastokenparser = 0		# no tokenparser() function by default



## -- DEFINITIONS --

class MSG(Definition):
    """Message Definition."""

    def __init__(self, toklist):
	apply( Definition.__init__, (self, toklist) )
	self.name = toklist[1]
	self.subject = None
	self.message = None
	#self.indent = 0		# used during parsing only
	self.hastokenparser = 1
	log.log( "<Definition>MSG(), MSG created, name '%s'" % (self.name), 9 )


    def tokenparser(self, toklist, toktypes, indent):

	for t in toklist:
	    if self.subject == None:
		self.subject = utils.stripquote(t)
	    elif self.message == None:
		self.message = utils.stripquote(t)
	    else:
		# tokens left and subject/message already defined
		raise ParseFailure, "Parse error during MSG definition"

	log.log( "<Definition>tokenparser(), MSG parsed, subject:'%s' message:'%s'" % (self.subject,self.message), 9 )

	#if self.indent == 0:
	#    self.subject = utils.stripquote(toklist[0])
	#    if len(toklist) > 1:
	#	self.message = utils.stripquote(toklist[1])
	#    self.indent = indent
	#elif indent > self.indent:
	#    self.message = utils.stripquote(toklist[0])
	#else:
	#    raise ParseFailure, "Indentation error parsing MSG definition"


    def __str__(self):
	#str = "<MSG name='%s' subject='%s' message='%s'>" % (self.name, self.subject, self.message)
	str = "<MSG %s>" % (self.name)
	return str



class M(Definition):
    """Message-list Definition."""

    def __init__(self, toklist):
	apply( Definition.__init__, (self, toklist) )
	self.name = toklist[1]
	self.MDict = {}			# Create dict of M's or MSG's
	log.log( "<Definition>M(), M created, name '%s'" % (self.name), 8 )


    def __str__(self):
	str = "<M %s:" % self.name
	for i in self.MDict.keys():
	    str = str + " %s" % self.MDict[i]
	str = str + ">"
	return str


    def __getitem__(self, item):
	return self.MDict[item]


#    def tokenparser(self, toklist, toktypes, indent):
#	## M doesn't need to parse any tokens.
#	log.log( "<Definition>M(), Warning, M shouldn't see tokens, toklist: %s" % (toklist), 3 )
#	return


    def give(self, obj):
	if obj.type == 'M':
	    self.MDict[obj.name] = obj
	elif obj.type == 'MSG':
	    self.MDict[obj.name] = obj
	else:
	    raise SyntaxError, "M can't take object of type %s" % obj.type




class DEF(Definition):
    """DEF Definition - defines global string aliases to be replaced
       during config file parsing only.  eg:
	DEF FSRULE="capac>=90%"
	...
	FS: fs='/' rule=$FSRULE action=" ... "

	This goes against the general Python-like format of the config
	file and may disappear in the future.
    """

    def __init__(self, list):
	apply( Definition.__init__, (self,list) )

	# if the last token isn't a carriage-return then we don't have the
	# whole line yet...
#	if list[-1] != '\012':
#	    #raise ParseNotcomplete
#	    raise ParseFailure

	# if we don't have 4 elements ['DEF', <str>, '=', <str>] then
	# raise an error
	if len(list) != 4:
	    #print "..DEF list:",list
	    raise ParseFailure, "DEF definition has %d tokens when expecting 4" % len(list)

	# OK, grab values
	self.name = list[1]		# the name of this DEFinition
	self.text = list[3]		# the text that is assigned to it
	log.log( "<Definition>DEF(), DEF created, name '%s', text '%s'" % (self.name,self.text), 8 )


class ALIAS(Definition):
    """ALIAS Definition - defines string aliases which can appear as
	arguments to action calls, etc. eg:
	ALIAS ALERT='root'
	...
	FS: fs='/' rule="capac>=90%" action="email(ALERT, 'fs nearly full')"
    """

    def __init__(self, list):
	apply( Definition.__init__, (self,list) )

	# if the last token isn't a carriage-return then we don't have the
	# whole line yet...  DEFUNCT
	#if list[-1] != '\012':
	#    raise ParseNotcomplete

	# if we don't have 4 elements ['ALIAS', <str>, '=', <str>] then
	# raise an error
	if len(list) != 4:
	    raise ParseFailure, "ALIAS definition has %d tokens when expecting 4" % len(list)

	# OK, grab values
	self.name = list[1]			# the name of this ALIAS
	self.text = utils.stripquote(list[3])	# the text that is assigned to it
	log.log( "<Definition>ALIAS(), ALIAS created, name '%s', text '%s'" % (self.name,self.text), 8 )


class N(Definition):
    """N Definition - defines Notification configs."""

    defs={'notifyperiod':'TIME',	# available definitions
    	  'escalperiod':'TIME'
	 }

    def __init__(self, list):
	apply( Definition.__init__, (self,list) )

	# Need at least 3 tokens
	if len(list) < 3:
	    raise ParseFailure, "Not enough tokens for N definition"

	# 3rd token should be a ':'
	if list[2] != ':':
	    raise ParseFailure, "N definition missing ':'"

	# tokens are ok
	self.name = list[1]		# the name of this Action
	self.lastNotify = 0		# time of last notify
	self.escalLevel = 0		# current level of escalation
	self.levels={}		# dict of notification levels

	# used during config parsing
	self.configLevel = -1
	self.configIndent = 0

	self.hastokenparser = 1

	log.log( "<Definition>N(), N created, name '%s'" % (self.name), 8 )


    def __str__(self):
	str = "<N name='%s' " % (self.name)
	for l in self.levels.keys():
	    str = str + " Level=%s:%s" % (l, self.levels[l])
	str = str + ">"
	return str
	

    def tokenparser(self, toklist, toktypes, indent):

	# no good if toklist empty
	if len(toklist) < 1:
	    #raise ParseNotcomplete
	    raise ParseFailure

	while len(toklist) > 0:
	    #print "--->toklist:",toklist

	    # start again if toklist starts with CR
	    if toklist[0] == '\012':
		del toklist[0]
		del toktypes[0]

	    elif toklist[0] in ('Level', 'level', 'LEVEL'):
		# Level must be a number.
		if toktypes[1] != 'NUMBER':
		    raise ParseFailure, 'N: Level definition expects a number, received a %s' % toktypes[1]
		if toklist[2] != ':':
		    raise ParseFailure

		level = toklist[1]
		self.addLevel(toklist[1])	# Create level
		self.configLevel = toklist[1]
		del toklist[:3]
		del toktypes[:3]

	    elif toklist[0] in self.defs.keys():
		# One of the defined assignments

		if toklist[1] != '=':
		    raise ParseFailure, 'Expecting "=" after "%s", got "%s' % (toklist[0], toklist[1])

		# assume number followed by letter at the moment...
		value = string.join(toklist[2:3], "")
		if self.defs[toklist[0]] == 'TIME':
		    # Convert time to seconds if required
		    value = utils.val2secs(value)

		assignment = 'self.%s=%d' % (toklist[0],value)
		exec assignment

		del toklist[:4]
		del toktypes[:4]

	    else:
		# Must be a notification command (or list of commands)
		notiflist = self.getNotifList( toklist )
		if len(notiflist) == 0:
		    raise ParseFailure, "Notification list is empty"
		else:
		    if self.configLevel == -1:
			# Error if no levels defined yet
			raise ParseFailure, "No notification levels have been defined yet"
		    self.addNotif(self.configLevel,indent,notiflist)
		    del toklist[:self.delcnt]
		    del toktypes[:self.delcnt]

	# Finished parsing tokens
	log.log( "<Definition>N.tokenparser(), '%s'" % (self), 9 )
	


    # Create a notification level - error if level already exists
    def addLevel(self, level):
	if level in self.levels.keys():
	    raise ParseFailure, "a: level %s already defined" % level

	# Create notification level in levels dict
	self.levels[level] = []


    # Try and create a notification command list from tokens and return this
    # list.
    def getNotifList(self, list):
	nlist = []		# list of notification commands
	nstr = ''		# current notification command as string
	brackets = 0		# track brackets depth
	self.delcnt = 0		# temporary counter so main loop can delete objects from list

	#print "getNotif(): list:",list
	for t in list:
	    if t == 'Level':	# stop if new Level defn - poor code!
		break

	    if t == '(':
		brackets = brackets + 1
	    if t == ')':
		brackets = brackets - 1
		if brackets < 0:
		    raise ParseFailure, "Too many close parentheses ')'"

	    nstr = nstr + t

	    self.delcnt = self.delcnt + 1

	if brackets != 0:
	    raise ParseFailure, "Parentheses not closed"

	if len(nstr) > 0:
    	    nlist.append(nstr)

	return nlist


    def addNotif(self, configLevel, indent, list):
	if len(self.levels[configLevel]) == 0:
	    self.levels[configLevel] = list
	    self.configIndent = indent
	else:
	    depth = indent - self.configIndent
	    if depth == 0:
		a = self.levels[configLevel]
		while type(a[-1]) == type([]):
		    a = a[-1]
		for l in list:
		    a.append(l)
	    elif depth > 0:
		a = self.levels[configLevel]
		while type(a[-1]) == type([]):
		    a = a[-1]
		a.append(list)
	    elif depth < 0:
		a = self.levels[configLevel]
		tmp = []		# temporary stack
		while type(a[-1]) == type([]):
		    tmp.append(a)
		    a = a[-1]
		a = tmp[depth]
		for l in list:
		    a.append(l)
	    self.configIndent = indent



def parseM( text, dict ):
    """parseM( text, dict ) - if text is in dict (assumed to be of type MsgDict)
       then (subj,body) list is returned, else empty list is returned.
    """

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
