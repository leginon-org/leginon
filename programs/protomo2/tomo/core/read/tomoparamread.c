/*----------------------------------------------------------------------------*
*
*  tomoparamread.c  -  core: retrieve parameters
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
#include "exception.h"
#include <stdlib.h>


/* functions */

extern Status TomoparamReadError
              (const char *sect,
               const char *ident,
               Status status)

{

  if ( status ) {

    pushexception( status );

    if ( ( ident != NULL ) && *ident ) {
      appendexception( ", " );
      appendexception( ident );
    }

    if ( ( sect != NULL ) && *sect ) {
      if ( ( ident != NULL ) && *ident ) {
        appendexception( ", section " );
      } else {
        appendexception( ", " );
      }
      appendexception( sect );
    }

  }

  return status;

}


extern Status TomoparamReadErrorConflict
              (const char *sect,
               const char *ident,
               const char *confl)

{
  Status status = E_TOMOPARAMREAD_CONFL;

  pushexception( status );

  if ( ( ident != NULL ) && *ident ) {

    appendexception( ", " );
    appendexception( ident );

    if ( ( confl != NULL ) && *confl ) {
      appendexception( " with " );
      appendexception( confl );
    }

    if ( ( sect != NULL ) && *sect ) {
      appendexception( ", " );
      appendexception( sect );
    }

  }

  return status;

}


extern Status TomoparamReadPush
              (Tomoparam *tomoparam,
               const char *ident,
               const char **sect,
               Bool req)

{
  Status status;

  status = TomoparamPush( tomoparam, ident, sect );
  if ( status ) return pushexception( status );

  if ( req ) {

    if ( *sect == NULL ) {
      status = pushexception( E_TOMOPARAM_UNSEC );
      const char *sname = TomoparamSname( tomoparam );
      if ( ( sname != NULL ) && *sname && ( ident != NULL ) && *ident ) {
        appendexception( ", " );
        appendexception( sname );
        appendexception( "." );
        appendexception( ident );
      }
    }

  }

  return status;

}


extern Status TomoparamReadRot
              (Tomoparam *tomoparam,
               const char *ident,
               Coord *rot,
               Size *dim)

{
  Size rdim;
  Coord *val;
  Size count;
  Status status;

  status = TomoparamReadCoord( tomoparam, ident, &rdim, NULL, &val, &count );
  if ( status ) return exception( status );

  if ( rdim > 1 ) {
    status = exception( E_TOMOPARAM_DIM ); goto exit;
  }
  if ( ( count != 1 ) && ( count != 3 ) ) {
    status = exception( E_TOMOPARAM_LEN ); goto exit;
  }

  if ( dim == NULL ) { status = exception( E_TOMOPARAM ); goto exit; }
  if ( *dim == 0 ) {
    *dim = ( count == 3 ) ? 3 : 2;
  } else if ( *dim == 2 ) {
    if ( count != 1 ) {
      status = exception(E_TOMOPARAM_LEN ); goto exit;
    }
  } else if ( *dim == 3 ) {
    if ( count != 3 ) {
      status = exception(E_TOMOPARAM_LEN ); goto exit;
    }
  } else {
    status = exception( E_TOMOPARAM_DIM ); goto exit;
  }

  for ( Size i = 0; i < count; i++ ) {
    rot[i] = val[i] * Pi / 180;
  }

  exit:
  free( val );

  return status;

}
