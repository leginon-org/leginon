/*----------------------------------------------------------------------------*
*
*  stringtableinsert.c  -  core: character string table
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

extern Status StringTableInsert
              (char **table,
               const char *string,
               Size *index)

{
  char *tab;
  Size len, siz = 0;

  if ( argcheck( table  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( string == NULL ) ) return exception( E_ARGVAL );

  if ( !*string ) return exception( E_ARGVAL );

  if ( *table != NULL ) {

    tab = *table;

    while ( *tab ) {
      char *ptr = tab;
      const char *str = string;
      while ( *ptr && *str && ( *ptr == *str ) ) { ptr++; str++; }
      if ( *ptr ) {
        /* not at end of p */
        do { ptr++; } while ( *ptr );
      } else if ( !*str ) {
        /* at end of p and s */
        if ( index != NULL ) *index = tab - *table;
        return E_STRINGTABLE_EXISTS;
      }
      tab = ++ptr;
    }

    siz = tab - *table;

  }

  len = strlen( string ) + 1;

  tab = realloc( *table, siz + len + 1 );
  if ( tab == NULL ) return exception( E_MALLOC );

  memcpy( tab + siz, string, len );

  tab[ siz + len ] = 0;

  *table = tab;

  if ( index != NULL ) *index = siz;

  return E_NONE;

}


extern Status StringTableInsertLen
              (char **table,
               const char *string,
               Size length,
               Size *index)

{
  char *tab;
  Size len, siz = 0;

  if ( argcheck( table  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( string == NULL ) ) return exception( E_ARGVAL );

  if ( !*string || !length ) return exception( E_ARGVAL );

  length = strnlen( string, length );

  if ( *table != NULL ) {

    tab = *table;

    while ( *tab ) {
      char *ptr = tab;
      const char *str = string;
      Size len = length;
      while ( *ptr && len && ( *ptr == *str ) ) { ptr++; str++; len--; }
      if ( *ptr ) {
        /* not at end of p */
        do { ptr++; } while ( *ptr );
      } else if ( !len ) {
        /* at end of p and s */
        if ( index != NULL ) *index = tab - *table;
        return E_STRINGTABLE_EXISTS;
      }
      tab = ++ptr;
    }

    siz = tab - *table;

  }

  len = length + 1;

  tab = realloc( *table, siz + len + 1 );
  if ( tab == NULL ) return exception( E_MALLOC );

  memcpy( tab + siz, string, length );

  tab[ siz + length ] = 0;

  tab[ siz + len ] = 0;

  *table = tab;

  if ( index != NULL ) *index = siz;

  return E_NONE;

}


extern Status StringTableInsertTail
              (char **table,
               const char *string,
               Size *index)

{
  char *tab;
  Size length, len, siz = 0;

  if ( argcheck( table  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( string == NULL ) ) return exception( E_ARGVAL );

  if ( !*string ) return exception( E_ARGVAL );

  length = strlen( string );

  if ( *table != NULL ) {

    tab = *table;

    while ( *tab ) {
      char *ptr = tab;
      const char *str = string;
      while ( *ptr && *str && ( *ptr == *str ) ) { ptr++; str++; }
      if ( *ptr ) {
        /* not at end of p */
        do { ptr++; } while ( *ptr );
        siz = ptr - tab;
        if ( siz > length ) {
          tab = ptr - length;
          str = string;
          while ( *str && ( *tab == *str ) ) { tab++; str++; }
          if ( !*str ) {
            if ( index != NULL ) *index = ( ptr - length ) - *table;
            return E_STRINGTABLE_EXISTS;
          }
        }
      } else if ( !*str ) {
        /* at end of p and s */
        if ( index != NULL ) *index = tab - *table;
        return E_STRINGTABLE_EXISTS;
      }
      tab = ++ptr;
    }

    siz = tab - *table;

  }

  len = length + 1;

  tab = realloc( *table, siz + len + 1 );
  if ( tab == NULL ) return exception( E_MALLOC );

  memcpy( tab + siz, string, len );

  tab[ siz + len ] = 0;

  *table = tab;

  if ( index != NULL ) *index = siz;

  return E_NONE;

}


extern Status StringTableInsertTailLen
              (char **table,
               const char *string,
               Size length,
               Size *index)

{
  char *tab;
  Size len, siz = 0;

  if ( argcheck( table  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( string == NULL ) ) return exception( E_ARGVAL );

  if ( !*string || !length ) return exception( E_ARGVAL );

  length = strnlen( string, length );

  if ( *table != NULL ) {

    tab = *table;

    while ( *tab ) {
      char *ptr = tab;
      const char *str = string;
      Size len = length;
      while ( *ptr && len && ( *ptr == *str ) ) { ptr++; str++; len--; }
      if ( *ptr ) {
        /* not at end of p */
        do { ptr++; } while ( *ptr );
        siz = ptr - tab;
        if ( siz > length ) {
          tab = ptr - length;
          str = string;
          len = length;
          while ( len && ( *tab == *str ) ) { tab++; str++; len--; }
          if ( !len ) {
            if ( index != NULL ) *index = ( ptr - length ) - *table;
            return E_STRINGTABLE_EXISTS;
          }
        }
      } else if ( !len ) {
        /* at end of p and s */
        if ( index != NULL ) *index = tab - *table;
        return E_STRINGTABLE_EXISTS;
      }
      tab = ++ptr;
    }

    siz = tab - *table;

  }

  len = length + 1;

  tab = realloc( *table, siz + len + 1 );
  if ( tab == NULL ) return exception( E_MALLOC );

  memcpy( tab + siz, string, length );

  tab[ siz + length ] = 0;

  tab[ siz + len ] = 0;

  *table = tab;

  if ( index != NULL ) *index = siz;

  return E_NONE;

}
