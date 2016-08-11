/*----------------------------------------------------------------------------*
*
*  tomoparamimageio.c  -  core: retrieve parameters
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
#include "tiffiodefs.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern Status TomoparamImageio
              (Tomoparam *tomoparam,
               const char *ident,
               ImageioParam *ioparam)

{
  const char *sect;
  const char *param;
  Status status, retstat = E_NONE;

  if ( argcheck( tomoparam == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( ioparam == NULL ) ) return pushexception( E_ARGVAL );

  *ioparam = ImageioParamDefault;

  if ( ident != NULL ) {
    status = TomoparamReadPush( tomoparam, ident, &sect, False );
    if ( exception( status ) ) return status;
    if ( sect == NULL ) return E_NONE;
  }

  ImageioParam imageio = ImageioParamDefault;
  Bool boolval;
  char *string;

  param = "format";
  status = TomoparamReadScalarString( tomoparam, param, &string );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      status = ImageioFormatCheck( string );
      if ( exception( status ) ) {
        retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
        free( string );
      } else {
        imageio.format = string;
      }
    }
  }

  param = "cap";
  status = TomoparamReadScalarString( tomoparam, param, &string );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      imageio.cap = ImageioCapCheck( string );
      if ( !imageio.cap ) {
        retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
      }
      free( string );
    }
  } else {
    imageio.cap = 0;
  }

  param = "tiff_int";
  status = TomoparamReadScalarBool( tomoparam, param, &boolval );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else if ( boolval ) {
      TiffioOptions *opt = ImageioGetFormatOpt( "tiff" );
      if ( opt != NULL ) {
        opt->flags &= ~TIFFIO_SMP_UINT;
        opt->flags |= TIFFIO_SMP_INT;
      }
    }
  }

  param = "tiff_orientation";
  status = TomoparamReadScalarString( tomoparam, param, &string );
  if ( status != E_TOMOPARAM_UNDEF ) {
    if ( status ) {
      retstat = TomoparamReadError( sect, param, status );
    } else {
      uint16_t flags;
      if ( !strcasecmp( string, "bottomleft" ) ) {
        flags = 0;
      } else if ( !strcasecmp( string, "bottomright" ) ) {
        flags = TIFFIO_ORI_RIG;
      } else if ( !strcasecmp( string, "topleft" ) ) {
        flags = TIFFIO_ORI_TOP;
      } else if ( !strcasecmp( string, "topright" ) ) {
        flags = TIFFIO_ORI_TOP | TIFFIO_ORI_RIG;
      } else {
        retstat = TomoparamReadError( sect, param, E_TOMOPARAMREAD_VAL );
      }
      if ( !retstat ) {
        TiffioOptions *opt = ImageioGetFormatOpt( "tiff" );
        if ( opt != NULL ) {
          opt->flags &= ~( TIFFIO_ORI_TOP | TIFFIO_ORI_RIG );
          opt->flags |= flags;
        }
      }
      free( string );
    }
  }

  if ( ident != NULL ) {
    status = TomoparamPop( tomoparam, NULL );
    if ( pushexception( status ) ) return status;
  }

  if ( !retstat ) {

    *ioparam = imageio;

  }

  return retstat ? E_TOMOPARAMREAD_ERROR : E_NONE;

}


extern Status TomoparamImageioFinal
              (ImageioParam *ioparam)

{

  if ( ioparam != NULL ) {

    if ( ioparam->format != NULL ) free( (char *)ioparam->format );
    *ioparam = ImageioParamDefault;

  }

  return E_NONE;

}
