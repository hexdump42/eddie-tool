ElvinRRD is what sits between an elvin server and rrdtool

in that it listens for elvin messages destined for a rrd

and accepts them, writing back the rrd files.



You can get it from:

http://www.psychofx.com/elvinrrd/



It is a python script (and it's config file) so doesn't need to be

installed as such.



Just un-tgz, and put into place.



Edit the elvinrrd.py and set the correct python path, and

elvin server details



Eg:

```
# Default Elvin URL and SCOPE

ELVIN_URL='elvin://beastie'

ELVIN_SCOPE='murphy'

```