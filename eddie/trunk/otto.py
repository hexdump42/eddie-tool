#!/opt/local/bin/python
## 
## File         : otto.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date         : 971204 
## 
## Description  : Otto main program
##
## $Id$
##


import proc
import df
import parseConfig
import directive
import definition
import config
import time

# Main config file - this file INCLUDEs all other config files
config_file = 'config/otto.cf'

# The guts of the Otto program - sets up the lists, reads config info, gets
# system information, then performs the checking.
def ottoguts():
    global ourList		# global list of all directives
    global defDict		# global dictionary of DEFinitions
    global MDict		# global dictionary of Messages

    # initialise our global lists/dicts
    ourList = directive.Rules()
    defDict = {}
    MDict = definition.MsgDict()

    # read in config and rules
    parseConfig.readFile(config_file, ourList, defDict, MDict)

    #print "M: ",ourList['M']
    #print "D: ",ourList['D']
    #print "FS: ",ourList['FS']
    #print "PID: ",ourList['PID']
    #print "SP: ",ourList['SP']


    # instantiate a process list
    directive.plist = proc.procList()
    #print p

    # instantiate a disk usage list
    directive.dlist = df.dfList()
    #print d

    ## debugging ##
    #print "-- The following DEFs are defined: --"
    #for i in defDict.keys():
    #	print "%s=%s" % (i, defDict[i])
    #print "-- The following Ms are defined: --"
    #for i in MDict.keys():
    #	print "%s: Subject \"%s\"\n---BODY---\n%s\n----------" % (i, MDict.subj(i), MDict[i])

    # Now do all the checking
    # note ... directive order is not defined (we don't currently care do we?)
    ## debugging - test with 'D' directive for now ##
    ## for d in ourList.keylist():
    for d in ('D'):
	list = ourList[d]
	for i in list:
	    i.docheck()

def main():

    # Main Loop
    while 1:
	try:
	    ottoguts()
	    print 'Sleeping for %d secs' % (config.scanperiod)
	    print 'Press CTRL-C to quit'
	    time.sleep( config.scanperiod )
	except KeyboardInterrupt:
	    print "Otto quitting ... bye bye"
	    break



if __name__ == "__main__":
    main()

