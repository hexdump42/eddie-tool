##
## File         : elvinPaged.py
##
## Author       : Rod Telford  <rtelford@codefx.com.au>
##                Chris Miles  <cmiles@codefx.com.au>
##
## Date         : 980418
##
## Description  : Elvin consumer for paging 
##
## $Id$
##
########################################################################
## (C) Chris Miles 2001
##
## The author accepts no responsibility for the use of this software and
## provides it on an ``as is'' basis without express or implied warranty.
##
## Redistribution and use in source and binary forms are permitted
## provided that this notice is preserved and due credit is given
## to the original author and the contributors.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
########################################################################


import time, types, os, sys, thread, signal, getopt
import eddieElvin


if __name__ == "__main__":
 
    p = eddieElvin.elvinPage()
    p.subscribe()
 
    try:
        signal.pause()
    except:
        sys.exit(0)

