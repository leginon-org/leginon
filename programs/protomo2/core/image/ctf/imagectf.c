/*----------------------------------------------------------------------------*
*
*  imagectf.c  -  image: contrast transfer function
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagectf.h"
#include "exception.h"


/* functions */

extern Status ImageCTF
              (const Image *image,
               void *addr,
               const EMparam *empar,
               const ImageCTFParam *param)

{
  Status status;

  if ( argcheck( image == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( addr  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( empar == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( param == NULL ) ) return exception( E_ARGVAL );

  switch( image->type ) {
    case TypeReal:
    case TypeImag:  status = ImageCTFReal( image, addr, empar, param ); break;
    case TypeCmplx: status = ImageCTFReal( image, addr, empar, param ); break;
    default: status = exception( E_IMAGECTF_TYPE );
  }

  return status;

}
