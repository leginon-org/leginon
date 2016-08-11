/*----------------------------------------------------------------------------*
*
*  sample_real.c  -  array: sampling
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "sample.h"
#include "exception.h"


/* functions */

extern Status SampleReal
              (Size dim,
               Type type,
               const Size *srclen,
               const void *srcaddr,
               const Size *smp,
               const Size *b,
               const Size *dstlen,
               void *dstaddr,
               const Size *c,
               const SampleParam *param)

{
  Status status;

  if ( argcheck( srclen == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( smp    == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstlen == NULL ) ) return exception( E_ARGVAL );

  switch ( dim ) {
    case 2:  status = exception( Sample2dReal( type, srclen, srcaddr, smp, b, dstlen, dstaddr, c, param ) ); break;
    case 3:  status = exception( Sample3dReal( type, srclen, srcaddr, smp, b, dstlen, dstaddr, c, param ) ); break;
    default: status = exception( E_SAMPLE_DIM );
  }

  return status;

}
