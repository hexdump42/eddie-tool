_Update: the Elvin project is no longer available.  Use Spread instead. See SpreadMessaging_


---


Elvin has two parts - libelvin and elvind



Official howto at: http://elvin.dstc.com/doc/impatient.html

but this is what I did



If you have the source, it generally compiles fairly easily

I chose to install into /opt so I used the following commands

```

ELVINDIR=/opt/elvin4

ELVINSRC=/home/sarcher/libelvin-4.1b3

ELVINDSRC=/home/sarcher/elvind-4.1b3

cd $ELVINSRC

./configure --prefix=$ELVINDIR && make && make install

cd $ELVINDSRC

./configure --prefix=$ELVINDIR && make && make install
```

if the above does not work, you can probably strip out some elvin functionality you likely won't need anyway.
This disables SSL and the management console.

```
./configure --prefix=$ELVINDIR --without-ssl --disable-mgmt && make && make install
```





You will probably need something like the following in your environment (bash example)

I leave it up to you how to make this exist after you logout

(wrapper around elvind is a good option)

```
PATH=$ELVINDIR/bin:$ELVINDIR/sbin:$ELVINDIR/libexec:$PATH

LD_LIBRARY_PATH=$ELVINDIR/lib/:$LD_LIBRARY_PATH

MANPATH=$ELVINDIR/man:$MANPATH

export PATH LD_LIBRARY_PATH MANPATH

```





edit the config:

(by default)  $ELVINDIR/etc/elvind.conf

change the "scope" name to something meaningful (I used "murphy" as my scope name)



now run it !

```
bash-2.05b# /opt/elvin4/sbin/elvind -ldd

elvind:Sep  1 22:19:58 :Information:Started elvind 4.1b3 (pid: 18932)

elvind:Sep  1 22:19:58 :Information:Licensed for 50 clients, using up to 1024 file descriptors.

elvind:Sep  1 22:19:58 :Notice:Activated server discovery for non-default server in scope 'murphy'

elvind:Sep  1 22:19:58 :Information:Loaded information on 1 users from /opt/elvin4/etc/elvind.passwd

elvind:Sep  1 22:19:58 :Notice:Accepting management commands on https://beastie.grunta.com:8008

elvind:Sep  1 22:19:58 :Notice:Accepting client connections on elvin:4.0/tcp,none,xdr/beastie.grunta.com:2917

```



If you got that far, you have a working elvin server!



### Install python elvin module ###



get the Elvin Python SDK



```
bash-2.05b# PYELVINSRC=/home/sarcher/python-elvin-4.0b5

bash-2.05b# cd $PYELVINSRC 

bash-2.05b# python setup.py install
```



If that worked ok, you should be able to import the elvin module now

```
bash-2.05b# python

Python 2.4.1 (#1, Jul 13 2005, 10:32:28) 

[GCC 3.3.4] on linux2

Type "help", "copyright", "credits" or "license" for more information.

>>> import elvin

>>>

```



Now you can use an elvin producer to send messages to it.

Lets use the python module!



To test if we can connect



```
sarcher@beastie:~$ python

Python 2.4.1 (#1, Jul 13 2005, 10:32:28) 

[GCC 3.3.4] on linux2

Type "help", "copyright", "credits" or "license" for more information.

>>> import elvin

>>> connection = elvin.connect("murphy")

>>> connection.close()

```



In the elvin stdout you will see something like:

```
elvind:Sep  1 22:53:02 :Notice:Established client connection 2 from 45773@203.55.81.43

unregistering a client in the CLOSING state (flushing queue)

elvind:Sep  1 22:54:46 :Notice:Closed client connection 2 from 45773@203.55.81.43
```



Then, Set up eddie with the correct elvin url / scope and make it to it !



## Notes ##

In the event you had to put the python modules somewhere other then the default path, you may
need to add that path to the python search path.

One way is to add it to the eddie wrapper. (note .. if you do this, and then run eddie without the wrapper all elvin will barf!)

Eg: in eddie\_wrapper :

```

PYTHONPATH=/usr/local/stow/py-elvin-4.0b5/lib/python2.4/site-packages:$PYTHONPATH

export PYTHONPATH

```

There are other ways of doing this, which i'll leave as an exercise to the reader.