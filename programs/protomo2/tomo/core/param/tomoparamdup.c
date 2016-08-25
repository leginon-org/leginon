/*----------------------------------------------------------------------------*
*
*  tomoparamdup.c  -  tomography: parameter files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoparamcommon.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern Tomoparam *TomoparamDup
                  (Tomoparam *tomoparam)

{
  Status status = E_MALLOC;

  Tomoparam *tomoparamdup = malloc( sizeof(Tomoparam) );
  if ( tomoparamdup == NULL ) goto error1;
  *tomoparamdup = TomoparamInitializer;

  if ( tomoparam->prfx != NULL ) {
    tomoparamdup->prfx = strdup( tomoparam->prfx );
    if ( tomoparamdup->prfx == NULL ) goto error2;
  }

  if ( tomoparam->sname != NULL ) {
    tomoparamdup->sname = strdup( tomoparam->sname );
    if ( tomoparamdup->sname == NULL ) goto error2;
  }

  status = StringTableDup( tomoparam->sect, &tomoparamdup->sect );
  if ( exception( status ) ) goto error2;

  status = StringTableDup( tomoparam->ident, &tomoparamdup->ident ); 
  if ( exception( status ) ) goto error2;

  status = StringTableDup( tomoparam->strlit, &tomoparamdup->strlit ); 
  if ( exception( status ) ) goto error2;

  tomoparamdup->varlen = tomoparam->varlen;
  tomoparamdup->vartab = malloc( tomoparam->varlen * sizeof(*tomoparam->vartab) );
  if ( tomoparamdup->vartab == NULL ) goto error3;
  memcpy( tomoparamdup->vartab, tomoparam->vartab, tomoparam->varlen * sizeof(*tomoparam->vartab) );

  tomoparamdup->vallen = tomoparam->vallen;
  tomoparamdup->valtab = malloc( tomoparam->vallen * sizeof(*tomoparam->valtab) );
  if ( tomoparamdup->valtab == NULL ) goto error3;
  memcpy( tomoparamdup->valtab, tomoparam->valtab, tomoparam->vallen * sizeof(*tomoparam->valtab) );

  return tomoparamdup;

  error3: status = E_MALLOC;
  error2: TomoparamDestroy( tomoparamdup );
  error1: pushexception( status );

  return NULL;

}
