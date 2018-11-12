/*----------------------------------------------------------------------------*
*
*  tomodiagnwrite.c  -  align: diagnostic output
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

extern Status TomodiagnWrite
              (Tomodiagn *diagn,
               Size index,
               const void *addr)

{
  Status status = E_NONE;

  if ( argcheck( diagn == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( addr  == NULL ) ) return pushexception( E_ARGVAL );

  if ( diagn->handle == NULL ) return pushexception( E_TOMODIAGN );

  if ( !diagn->status ) {

    status = ImageioWrite( diagn->handle, index * diagn->size, diagn->size, addr );
    if ( exception( status ) ) {
      diagn->status = status;
    }

  }

  return status;

}
