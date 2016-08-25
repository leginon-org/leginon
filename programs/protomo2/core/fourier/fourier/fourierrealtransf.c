/*----------------------------------------------------------------------------*
*
*  fourierrealtransf.c  -  fourier: Fourier transforms
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "fouriercommon.h"
#include "exception.h"


/* functions */

extern Status FourierRealTransf
              (const Fourier *fou,
               const Real *src,
               Cmplx *dst,
               Size count)

{
  Status status;

  if ( argcheck( fou == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dst == NULL ) ) return exception( E_ARGVAL );

  status = FourierCheck( fou, FourierForward | FourierRealSeq );
  if ( exception( status ) ) return status;

  status = FourierTransf( fou, src, dst, count );
  logexception( status );

  return status;

}


extern Status FourierRealEvenTransf
              (const Fourier *fou,
               const Real *src,
               Real *dst,
               Size count)

{
  Status status;

  if ( argcheck( fou == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dst == NULL ) ) return exception( E_ARGVAL );

  status = FourierCheck( fou, FourierForward | FourierRealSeq | FourierEven );
  if ( exception( status ) ) return status;

  status = FourierTransf( fou, src, dst, count );
  logexception( status );

  return status;

}


extern Status FourierRealOddTransf
              (const Fourier *fou,
               const Real *src,
               Imag *dst,
               Size count)

{
  Status status;

  if ( argcheck( fou == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dst == NULL ) ) return exception( E_ARGVAL );

  status = FourierCheck( fou, FourierForward | FourierRealSeq | FourierOdd  );
  if ( exception( status ) ) return status;

  status = FourierTransf( fou, src, dst, count );
  logexception( status );

  return status;

}
