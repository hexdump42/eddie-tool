Eddie-Tool Monitoring Agent
===========================

Installation
------------

To install from source (i.e. you downloaded a tarball)::

  $ python setup.py install

(if required, the setuptools Python package will be downloaded
and installed along with Eddie-Tool.)

If you already have setuptools installed and like to use
`easy_install` you can just use::

  $ easy_install Eddie-Tool

(with either method, you may need to run the command as root
to be able to write to the Python packages directory).

The Eddie-Tool libraries should now be installed, along with
a new command called `eddie-agent`.  This will be located
in the same location as the `python` interpreter (i.e.
`/usr/bin` usually).


Configuration
-------------

Refer to the Eddie-Tool User's Manual for details on
configuration and creating monitoring tools.  The manual
can be found at:

* doc/manual.html in the source;

* doc/manual.html in the installed egg directory (look
  in the Python lib site-packages).

* http://eddie-tool.net/doc/manual.html

The quickest way to get started is to copy the sample
configuration directory `config-sample` (found in the
source and in the installed egg directory) and customise
it.


Usage
-----

Start the Eddie-Tool agent using::

  $ eddie-agent /path/to/eddie.cf

