/*----------------------------------------------------------------------------*
*
*  fourierinvimag.c  -  fourier: Fourier transforms
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

extern Status FourierInvImag
              (Size dim,
               const Size *len,
               const Cmplx *src,
               Imag *dst,
               Size count,
               FourierOpt opt)

{
  Fourier *fou;
  Status status, stat;

  fou = FourierInit( dim, len, opt, FourierBackward | FourierImagSeq | FourierMulti );
  status = testcondition( fou == NULL );
  if ( popexception( status ) ) return status;

  status = FourierTransf( fou, src, dst, count );
  logexception( status );

  stat = FourierFinal( fou );
  logexception( stat );
  if ( !status ) status = stat;

  return status;

}


extern Status FourierInvImagEven
              (Size dim,
               const Size *len,
               const Imag *src,
               Imag *dst,
               Size count,
               FourierOpt opt)

{
  Fourier *fou;
  Status status, stat;

  fou = FourierInit( dim, len, opt, FourierBackward | FourierImagSeq | FourierEven | FourierMulti );
  status = testcondition( fou == NULL );
  if ( popexception( status ) ) return status;

  status = FourierTransf( fou, src, dst, count );
  logexception( status );

  stat = FourierFinal( fou );
  logexception( stat );
  if ( !status ) status = stat;

  return status;

}


extern Status FourierInvImagOdd
              (Size dim,
               const Size *len,
               const Real *src,
               Imag *dst,
               Size count,
               FourierOpt opt)

{
  Fourier *fou;
  Status status, stat;

  fou = FourierInit( dim, len, opt, FourierBackward | FourierImagSeq | FourierOdd | FourierMulti );
  status = testcondition( fou == NULL );
  if ( popexception( status ) ) return status;

  status = FourierTransf( fou, src, dst, count );
  logexception( status );

  stat = FourierFinal( fou );
  logexception( stat );
  if ( !status ) status = stat;

  return status;

}
