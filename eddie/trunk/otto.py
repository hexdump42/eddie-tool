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

# main config file - this file INCLUDEs all other config files
config_file = 'config/otto.cf'

def main():


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
    p = proc.procList()
    #print p

    # instantiate a disk usage list
    d = df.dfList()
    #print d

    print "-- The following DEFs are defined: --"
    for i in defDict.keys():
	print "%s=%s" % (i, defDict[i])
    print "-- The following Ms are defined: --"
    for i in MDict.keys():
	print "%s: Subject \"%s\"\n---BODY---\n%s\n----------" % (i, MDict.subj(i), MDict[i])

    # Now do all the checking
    # note ... directive order is not defined (we don't currently care do we?)
    #for d in ourList.keylist():
    #    print "d = ",d
    #    #eval('directive.'+d+'.docheck()')

if __name__ == "__main__":
    main()

