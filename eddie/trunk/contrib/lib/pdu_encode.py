#!/opt/local/bin/python
## 
## File         : pdu_encode.py 
## 
## Author       : Rod Telford  <rtelford@connect.com.au>
##                Chris Miles  <cmiles@connect.com.au>
## 
## Date         : 980518
## 
## Description  : encodes to PDU format for SMS paging
##
## $Id$
##

import sys, string
from math import log

def encodeSM(mess):

    len_i = len(mess)
    len_h = "%02x" % len_i

    eb = sto8bit(mess)    
    enc = to7bb(eb)
    hex_s = enc2hex(enc)
    return "%s%s" % (len_h, hex_s)

# convert an ascii string to a 8bit ascii coded bit string
def sto8bit(mess):
    bits = ""
    l = len(mess)

    i = l - 1
    while i >= 0:
        bits = bits + binary(ord(mess[i]))
	i = i - 1

    return bits

# convert an 8bit ASCII encoded bit string into a 7bit packed bit string
def to7bb(mess):
    ret = ""

    l = len(mess)
    (num, rem) = divmod(l, 8)

    for i in range(0, num + 1): 
        byte = ['0','0','0','0','0','0','0','0']

        for j in range(0, 8):
	    off = l - (8*i) - j - 1
	    if (off >= 0):
	        byte[7 - j] = mess[off]

	ret = ret + string.join(byte, "")

    return(ret)

def enc2hex(enc_bin):
    ret = ""

    hex = { '0000' : '0', '0001' : '1', '0010' : '2', '0011' : '3', \
            '0100' : '4', '0101' : '5', '0110' : '6', '0111' : '7', \
            '1000' : '8', '1001' : '9', '1010' : 'a', '1011' : 'b', \
            '1100' : 'c', '1101' : 'd', '1110' : 'e', '1111' : 'f'     }

    l = len(enc_bin) / 4

    for i in range(0, l):
        first = i * 4
        last = first + 4
        key = enc_bin[first:last]
        ret = ret + hex[key] 

    return(ret)

# return a bit string rep of a given number
def binary(num):
    bits = int(log(num)/log(2) + 1) 
    out = []

    # is this the full seven bits
    pad = 7 - bits
    for i in range(0, pad):
        out.append("0")


    for i in range(bits, 0, -1):
        i = i - 1
	if (num & pow(2,i)):
	    out.append("1")
	else:
	    out.append("0")

    return(string.join(out, ""))

def encPhone(phno):
    
    phno = "%s" % phno[:-1]
    ret = '%02x91' % (len(phno) - 1)

    for i in range(1, len(phno), 2):
	try:
            ret = ret + "%c%c" % (phno[i+1], phno[i])
        except IndexError:
            ret = ret + "F%c" % (phno[i])
	
    return(ret)

if __name__ == "__main__":
    print "Enter Message: ",
    m = sys.stdin.readline()
    string.strip(m)
    e = encodeSM(m)

    print "Enter Phone: ",
    p = sys.stdin.readline()
    string.strip(p)
    ps = encPhone(p)
    print "1100%s0000AA%s" % (ps, e)
    sys.exit(0)
    
