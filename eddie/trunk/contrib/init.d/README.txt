This directory contains various init.d scripts for controlling Eddie.
Use the script appropriate for your operating system & distribution.
They may need to be modified to suit your specific environment.


Redhat Linux
------------

 Install the chosen init.d script by copying to /etc/init.d/ and
 running chkconfig.

 Example:
 {{{
 # cp eddie-agent-init.d_script_for_redhat /etc/init.d/eddie-agent
 # /sbin/chkconfig --add eddie-agent
 }}}

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

  The SMF method and manifest scripts are supplied.  Import
  them using svccfg.

 Older Solaris releases:

  Copy eddie_wrapper-init.d_script_for_solaris to /etc/init.d/
  and create symlinks from the /etc/rc*.d/ directories as
  required.

