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

# Python specific modules
import string

# Eddie specific modules
import utils, log


# Define exceptions
ParseFailure = 'ParseFailure'
ParseNotcomplete = 'ParseNotcomplete'



##
## The Message dictionary class.
##
class MsgDict:
    def __init__(self):
	self.hash = {}		# Dictionary of M objects keyed by name

    # Overload '+', eg: rules + directive_rule
    def __add__(self, new):
	self.hash[new.name] = new	# Add M object to dictionary
	return(self)

    # Overload '[]' for setting
    def __setitem__(self, name, new):
	self.hash[name] = new		# Add M object to dictionary
	return(self)

    # Overload '[]', eg: returns corresponding object for name
    def __getitem__(self, name):
	try:
	    return self.hash[name]
	except KeyError:
	    return None

    def keys(self):
	return self.hash.keys()
    
    def delete(self, name):
	del self.hash[name]

    def __str__(self):
	return "%s" % self.hash


##
## The base definition class.  Derive all definition-types from this base class.
##
class Definition:
    def __init__(self, list):
	self.basetype = 'Definition'	# the object can know its own basetype
	self.type = list[0]		# the definition type of this instance



## -- DEFINITIONS --

##
## MESSAGE DEFINITION
##
class MSG(Definition):
    def __init__(self, toklist):
	apply( Definition.__init__, (self, toklist) )
	self.name = toklist[1]
	self.subject = ""
	self.message = ""
	log.log( "<Definition>MSG(), M created, name '%s'" % (self.name), 9 )

    def tokenparser(self, toklist, toktypes, indent):
	self.subject = toklist[0]
	self.message = toklist[1]

    def __str__(self):
	str = "<MSG name='%s' subject='%s' message='%s'>" % (self.name, self.subject, self.message)
	return str



##
## MESSAGE-LIST DEFINITION
##
class M(Definition):
    def __init__(self, toklist):
	apply( Definition.__init__, (self, toklist) )
	self.name = toklist[1]
	self.MDict = {}			# Create dict of M's or MSG's
	log.log( "<Definition>M(), M created, name '%s'" % (self.name), 8 )


    def __str__(self):
	str = "<M name='%s'" % self.name
	for i in self.MDict.keys():
	    str = str + " %s" % self.MDict[i]
	str = str + ">"
	return str


    def __getitem__(self, item):
	return self.MDict[item]


    def tokenparser(iself, toklist, toktypes, indent):
        print "(*) M.tokenparser() -> NOTHING TO DO"
	return


    def give(self, obj):
	if obj.type == 'M':
	    self.MDict[obj.name] = obj
	elif obj.type == 'MSG':
	    self.MDict[obj.name] = obj
	else:
	    raise SyntaxError, "M can't take object of type %s" % obj.type




##
## DEF DEFINITION - defines general definitions, access with $defn_name
##
class DEF(Definition):
    def __init__(self, list):
	apply( Definition.__init__, (self,list) )

	# if the last token isn't a carriage-return then we don't have the
	# whole line yet...
	if list[-1] != '\012':
	    raise ParseNotcomplete

	# if we don't have 5 elements ['DEF', <str>, '=', <str>, '012'] then
	# raise an error
	if len(list) != 5:
	    raise ParseFailure, "DEF definition has %d tokens when expecting 5" % len(list)

	# OK, grab values
	self.name = list[1]		# the name of this DEFinition
	self.text = list[3]		# the text that is assigned to it
	log.log( "<Definition>DEF(), DEF created, name '%s', text '%s'" % (self.name,self.text), 8 )


##
## N DEFINITION - defines Notification configs
class N(Definition):
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

	log.log( "<Definition>N(), N created, name '%s'" % (self.name), 8 )
	print "<Definition>N(), N created, name '%s'" % (self.name) #DEBUG


    def __str__(self):
	str = "<N name='%s' " % (self.name)
	for l in self.levels.keys():
	    str = str + " Level=%s:%s" % (l, self.levels[l])
	str = str + ">"
	return str
	

    def tokenparser(self, toklist, toktypes, indent):

	# no good if toklist empty
	if len(toklist) < 1:
	    raise ParseNotcomplete

	# start again if toklist starts with CR
	if toklist[0] == '\012':
	    return

	if toklist[0] in ('Level', 'level', 'LEVEL'):
	    # Haven't finished if we don't have a CR or ':'
	    if toklist[-1] != '\012' and toklist[-1] != ':':
		raise ParseNotcomplete

	    # Level definition
	    if len(toklist) != 3:
		# 3 tokens are required, ie: ['Level', <num>, ':']
		raise ParseFailure, 'N: Expecting 3 tokens, found %d' % len(toklist)

	    # Level must be a number.
	    if toktypes[1] != 'NUMBER':
		raise ParseFailure, 'N: Level definition expects a number, received a %s' % toktypes[1]

	    level = toklist[1]
	    self.addLevel(toklist[1])	# Create level
	    self.configLevel = toklist[1]
	    return

	# Haven't finished if we don't have a CR
	if toklist[-1] != '\012':
	    raise ParseNotcomplete

	if toklist[0] in self.defs.keys():
	    # One of the defined assignments

	    if toklist[1] != '=':
		raise ParseFailure, 'Expecting "=" after "%s", got "%s' % (toklist[0], toklist[1])

	    value = string.join(toklist[2:-1], "")
	    if self.defs[toklist[0]] == 'TIME':
		# Convert time to seconds if required
		value = utils.val2secs(value)

	    assignment = 'self.%s=%d' % (toklist[0],value)
	    exec assignment

	    return

	# Must be a notification command (or list of commands)
	notiflist = self.getNotifList( toklist[:-1] )
	if len(notiflist) == 0:
	    raise ParseNotcomplete
	else:
	    if self.configLevel == -1:
		# Error if no levels defined yet
		raise ParseFailure, "No notification levels have been defined yet"
	    self.addNotif(self.configLevel,indent,notiflist)


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

	for t in list:
#	    if t == ',' and brackets == 0:
#		if len(nstr) > 0:
#		    #nlist.append(nstr)
#		    #nstr = ''
#		    pass
#	    else:
		if t == '(':
		    brackets = brackets + 1
		if t == ')':
		    brackets = brackets - 1
		    if brackets < 0:
			raise ParseFailure, "Too many close parentheses ')'"

		nstr = nstr + t

	if len(nstr) > 0:
    	    nlist.append(nstr)

	if brackets != 0:
	    raise ParseFailure, "Parentheses not closed"

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




##
## parseList( list, dict ) - cycles thru list, if any entries are keys in dict, replaces
##   entry with value from dict.
# NOT NEEDED ANYMORE ??
#def parseList( list, dict ):
#    newlist = []
#    for l in list:
#	try:
#	    # is l a key in dict ?  if yes, it is added
#	    tmp = dict[l]
#	    tmplist = utils.trickySplit( tmp, ',' )
#	    tmplist = parseList( tmplist, dict )
#	    for i in tmplist:
#		newlist.append(i)
#	except KeyError:
#	    # if no, just add l
#	    newlist.append(l)
#    return newlist
#

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
