/*----------------------------------------------------------------------------*
*
*  iopath.c  -  io: common routines
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
#include <unistd.h>


/* functions */

extern char *IOCurrentPath
             (const char *path)

{
  char *fullpath;

  if ( path == NULL ) {

    fullpath = strdup( "" );

  } else if ( *path == DIRSEP ) {

    fullpath = strdup( path );

  } else if ( ( path[0] == '-' ) && !path[1] ) {

    fullpath = strdup( path );

  } else {

    fullpath = NULL;
    size_t cwdsize = PATH_MAX;
    char *cwd = malloc( cwdsize );
    if ( cwd == NULL ) {
      logexception( E_MALLOC ); return NULL;
    }
    if ( getcwd( cwd, cwdsize ) == NULL ) {
      logexception( E_ERRNO );
    } else {
      size_t cwdlen = strlen( cwd );
      size_t pathlen = strlen( path );
      fullpath = malloc( cwdlen + 1 + pathlen + 1 );
      if ( fullpath == NULL ) {
        logexception( E_MALLOC );
      } else {
        char *ptr = fullpath;
        memcpy( ptr, cwd, cwdlen ); ptr += cwdlen;
        *ptr++ = DIRSEP;
        memcpy( ptr, path, pathlen ); ptr += pathlen;
        *ptr = 0;
      }
    }
    free( cwd );

  }

  return fullpath;

}


extern char *IOPathName
             (const char *path)

{
  const char *ptr;

  if ( path == NULL ) {

    ptr = "";

  } else {

    ptr = strrchr( path, DIRSEP );
    if ( ptr == NULL ) {
      ptr = path;
    } else {
      ptr++;
    }

  }

  char *name = strdup( ptr );

  return name;

}


extern char *IOPathDir
             (const char *path)

{
  size_t len;

  if ( path == NULL ) {

    len = 1;

  } else {

    const char *ptr = strrchr( path, DIRSEP );
    if ( ptr == NULL ) {
      len = 1;
    } else {
      len = ptr - path + 1;
      if ( ptr == path ) len++;
    }

  }

  char *name = malloc( len );
  if ( name == NULL ) return NULL;

  if ( --len ) {
    memcpy( name, path, len );
  }
  name[len] = 0;

  return name;

}
