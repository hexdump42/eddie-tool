#!/opt/local/bin/python 
## 
## File		: action.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date		: 971217 
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


#### DEFINE ALL THE ACTIONS AVAILABLE ####

# mail()
def mail(user,*arg):
    print "    ACTION: mail("+user+",",
    for i in arg:
	print i,
    print ")"

# system()
def system(cmd):
    pass
    print "    ACTION: system("+cmd+")"

# restart()
def restart(cmd):
    pass
    print "    ACTION: restart("+cmd+")"


##
## END - action.py
##
