/*----------------------------------------------------------------------------*
*
*  ccf.c  -  array: cross-correlation functions
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "ccf.h"
#include "exception.h"


/* functions */

extern Status CCF
              (Type type,
               Size count,
               const void *src0,
               const void *src1,
               void *dst,
               const CCMode mode)

{
  Status status;

  if ( argcheck( src0 == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src1 == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dst  == NULL ) ) return exception( E_ARGVAL );

  switch ( type ) {
    case TypeReal:  status = CCFReal ( count, src0, src1, dst, mode ); break;
    case TypeImag:  status = CCFImag ( count, src0, src1, dst, mode ); break;
    case TypeCmplx: status = CCFCmplx( count, src0, src1, dst, mode ); break;
    default: return exception( E_CCF_TYPE );
  }

  return status;

}


extern Status CCFReal
              (Size count,
               const void *src0,
               const void *src1,
               void *dst,
               const CCMode mode)

{

  if ( argcheck( src0 == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src1 == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dst  == NULL ) ) return exception( E_ARGVAL );

  switch ( mode ) {
    case CC_XCF: XCFReal( count, src0, src1, dst ); break;
    case CC_MCF: MCFReal( count, src0, src1, dst ); break;
    case CC_PCF: PCFReal( count, src0, src1, dst ); break;
    case CC_DBL: DBLReal( count, src0, src1, dst ); break;
    default: return exception( E_CCF_MODE );
  }

  return E_NONE;

}


extern Status CCFImag
              (Size count,
               const void *src0,
               const void *src1,
               void *dst,
               const CCMode mode)

{

  if ( argcheck( src0 == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src1 == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dst  == NULL ) ) return exception( E_ARGVAL );

  switch ( mode ) {
    case CC_XCF: XCFImag( count, src0, src1, dst ); break;
    case CC_MCF: MCFImag( count, src0, src1, dst ); break;
    case CC_PCF: PCFImag( count, src0, src1, dst ); break;
    case CC_DBL: DBLImag( count, src0, src1, dst ); break;
    default: return exception( E_CCF_MODE );
  }

  return E_NONE;

}


extern Status CCFCmplx
              (Size count,
               const void *src0,
               const void *src1,
               void *dst,
               const CCMode mode)

{

  if ( argcheck( src0 == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src1 == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dst  == NULL ) ) return exception( E_ARGVAL );

  switch ( mode ) {
    case CC_XCF: XCFCmplx( count, src0, src1, dst ); break;
    case CC_MCF: MCFCmplx( count, src0, src1, dst ); break;
    case CC_PCF: PCFCmplx( count, src0, src1, dst ); break;
    case CC_DBL: DBLCmplx( count, src0, src1, dst ); break;
    default: return exception( E_CCF_MODE );
  }

  return E_NONE;

}
