##
## File	       : p_iostat_class.py
##
## Author      : Rod Telford <rtelford@connect.com.au>
##
## Date        : 980728
##
## Description : An implementation of an iostat class
##
## $Id$
##

import sys
import string
import solkstat

##
## Class p_iostat
##
class p_iostat:
    def __init__(self):
	self.head = solkstat.open()

	self.data     = {}
	self.old_data = {}
	
	self.snaptime     = {}
	self.old_snaptime = {}

	self.stats = {}

	# OK initalise and array of disk_names
	# and initalise the old_data and old_snamptime

	tmp = self.head
	while tmp:
	    if tmp.ks_type == 3:
	        name = tmp.ks_name
		data = tmp.ks_data

	        self.old_data[name] = data
		self.data[name]     = data

		self.old_snaptime[name] = tmp.ks_snaptime
		self.snaptime[name]     = tmp.ks_snaptime

		# can't assign to stat as it DOESN'T copy dictionary, uses
		# same one for all!
		self.stats[name] = { 'reads' : 0,        'writes' : 0,
	                            'kreads' : 0,       'kwrites' : 0,
	                          'avg_wait' : 0,       'ave_run' : 0,
	                     'ave_wait_time' : 0, 'ave_serv_time' : 0,
	                           'service' : 0,  'wait_percent' : 0,   
	                           'putthru' : 0                        }
		
	    tmp = tmp.getnext()

        self.disk_names = self.data.keys()
    

    def getSnapshot(self):
	tmp = self.head
	while tmp:
	    if tmp.ks_type == 3:
	        name = tmp.ks_name

		# save the old values
 	        self.old_data[name]     = self.data[name]
	        self.old_snaptime[name] = self.snaptime[name]

		# Get some new values
		self.data[name]       = tmp.ks_data
		self.snaptime[name]   = tmp.ks_snaptime

		self.calculate_stat(name)


	    tmp = tmp.getnext()

	    
    def calculate_stat(self, name):
	# how much time has elapsed
	hr_etime = (self.snaptime[name] - self.old_snaptime[name]) 
	etime = hr_etime / 1000000000L / 1.0

	if hr_etime == 0:
	    hr_etime = 10000000000L

	# set up reads per sec
	rds = (self.data[name]['reads']  - self.old_data[name]['reads']) 
	rps = rds / etime
	self.stats[name]['reads'] = rps 

	# get writes per sec
	wts = (self.data[name]['writes']  - self.old_data[name]['writes'])
	wps = wts / etime
	self.stats[name]['writes'] = wps 

	# set up putthru ( the recipricol of thruput)
	putthru = wts + rds
	if putthru != 0:
	    putthru = (10.0 / putthru) * etime

	self.stats[name]['putthru'] = putthru

	# get krp/s
	krps = (self.data[name]['nread']  - self.old_data[name]['nread'])
	self.stats[name]['kreads'] = (krps / etime) / 1024

	# get kwp/s
	kwps = (self.data[name]['nwritten']  - self.old_data[name]['nwritten'])
	self.stats[name]['kwrites'] = (kwps / etime) / 1024

	# Calculate the average read time
	avw = (self.data[name]['wlentime']  - self.old_data[name]['wlentime']) * (1.0 / hr_etime)
	self.stats[name]['avg_wait'] = avw 

	# Calculate the average write time
	avr = (self.data[name]['rlentime']  - self.old_data[name]['rlentime']) * (1.0 / hr_etime)
	self.stats[name]['avg_run'] = avr 

        # Calculate the ave wait time and ave serv time
	read_writes = rps + wps

	if read_writes > 0:
	    avwait = (avw * 1000.0) / read_writes
	    avserv = (avr * 1000.0) / read_writes
	else:
	    avwait = 0.0
	    avserv = 0.0

	self.stats[name]['avg_wait_time'] = avwait
	self.stats[name]['avg_serv_time'] = avserv
	self.stats[name]['service'] = avserv + avwait

	# Calculate the wait percent
	w_pct = (self.data[name]['wtime']  - self.old_data[name]['wtime']) * 100.0
	self.stats[name]['wait_percent'] = w_pct / hr_etime

	# Calculate the run percent
	r_pct = (self.data[name]['rtime']  - self.old_data[name]['rtime']) * 100.0
	self.stats[name]['run_percent'] = r_pct / hr_etime


