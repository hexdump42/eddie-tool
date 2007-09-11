Notes on installing Eddie-Tool for Win32 (Windows XP/2000/2003/Server/etc).
- Chris Miles 2005-08-05

Download and install Python for Windows.  Latest release version is
recommended.  Eddie on win32 requires Python 2.3 or newer.
  http://www.python.org

Download and install the Python for Windows Extensions (aka win32all or
pywin32)
  http://starship.python.net/crew/mhammond/
(Download the correct version of pywin32 for the version of Python you
installed)

Download and unzip Eddie-Tool

Create a config for Eddie.
Shortcut is to copy 'config.sample' to 'config' and customise the files inside.
'eddie.cf' certainly needs to be customised.  'win32_sample.rules' offers a
good starting point.

To start Eddie (from DOS/CMD prompt):
  cd eddie\bin
  c:\Python24\python eddie.py


Notes:
 To find the instance names of the network interfaces try something like this:
  cd eddie\lib\Windows
  c:\Python24\python
  >>> import win32perf
  >>> win32perf.getInstances('Network Interface')
  Copy the string exactly to the name parameter of an IF directive.

and similarly to find the names of the physical disks (for DISK directives)
  >>> win32perf.getInstances('PhysicalDisk')

Elvin:
 If you want to use elvinrrd action to send system statistics to a central
 store for analysis you can download the Elvin Python SDK from
   http://elvin.dstc.edu.au/projects/pe4/index.html
   (you may end up being redirected to Mantara software to download the
   "evaluation" version).

  Note that you also need an Elvin Router (from the same address above) and
  software to listen for and save the data.  That is beyond the scope of
  this document, but ask on the Eddie-Tool mailing list if you want more
  information.

