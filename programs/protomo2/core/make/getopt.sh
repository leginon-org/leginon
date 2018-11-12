#!/bin/sh
#
# Copyright © 2012 Hanspeter Winkler
#

set -e

awk '
  $3 == "SET" { set[$1] = $2; next }
  $4 == "SET" { set[$1] = set[$1] " -l" $2 }
  $4 != "SET" { lib[$1] = lib[$1] " -l" $2 }
  $3 == "/usr" { next }
  $3 == "NOTFOUND" { next }
  { libpath = $3 "/lib"; incpath = $3 "/include" }
  $3 == "LIBPATH" { libpath = "$(LIBPATH)"; incpath = "$(LIBINCS)" }
  {
    p = "-L" libpath
    if ( index( path[$1], p ) == 0 ) {
      path[$1] = path[$1] " " p
      incl[$1] = incl[$1] " -I" incpath
    }
  }
  END {
    for ( i in set ) {
      if ( index( set[i], "-l" ) ) {
        print "LIB" i " =" path[i] set[i]
      } else {
        print "LIB" i " = " set[i]
      }
    }
    for ( i in lib ) {
      printf( "\n" )
      print "INC" i " =" incl[i]
      print "LIB" i " =" path[i] lib[i]
    }
 }
'
