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
## $Id
##


import proc
import df
import parseConfig
import directive
import config

# main config file - this file INCLUDEs all other config files
config_file = 'config/otto.cf'

def main():

    # global list of all directives
    global ourList
    ourList = directive.Rules()
 
    # read in config and rules
    parseConfig.readFile(config_file, ourList)
 
    print "M: ",ourList['M']
    print "D: ",ourList['D']
    print "FS: ",ourList['FS']
    print "PID: ",ourList['PID']
    print "SP: ",ourList['SP']

    
    # instantiate a process list
    p = proc.procList()
    #print p

    # instantiate a disk usage list
    d = df.dfList()
    #print d

    # Parse all configuration options
    # (... and remove them from the Rules List ...)
    # !! TODO !!
    config.parseConfig( ourList );

    # Define Messages (M-directives)
    # (... and remove them from the Rules List ...)
    # !! TODO !!
    ourList.delete( 'M' )

    # Now do all the checking
    # note ... directive order is not defined (we don't currently care do we?)
    for d in ourList.keylist():
	print "d = ",d
	#eval('directive.'+d+'.docheck()')

if __name__ == "__main__":
    main()

