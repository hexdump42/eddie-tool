#!/opt/local/bin/python 
## 
## File         : snpp.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date         : 980417
## 
## Description  : Implementation of rfc1861 client. Note only level
##                one paging is supported at this time	
##
## $Id$
##
##

import string
from socket import *

SNPPpageFail = 'SNPPpageFail'

class level1:
    def __init__(self, host='pagehost', port=444):
	self.host = host
	self.port = port
	self.mess = None
	self.page = None

    def pager(self, p):
	self.page = p

    def message(self, m):
	self.mess = m

    def send(self):

    	if self.page == None:
	    raise SNPPpageFail, "No destination pager Id defined"

    	if self.mess == None:
	    raise SNPPpageFail, "You have no specified a message"

	s = socket(AF_INET, SOCK_STREAM)

	# connect to the SNPP host
	s.connect(self.host, self.port)

	ret = s.recv(1024)
	rc = string.split(ret)[0]

	if rc != '220':
 	    raise SNPPpageFail, "%s" % ret

	# Send the Page ID
	s.send('PAGE %d\n' % self.page)
	ret = s.recv(1024)
	rc = string.split(ret)[0]

	if rc != '250':
 	    raise SNPPpageFail, "%s" % ret

	# Send the Message
	s.send('MESS %s\n' % self.mess)
	ret = s.recv(1024)
	rc = string.split(ret)[0]

	if rc != '250':
 	    raise SNPPpageFail, "%d" % ret

 	s.send('SEND\n')
 	ret = s.recv(1024)
	rc = string.split(ret)[0]
	
	if rc != '250':
 	    raise SNPPpageFail, "%d" % ret

	# send a disconnect and ignore the output
	s.send('QUIT\n')
	s.recv(1024)

	s.close()

##
## END - snpp.py
##

