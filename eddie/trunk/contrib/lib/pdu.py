#!/opt/local/bin/python
## 
## File         : pdu.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date         : 980518
## 
## Description  : object class to SMS pdu format
##
## $Id$
##

import sys, string
import pdu_utils

class pdu:
    def __init__(self, *arg):
	self.pdu_enc = { 
	            "pdu_type" : None,    # this is a foo foo
		    "mr"       : "00",
		    "ph_len"   : None,
		    "ph_type"  : "91",
		    "oada"     : None,
		    "pid"      : "00",
		    "enc_type" : "00",
		    "vp"       : "AA",
		    "udl"      : None,
		    "ud"       : None	}     

	#
	# OK we are initiating a message to send
	#
	if (len(arg) == 2):
	    self.phone       = arg[0]   # set the clear text phone
	    self.message     = arg[1]   # set the clear text message
	    self.type        = 1        # 1 is orginated 0 is termainated 
	    self['pdu_type'] = "11"     # ditto

	    self.encPhone()     # encode the phone number
	    self.encodeSM()     # encode the message
    
    def __setitem__(self, key, val):
	self.pdu_enc[key] = val

    def __getitem__(self, key):
        try:
	    return(self.pdu_enc[key])
	except KeyError:
	    return None

    def __str__(self):
	ret = "%s%s%s%s%s%s%s%s%s%s" % (self['pdu_type'],
	 				self['mr'],
	 				self['ph_len'],
	 				self['ph_type'],
	 				self['oada'],
	 				self['pid'],
	 				self['enc_type'],
	 				self['vp'],
	 				self['udl'],
	 				self['ud'])

	return(ret)
        

    def encPhone(self):
    
        print self.phone
        len_h = '%02x' % (len(self.phone) - 1)
        ret = ''

        for i in range(1, len(self.phone), 2):
	    try:
		ret = ret + "%c%c" % (self.phone[i+1], self.phone[i])
	    except IndexError:
		ret = ret + "F%c" % (self.phone[i])
	
	self.pdu_enc['ph_len'] = len_h
	self.pdu_enc['oada']   = ret

	return(0)


    def encodeSM(self):

	len_i = len(self.message)
	len_h = "%02x" % len_i

	eb       = pdu_utils.sto8bit(self.message)    
	enc      = pdu_utils.to7bb(eb)
	hex_s    = pdu_utils.enc2hex(enc)

	self.pdu_enc['udl'] = len_h
	self.pdu_enc['ud']  = hex_s
	return(0)


if __name__ == "__main__":
    print "Enter Message: ",
    m = sys.stdin.readline()
   # m = "%s" % m[:-1]

    print "Enter Phone: ",
    p = sys.stdin.readline()
    p = "%s" % p[:-1]

    my_pdu = pdu(p, m)
    foo = str( my_pdu )
    print foo

    sys.exit(0)
    
