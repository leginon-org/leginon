#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
Makefile - makes em.so for a C to Python interface
           (allows easier emScope calls in C)
           makes emTCL.so for a TCL to C interface
           (allows calls from TCL to emScope via em.so)
magic - the compile line used within Matlab to build em.mexglx
           (allows calls from Matlab to emScope via em.so)
        this can be difficult to get working with all the external
        library dependencies.
client.py - the thin python wrapper to emScope server for use on the client
            side of emScope. Used to create a instance of client w/ an
            address, then calls to emScope server can be made with said
            instance.
*.m - part of a quick example program using the Matlab interface to emScope

em.c, em.h - a C helper library for calling Python, makes using emScope with
             C easier.
emTCL.c - an interface to TCL using em.so
emMatlab.c - an interface to Matlab using em.so

Basic overview of using Matlab and emScope:
Start the emScope RPC server on the server PC.
Start Matlab with em.mexglx in the path
Make calls in format:
if_return_value = em(server_address, 'get' | 'set', parameter, if_value);

Examples:
mag = em('http://tecnai:8000', 'get', 'magnification');
em('http://tecnai:8000', 'set', 'magnification', mag * 2);

image = em('http://tecnai:8001', 'get', 'image data');
