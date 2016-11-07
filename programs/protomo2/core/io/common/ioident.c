/*----------------------------------------------------------------------------*
*
*  ioident.c  -  io: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "io.h"
#include "baselib.h"
#include <pwd.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/utsname.h>
#include <unistd.h>


/* functions */

extern IOIdent IOGetIdent
               (const char *str,
                IOIdent id0)

{
  #define nchar 4
  #define nmax  4
  #define buflen 256
  char buf[nchar+buflen];
  Size n = 0;
  uint64_t id = id0;

  if ( !id ) {

    Time t = TimeGet();
    if ( t.date && t.time ) {
      uint32_t d = t.date & 0xf; t.date >>= 4; d += 10 * ( t.date & 0xf ); t.date >>= 4;
      uint32_t m = t.date & 0xf; t.date >>= 4; m += 10 * ( t.date & 0xf ); t.date >>= 4;
      uint32_t y = t.date & 0xf; t.date >>= 4; y += 10 * ( t.date & 0xf ); t.date >>= 4;
      id = y % 100;
      id *= 12; id += m - 1;
      id *= 32; id += d;
      id *= 24 * 60 * 60 * 1000; id += t.time;
    } else {
      id = random();
    }

  }

  if ( str == NULL ) {

    struct utsname un;
    struct passwd pw; struct passwd *p;
    if ( !uname( &un ) ) {
      char *u;
      u = un.nodename; while ( u[n] && ( n < nmax ) ) { buf[n] = u[n]; n++; }
      u = un.release;  while ( u[n] && ( n < nmax ) ) { buf[n] = u[n]; n++; }
      u = un.version;  while ( u[n] && ( n < nmax ) ) { buf[n] = u[n]; n++; }
    }
    if ( !getpwuid_r( getuid(), &pw, buf + nchar, buflen, &p ) ) {
      if ( p != NULL ) {
        while ( *pw.pw_name && ( n < nmax ) ) { buf[n] = *pw.pw_name++; n++; }
      }
    }

  } else {

    while ( str[n] && ( n < nmax ) ) { buf[n] = str[n]; n++; }

  }

  uint64_t h = 0;
  for ( Size i = 0; i < nchar; i++ ) {
    h *= 40;
    if ( i < n ) {
      char c = buf[i] & 0x7f;
      if ( c == '$' ) {
        c = 36;
      } else if ( c == '-' ) {
        c = 37;
      } else if ( c == '.' ) {
        c = 38;
      } else if ( c <  '0' ) {
        c = 39;
      } else if ( c <= '9' ) {
        c -= '0';
      } else if ( c <  'A' ) {
        c = 39;
      } else if ( c <= 'Z' ) {
        c -= 'A' - 10;
      } else if ( c <  'a' ) {
        c = 39;
      } else if ( c <= 'z' ) {
        c -= 'a' - 10;
      } else {
        c = 39;
      }
      h += c;
    }
  }

  id |= h << 42;

  return id;

}
