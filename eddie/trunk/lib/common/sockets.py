#!/usr/local/bin/python
##
## File         : sockets.py
##
## Author       : Rod Telford  <rtelford@codefx.com.au>
##                Chris Miles  <cmiles@codefx.com.au>
##
## Start Date   : 20010615
##
## Description  : provides a sockets interface into the
##                running eddie state
##
## $Id$
##
########################################################################
## (C) CodeFX 2001
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



import sys,os,socket,string,select,time,threading
import log

# class wrapper for socket
class socketstate:
    def __init__(self,family,type,s=None):
        #self.state=CONNECTING
        self.fields=['V1.0',string.zfill('0',6),string.zfill('0',5),'0','0',string.zfill('0',8),string.zfill('0',8),string.zfill('0',20),string.zfill('0',5),'0001']
        self.comment=''
        self.resendonerror=1
        self.family=family
        self.type=type
        if s:
            self.s=s
        else:
            self.s=socket.socket(family,type)
            self.s.setsockopt (
                socket.SOL_SOCKET, socket.SO_REUSEADDR,
                self.s.getsockopt (socket.SOL_SOCKET, 
                                   socket.SO_REUSEADDR) | 1)


    def accept(self):
        conn,addr=self.s.accept()
        return socketstate(self.family,self.type,conn),addr

    def __getattr__(self,name):
        if self.s:
            return getattr(self.s,name)
        else:
            return None


def listen(s, Config, die_event):

    while not die_event.isSet():
        # Select timeout 1 second
        r,w,e=select.select([s],[s],[s], 1.0)
        if r:
            ccsock, addr = s.accept()

            ccsock.send('Eddie Console Gateway - eddie v%s CodeFX 2001\n' % "0.25")

            # Loop the active config and print the state of each rule
            for d in Config.ruleList.keys():
                list = Config.ruleList[d]
                if list != None:
                    for i in list:
                        # if directive template is 'self', do not schedule it
                        if i.args.template != 'self':
                            ccsock.send("%s - %s\n" % (i, i.state.status))
			
            ccsock.close()


def console_server_thread(Config, die_event, consport):

    socketerrors = 0
    s = None
    while not die_event.isSet():
        try:
            # set up socket if required
            if s == None:
                s=socketstate(socket.AF_INET,socket.SOCK_STREAM)
                s.bind('', consport)

            s.listen(50)

            log.log( "<sockets>console_server_thread(), Bind to port %d successful" % (consport), 6 )

            # main loop
            listen(s, Config, die_event)

            s.close()

        except socket.error:
            socketerrors = socketerrors + 1
            s.close()
            s = None

            if sys.exc_value[0] == 125:         # port already in use
                log.log("<sockets>console_server_thread(), Port %d already in use." % (consport), 6 )
                exit(2)

            if sys.exc_value[0] == 131:         # 'Connection reset by peer'
                log.log( "<sockets>console_server_thread(), Connection reset by peer - continuing.", 8 )
                continue

            log.log( "<sockets>console_server_thread(), Socket error - resetting socket and continuing: %s, %s" % (sys.exc_type,sys.exc_value), 8 )

            if socketerrors > 100:
                log.log( "<sockets>console_server_thread(), Too many socket errors ... exiting.", 7 )
                exit(5)


