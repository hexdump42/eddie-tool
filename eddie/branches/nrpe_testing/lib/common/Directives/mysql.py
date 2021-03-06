
'''
File                : mysql.py 

Start Date        : 20020408

Description        : Directives for mysql checks

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 2002-2005'

__author__ = 'Chris Miles; Dougal Scott'

__license__ = '''
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
'''


# Imports: Eddie
import log, directive

# Imports python
import sys, string, time

################################################################################
class MYSQL(directive.Directive):
    """
    Eddie directive for performing mysql checks
    Syntax:
            MYSQL x: host="<hostname>"         Defaults to localhost
                 port=<portnum>                Defaults to 3306
                 user="<username>"
                 password="<password>"
                 query="SELECT foo from bar"        Defaults to none
                 rule="<rule>" 
                 action=<actions>
    Excamples:
            MYSQL traffic:
            host='localhost'
            user='eddie'
            passwd='sekrit'
            rule='xtot>1000'
            action=email(...)

    You will need to run something like the following, or use an
    existing user, in mysql to let eddie in to the db:

    grant select on *.* to 'eddie'@'%' identified by 'eddiepassword'
    grant select on *.* to 'eddie'@localhost identified by 'eddiepassword'

    """

    ############################################################################
    def __init__(self, toklist):
        apply( directive.Directive.__init__, (self, toklist) )
        self.available=1
        try:
            import MySQLdb
            self.MySQLdb=MySQLdb
        except ImportError:
            # If it fails don't barf just nod and keep on going
            # It just won't be able to do anything
            self.available=0
            exctype,value=sys.exc_info()[:2]
            log.log("<mysql>__init__(): MySQLdb not importable %s, %s" % (exctype, value),5)        # Should be 3 but it whinges a lot
            #raise directive.ParseFailure, "Cannot import MySQLdb module - mysql directive not available"

    ############################################################################
    def tokenparser(self, toklist, toktypes, indent):
        """
        Parse directive arguments.
        """

        apply(directive.Directive.tokenparser,(self, toklist, toktypes, indent))

        # test required arguments
        try:
            self.args.host
        except AttributeError:
            self.args.host='localhost'

        try:
            self.args.port=int(self.args.port)
        except ValueError:
            raise directive.ParseFailure, "Port must be an integer"
        except AttributeError:
            self.args.port=3306

        try:
            self.args.rule
        except AttributeError:
            raise directive.ParseFailure, "Rule not specified"

        try:
            self.args.user
        except AttributeError:
            raise directive.ParseFailure, "User not specified"

        try:
            self.args.query
        except AttributeError:
            self.args.query=None

        try:
            self.args.password
        except AttributeError:
            raise directive.ParseFailure, "Password not specified"

        # Set variables for Actions to use
        self.defaultVarDict['host'] = self.args.host
        self.defaultVarDict['port'] = self.args.port
        self.defaultVarDict['user'] = self.args.user
        self.defaultVarDict['password'] = self.args.password
        self.defaultVarDict['query'] = self.args.query

        # define the unique ID
        if self.ID == None:
            self.ID = '%s.MYSQL.%s:%s.%s' % (log.hostname, self.args.host, self.args.port, self.args.rule)
        self.state.ID = self.ID

    ############################################################################
    def getData(self):
        """
        Grab data about the database
        """

        if not self.available:
            raise directive.DirectiveError, "MySQLdb not available"

        data = {}
        data['connected']=0
        data['errmsg']=''
        data['querytime']=-1

        # Connect to the database
        try:
            db=self.MySQLdb.connect(host=self.args.host, port=self.args.port, user=self.args.user, passwd=self.args.password)
            curs=db.cursor()
            data['connected']=1
            starttime=time.time()
                
            if self.args.query==None:
                curs.execute("SHOW STATUS")
                data['querytime']=(time.time()-starttime)*1000
                ans=curs.fetchone()
                while(ans!=None):
                    data[ans[0].lower()]=ans[1]
                    ans=curs.fetchone()
            else:
                curs.execute(self.args.query)
                data['querytime']=(time.time()-starttime)*1000
                result=[]
                ans=curs.fetchone()
                count=0
                while(ans!=None):
                    data['result%d' % count]=ans[0]
                    count=count+1
                    result.append(ans)
                    ans=curs.fetchone()
                data['result']=result

            curs.close()
            db.close()
        except self.MySQLdb.OperationalError,msg:
            log.log("<mysql>MYSQL.getData(): ID '%s' Operational Error: %s" % (self.ID, msg), 7)
            data['errmsg']=msg
            return data
        except:
            systype,value=sys.exc_info()[:2]
            raise directive.DirectiveError, "Problem with %s: %s,%s" % (self.state.ID, systype, value)

        return data

##
## END - mysql.py
##
