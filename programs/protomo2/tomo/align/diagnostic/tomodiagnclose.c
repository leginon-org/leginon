/*----------------------------------------------------------------------------*
*
*  tomodiagnclose.c  -  align: diagnostic output
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomodiagncommon.h"
#include "exception.h"


/* functions */

extern Status TomodiagnClose
              (Tomodiagn *diagn)

{
  Status status;

  if ( argcheck( diagn == NULL ) ) return pushexception( E_ARGVAL );

  if ( diagn->handle == NULL ) return pushexception( E_TOMODIAGN );

  if ( !diagn->status ) {
    status = ImageioUndel( diagn->handle );
    if ( exception( status ) ) goto exit;
  }

  status = ImageioClose( diagn->handle );
  logexception( status );

  diagn->handle = NULL;

  exit:

  return status;

}
