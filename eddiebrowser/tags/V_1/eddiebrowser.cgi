#!/opt/python/bin/python

## EDDIE RRD Browser - Chris Miles <chris@psychofx.com> 2002-06-16
##  A smart CGI interface for browsing and graphing RRD stats.  Can be used
##  with any RRDs but commonly used in conjuction with EDDIE-Tool and
##  elvinrrd generated system/network RRD stats.
## $Id$
## $Source$

## Settings ##

# RRD_DIR: a directory containing all the RRD files.
RRD_DIR = '/export/rrd'
# GLOBAL_CONFIG: location of global config file
GLOBAL_CONFIG = '/export/rrd/eddiebrowser.cfg'

## End of settings ##


__version__ = '0.3.0'


import cgi, os, sys, traceback, string, re



class GlobalConfig:
    def __init__(self):
	self.settings = {}

	self.settings['ho'] = 'h'		# order by hosts (default)
	self.settings['start'] = "-151200"	# daily view (default)
	self.aliases = {}


    def parseGlobalConfig(self,cfgfile):
	"""parseGlobalConfig( location_of_config_file )
	Read global settings.
	"""

	try:
	    fp = open( cfgfile, 'r' )
	except IOError, err:
	    raise IOError, "Cannot open global config file: %s (%s)"%(cfgfile,err)

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
		if s not in exclude:
		    settingstr += '<input type=hidden name="%s" value="%s">\n' % (s,self.settings[s])

	elif type=='get':
	    for s in self.settings.keys():
		if s not in exclude:
		    if settingstr != '':
			settingstr += '&'
		    settingstr += '%s=%s' % (s,self.settings[s])

	return settingstr



def parseConfig(dir):
    cfg = {}	# config dictionary

    cfgfile = os.path.join( dir, ".eddiebrowser.cfg" )

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


def getHostsFromDir(dir, hosts):
    cfg = parseConfig(dir)
    if cfg == None:
	return None

    files = cfg['FILES']
    inx = re.compile( files )

    for f in os.listdir(dir):
    	sre = inx.match(f)
	if sre != None:
	    h = sre.group('hostname')
	    if h not in hosts:
		hosts.append(h)


def getAllHosts():
    hosts = []
    dirs = os.listdir( RRD_DIR )
    for d in dirs:
	dir = os.path.join( RRD_DIR, d )
	getHostsFromDir(dir, hosts)

    return hosts


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
    print "<center><b>EDDIE RRD Browser (v%s)</b>" % (__version__)
    print "<br>&copy; Chris Miles 2002-2003</center>"

    print "<p>Select a host</p>"

    hosts = getAllHosts()

    #print "<p>hosts:",hosts,"</p>"
    print "<form name='selecthost' action='%s' method=GET>" % (os.environ['SCRIPT_NAME'])

    print cfg.keepSettings(type='form')	# print settings as hidden fields

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
    print '<input type=submit value="GO">'

    print "</form>"
    if cfg.settings['ho'] == 'a':
	print '<font size=-1>[<a href="%s?ho=h">sort by hostname</a>]</font>' % (os.environ['SCRIPT_NAME'])
    else:
	print '<font size=-1>[<a href="%s?ho=a">sort by alias</a>]</font>' % (os.environ['SCRIPT_NAME'])


def error_html( msg ):
    """Display an error as text/html, including Content-type."""

    print "Content-Type: text/html"     # html error msg
    print                               # blank line, end of headers
    print "<HTML><HEAD><Title>Error message</Title></HEAD>"
    print "<BODY>"
    print msg
    print "</BODY></HTML>"


def error_rrd( RRDtool, msg ):
    """Display an error as image/png, using RRD to display the message."""

    # Return the raw PNG image
    if type(msg) == type( (1,2) ):
	rrdopt = [ '--imgformat', 'PNG',
	    '-',	# stdout
	    ]
	for m in msg:
	    rrdopt.append( 'COMMENT:%s' % (m) )
    else:
	rrdopt = ( '--imgformat', 'PNG',
	    '-',	# stdout
	    'COMMENT:%s' % (msg)
	    )

    rrd = RRDtool.RRDtool()
    print "Content-Type: image/png"     # PNG data is following
    print                               # blank line, end of headers
    rrd.graph( tuple(rrdopt) )


def graph( form ):
    """Graph an RRD data source using pyrrdtool module."""

    try:
	import RRDtool		# http://projects.gasperino.org/
    except ImportError,msg:
	error_html( "<b>Cannot import RRDtool python module, error follows:<br>%s</b>"%(msg) )
	return 1

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

    if '/' in rrd or '/' in dir:
	# security check - directories not permitted
	error_html( "illegal rrd or dir" )
	return 1

    # read .eddiebrowser.cfg
    cfg = parseConfig( os.path.join( RRD_DIR, dir ) )
    if not cfg:
	error_rrd( RRDtool, 'Error reading config in dir: %s'%(dir) )
	return

    files = cfg['FILES']
    inx = re.compile( files )
    sre = inx.match(rrd)
    if sre != None:
	vars = sre.groupdict()
    else:
	vars = {}

    graphoptions = [ '--imgformat', 'PNG' ]

    # parse general options
    sourcefile = os.path.join( RRD_DIR, dir, rrd )

    if 'GRAPH_TITLE' in cfg.keys():
	graphoptions.append( '--title=%s' % (cfg['GRAPH_TITLE']) )
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
		graphdef['file'] = os.path.join( RRD_DIR, dir, graphdef['file'] )
	else:
	    graphdef['file'] = sourcefile

	if not os.path.isfile( graphdef['file'] ):
	    error_rrd( RRDtool, 'ERROR: cannot read RRD file: %s' % (graphdef['file']) )
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

    try:
	# Return the raw PNG image
	print "Content-Type: image/png"     # PNG data is following
	print                               # blank line, end of headers

	rrd = RRDtool.RRDtool()
	r = rrd.graph( tuple(graphoptions) )
	sys.stderr.write( 'r=%s'%(r) )

    except:	# catch all
	e = sys.exc_info()
	tb = traceback.format_list( traceback.extract_tb( e[2] ) )
	msg1 = "%s" % e[0]
	msg2 = "%s" % e[1]
	error_rrd( RRDtool, (msg1,msg2) )
	return 1

#    rrd = RRDtool.RRDtool()
#    rrd.graph( ( '--imgformat', 'PNG',
#	'--vertical-label=cpu use (%)',
#	'--start=-151200',
#	'-',	# stdout
#	'DEF:A=/export/rrd/cpulinux/cpulinux-crazy.rrd:cpu_user:AVERAGE',
#	'DEF:B=/export/rrd/cpulinux/cpulinux-crazy.rrd:cpu_nice:AVERAGE',
#	'DEF:C=/export/rrd/cpulinux/cpulinux-crazy.rrd:cpu_system:AVERAGE',
#	'DEF:D=/export/rrd/cpulinux/cpulinux-crazy.rrd:cpu_idle:AVERAGE',
#	'AREA:A#0000FF:crazy cpu_user',
#	'STACK:B#00FFFF:crazy cpu_nice',
#	'STACK:C#00FF00:crazy cpu_system',
#	'LINE1:D#A0522D:crazy cpu_idle',
#	'GPRINT:A:MAX:(max=%lf)'
#	) )


def showHostInfo(dir, hostname, start):
    cfg = parseConfig(dir)
    if cfg == None:
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
		vars = { 'filename': f, 'start': start }
		vars.update( sre.groupdict() )
		if 'SHOW:%s'%(hostname) in cfg.keys():
		    # use a hostname-specific SHOW if available
		    img = '<img src="%s" border=0>' % (cfg['SHOW:%s'%(hostname)])
		elif 'SHOW' in cfg.keys():
		    # otherwise just use SHOW if specified
		    img = '<img src="%s" border=0>' % (cfg['SHOW'])
		else:
		    # otherwise use built-in
		    show = "%s?mode=graph&dir=%s&rrd=%%(filename)s&start=%%(start)s" % (os.environ['SCRIPT_NAME'],dir.split('/')[-1])
		    img = '<img src="%s" border=0>' % (show)
		print img % vars



def showTypes( hostname, start ):
    """Get types of data to show for <hostname>."""

    types = {}

    dirs = os.listdir( RRD_DIR )
    for d in dirs:
	dir = os.path.join( RRD_DIR, d )
	showHostInfo(dir, hostname, start)

    return


def showHost( hostname, start, cfg ):
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

    cursettings = cfg.keepSettings(type='get')

    # chris 2003-05-26: get hosts to make selection list and next/previous links
    hosts = getAllHosts()
    hostselect = "<select name='hostname' onChange=selecthost.submit()>"
    if cfg.settings['ho'] == 'a':
	# sort by aliases
	hosts.sort(cfg.aliasSort)
	for h in hosts:
	    selected = ''
	    if h == hostname:
		selected = 'selected'
	    hostselect += "<option value='%s' %s>" % (h,selected)
	    if h in cfg.aliases.keys():
		hostselect += "%s" % (cfg.aliases[h])
		hostselect += " (%s)"%(h)
	    else:
		hostselect += "%s"%(h)
	    hostselect += "</option>"
    else:
	# sort by hostnames
	hosts.sort(nocaseSort)
	for h in hosts:
	    selected = ''
	    if h == hostname:
		selected = 'selected'
	    hostselect += "<option value='%s' %s>%s" % (h,selected,h)
	    if h in cfg.aliases:
		hostselect += " (%s)"%(cfg.aliases[h])
	    hostselect += "</option>"
    hostselect += "</select>"

    prev = ''
    next = ''
    for i in range(0,len(hosts)):
	if hosts[i] == hostname:
	    if i>0:
		prev = '<a href="%s?hostname=%s&%s">&lt;--</a>' % (os.environ['SCRIPT_NAME'], hosts[i-1], cursettings)
	    if i<len(hosts)-1:
		next = hosts[i+1]
		next = '<a href="%s?hostname=%s&%s">--&gt;</a>' % (os.environ['SCRIPT_NAME'], hosts[i+1], cursettings)


    print "<center>"
    print "<form name='selecthost' action='%s' method=GET>" % (os.environ['SCRIPT_NAME'])
    print cfg.keepSettings(type='form')		# pass settings as hidden fields
    print """<Table width="100%%"><tr>
	<td align="left" width="30%%">
	    <font size="-1">
	    [<a href="./eddiebrowser.cgi?%s">Control Panel</a>]
	    </font></td>
	<td align="center" width="40%%"><b>%s</b></td>
	<td align="right" valign="middle" width="30%%">%s&nbsp;%s&nbsp;%s</td>
	</tr></Table>""" % (cursettings,hostname,prev,hostselect,next)
    print "</form>"

    cursettings = cfg.keepSettings( type='get', exclude=('start',) )

    if start == "-14400":
	print "[&nbsp;hourly&nbsp;]"
    else:
	print '[&nbsp;<a href="%s?hostname=%s&start=-14400&%s">hourly</a>&nbsp;]' % (os.environ['SCRIPT_NAME'], hostname, cursettings)
    if start == "-151200":
	print "[&nbsp;daily&nbsp;]"
    else:
	print '[&nbsp;<a href="%s?hostname=%s&start=-151200&%s">daily</a>&nbsp;]' % (os.environ['SCRIPT_NAME'], hostname, cursettings)
    if start == "-864000":
	print "[&nbsp;weekly&nbsp;]"
    else:
	print '[&nbsp;<a href="%s?hostname=%s&start=-864000&%s">weekly</a>&nbsp;]' % (os.environ['SCRIPT_NAME'], hostname, cursettings)
    if start == "-3628800":
	print "[&nbsp;monthly&nbsp;]"
    else:
	print '[&nbsp;<a href="%s?hostname=%s&start=-3628800&%s">monthly</a>&nbsp;]' % (os.environ['SCRIPT_NAME'], hostname, cursettings)
    if start == "-41472000":
	print "[&nbsp;yearly&nbsp;]"
    else:
	print '[&nbsp;<a href="%s?hostname=%s&start=-41472000&%s">yearly</a>&nbsp;]' % (os.environ['SCRIPT_NAME'], hostname, cursettings)
    print "</center>"

    showTypes( hostname, start )

    print "</BODY>"


def main():

    form = cgi.FieldStorage()

    if 'mode' in form.keys():
	if form['mode'].value == 'graph':
	    graph( form )
	    return 1

    print "Content-Type: text/html"     # HTML is following
    print                               # blank line, end of headers

    print "<HTML>"

    cfg = GlobalConfig()
    cfg.parseGlobalConfig(GLOBAL_CONFIG)
    cfg.parseForm(form)

    if 'hostname' in form.keys():
	if 'start' in form.keys():
	    start = form['start'].value
	else:
	    start = "-151200"		# default to daily
	showHost( form['hostname'].value, start, cfg )
    else:
        controlPanel(cfg)
#    else:
#	print "<p>Unknown options"
#	for i in form.keys():
#	    print "<br><li>",i,"=",form[i].value


    print "</HTML>"

    return 0


if __name__ == "__main__":

    try:
	main()
    except:
	print "Content-Type: text/html"     # html error msg
	print                               # blank line, end of headers
	e = sys.exc_info()
	tb = traceback.format_list( traceback.extract_tb( e[2] ) )
	print "<p><font color=blue>Exception in %s :</font>" % (sys.argv[0])
	#print "<br><pre><font color=red>%s, %s, %s</font></pre></p>" % (e[0], e[1], tb)
	print "<br><font color=red><pre>"
	print e[0]
	print e[1]
	for t in tb:
	    print t,
	print "</pre></font></p>"


