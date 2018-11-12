/*----------------------------------------------------------------------------*
*
*  strings.c  -  core: character string operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "strings.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Size StringListCount
            (char **list)

{
  Size count = 0;

  if ( list != NULL ) {

    for ( char **lst = list; *lst != NULL; lst++ ) {
      count++;
    }

  }

  return count;

}


extern void StringListFree
            (char **list)

{

  if ( list != NULL ) {

    for ( char **lst = list; *lst != NULL; lst++ ) {
      free( *lst );
    }

    free( list );

  }

}
