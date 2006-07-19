function conn = connect_db(db)
%
% DESCRIPTION: 
%      Returns connection to the database db.
%
% USAGE: 
%     conn = connect_db(db)
%     
%     db   : Name of the database 'leginon', 'dbemdata' or 'processing'
%     conn : Connection. 
%
% See also DATABASE.
%
% Copyright 2004-2005 Denis Fellman and Satya P. Mallick  


switch lower(db) 
    case  'leginon' 
        dbserver='jdbc:mysql://cronus4.scripps.edu/';
        user='anonymous';
        pass='';
    case  'dbemdata'
        dbserver='jdbc:mysql://cronus4.scripps.edu/';
        user='usr_object';
        pass='';
    case  'processing'
        dbserver='jdbc:mysql://cronus4.scripps.edu/';
        user='usr_object';
        pass='';
end 

driver='org.gjt.mm.mysql.Driver';
url=strcat(dbserver,db);
conn = database(db, user, pass, driver, url);
    
