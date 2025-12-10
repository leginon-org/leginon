**Abstract**

Leginon system includes the python-side programs that are writen in python and c, the
MySQL database and server, and the mainly php-based image and data viewers on a web
server.

The python-side programs provide a modular framework for building applications for TEM
image acquisition and analysis. Nodes can be connected through abstract events in Leginon's
modular architecture design. This gives Leginon the flexibility of application customization
at multiple levels. Because nodes can be launched from different machines, Leginon's
applications can inherently use distributed memory systems.

The MySQL-side database and server keep track of all information (metadata) accompanying
the acquired images efficiently.

The php-side web server and scripts retrieve information from the database and the file
storage system to display both raw information and organized reports.

NRAMM development includes the python-side and the php-side scripts. MySQL side uses
directly the open-source distribution.

The website <http://leginon.org> is the central location for leginon information and links.

The Forums are where users and
developers post their questions and answers.

Official bug report and feature request should be entered through this website using the [New Issue](http://emg.nysbc.org/redmine/projects/leginon/issues/new) tab.

[Terminology >](/leginon/Leginon_Manual/An_Introduction_to_Leginon/Terminology)
