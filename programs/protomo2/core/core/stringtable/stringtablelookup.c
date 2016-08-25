/*----------------------------------------------------------------------------*
*
*  stringtablelookup.c  -  core: character string table
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
#include <string.h>


/* functions */

extern Status StringTableLookup
              (const char *table,
               const char *string,
               Size *index)

{
  const char *tab;

  if ( argcheck( string == NULL ) ) return exception( E_ARGVAL );

  if ( !*string ) return exception( E_ARGVAL );

  if ( table == NULL ) return E_STRINGTABLE_NOTFOUND;

  tab = table;

  while ( *tab ) {
    const char *ptr = tab;
    const char *str = string;
    while ( *ptr && *str && ( *ptr == *str ) ) { ptr++; str++; }
    if ( *ptr ) {
      /* not at end of p */
      do { ptr++; } while ( *ptr );
    } else if ( !*str ) {
      /* at end of p and s */
      if ( index != NULL ) {
        *index = tab - table;
      }
      return E_NONE;
    }
    tab = ++ptr;
  }

  return E_STRINGTABLE_NOTFOUND;

}


extern Status StringTableLookupLen
              (const char *table,
               const char *string,
               Size length,
               Size *index)

{
  const char *tab;

  if ( argcheck( string == NULL ) ) return exception( E_ARGVAL );

  if ( !*string || !length ) return exception( E_ARGVAL );

  if ( table == NULL ) return E_STRINGTABLE_NOTFOUND;

  length = strnlen( string, length );

  tab = table;

  while ( *tab ) {
    const char *ptr = tab;
    const char *str = string;
    Size len = length;
    while ( *ptr && len && ( *ptr == *str ) ) { ptr++; str++; len--; }
    if ( *ptr ) {
      /* not at end of p */
      do { ptr++; } while ( *ptr );
    } else if ( !len ) {
      /* at end of p and s */
      if ( index != NULL ) {
        *index = tab - table;
      }
      return E_NONE;
    }
    tab = ++ptr;
  }

  return E_STRINGTABLE_NOTFOUND;

}
