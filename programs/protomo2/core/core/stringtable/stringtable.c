/*----------------------------------------------------------------------------*
*
*  stringtable.c  -  core: character string table
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


/* functions */

extern Status StringTableFree
              (char **table)

{

  if ( argcheck( table == NULL ) ) return exception( E_ARGVAL );

  if ( *table != NULL ) {
    free( *table );
    *table = NULL;
  }

  return E_NONE;

}


extern Size StringTableSize
            (const char *table)

{
  const char *tab;

  if ( table == NULL ) return 0;

  tab = table;

  while ( *tab ) {
    const char *ptr = tab;
    while ( *ptr ) { ptr++; }
    tab = ++ptr;
  }

  return tab - table + 1;

}
