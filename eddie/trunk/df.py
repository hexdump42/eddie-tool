#!/opt/local/bin/python 
## 
## File		: df.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 971204 
## 
## Description	: Library of classes that deal with a solaris df list
##
## $Id$
##

import os
import string

##
## Class dfList - instantiates with a list of disk stats
##
class dfList:
    def __init__(self):
	self.hash = {}
	self.list = []
	 
	rawList = os.popen('df -kFufs', 'r')
	rawList.readline()
 
	for line in rawList.readlines():
	    fields = string.split(line)
	    p = df(fields)
	    self.list.append(p)
	    self.hash[fields[0]] = p
	

    def __str__(self):
	rv = 'Filesystem               kbytes    used   avail  pct    Mount on\n'
 	for item in self.list:
 	    rv = rv + str(item) + '\n'

	return(rv)
	    

    def keys(self):
        return(self.hash.keys())

##
## Class df : holds stats on disk usage
##
class df:
    def __init__(self, *arg):
	self.raw = arg[0]

	self.fs      = self.raw[0]	# Filesystem
	self.size    = self.raw[1]	# Size of filesystem
	self.used    = self.raw[2]	# kb used
	self.avail   = self.raw[3]	# kb free
	self.pctused = self.raw[4]	# Percentage Used
	self.mountpt = self.raw[5]	# Mount point


    def __str__(self):
	f = string.ljust(self.fs, 20)
	s = string.rjust(self.size, 7)
	u = string.rjust(self.used, 7)
	a = string.rjust(self.avail, 7)
	p = string.center(self.pctused, 5)
	m = string.ljust(self.mountpt, 15)
	
	return( '%s\t%s\t%s\t%s\t%s\t%s' % (f, s, u, a, p, m) )

##
## END - df.py
##
