# Using Spread with Eddie-Tool #

## Install Spread ##

If you need to, you can download and install it from http://www.spread.org/download.html

(Note that I have only tested the 3.x release of Spread. 3.17.4 at the time of writing this.)


## Install the Python Spread module ##

If you are using setuptools, you can easy\_install it:
```
# easy_install SpreadModule
```

Otherwise grab it from http://www.python.org/other/spread/ and install it manually.


## Configure Spread ##

Configure spread.conf, at `/usr/local/etc/spread.conf` by default.

By default, spread.conf is configured to listen on localhost.  To test eddie-tool with spread, this may be enough to get started with.
```
Spread_Segment  127.0.0.255:4803 {
       localhost               127.0.0.1
}
```

The next simplest configuration is to define a local network segment for Spread to listen on.  Here we define a segment for 10.0.0.0/24, where the host running the Spread daemon is called `crazy` with IP `10.0.0.15`:
```
Spread_Segment  10.0.0.255:4803 {
        crazy              10.0.0.15
}
```

Now start Spread:
```
$ /usr/local/sbin/spread
```

After a few seconds it should confirm your segment configuration.  For example:
```
Conf_init: using file: /usr/local/etc/spread.conf
Successfully configured Segment 0 [10.0.0.255:4803] with 1 procs:
                       crazy: 10.0.0.15
Finished configuration file.
Conf_init: My name: crazy, id: 10.0.0.15, port: 4803
Membership id is ( 167772175, 1235973943)
--------------------
Configuration at crazy is:
Num Segments 1
        1       10.0.0.255        4803
                crazy                   10.0.0.15       
====================
```

To test it you will find a couple of scripts in the contrib directory of the eddie-tool source.  Run `elvinrrd_spread_watch.py` in one terminal, then use `elvinrrd_spread_send.py` to send some test messages.

For example, `elvinrrd_spread_watch.py` would see something like:
```
$ python elvinrrd_spread_watch.py -s crazy
Connecting to Spread server: crazy:4803

Mon Mar  2 17:16:02 2009
* Membership change for group: elvinrrd
  Members joined: #r25980117#crazy
  Members in group now:  #r25980117#crazy

Mon Mar  2 17:16:07 2009
{'ELVINRRD': 'loadavg1-myhost',
 'loadavg1': '0.01',
 'timestamp': 1235974567.358016}
  timestamp = 2009-03-02 17:16:07.358016
```

if `elvinrrd_spread_send.py` had sent:
```
$ python elvinrrd_spread_send.py  -s crazyloadavg1-myhost loadavg1=0.01
Connecting to Spread server: crazy:4803
Sending message:
{'ELVINRRD': 'loadavg1-myhost',
 'loadavg1': '0.01',
 'timestamp': 1235974567.358016}
message sent OK
```

## ElvinRRD ##

ElvinRRD requires rrdtool (and the Python module for it) so download and install rrdtool from http://oss.oetiker.ch/rrdtool/

Get ElvinRRD from http://www.psychofx.com/elvinrrd/download/, unpack and run it with:
```
$ python2.5 elvinrrd.py -celvinrrd.cf -S localhost
```
Specifying the address of the Spread server for "-S".