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

config_file = 'config/otto.cf'

def main():

    global ourList
    ourList = directive.Rules()
 
    file = config.rules
    parseConfig.readFile(config_file, ourList)
 
    print "M: ",ourList['M']
    print "D: ",ourList['D']
    print "FS: ",ourList['FS']
    print "PID: ",ourList['PID']
    print "SP: ",ourList['SP']

    
    # instansiate a process list
    p = proc.procList()
#   print p

    # instansiate a disk usage list
    d = df.dfList()
#   print d

if __name__ == "__main__":
    main()

