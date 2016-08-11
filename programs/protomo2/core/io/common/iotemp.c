/*----------------------------------------------------------------------------*
*
*  iotemp.c  -  io: common routines
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
#include "exception.h"
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>


/* functions */

extern char *IOPathTemp
             (const char *path)

{
  const char *name;
  Size namelength, dirlength, sffxlength = 0;
  const unsigned char digits[] = "0123456789abcdef";
  struct {
    struct timeval time;
    pid_t pid;
  } uniqbuf;
  unsigned char *buf = (unsigned char *)&uniqbuf;

  if ( path == NULL ) {
    namelength = 0; path = "";
  } else {
    namelength = strlen( path );
  }

  const char *dir = ""; /* or read from env variable */

  char *ptr = strrchr( path, DIRSEP );
  if ( ptr == NULL ) {
    dirlength = strlen( dir );
    name = path;
  } else {
    dir = path;
    dirlength = ptr - path;
    name = ptr + 1;
    namelength -= dirlength + 1;
  }

  if ( dirlength && ( dir[dirlength - 1] == DIRSEP ) ) {
    dirlength--;
  }

  char *sffx = strrchr( name, '.' );
  if ( sffx != NULL ) {
    sffxlength = namelength - ( sffx - name );
    namelength = sffx - name;
  }

  char *tmp = malloc( dirlength + 1 + namelength + sffxlength + 1 + 2 * sizeof(uniqbuf) + 1 );
  if ( tmp == NULL ) {
    logexception( E_MALLOC ); return NULL;
  }

  gettimeofday( &uniqbuf.time, NULL );
  uniqbuf.pid = getpid();

  ptr = tmp;
  if ( *dir ) {
    if ( dirlength ) {
      memcpy( ptr, dir, dirlength ); ptr += dirlength;
    }
    *ptr++ = DIRSEP;
  }
  if ( *name ) {
    memcpy( ptr, name, namelength ); ptr += namelength;
    *ptr++ = '_';
  }
  for ( Size i = 0; i < sizeof(uniqbuf); i++ ) {
    if ( buf[i] ) {
      *ptr++ = digits[ buf[i] & 0xf ];
      buf[i] >>= 4;
      *ptr++ = digits[ buf[i] & 0xf ];
    }
  }
  if ( sffxlength ) {
    memcpy( ptr, sffx, sffxlength ); ptr += sffxlength;
  }
  *ptr = 0;

  return tmp;

}
