#!/opt/local/bin/python

import proc
import df

def main():
    
    # instansiate a process list
#   p = proc.procList()
#   print p

    # instansiate a disk usage list
    d = df.dfList()
    print d

if __name__ == "__main__":
    main()

