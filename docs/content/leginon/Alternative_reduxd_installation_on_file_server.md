This approach is less tested, but has been found necessary in the case of a very high load system (multiple microscopes acquiring data, multiple processing jobs, multiple web clients and servers, etc). The problem has been that all of this demand for image I/O is occuring over NFS, and the NFS server is not coping with the high demand. One solution we have been investigating is to run reduxd directly on the file server rather than the web server. This means reduxd has direct access to the image files (not through NFS) and the web server now accesses reduxd over the network rather than locally. This has two potential benefits: 1) less load on the NFS server, 2) only transferring JPEGs over the network, not MRCs.

How to do it:

1.  Install required myami components on the file server, at least pyami, sinedon, numextension, redux, leginon, modules, and any other 3rd part packages required by those.
2.  (optional) edit init.d/reduxd and use the optional high priority command line (see comment in that file)
3.  Configure redux.cfg on file server and start reduxd
4.  On web server, configure config.php: turn off all caching options, set redux server host to be the file server
5.  skip starting reduxd on the web server
6.  skip imcache as described below, since this also uses redux locally and accesses images over NFS
