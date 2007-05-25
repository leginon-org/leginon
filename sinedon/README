WHAT IS SINEDON?

Sinedon is an object-relational mapping package written in the Python
programming language.  The goal of Sinedon is to make it easy for a
programmer to build a database through Python scripting rather than by
using standard SQL commands.  Dictionary-like classes are defined in Python
which define the structure of tables in the database.  The keys of a class
map to the table columns.  An object of a class, with its dictionary values
filled in, is mapped to one row in the table that corresponds to that
class.  Objects of different classes may also reference each other, which
creates relational links between records of two tables using foreign keys.
The python programmer never needs to create tables or perform any
configuration of the tables.  Sinedon will automatically create the tables
when they are needed.  If a class changes in structure, the structure of
the mapped table will automatically be updated as well.  SQL queries are
also transparent to the Python programmer.  A query is done by creating a
python instance with the known key-value pairs filled in.  The query will
return a list of objects from the database that match the query object.

INSTALLATION

To install, run this as root:
	python setup.py install

See examples directory for some examples of how to use sinedon.

Here is a brief introduction:

Config File:
Sinedon can be given default database connection parameters in a config
file called sinedon.cfg which should be in your home directory or in the
current directory where you run your python script from.  See the example
config file: examples/sinedon.cfg.

Defining Python classes that will map to database tables:
You must create a Python module that will map to a MySQL database.
In the module, you will define a class for each table in your database.
These classes must be subclasses of sindedon.Data.  See examples/mydata1.py
and examples/mydata2.py for an example of such a module.

Connecting to the database through Sinedon:
First, the database connection parameters must be configured, either through
a config file as mentioned above, or at runtime using sinedon.setConfig().
For example:  sinedon.setConfig('mymodule', host='myhost', passwd=...)
will create a mapping between the module 'mymodule.py' and the database
given by the connection parameters.
Once the mapping is configured, you can connect as follows:
db = sinedon.getConnection('mymodule')
