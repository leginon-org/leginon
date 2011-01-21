'''
Sinedon is a simple way to define an object relational mapping between
Python objects and a MySQL database.

At the global level, you have the following classes and functions available:

sinedon.Data
  This is the base class from which you can create your own classes which
  are mapped to tables in the database

sinedon.getConfig(modulename)
  Call this function to get the currently configured database connection
  parameters for the named module.

sinedon.setConfig(modulename, host=hostname, db=dbname, user=username, ...)
  Call this function to set the database connection parameters for the
  named module

getConnection(modulename)
  Call this function to get a connection to the named database
'''

from sinedon.data import Data
from dbconfig import getConfig, setConfig
from connections import getConnection
import warnings
warnings.filterwarnings('ignore', module='sinedon')

# existing_file setting determines what to do if a sinedon object insert
# will cause a file to be overwritten.  Possible values:
#  'warning':  print warning to stderr, but overwrite file anyway
#  'exception':  raise an exception without overwriting the file
#  'skip':  skip writing the file and print warning to stderr
#  None:  overwrite file without warning
existing_file = 'warning'
