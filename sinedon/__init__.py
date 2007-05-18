'''
Sinedon is a simple way to define an object relational mapping between
Python objects and a MySQL database.

Data
DB
getConfig
setConfig
'''

from data import Data
from dbdatakeeper import DBDataKeeper
DB = DBDataKeeper
from dbconfig import getConfig, setConfig
