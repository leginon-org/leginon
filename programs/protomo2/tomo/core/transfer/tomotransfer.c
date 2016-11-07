/*----------------------------------------------------------------------------*
*
*  tomotransfer.c  -  tomography: transfer functions
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomotransfer.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Tomotransfer *TomotransferCreate
                     (Size n)

{

  Tomotransfer *trans = malloc( n * sizeof(Tomotransfer) );
  if ( trans == NULL ) { logexception( E_MALLOC ); return NULL; }

  for ( Size i = 0; i < n; i++ ) {
    trans[i] = TomotransferInitializer;
  }

  return trans;

}


extern Status TomotransferDestroy
              (Size n,
               Tomotransfer *trans)

{

  if ( trans != NULL ) {

    free( trans );

  }

  return E_NONE;

}
