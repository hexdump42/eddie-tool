Notes on running Eddie-Tool for OpenBSD
- Mark Taylor 2006-05-12


WARNING:

If you are going to use EDDIE-tool in an OpenBSD environment, please ensure
that you have OpenBSD 3.9 or later, or you will experience Python segfaults,
due to a race condition in their libc and libpthread implementation.


EXPLAINATION:

EDDIE-tool is heavily threaded.  You can configure the number of threads that
EDDIE will use.  Every time a directive is executed, a new thread is started
for it, and the thread is destroyed when the directive is completed, usually
moments later.

Up until OpenBSD 3.9, there was a race condition in OpenBSD's libc
implementation of "atexit" and "atexit_register_cleanup" when running in a
threaded environment.  The shared linked-list used to manage "atexit" registered
routines was not locked prior to being modified/accessed.  So there was a chance
that simultaneous threads starting up or exiting would corrupt the linked list,
and the application would generate a segfault (EDDIE would terminate).

This was fixed just prior to the OpenBSD 3.9 release.

For part of the patchset, see the 1.12 patch for atexit.c at:
http://www.openbsd.org/cgi-bin/cvsweb/src/lib/libc/stdlib/atexit.c

Note that there are a few other files involved in this patchset, including a few
in libpthread.

For me, prior to patching libc and libpthread, EDDIE-tool ran from somewhere
between ten seconds and six minutes, with about one hundred directives.  After
backporting these libc and libpthread changes to my OpenBSD 3.6 environment,
EDDIE-tool runs fine for me.

