/*----------------------------------------------------------------------------*
*
*  textioreadlist.c  -  io: text file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "textiocommon.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern Status TextioReadlist
              (Textio *textio,
               StringParse parse,
               Size fieldcount,
               void **list,
               Size *count)

{
  StringParseParam param;
  char *line;
  Size linenr;
  Status status;

  if ( argcheck( textio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( parse  == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( !fieldcount ) ) return pushexception( E_ARGVAL );

  memset( &param, 0, sizeof(param) );
  status = parse( NULL, NULL, NULL, &param );
  if ( pushexception( status ) ) return status;

  Size elsize = fieldcount * param.dstsize;
  void *buf = malloc( elsize );
  if ( buf == NULL ) return pushexception( E_MALLOC );

  memset( &param, 0, sizeof(param) );
  param.list.parse = parse;
  param.list.param = NULL;
  param.list.count = fieldcount;
  param.list.space = True;
  param.list.sep = ' ';

  char *lst = NULL;
  Size cnt = 0;

  for ( Size size = 0; ; size += elsize ) {

    status = TextioReadline( textio, &line, &linenr );
    if ( pushexception( status ) ) goto error;

    if ( line == NULL ) break;

    status = StringParseList( line, NULL, buf, &param );
    if ( pushexception( status ) ) goto error;

    if ( list != NULL ) {

      void *ptr = realloc( lst, size + elsize );
      if ( ptr == NULL ) goto error;
      lst = ptr;

      memcpy( lst + size, buf, elsize );

    }

    cnt++;

  }

  free( buf );

  if ( list == NULL ) {
    free( lst );
  } else {
    *list = lst;
  }
  if ( count != NULL ) {
    *count = cnt;
  }

  return E_NONE;

  error:

  free( buf );
  if ( lst != NULL ) free( lst );

  return status;

}
