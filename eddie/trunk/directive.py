#!/opt/local/bin/python 
## 
## File		: directive.py 
## 
## Author	: Rod Telford 
## 
## Date		: 971205 
## 
## Description	: 
##
## $Id$
##

import os
import string

class Rules:
    def __init__(self):
	self.hash = {}

    def __add__(self, new):
	try:
	    tl = self.hash[new.type]

	except KeyError:
	    self.hash[new.type] = []
	    tl = self.hash[new.type]

	tl.append(new)

	self.hash[new.type] = tl
	return(self)

    def __getitem__(self, key):
    	return self.hash[key]

class Directive:
    def __init__(self, *arg):
	self.raw = arg[0]
	self.type = string.split(self.raw)[0]
#	print self.raw


class FS(Directive):
    pass


class M(Directive):
    pass


class A(Directive):
    pass


class PID(Directive):
    pass


class D(Directive):
    pass


class SP(Directive):
    pass


class R(Directive):
    pass


##
## END - directive.py
##
