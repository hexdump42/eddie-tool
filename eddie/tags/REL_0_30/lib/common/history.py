## 
## File         : history.py 
## 
## Author       : Rod Telford  <rtelford@psychofx.com>
##                Chris Miles  <chris@psychofx.com>
## 
## Start Date   : 19980209 
## 
## Description  : Eddie history handler
##
## $Id$
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


import log

# Define History Variables
# set history length - TODO: this could possibly be dynamic later...
historySize = 5	# keep 5 levels of history max


# Store a list of previous items
class history:
    def __init__(self):
	self.histdict = {}


    def save(self,name,item):
	try:
	    histlist = self.histdict[name]
	    Len = len(histlist)		# current history length
    	    histlist = [item] + histlist[0:min( Len, historySize-1 )]
	except KeyError:
    	    histlist = [item]

	self.histdict[name] = histlist
	log.log( "<history>save(), saved '%s' of '%s'" % (name,item), 9 )

	#debug
	#Len = len(histlist)		# current history length
       	#print "Len=",len(histlist)," histlist:", histlist
	#for i in range( 0, Len ):
	#    print i, ":", histlist[i]
	
    def list(self,name,num=0):
	try:
	    histlist = self.histdict[name]
	    return histlist[num]
	except:
	    return []



###
### END history.py
###
