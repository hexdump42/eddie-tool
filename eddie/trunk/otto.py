#!/opt/local/bin/python

import proc
import df
import parseConfig
import directive
import config

def main():

    global ourList
    ourList = directive.Rules()
 
    file = config.rules
    parseConfig.readFile(file, ourList)
 
    print ourList
    print ourList['M']

    
    # instansiate a process list
    p = proc.procList()
#   print p

    # instansiate a disk usage list
    d = df.dfList()
#   print d

if __name__ == "__main__":
    main()

