/*----------------------------------------------------------------------------*
*
*  stringtablecopy.c  -  core: character string table
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "stringtable.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern Status StringTableDup
              (const char *src,
               char **dst)

{
  char *tab = NULL;

  if ( argcheck( dst == NULL ) ) return exception( E_ARGVAL );

  if ( src != NULL ) {

    Size siz = StringTableSize( src );

    if ( siz ) {
      tab = malloc( siz );
      if ( tab == NULL ) return exception( E_MALLOC );
      memcpy( tab, src, siz );
    }

  }

  *dst = tab;

  return E_NONE;

}
