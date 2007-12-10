
'''
File                : dbi.py 

Start Date        : 20060508

Description        : Directives for DBI checks

$Id$
'''

__version__ = '$Revision$'

__copyright__ = 'Copyright (c) Chris Miles 2006'

__author__ = 'Mark Taylor; Chris Miles; Dougal Scott'

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
from eddietool.common import log, directive, utils

# Imports python
import sys, string, time

################################################################################
class DBI(directive.Directive):
    """
    Eddie directive for performing database checks
    
    Syntax:
        DBI name:
            dbtype="<type>"             # 'pg' for Postgres, 'mysql' for mysql, etc...
            host="<hostname>"           # Defaults to localhost
            port=<portnum>
            user="<username>"
            password="<password>"
            query="<SQL query>"         # Defaults to none
            rule="<rule>" 
            action=<actions>
    
    Examples:
        DBI postgresql_check:
            dbtype='pg'
            host='localhost'
            database='monitoring'
            user='monitoring'
            password='sshhh'
            query='select * from monitoring'
            rule='not connected or results != 1 or result1 != 42'
            action=email(ALERT_EMAIL, 'PostgreSQL DB %(database)s failed test', 'Query: %(query)s\nConnected: %(connected)s\nError: %(errmsg)s')
        
        DBI db_connections:
            dbtype='pg'
            host='localhost'
            database='mydb'
            user='pgsql'
            password='sekrit'
            query='select count(1) from pg_stat_activity'
            rule='connected and results > 0 and result1 > 40'
            action=email('alert', 'Database %(database)s on %(h)s: too many connections (currently %(result1)s)')
            console='%(database)s on %(host)s : connections = %(result1)d'

    """

    ############################################################################
    def __init__(self, toklist):
        apply( directive.Directive.__init__, (self, toklist) )
        self.available = -1

    ############################################################################
    def tokenparser(self, toklist, toktypes, indent):
        """
        Parse directive arguments.
        """

        apply(directive.Directive.tokenparser,(self, toklist, toktypes, indent))

        # test required arguments
        try:
            self.args.dbtype
        except AttributeError:
            raise directive.ParseFailure, "dbtype not specified"

        try:
            self.args.host
        except AttributeError:
            self.args.host = 'localhost'

        try:
            self.args.port = int(self.args.port)
        except ValueError:
            raise directive.ParseFailure, "Port must be an integer"
        except:
            self.args.port = None

        try:
            self.args.database
        except AttributeError:
            self.args.database = ''

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
            if self.args.dbtype == 'mysql':
                self.args.query = 'SHOW STATUS'
            elif self.args.dbtype == 'pg':
                self.args.query = ''  # XXX(mtaylor): finish this 'default' query for Postgres...
            else:
                raise directive.ParseFailure, "No query specified, and no default available for dbtype %s" % (self.args.dbtype)

        try:
            self.args.password
        except AttributeError:
            raise directive.ParseFailure, "Password not specified"

        # Set variables for Actions to use
        for k in ('dbtype', 'host', 'port', 'user', 'password', 'database', 'query'):
            self.defaultVarDict[k] = eval("self.args.%s" % (k))

        # define the unique ID
        if self.ID == None:
            self.ID = '%s.DBI.%s.%s:%s.%s' % (log.hostname, self.args.dbtype, self.args.host, self.args.port, self.args.rule)
        self.state.ID = self.ID

    ############################################################################
    def getData(self):
        """
        Grab data about the database
        """

        data = {}
        data['connected'] = False
        data['errmsg'] = ''
        data['querytime'] = -1

        if self.available == -1:
            try:
                exec("import "+self.args.dbtype+"db")
                self.dbi = eval(self.args.dbtype+"db")
                self.available = 1
            except ImportError:
                # If it fails don't barf just nod and keep on going
                # It just won't be able to do anything
                self.available = 0
                exctype,value = sys.exc_info()[:2]
                log.log("<dbi>getData(): %s db module is not importable %s, %s" % (self.args.dbtype,exctype,value), 5)

        if not self.available:
            data['errmsg'] = "dbi for %s is not available" % (self.args.dbtype)
            return data

        # Connect to the database
        # XXX(mtaylor): need a connection timeout here...
        try:
            try:
                db = self.dbi.connect(host=self.args.host, port=self.args.port, user=self.args.user, passwd=self.args.password)
            except TypeError:
                try:
                    db = self.dbi.connect(host=self.args.host, user=self.args.user, password=self.args.password, database=self.args.database)
                except:
                    data['errmsg'] = 'db connect failure'
                    return data
            except:
                data['errmsg'] = 'db connect failure'
                return data

            curs = db.cursor()
            data['connected'] = True
            starttime = time.time()

            # allow for query like "SELECT COUNT(1) FROM x WHERE y > %(_maxval)d"
            q = utils.parseVars(self.args.query, self.defaultVarDict)

            # XXX(mtaylor): need a query timeout here...
            curs.execute(q)
            data['querytime'] = (time.time()-starttime)*1000
            result = []
            data['result1'] = ''   # populate 'result1' so rule/console string may work instead of causing exception...
            ans = curs.fetchone()
            if curs.rowcount > 1:
                # Return results as 'result1', 'result2', ..., with *first column* of every row returns:
                count = 0
                while ans != None:
                    data['result%d'%(count+1)] = utils.typeFromString(ans[0])
                    count = count+1
                    result.append(ans)
                    ans = curs.fetchone()
                data['results'] = count
            else:
                # Return results as 'result1', 'result2', ..., with *first row's* returns:
                for i in range(len(ans)):
                    data['result%d'%(i+1)] = utils.typeFromString(ans[i])
                result.append(ans)
                data['results'] = len(ans)

            data['result'] = result

            curs.close()
            db.close()  # XXX(mtaylor): should create self.args.persist to persist the connection, and auto-reopen if it db gets restarted
        except self.dbi.OperationalError,msg:
            log.log("<dbi>DBI.getData(): ID '%s' Operational Error: %s" % (self.ID, msg), 7)
            data['errmsg'] = msg
            try:
                db.close()
            except:
                pass
            return data
        except:
            systype,value = sys.exc_info()[:2]
            try:
                db.close()
            except:
                pass
            raise directive.DirectiveError, "Problem with %s: %s,%s" % (self.state.ID, systype, value)

        return data

##
## END - dbi.py
##
