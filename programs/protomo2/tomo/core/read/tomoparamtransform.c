/*----------------------------------------------------------------------------*
*
*  tomoparamtransform.c  -  core: retrieve parameters
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoparamreadcommon.h"
#include "mat.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern Status TomoparamTransform
              (Tomoparam *tomoparam,
               const char *ident,
               Size *dimptr,
               Transform *transform,
               Bool translation)

{
  const char *sect;
  const char *param;
  Status status, retstat = E_NONE;

  if ( argcheck( tomoparam == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( dimptr == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( transform == NULL ) ) return pushexception( E_ARGVAL );

  *transform = TransformInitializer;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, False );
    if ( exception( status ) ) return status;
    if ( sect == NULL ) return E_NONE;
  }

  Size dim = *dimptr;
  const char *Apar = NULL; Coord Abuf[3*3];
  const char *bpar = NULL; Coord bbuf[3];
  const char *Dpar = NULL; Coord Dbuf[3];
  Coord *rot = Dbuf;

  param = "A";
  status = TomoparamReadMatn( tomoparam, param, Abuf, 3, &dim );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      Apar = param;
    }
  }

  param = "b";
  status = TomoparamReadArrayCoord( tomoparam, param, bbuf, 3, &dim );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( !translation ) {
      retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_PAR );
    } else {
      bpar = param;
    }
  }

  param = "D";
  status = TomoparamReadArrayCoord( tomoparam, param, Dbuf, 3, &dim );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( Apar != NULL ) {
      retstat = TomoparamReadErrorConflict( sect, param, Apar );
    } else {
      MatnDiag( dim, Dbuf, Abuf );
      Dpar = param;
    }
  }

  param = "rot";
  status = TomoparamReadRot( tomoparam, param, rot, &dim );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( ( Apar != NULL ) || ( Dpar != NULL ) ) {
      if ( Apar != NULL ) retstat = TomoparamReadErrorConflict( sect, param, Apar );
      if ( Dpar != NULL ) retstat = TomoparamReadErrorConflict( sect, param, Dpar );
    } else if ( dim == 3 ) {
      Mat3Rot( rot, (void *)Abuf ); Apar = param;
    } else {
      Mat2Rot( rot, (void *)Abuf ); Apar = param;
    }
  }

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) return status;
  }

  if ( !retstat && dim ) {
    if ( ( Apar != NULL ) || ( Dpar != NULL ) ) {
      Size Asize = dim * dim * sizeof(Coord);
      transform->A = malloc( Asize );
      if ( transform->A == NULL ) { status = pushexception( E_MALLOC ); goto error; }
      memcpy( transform->A, Abuf, Asize );
    }
    if ( bpar != NULL ) {
      Size bsize = dim * sizeof(Coord);
      transform->b = malloc( bsize );
      if ( transform->b == NULL ) { status = pushexception( E_MALLOC ); goto error; }
      memcpy( transform->b, bbuf, bsize );
    }
    transform->dim = dim;
    *dimptr = dim;
  }

  return retstat ? E_TOMOPARAMREAD_ERROR : E_NONE;

  error:
  if ( transform->A != NULL ) free( transform->A );
  if ( transform->b != NULL ) free( transform->b );
  *transform = TransformInitializer;
  return status;

}


extern Status TomoparamTransform2
              (Tomoparam *tomoparam,
               const char *ident,
               Transform *transform)

{
  Size dim = 2;
  Status status;

  status = TomoparamTransform( tomoparam, ident, &dim, transform, False );
  logexception( status );

  return status;

}


extern Status TomoparamTransform3
              (Tomoparam *tomoparam,
               const char *ident,
               Transform *transform)

{
  Size dim = 3;
  Status status;

  status = TomoparamTransform( tomoparam, ident, &dim, transform, False );
  logexception( status );

  return status;

}


extern Status TomoparamTransformFinal
              (Transform *transform)

{

  if ( transform != NULL ) {

    if ( transform->A != NULL ) free( transform->A );
    if ( transform->b != NULL ) free( transform->b );
    *transform = TransformInitializer;
  }

  return E_NONE;

}
