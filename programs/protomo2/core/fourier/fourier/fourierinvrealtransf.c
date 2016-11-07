/*----------------------------------------------------------------------------*
*
*  fourierinvrealtransf.c  -  fourier: Fourier transforms
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

extern Status FourierInvRealTransf
              (const Fourier *fou,
               const Cmplx *src,
               Real *dst,
               Size count)

{
  Status status;

  if ( argcheck( fou == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dst == NULL ) ) return exception( E_ARGVAL );

  status = FourierCheck( fou, FourierBackward | FourierRealSeq );
  if ( exception( status ) ) return status;

  status = FourierTransf( fou, src, dst, count );
  logexception( status );

  return status;

}


extern Status FourierInvRealEvenTransf
              (const Fourier *fou,
               const Real *src,
               Real *dst,
               Size count)

{
  Status status;

  if ( argcheck( fou == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dst == NULL ) ) return exception( E_ARGVAL );

  status = FourierCheck( fou, FourierBackward | FourierRealSeq | FourierEven );
  if ( exception( status ) ) return status;

  status = FourierTransf( fou, src, dst, count );
  logexception( status );

  return status;

}


extern Status FourierInvRealOddTransf
              (const Fourier *fou,
               const Imag *src,
               Real *dst,
               Size count)

{
  Status status;

  if ( argcheck( fou == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dst == NULL ) ) return exception( E_ARGVAL );

  status = FourierCheck( fou, FourierBackward | FourierRealSeq | FourierOdd );
  if ( exception( status ) ) return status;

  status = FourierTransf( fou, src, dst, count );
  logexception( status );

  return status;

}
