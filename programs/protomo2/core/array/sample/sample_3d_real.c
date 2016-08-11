/*----------------------------------------------------------------------------*
*
*  sample_3d_real.c  -  array: sampling
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

extern Status Sample3dReal
              (Type type,
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

  switch ( type ) {
    case TypeUint8:  status = exception( Sample3dUint8Real ( srclen, srcaddr, smp, b, dstlen, dstaddr, c, param ) ); break;
    case TypeUint16: status = exception( Sample3dUint16Real( srclen, srcaddr, smp, b, dstlen, dstaddr, c, param ) ); break;
    case TypeUint32: status = exception( Sample3dUint32Real( srclen, srcaddr, smp, b, dstlen, dstaddr, c, param ) ); break;
    case TypeInt8:   status = exception( Sample3dInt8Real  ( srclen, srcaddr, smp, b, dstlen, dstaddr, c, param ) ); break;
    case TypeInt16:  status = exception( Sample3dInt16Real ( srclen, srcaddr, smp, b, dstlen, dstaddr, c, param ) ); break;
    case TypeInt32:  status = exception( Sample3dInt32Real ( srclen, srcaddr, smp, b, dstlen, dstaddr, c, param ) ); break;
    case TypeReal:   status = exception( Sample3dRealReal  ( srclen, srcaddr, smp, b, dstlen, dstaddr, c, param ) ); break;
    default:         status = exception( E_SAMPLE_DATATYPE );
  }

  return status;

}
