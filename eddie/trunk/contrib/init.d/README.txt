init.d/SMF contributions
========================

This directory contains various scripts & manifests for controlling Eddie.
Use the script appropriate for your operating system & distribution.
You should modify the file appropriately to suit your specific environment.


Redhat Linux
------------

Install the chosen init.d script by copying to /etc/init.d/ and
running chkconfig.

Example::

 # cp eddie-agent-init.d_script_for_redhat /etc/init.d/eddie-agent
 # /sbin/chkconfig --add eddie-agent

eddie-agent-init.d_script_for_redhat:
 
 Use to control the eddie-agent daemon directly.

eddie_wrapper-init.d_script_for_redhat:

 Use to control the eddie-agent daemon via the eddie_wrapper
 script (found in Eddie source contrib/eddie_wrapper).  This
 script attempts to re-start eddie-agent if it dies for
 any reason.


Solaris
-------

Solaris 10 / SMF:

 An SMF manifest is provided.  Modify it to specify the location
 of `eddie-agent` and the config file, then import it to create
 the service with::

  # svccfg import eddie-agent.xml

 View the service state and start/stop it with::

  # svcs -v eddie-agent
  # svcadm enable eddie-agent
  # svcadm disable eddie-agent

Older Solaris releases:

 Copy eddie_wrapper-init.d_script_for_solaris to /etc/init.d/
 and create symlinks from the /etc/rc*.d/ directories as
 required.

