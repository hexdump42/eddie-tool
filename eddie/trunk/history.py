#!/opt/local/bin/python
## 
## File         : history.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date         : 980209 
## 
## Description  : Otto history handler
##
## $Id$
##


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
