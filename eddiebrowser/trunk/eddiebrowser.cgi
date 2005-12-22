#! /usr/bin/env python

"""
   eddiebrowser - http://eddie-tool.net/eddiebrowser/

    A smart CGI interface for browsing and graphing RRD stats.  Can be used
    with any RRDs but commonly used in conjuction with EDDIE Tool and
    ElvinRRD generated system/network RRD stats.
    (c) Chris Miles 2002-2005 http://chrismiles.info/
  
   $Id$
   $URL$
"""


#### Settings ####

## GLOBAL_CONFIG: location of global config file
GLOBAL_CONFIG = '/opt/eddiebrowser/configs/eddiebrowser.cfg'

#### End of settings ####


__version__ = '0.6.2-svn'
__copyright__ = 'Chris Miles 2002-2005'


import cgi
import os
import sys
import traceback
import string
import re
import cgitb

cgitb.enable()

try:
    import rrdtool		# Included in rrdtool package; or
    				# py-rrdtool from http://sourceforge.net/projects/py-rrdtool/
				#              or http://www.nongnu.org/py-rrdtool/
except ImportError,msg:
    raise "Cannot import rrdtool module - get this from http://sourceforge.net/projects/py-rrdtool/",msg
    sys.exit( -1 )


class GlobalConfig:
    def __init__(self):
	self.settings = {}

	self.settings['ho'] = 'h'		# order by hosts (default)
	self.settings['start'] = "-151200"	# daily view (default)
	self.settings['width'] = None
	self.settings['zoom'] = None
	self.settings['smooth'] = None
	self.aliases = {}
	self.hosts = []				# list of all hostnames
	self.datanames = []			# list of all data names
	self.datagroups = {}			# dict of all data groups
	self.filter = None			# Filter object
	try:
	    self.rrd_dir = RRD_DIR		# Default to global var RRD_DIR if possible
	except NameError:
	    self.rrd_dir = None
	self.rrd_conf_dir = None
	self.dummy_rrd = 'dummy.rrd'


    def parseGlobalConfig(self,cfgfile):
	"""parseGlobalConfig( location_of_config_file )
	Read global settings.
	"""

	try:
	    fp = open( cfgfile, 'r' )
	except IOError, err:
	    # Global config file is optional - not worth raising exception about it missing
	    #raise IOError, "Cannot open global config file: %s (%s)"%(cfgfile,err)
	    return

	cfg_re = "([a-zA-Z0-9_]+?) (.+)"
	inx = re.compile(cfg_re)

	line = fp.readline()
	while len(line) != 0:
	    line = string.strip(line)
	    if len(line) > 0 and line[0] != '#':
		sre = inx.match(line)
		if sre:
		    if sre.group(1) == 'alias':
			self.setAlias(sre.group(2))
		    elif sre.group(1) == 'rrd_dir':
			self.rrd_dir = sre.group(2)
		    elif sre.group(1) == 'rrd_conf_dir':
			self.rrd_conf_dir = sre.group(2)
		    elif sre.group(1) == 'dummy_rrd':
			self.dummy_rrd = sre.group(2)

	    line = fp.readline()

	fp.close()


    def parseForm(self, form):
	"""parseForm: parse options from cgi form fields.
	"""

	for s in self.settings.keys():
	    if s in form.keys():
		self.settings[s] = form[s].value


    def setAlias(self, aliasstr):
	"""setAlias: set an alias from config string
	"""

	alias_re = "([a-zA-Z0-9_]+?) (.+)"
	inx = re.compile(alias_re)

	sre = inx.match(aliasstr)
	if sre:
	    self.aliases[sre.group(1)] = sre.group(2)
	else:
	    raise "GlobalConfigError", "Error with alias: %s"%(aliasstr)


    def aliasSort( self, a, b ):
	"""aliasSort: sort by aliases keyed by a and b.
	Case insensitive sort.
	"""

	if a not in self.aliases.keys() and b not in self.aliases.keys():
	    if a.lower() < b.lower():
		return -1
	    elif a.lower() > b.lower():
		return 1
	    else:
		return 0
	if a not in self.aliases.keys():
	    return 1
	if b not in self.aliases.keys():
	    return -1
	if self.aliases[a].lower() < self.aliases[b].lower():
	    return -1
	elif self.aliases[a].lower() > self.aliases[b].lower():
	    return 1
	else:
	    return 0


    def keepSettings(self, type='form', exclude=()):
        """keepSettings: return string of current settings for use in forms
	If type=='form': print settings as hidden form fields (default)
	If type=='get': print settings as URL fields
	Returns a string of either type.
	Any fields listed in the exclude list will be excluded.
	"""

	settingstr = ""

	if type=='form':
	    for s in self.settings.keys():
		if s not in exclude and self.settings[s]:
		    settingstr += '<input type="hidden" name="%s" value="%s">\n' % (s,self.settings[s])
	    if self.filter and 'fltgroup' not in exclude:
		for g in self.filter.filtergroups:
		    settingstr += '<input type="hidden" name="fltgroup" value="%s">\n' % (g)

	elif type=='get':
	    settings = []
	    for s in self.settings.keys():
		if s not in exclude and self.settings[s]:
		    settings.append( '%s=%s' % (s,self.settings[s]) )
	    if self.filter and 'fltgroup' not in exclude:
		for g in self.filter.filtergroups:
		    settings.append( 'fltgroup=%s' % (g) )
	    settingstr = string.join( settings, '&' )

	return settingstr


    # chris 2003-06-22: Read all settings from dir/.eddiebrowser.cfg
    #	into GlobalConfig object.
    def readDirConfigs( self ):
	"""Read settings from all required data type specific config files.
	"""

	dirs = os.listdir( self.rrd_dir )
	for d in dirs:
	    datadir = os.path.join( self.rrd_dir, d )
	    # First try rrd_conf_dir/<datatype>.cfg
	    conf1 = os.path.join( self.rrd_conf_dir, d + ".cfg" )
	    if os.path.exists( conf1 ):
		self.getSettingsFromDir( conf1, datadir )
	    else:
		# Second try rrd_dir/<datatype>/.eddiebrowser.cfg
		conf2 = os.path.join( self.rrd_dir, d, ".eddiebrowser.cfg" )
		self.getSettingsFromDir( conf2, datadir )


    def getSettingsFromDir( self, cfgfile, datadir ):
	"""Read data type specific settings from cfgfile.
	"""

	cfg = parseConfig( cfgfile )
	if cfg == None:
	    return None

	# Get data name
	dataname = cfg['NAME']
	self.datanames.append( dataname )

	# Get data group
	try:
	    groupname = cfg['GROUP']
	    if groupname in self.datagroups.keys():
		self.datagroups[groupname].append( dataname )
	    else:
		self.datagroups[groupname] = [dataname,]
	except KeyError:
	    pass	# GROUP is optional

	# Get hostnames from filenames
	files = cfg['FILES']
	inx = re.compile( files )

	for f in os.listdir( datadir ):
	    sre = inx.match(f)
	    if sre != None:
		h = sre.group('hostname')
		if h not in self.hosts:
		    self.hosts.append(h)


    def getAllHosts( self ):
	"""Return list of hostnames."""

	return self.hosts


    def parseFilter( self, form ):
	"""Create a filter if required."""

	self.filter = Filter( form )
	if not self.filter.on:
	    self.filter = None
	    return None
	else:
	    return self.filter



def parseConfig( cfgfile ):
    cfg = {}	# config dictionary

    #cfgfile = os.path.join( dir, ".eddiebrowser.cfg" )

    try:
	fp = open( cfgfile, 'r' )
    except IOError, err:
	return None

    cfg_re = "([a-zA-Z0-9_:]+?)=(.+)"
    inx = re.compile(cfg_re)

    line = fp.readline()
    while len(line) != 0:
	line = string.strip(line)
	if len(line) > 0 and line[0] != '#':
	    #(var, val) = string.split(line, '=')
	    sre = inx.match(line)
	    if sre:
		cfg[sre.group(1)] = sre.group(2)
	line = fp.readline()

    fp.close()

    return cfg




def nocaseSort( a, b ):
    """nocaseSort: sort strings, ignore case (i.e., alphabetic sort)
    """

    if a.lower() < b.lower():
	return -1
    elif a.lower() > b.lower():
	return 1
    else:
	return 0


def controlPanel(cfg):
    print "<HEAD><Title>eddiebrowser control panel</Title>"
    print """<SCRIPT TYPE="text/javascript">
	<!--
	function eb_selectallfltgroups() {
	    // Select all checkboxes in the selecthost form with ids beginning
	    //   with 'fltgroup_'
	    changeAllFormChecks( 'selecthost', 'fltgroup_', true );
	}
	function eb_unselectallfltgroups() {
	    // Un-select all checkboxes in the selecthost form with ids beginning
	    //   with 'fltgroup_'
	    changeAllFormChecks( 'selecthost', 'fltgroup_', false );
	}
	function changeAllFormChecks(formid, checkid, checked) {
	    // Select or unselect all checkboxes within a form.
	    //  form : form id
	    //  checkid : partial id of checkboxes to match
	    //  checked : true or false
	    form = document.getElementById(formid);
	    for(i=0; i<form.elements.length; i++) {
		if(form[i].type == 'checkbox' && form[i].id.substring(0,checkid.length) == checkid) {
		    form[i].checked = checked;
		}
	    }
	}
	//-->
	</SCRIPT>"""
    print "</HEAD><BODY>"

    print "<center><b>EDDIE RRD Browser (v%s)</b>" % (__version__)
    print "<br>&copy; %s</center>" % (__copyright__)

    cfg.readDirConfigs()
    hosts = cfg.getAllHosts()


    print "<form id='selecthost' name='selecthost' action='%s' method=GET>" % (os.environ['SCRIPT_NAME'])

    print '<Table border="0">'
    print '<tr valign="top"><td rowspan="2"><p>Select a host</p>'

    print cfg.keepSettings(type='form', exclude=('fltgroup',))	# print settings as hidden fields

    print "<select name='hostname' onChange=selecthost.submit()>"

    if cfg.settings['ho'] == 'a':
	# sort by aliases
	hosts.sort(cfg.aliasSort)
	for h in hosts:
	    print "<option value='%s'>" % (h)
	    if h in cfg.aliases.keys():
		print "%s" % (cfg.aliases[h])
		print " (%s)"%(h)
	    else:
		print "%s"%(h)
    else:
	# sort by hostnames
	hosts.sort(nocaseSort)
	for h in hosts:
	    print "<option value='%s'>%s" % (h,h)
	    if h in cfg.aliases:
		print " (%s)"%(cfg.aliases[h])

    print "</select>"
    print '<input type=submit value="GO"><br>'

    if cfg.settings['ho'] == 'a':
	print '<font size=-1>[<a href="%s?ho=h">sort by hostname</a>]</font>' % (os.environ['SCRIPT_NAME'])
    else:
	print '<font size=-1>[<a href="%s?ho=a">sort by alias</a>]</font>' % (os.environ['SCRIPT_NAME'])

    print "</td>"

    # chris 2003-06-22: show options for restricting to selected data types
    #	or data groups.

    print '<td align="left" colspan="2">Limit DataTypes to:'
    print """<input type="button" value="Select all" onclick="javascript:eb_selectallfltgroups()"> """
    print """<input type="button" value="Select None" onclick="javascript:eb_unselectallfltgroups()"> """
    print '</td></tr>'
    print '<tr><td valign="top">'
    print "<dl>"
    groups = cfg.datagroups.keys()
    groups.sort()
    numgroups = len(groups)
    i = 0
    for g in groups:
	if cfg.filter and g in cfg.filter.filtergroups:
	    checked = 'checked'
	else:
	    checked = ''
	print '<dt><input type="checkbox" name="fltgroup" id="fltgroup_%s" value="%s" %s>%s'%(g,g,checked,g)
	# Display all data types within groups to filter on
	# - commented out for now; needs a good clean up.
#	print "<dl>"
#	for d in cfg.datagroups[g]:
#	    print '<dd><input type="checkbox" name="fltgrp%s" value="%s">%s'%(g,d,d)
#	print "</dl>"
	i += 1
	if i == numgroups/2:
	    print '</dl></td><td valign="top">'
	    print '<dl>'

    print "</dl></td></tr>"
    print "<tr><td>&nbsp;</td><td><i>If none are selected, all DataTypes will be shown.</td></tr>"
    print "</Table>"
    print "</form>"
    print "</BODY>"


def error_html( msg ):
    """Display an error as text/html, including Content-type."""

    print "Content-Type: text/html"     # html error msg
    print                               # blank line, end of headers
    print "<HTML><HEAD><Title>Error message</Title></HEAD>"
    print "<BODY>"
    print msg
    print "</BODY></HTML>"


def error_rrd( rrdtool, msg, dummy_rrd ):
    """Display an error as image/png, using RRD to display the message."""

    sys.stderr.write( "eddiebrowser.cgi: %s\n" %(str(msg)) )

    # Return the raw PNG image
    if type(msg) == type( (1,2) ):
	rrdopt = [ '--imgformat', 'PNG',
	    '-',	# stdout
	    ]
	for m in msg:
	    m = m.replace( ':', ';' )	# comments can't contain ":" !
	    rrdopt.append( 'COMMENT:%s' % (m) )
    else:
	msg = msg.replace( ':', ';' )	# comments can't contain ":" !
	rrdopt = [ '--imgformat', 'PNG',
	    '-',	# stdout
	    'COMMENT:%s' % (msg)
	    ]

    rrdopt.append( "DEF:dummy=%s:dummy:AVERAGE" %(dummy_rrd) )
    rrdopt.append( 'LINE1:dummy#ffffff' )

    rrd = rrdtool
    rrd.graph( *rrdopt )


def graph( form, globalcfg ):
    """Graph an RRD data source using pyrrdtool module."""

    print "Content-Type: image/png"     # PNG data is following
    print                               # blank line, end of headers

    try:
	rrd = form['rrd'].value
    except KeyError:
	error_html( "rrd not specified" )
	return 1

    try:
	dir = form['dir'].value
    except KeyError:
	error_html( "dir not specified" )
	return 1

    try:
	start = form['start'].value
    except KeyError:
	start = None	# optional

    try:
	zoom = form['zoom'].value
    except KeyError:
	zoom = None	# optional

    try:
	width = form['width'].value
    except KeyError:
	width = None	# optional

    try:
	step = form['step'].value
    except KeyError:
	step = None	# optional

    try:
	smooth = form['smooth'].value
    except KeyError:
	smooth = None	# optional

    if '/' in rrd or '/' in dir:
	# security check - directories not permitted
	error_html( "illegal rrd or dir" )
	return 1

    # read .eddiebrowser.cfg
    conf1 = os.path.join( globalcfg.rrd_conf_dir, dir + ".cfg" )
    if os.path.exists( conf1 ):
	cfg = parseConfig( conf1 )
    else:
	conf2 = os.path.join( globalcfg.rrd_dir, dir, ".eddiebrowser.cfg" )
	cfg = parseConfig( conf2 )

    if not cfg:
	error_rrd( rrdtool, 'Error reading config in dir: %s'%(dir), globalcfg.dummy_rrd )
	return

    files = cfg['FILES']
    inx = re.compile( files )
    sre = inx.match(rrd)
    if sre != None:
	vars = sre.groupdict()
    else:
	vars = {}

    graphoptions = [ '--imgformat', 'PNG' ]
    graphoptions += [ '--alt-autoscale-max' ]
    graphoptions += [ '--alt-y-grid' ]

    if width:
	graphoptions += [ '--width', width ]

    if zoom:
	graphoptions += [ '--zoom', zoom ]

    if step:
	graphoptions += [ '--step', step ]

    if smooth:
	graphoptions += [ '--slope-mode' ]

    # parse general options
    sourcefile = os.path.join( globalcfg.rrd_dir, dir, rrd )

    if 'GRAPH_TITLE' in cfg.keys():
	graph_title = cfg['GRAPH_TITLE'] % vars
	graphoptions.append( '--title=%s' % (graph_title) )
    if 'GRAPH_VERTICAL_LABEL' in cfg.keys():
	graphoptions.append( '--vertical-label=%s' % (cfg['GRAPH_VERTICAL_LABEL']) )
    if 'GRAPH_VERTICAL_LABEL' in cfg.keys():
	stat_fmt = cfg['GRAPH_VERTICAL_LABEL']
    else:
	stat_fmt = "%lf"
    if start:
	graphoptions.append( '--start=%s' % (start) )
    if 'GRAPH_BASE' in cfg.keys():
	graphoptions.append( '--base=%s' % (cfg['GRAPH_BASE']) )

    graphoptions.append( '-' )	# output to stdout (ie: web browser)
    pos_def = len(graphoptions)
    pos_cdef = len(graphoptions)
    pos_graph = len(graphoptions)

    # parse defs
    try:
	graphdefnames = cfg['GRAPH_DEFS'].split(',')
    except KeyError:
	error_html( 'GRAPH_DEFS missing' )
	return 1
    except:
	error_html( 'GRAPH_DEFS illegal' )
	return 1

    for d in graphdefnames:
	graphdef = {}

	if 'GRAPH_RPN_%s'%d in cfg.keys():
	    graphdef['cdef'] = cfg['GRAPH_RPN_%s'%d]
	else:
	    graphdef['cdef'] = None

	if 'GRAPH_SOURCE_%s'%d in cfg.keys():
	    graphdef['source'] = cfg['GRAPH_SOURCE_%s'%d]
	elif not graphdef['cdef']:
	    error_html( 'GRAPH_SOURCE_%s missing'%(d) )
	    return 1

	if 'GRAPH_SOURCETYPE_%s'%d in cfg.keys():
	    graphdef['sourcetype'] = cfg['GRAPH_SOURCETYPE_%s'%d]
	else:
	    graphdef['sourcetype'] = "AVERAGE"

	if 'GRAPH_FILE_%s'%d in cfg.keys():
	    graphdef['file'] = cfg['GRAPH_FILE_%s'%d]
	    if graphdef['file']:
		graphdef['file'] = graphdef['file'] % (vars)
		graphdef['file'] = os.path.join( globalcfg.rrd_dir, dir, graphdef['file'] )
	else:
	    graphdef['file'] = sourcefile

	if not os.path.isfile( graphdef['file'] ):
	    error_rrd( rrdtool, 'ERROR: cannot read RRD file: %s' % (graphdef['file']), globalcfg.dummy_rrd )
	    return 1

	if 'GRAPH_LABEL_%s'%d in cfg.keys():
	    graphdef['label'] = cfg['GRAPH_LABEL_%s'%d]
	    if graphdef['label']:
		graphdef['label'] = graphdef['label'] % (vars)
	else:
	    graphdef['label'] = ""

	if 'GRAPH_TYPE_%s'%d in cfg.keys():
	    graphdef['type'] = cfg['GRAPH_TYPE_%s'%d]
	else:
	    graphdef['type'] = None

	if 'GRAPH_COLOR_%s'%d in cfg.keys():
	    graphdef['color'] = cfg['GRAPH_COLOR_%s'%d]
	else:
	    graphdef['color'] = "000000"

	if graphdef['cdef']:
	    cdefline = 'CDEF:%s=%s' % (d, graphdef['cdef'])
	    graphoptions.insert( pos_cdef, cdefline )
	    pos_cdef += 1
	    pos_graph += 1
	else:
	    defline = 'DEF:%s=%s:%s:%s' % (d, graphdef['file'], graphdef['source'], graphdef['sourcetype'])
	    graphoptions.insert( pos_def, defline )
	    pos_def += 1
	    pos_cdef += 1
	    pos_graph += 1

	if graphdef['type']:
	    graphline = '%s:%s#%s:%s' % (graphdef['type'], d, graphdef['color'], graphdef['label'])
	    graphoptions.insert( pos_graph, graphline )
	    pos_graph += 1

	    i = 1
	    while 1:
		if 'GRAPH_GPRINT_%s%d'%(d,i) in cfg.keys():
		    gprintline = 'GPRINT:%s:%s' % (d,cfg['GRAPH_GPRINT_%s%d'%(d,i)])
		    graphoptions.insert( pos_graph, gprintline )
		    pos_graph += 1
		    i += 1
		else:
		    break
	    graphoptions.insert( pos_graph, "COMMENT:\\n" )
	    pos_graph += 1

    #error_html( "graphoptions: %s"%(graphoptions) )

    graphoptions.append( '--font=LEGEND:7' )

    try:
	# Return the raw PNG image

	rrd = rrdtool
	r = rrd.graph( *graphoptions )
	sys.stderr.write( 'r=%s'%(r) )

    except:	# catch all
	e = sys.exc_info()
	tb = traceback.format_list( traceback.extract_tb( e[2] ) )
	msg1 = "%s" % e[0]
	msg2 = "%s" % e[1]
	error_rrd( rrdtool, (msg1,msg2), globalcfg.dummy_rrd )
	return 1



def showHostInfo(dir, hostname, graph_options, globalcfg, filter=None):
    conf1 = os.path.join( globalcfg.rrd_conf_dir, dir + ".cfg" )
    if os.path.exists( conf1 ):
	cfg = parseConfig( conf1 )
    else:
	conf2 = os.path.join( globalcfg.rrd_dir, dir, ".eddiebrowser.cfg" )
	cfg = parseConfig( conf2 )

    if cfg == None:
	return None

    dir = os.path.join( globalcfg.rrd_dir, dir )

    if filter:
	if cfg['GROUP'] not in filter.filtergroups and cfg['NAME'] not in filter.filtertypes:
	    return None

    files = cfg['FILES']
    inx = re.compile( files )

    dirlist = os.listdir(dir)
    dirlist.sort()
    for f in dirlist:
    	sre = inx.match(f)
	if sre != None:
	    h = sre.group('hostname')
	    if h == hostname:
		vars = { 'filename': f }
		vars.update( sre.groupdict() )
		if 'SHOW:%s'%(hostname) in cfg.keys():
		    # use a hostname-specific SHOW if available
		    img = '<img src="%s" border=0>' % (cfg['SHOW:%s'%(hostname)])
		elif 'SHOW' in cfg.keys():
		    # otherwise just use SHOW if specified
		    img = '<img src="%s" border=0>' % (cfg['SHOW'])
		else:
		    # otherwise use built-in
		    show = "%s?mode=graph&dir=%s&rrd=%%(filename)s" % (os.environ['SCRIPT_NAME'],dir.split('/')[-1])
		    if graph_options['start']:
			show += "&start=%s" % (graph_options['start'])
		    if graph_options['width']:
			show += "&width=%s" % (graph_options['width'])
		    if graph_options['zoom']:
			show += "&zoom=%s" % (graph_options['zoom'])
		    if graph_options['step']:
			show += "&step=%s" % (graph_options['step'])
		    if graph_options['smooth']:
			show += "&smooth=1"

		    img = '<img src="%s" border=0>' % (show)
		print img % vars



def showTypes( hostname, graph_options, globalcfg, filter=None ):
    """Get types of data to show for <hostname>."""

    types = {}

    dirs = os.listdir( globalcfg.rrd_dir )
    for d in dirs:
	#dir = os.path.join( globalcfg.rrd_dir, d )
	showHostInfo(d, hostname, graph_options, globalcfg, filter)

    return


def showHost( hostname, form, cfg ):
    """Show graphs/info for host <hostname>."""

    #print '<!-- GENERATED-BY="%s" -->' % (sys.argv[0])
    print '<!-- GENERATED-BY="%s%s" -->' % (os.environ['SERVER_NAME'],os.environ['SCRIPT_NAME'])
    print '<!-- COPYRIGHT="Chris Miles http://chrismiles.info/" -->'

    print """<HEAD>
<META HTTP-EQUIV="Refresh" CONTENT="300">
<META HTTP-EQUIV="Pragma" CONTENT="no-cache">
<META HTTP-EQUIV="Expires" CONTENT="Sun, 02 Apr 2000 04:55:58 GMT">
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=iso-8859-1">

<Title>Eddie stats for %s</Title>
</HEAD>

<BODY bgcolor="white">
""" % (hostname)


    # Graph options
    graph_options = {}

    # Parse the CGI values
    try:
	graph_options['start'] = form['start'].value
    except KeyError:
	#graph_options['start'] = "-151200"		# default to daily
	graph_options['start'] = None

    try:
	graph_options['width'] = form['width'].value
    except KeyError:
	graph_options['width'] = None

    try:
	graph_options['step'] = form['step'].value
    except KeyError:
	graph_options['step'] = None

    try:
	graph_options['zoom'] = form['zoom'].value
    except KeyError:
	graph_options['zoom'] = None

    try:
	graph_options['smooth'] = form['smooth'].value
    except KeyError:
	graph_options['smooth'] = None

    cursettings = cfg.keepSettings(type='get')

    # build list of hosts as <option>s
    # chris 2003-06-22: moved host list to cfg object
    cfg.readDirConfigs()
    # chris 2003-05-26: get hosts to make selection list and next/previous links
    hosts = cfg.getAllHosts()
    hostselect_options = ""
    if cfg.settings['ho'] == 'a':
	# sort by aliases
	hosts.sort(cfg.aliasSort)
	for h in hosts:
	    selected = ''
	    if h == hostname:
		selected = 'selected'
	    hostselect_options += "<option value='%s' %s>" % (h,selected)
	    if h in cfg.aliases.keys():
		hostselect_options += "%s" % (cfg.aliases[h])
		hostselect_options += " (%s)"%(h)
	    else:
		hostselect_options += "%s"%(h)
	    hostselect_options += "</option>"
    else:
	# sort by hostnames
	hosts.sort(nocaseSort)
	for h in hosts:
	    selected = ''
	    if h == hostname:
		selected = 'selected'
	    hostselect_options += "<option value='%s' %s>%s" % (h,selected,h)
	    if h in cfg.aliases:
		hostselect_options += " (%s)"%(cfg.aliases[h])
	    hostselect_options += "</option>"
    hostselect_options += "</select>"

    hostselect_top = "<select name='hostname' onChange=selecthost.submit()>" + hostselect_options
    hostselect_bot = "<select name='hostname' onChange=selecthostbot.submit()>" + hostselect_options

    # Build previous and next links
    prev = ''
    next = ''
    for i in range(0,len(hosts)):
	if hosts[i] == hostname:
	    if i>0:
		prev = '<a href="%s?hostname=%s&%s">&lt;--</a>' % (os.environ['SCRIPT_NAME'], hosts[i-1], cursettings)
	    if i<len(hosts)-1:
		next = hosts[i+1]
		next = '<a href="%s?hostname=%s&%s">--&gt;</a>' % (os.environ['SCRIPT_NAME'], hosts[i+1], cursettings)

    if hostname in cfg.aliases.keys():
	alias = " (%s)" % (cfg.aliases[hostname])
    else:
	alias = ""

    print "<center>"
    print "<form name='selecthost' action='%s' method=GET>" % (os.environ['SCRIPT_NAME'])
    print cfg.keepSettings(type='form')		# pass settings as hidden fields
    print """<Table width="100%%"><tr>
	<td align="left" width="30%%">
	    <font size="-1">
	    [<a href="./eddiebrowser.cgi?%s">Control Panel</a>]
	    </font></td>
	<td align="center" width="40%%"><b>%s%s</b></td>
	<td align="right" valign="middle" width="30%%">%s&nbsp;%s&nbsp;%s</td>
	</tr></Table>""" % (cursettings,hostname,alias,prev,hostselect_top,next)
    print "</form>"

    cursettings = cfg.keepSettings( type='get', exclude=('start',) )

    if graph_options['start'] == "-14400":
	print "[&nbsp;hourly&nbsp;]"
    else:
	print '[&nbsp;<a href="%s?hostname=%s&start=-14400&%s">hourly</a>&nbsp;]' % (os.environ['SCRIPT_NAME'], hostname, cursettings)
    if graph_options['start'] == "-151200":
	print "[&nbsp;daily&nbsp;]"
    else:
	print '[&nbsp;<a href="%s?hostname=%s&start=-151200&%s">daily</a>&nbsp;]' % (os.environ['SCRIPT_NAME'], hostname, cursettings)
    if graph_options['start'] == "-864000":
	print "[&nbsp;weekly&nbsp;]"
    else:
	print '[&nbsp;<a href="%s?hostname=%s&start=-864000&%s">weekly</a>&nbsp;]' % (os.environ['SCRIPT_NAME'], hostname, cursettings)
    if graph_options['start'] == "-3628800":
	print "[&nbsp;monthly&nbsp;]"
    else:
	print '[&nbsp;<a href="%s?hostname=%s&start=-3628800&%s">monthly</a>&nbsp;]' % (os.environ['SCRIPT_NAME'], hostname, cursettings)
    if graph_options['start'] == "-41472000":
	print "[&nbsp;yearly&nbsp;]"
    else:
	print '[&nbsp;<a href="%s?hostname=%s&start=-41472000&%s">yearly</a>&nbsp;]' % (os.environ['SCRIPT_NAME'], hostname, cursettings)
    print "</center>"

    showTypes( hostname, graph_options, cfg, cfg.filter )

    if graph_options.has_key('width') and graph_options['width']:
	narrower = int(graph_options['width']) - 100
	wider = int(graph_options['width']) + 100
    else:
	narrower = 300
	wider = 500

    if graph_options.has_key('zoom') and graph_options['zoom']:
	zoomin = float(graph_options['zoom']) * 1.5
	zoomout = float(graph_options['zoom']) / 1.5
    else:
	zoomin = 1.5
	zoomout = 0.75

    if graph_options.has_key('smooth') and graph_options['smooth']:
	smooth = ''
	smoothtext = 'accurate'
    else:
	smooth = '&smooth=1'
	smoothtext = 'smooth'

    print '<br />Graph:'
    cursettings = cfg.keepSettings( type='get', exclude=('width',) )
    print 'width <a href="%s?hostname=%s&width=%s&%s">&ndash;</a>' % (os.environ['SCRIPT_NAME'], hostname, narrower, cursettings)
    print '<a href="%s?hostname=%s&width=%s&%s">+</a>' % (os.environ['SCRIPT_NAME'], hostname, wider, cursettings)

    cursettings = cfg.keepSettings( type='get', exclude=('zoom',) )
    print '| zoom <a href="%s?hostname=%s&zoom=%s&%s">&ndash;</a>' % (os.environ['SCRIPT_NAME'], hostname, zoomout, cursettings)
    print '<a href="%s?hostname=%s&zoom=%s&%s">+</a>' % (os.environ['SCRIPT_NAME'], hostname, zoomin, cursettings)

    cursettings = cfg.keepSettings( type='get', exclude=('smooth',) )
    print '| <a href="%s?hostname=%s&%s%s">%s</a>' % (os.environ['SCRIPT_NAME'], hostname, cursettings, smooth, smoothtext)

    cursettings = cfg.keepSettings( type='get', exclude=('smooth','width','zoom') )
    print '| (<a href="%s?hostname=%s&%s">reset all</a>)' % (os.environ['SCRIPT_NAME'], hostname, cursettings)

    print "<form name='selecthostbot' action='%s' method=GET>" % (os.environ['SCRIPT_NAME'])
    print cfg.keepSettings(type='form')		# pass settings as hidden fields
    print """<Table width="100%%"><tr>
	<td align="left" width="30%%">
	    <font size="-1">
	    [<a href="./eddiebrowser.cgi?%s">Control Panel</a>]
	    </font></td>
	<td align="center" width="40%%"><b>%s%s</b></td>
	<td align="right" valign="middle" width="30%%">%s&nbsp;%s&nbsp;%s</td>
	</tr></Table>""" % (cursettings,hostname,alias,prev,hostselect_bot,next)
    print "</form>"

    print "</BODY>"


class Filter:
    def __init__( self, form ):
	self.on = False
	if 'noflt' in form.keys() and form['noflt'].value == 'on':
	    # No filtering; i.e., show everything
	    return

	self.filtergroups = []
	self.filtertypes = []

	value = form.getvalue("fltgroup", "")
	if isinstance(value, list):
	    # Multiple fields specified
	    self.filtergroups = value
	    self.on = True
	elif value:
	    # Single or no field specified
	    self.filtergroups = [value,]
	    self.on = True

	for f in form.keys():
	    if f[:6] == 'fltgrp':
		value = form.getvalue(f, "")
		if isinstance(value, list):
		    # Multiple fields specified
		    self.filtertypes += value
		    self.on = True
		elif value:
		    # Single or no field specified
		    self.filtertypes += [value,]
		    self.on = True


#### Main ####

def main():

    cfg = GlobalConfig()
    cfg.parseGlobalConfig(GLOBAL_CONFIG)

    form = cgi.FieldStorage()

    if 'mode' in form.keys():
	if form['mode'].value == 'graph':
	    # Graph an RRD data source and output a PNG image
	    graph( form, cfg )
	    return 1

    print "Content-Type: text/html"     # HTML is following
    print                               # blank line, end of headers

    print "<HTML>"

    cfg.parseForm(form)

    hostname = None
    if 'hostname1' in form.keys():
	hostname = form['hostname1'].value
    elif 'hostname' in form.keys():
	hostname = form['hostname'].value

    cfg.parseFilter( form )		# get groups/datatypes to filter by

    if hostname:
	showHost( hostname, form, cfg )
    else:
        controlPanel(cfg)
#    else:
#	print "<p>Unknown options"
#	for i in form.keys():
#	    print "<br><li>",i,"=",form[i].value


    print "</HTML>"

    return 0



if __name__ == "__main__":

    main()

