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
import action
import log
import history

# Main config file - this file INCLUDEs all other config files
config_file = 'config/otto.cf'


# The guts of the Otto program - sets up the lists, reads config info, gets
# system information, then performs the checking.
def ottoguts(ottoHistory):
    global ourList		# global list of all directives
    global defDict		# global dictionary of DEFinitions
    global MDict		# global dictionary of Messages
    global ADict		# global dictionary of Actions


    # initialise our global lists/dicts
    ourList = directive.Rules()
    defDict = {}
    MDict = definition.MsgDict()
    ADict = {}

    # read in config and rules
    parseConfig.readFile(config_file, ourList, defDict, MDict, ADict)

    directive.ADict = ADict		# make ADict viewable in directive module
    action.MDict = MDict		# make MDict viewable in action module

    #print "M: ",ourList['M']
    #print "D: ",ourList['D']
    #print "FS: ",ourList['FS']
    #print "PID: ",ourList['PID']
    #print "SP: ",ourList['SP']


    # instantiate a process list
    log.log( "<otto>ottoguts(), creating process list", 8 )
    directive.plist = proc.procList()

    # instantiate a disk usage list
    log.log( "<otto>ottoguts(), creating df list", 8 )
    directive.dlist = df.dfList()

    ## debugging ##
    #print "-- The following DEFs are defined: --"
    #for i in defDict.keys():
    #	print "%s=%s" % (i, defDict[i])
    #print "-- The following Ms are defined: --"
    #for i in MDict.keys():
    #	print "%s: Subject \"%s\"\n---BODY---\n%s\n----------" % (i, MDict.subj(i), MDict[i])
    #print "-- The following As are defined: --"
    #for i in ADict.keys():
    #	print "%s=%s" % (i, ADict[i])

    # Now do all the checking
    # note ... directive order is not defined (we don't currently care do we?)
    log.log( "<otto>ottoguts(), beginning checks", 8 )

    ## debugging - test with 'D' directive for now ##
    ## for d in ourList.keylist():
    for d in ('FS',):
	list = ourList[d]
	if list != None:
	    for i in list:
		i.docheck()
	else:
	    log.log( "<otto>ottoguts(), ourList['%s'] is empty" % (d), 6 )

    # Save history (debug.. FS only for now...)
    ottoHistory.save('FS',directive.dlist)
    ottoHistory.save('PS',directive.plist)



def main():
    history.ottoHistory = history.history()

    # Main Loop
    while 1:
	try:
	    ottoguts(history.ottoHistory)

	    log.log( '<otto>main(), sleeping for %d secs' % (config.scanperiod), 6 )
	    print 'Press CTRL-C to quit'
	    time.sleep( config.scanperiod )
	except KeyboardInterrupt:
	    log.log( '<otto>main(), KeyboardInterrupt encountered - quitting', 2 )
	    print "\nOtto quitting ... bye bye"
	    break



if __name__ == "__main__":
    main()

###
### END otto.py
###
