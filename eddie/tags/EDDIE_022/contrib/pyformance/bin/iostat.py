#!/opt/python/bin/python
##
## File        : iostat.py
##
## Author      : Rod Telford <rtelford@connect.com.au>
##
## Date        : 980728
##
## Description : Tricked up iostat in python
##
## $Id$
##

import sys
import time
import string
import getopt
import signal
from p_iostat_class import *

def main():
    global interval
    global iostat

    signal.signal( signal.SIGALRM, signal.SIG_IGN )
    signal.signal( signal.SIGTERM, exit )
    signal.signal( signal.SIGINT, exit )
    
    # get the options and args
    opts, args = getopt.getopt(sys.argv[1:], '')

    # args[0] should be the interval
    try:
        interval = int(args[0])
    except IndexError:
        interval = 5

    iostat = p_iostat()

    print "please wait %d secs" % (interval)

    # If iterations not specified loop forever
    try:
        for i in range(int(args[1])):
	    doIostat()
    except IndexError:
        while 1:
	    doIostat()


def doIostat():
    #time.sleep(interval)
    signal.alarm(interval)
    signal.pause()

    iostat.getSnapshot()

    # print the header
    print "          ------throughput------ -----wait queue----- -----active queue-----"
    print "disk      r/s  w/s   Kr/s   Kw/s qlen res_t svc_t %ut qlen  res_t  svc_t %ut"

    iostat.disk_names.sort()

    # for each disk on this machine
    for disk in iostat.disk_names:
	# deref the stat for this disk
	stat = iostat.stats[disk]

	# print out the stats
	print "%-8.8s" % (disk),
	print "%4.1f" % (stat['reads']),
	print "%4.1f" % (stat['writes']),
	print "%6.1f" % (stat['kreads']),
	print "%6.1f" % (stat['kwrites']),

	print "%4.2f" % (stat['avg_wait']),
	print "%5.2f" % (stat['avg_wait_time']),
	print "%5.2f" % (stat['wait_percent'] * stat['putthru']),
	print "%3.0f" % (stat['wait_percent']),

	print "%4.2f" % (stat['avg_run']),
	print "%6.2f" % (stat['avg_serv_time']),
	print "%6.2f" % (stat['run_percent'] * stat['putthru']),
	print "%3.0f" % (stat['run_percent'])

def exit(*args):
    print
    sys.exit()

if __name__ == "__main__":
    main()



