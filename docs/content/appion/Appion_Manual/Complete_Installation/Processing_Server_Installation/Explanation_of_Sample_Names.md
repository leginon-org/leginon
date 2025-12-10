MySQL database usernames, Leginon/Appion username, and your linux login username are all different. Each serves its own purpose.

Database names, user, and password need to be entered during web server and sinedon.cfg setup.
In our example, we have:

  --------------------------------------------------- --------------
  purpose                                             example name
  database name for leginon parameters and metadata   leginondb
  database name for project management                projectdb
  database name prefix for appion processing          ap
  database user name                                  usr_object
  database user password                              (not set)
  --------------------------------------------------- --------------

username for Leginon image viewing and appion processing/reporting from the web = username registered for Leginon running
Firstname used in the registration + Lastname used in the registration = fullname entered in leginon.cfg

Relevant Topics:
[Database Server Installation](/appion/Appion_Manual/Complete_Installation/Database_Server_Installation)
[Configure sinedon.cfg](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Configure_sinedoncfg)
[Web Server Installation](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation)
