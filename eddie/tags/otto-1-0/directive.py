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

class Directive:
    def __init__(self, *arg):
	self.raw = arg[0]
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
