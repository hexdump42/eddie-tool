#!/opt/local/bin/python
##
## File         : elvinPaged.py
##
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
##
## Date         : 980418
##
## Description  : Elvin consumer for paging 
##
## $Id$
##


import time, types, os, sys, thread, signal, getopt
import eddieElvin


if __name__ == "__main__":
 
    p = eddieElvin.elvinPage()
    p.subscribe()
 
    try:
        signal.pause()
    except:
        sys.exit(0)

