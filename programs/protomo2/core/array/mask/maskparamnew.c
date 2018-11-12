/*----------------------------------------------------------------------------*
*
*  maskparamnew.c  -  array: mask operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "maskparam.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern MaskParam *MaskParamNew
                  (MaskParam **param)


{
  MaskParam *new, *ptr;
  Size n = 0;

  if ( param == NULL ) {
    logexception( E_ARGVAL ); return NULL;
  }

  ptr = *param;
  if ( ptr != NULL ) {
    while ( ptr->flags & MaskFunctionMask ) ptr++;
    n = ptr - *param;
  }

  new = malloc( ( n + 2 ) * sizeof(MaskParam) );
  if ( new == NULL ) {
    logexception( E_MALLOC ); return NULL;
  }
  if ( n ) {
    memcpy( new, *param, n * sizeof(MaskParam) );
  }
  new[n] = new[n+1] = MaskParamInitializer;

  *param = new;

  return new + n;

}
