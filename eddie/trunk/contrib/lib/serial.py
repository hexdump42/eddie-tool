#!/opt/local/bin/python
## 
## File         : serial.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date         : 980518
## 
## Description  : This does unbuffered IO to a serial port 
##
## $Id$
##
##

import os, sys, fcntl, termios, select
from TERMIOS import *
from FCNTL import *

class modem:
    def __init__(self, *arg):
	self.timedout = 0
	self.open()

    def open(self, portName="/dev/cua/b"):

	# ok lets try setting up the serial port
	try:
	    # You probably just want to use the builtin open(), here...
	    self.fd = os.open(portName, O_RDWR|O_NDELAY, 0777)

	    # Set up symbolic constants for the list elements returned by
	    # tcgetattr.
	    [iflag, oflag, cflag, lflag, ispeed, ospeed, cc] = range(7)

	    # Get the port baud rate, etc.
	    settings = termios.tcgetattr(self.fd)

	    # Set the baud rate.
	    settings[ospeed] = B9600 # Output speed
	    settings[ispeed] = B0    # Input speed (B0 => match output)

	    # Go for 8N1 with hardware handshaking.
	    settings[cflag] = (((settings[cflag] & ~CSIZE) | CS8) & ~PARENB)

	    # NOTE:  This code relies on an UNDOCUMENTED
	    # feature of Solaris 2.4. Answerbook explicitly states
	    # that CRTSCTS will not work.  After much searching you
	    # will discover that termiox ioctl() calls are to
	    # be used for this purpose.  After reviewing Sunsolve
	    # databases, you will find that termiox's TCGETX/TCSETX
	    # are not implemented.  *snarl*
	    settings[cflag] = settings[cflag] | CRTSCTS

	    # Don't echo received chars, or do erase or kill input processing.
	    settings[lflag] = (settings[lflag] & ~(ECHO | ICANON))

	    # Do NO output processing.
	    settings[oflag] = 0

	    # Install the modified line settings.
	    termios.tcsetattr(self.fd, TCSANOW, settings)

	    # Set it up for non-blocking I/O.
	    fcntl.fcntl(self.fd, F_SETFL, O_NONBLOCK)

	    self.fdo = os.fdopen(self.fd)

	except os.error, info:
            # mention prot name in error
            raise os.error, "Can't open %s: %s" % (portName, info)

    #
    # A function to write data to the serial port
    #
    def write(self, text):
        os.write(self.fd, text)
	self.fdo.flush()

    #
    # A function to read from the serial port
    #
    def getline(self, t_out):

	self.timedout = 0
	ret = ""

        while (self.timedout == 0):
	    sel = select.select([self.fd], [], [], t_out)

	    if (sel[0] != []):
		c = os.read(self.fd, 1)

		if((ord(c) == 10) or (ord(c) == 13)):
		    return ret
		else:
		    ret = ret + c 
	    else:
	        self.timedout = 1
		return ret

    #
    # A function to lookfor a string
    #
    def lookfor(self, find_str, t_out):
        str = self.getline(t_out)
	self.found = 0

	while (self.timedout == 0):
	    if (str == find_str):
	        return 1

	    str = self.getline(t_out)

	if (str == find_str):
	    return 1
        else:
	    return 0


    def close(self):
	os.close(self.fd)

#
# This is a test driver
#
if __name__ == "__main__":
    print "Running test page to 0414786118"
    m = modem()

    m.write("at+cmgs=160\r")
    pf = m.lookfor("> ", 1)

    if (pf == 1):
        m.write("11000b911614746811F80000AA0f54747a0e4acf416110bd3ca72b00\r\n")
        of = m.lookfor("OK", 10)

    if ( of == 1):
        print "found ok"
        print "message sent"

    m.close()
    sys.exit(0)

