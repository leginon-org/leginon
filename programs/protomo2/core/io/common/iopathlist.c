/*----------------------------------------------------------------------------*
*
*  iopathlist.c  -  io: common routines
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


/* functions */

extern char *IOPathList
             (const char **pathlist,
              const char *path)

{
  size_t pathlen, len;
  const char *dir, *ptr;

  if ( pathlist == NULL )  return NULL;

  pathlen = ( path == NULL ) ? 0 : strlen( path );

  if ( pathlen && ( *path == DIRSEP ) ) {

    ptr = *pathlist + strlen( *pathlist );
    len = 0;

  } else {

    /* skip separators */
    dir = *pathlist;
    while ( *dir == PATHSEP ) dir++;
    if ( !*dir ) {
      *pathlist = dir;
      return NULL;
    }

    /* skip over path component and remove trailing slashes */
    ptr = dir;
    while ( *ptr && ( *ptr != PATHSEP ) ) ptr++;
    const char *end = ptr - 1;
    while ( ( end != dir ) && ( *end == DIRSEP ) ) end--;
    len = end - dir + 1;
    if ( *end != DIRSEP ) len++;
    while ( *ptr == PATHSEP ) ptr++;

  }

  char *buf = malloc( len + pathlen + 1 );
  if ( buf == NULL ) return NULL;
  char *str = buf;

  if ( len ) {
    memcpy( str, dir, len );
    str[ len - 1 ] = DIRSEP;
    str += len;
  }

  if ( pathlen ) {
    memcpy( str, path, pathlen );
    str += pathlen;
  }

  *str = 0;

  *pathlist = ptr;

  return buf;

}
