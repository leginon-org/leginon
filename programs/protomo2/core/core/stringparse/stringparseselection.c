/*----------------------------------------------------------------------------*
*
*  stringparseselection.c  -  core: character string operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "stringparse.h"
#include "exception.h"


/* functions */

extern Status StringParseSelection
              (const char *str,
               const char **end,
               void *dst,
               StringParseParam *param)

{
  Size dstsize = 0;
  Status status;

  if ( ( str == NULL ) || ( param == NULL ) ) {
    status = exception( E_ARGVAL ); goto exit;
  }

  StringParseParam pairparam;
  pairparam.pair.parse = StringParseSize;
  pairparam.pair.single = True;
  pairparam.pair.space = param->selection.space;
  pairparam.pair.sep = '-';

  StringParseParam listparam;
  listparam.list.parse = StringParsePair;
  listparam.list.param = &pairparam;
  listparam.list.count = param->selection.count;
  listparam.list.space = param->selection.space;
  listparam.list.sep = ',';

  status = StringParseList( str, end, dst, &listparam );
  if ( exception( status ) ) goto exit;

  dstsize = listparam.list.dstsize;

  param->selection.count = listparam.list.count;
  param->selection.min = SizeMax;
  param->selection.max = 0;
  param->selection.empty = False;

  if ( dst != NULL ) {

    param->selection.count = 0;

    Size *s = dst;
    Size *d = dst;

    for ( Size i = 0; i < listparam.list.count; i++ ) {

      Size min = *s++;
      Size max = *s++;
      if ( min <= max ) {
        *d++ = min;
        *d++ = max;
        param->selection.count++;
        if ( min < param->selection.min ) param->selection.min = min ;
        if ( max > param->selection.max ) param->selection.max = max ;
      }  else {
        param->selection.empty = True;
      }

    }

  }

  exit:

  if ( param != NULL ) {
    param->dstsize = dstsize;
  }

  return status;

}
