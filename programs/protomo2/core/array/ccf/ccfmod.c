/*----------------------------------------------------------------------------*
*
*  ccfmod.c  -  array: cross-correlation functions
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

extern Status CCFmod
              (Type type,
               Size count,
               void *dst,
               const CCMode mode)

{
  Status status;

  if ( argcheck( dst  == NULL ) ) return exception( E_ARGVAL );

  switch ( type ) {
    case TypeReal:  status = CCFmodReal ( count, dst, mode ); break;
    case TypeCmplx: status = CCFmodCmplx( count, dst, mode ); break;
    default: return exception( E_CCF_TYPE );
  }

  return status;

}


extern Status CCFmodReal
              (Size count,
               void *dst,
               const CCMode mode)

{

  if ( argcheck( dst  == NULL ) ) return exception( E_ARGVAL );

  switch ( mode ) {
    case CC_DBL: break;
    case CC_PCF: PCFmodReal( count, dst ); break;
    case CC_MCF: MCFmodReal( count, dst ); break;
    case CC_XCF: break;
    default: return exception( E_CCF_MODE );
  }

  return E_NONE;

}


extern Status CCFmodCmplx
              (Size count,
               void *dst,
               const CCMode mode)

{

  if ( argcheck( dst  == NULL ) ) return exception( E_ARGVAL );

  switch ( mode ) {
    case CC_DBL: break;
    case CC_PCF: PCFmodCmplx( count, dst ); break;
    case CC_MCF: MCFmodCmplx( count, dst ); break;
    case CC_XCF: break;
    default: return exception( E_CCF_MODE );
  }

  return E_NONE;

}


extern Status CCFmodcalc
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
    case TypeReal:  status = CCFmodcalcReal ( count, src0, src1, dst, mode ); break;
    case TypeCmplx: status = CCFmodcalcCmplx( count, src0, src1, dst, mode ); break;
    default: return exception( E_CCF_TYPE );
  }

  return status;

}


extern Status CCFmodcalcReal
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
    case CC_DBL: DBLReal( count, src0, src1, dst ); break;
    case CC_PCF:
    case CC_MCF:
    case CC_XCF: XCFReal( count, src0, src1, dst ); break;
    default: return exception( E_CCF_MODE );
  }

  return E_NONE;

}


extern Status CCFmodcalcCmplx
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
    case CC_DBL: DBLCmplx( count, src0, src1, dst ); break;
    case CC_PCF:
    case CC_MCF:
    case CC_XCF: XCFCmplx( count, src0, src1, dst ); break;
    default: return exception( E_CCF_MODE );
  }

  return E_NONE;

}
