/*----------------------------------------------------------------------------*
*
*  fourierimag.c  -  fourier: Fourier transforms
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

extern Status FourierImag
              (Size dim,
               const Size *len,
               const Imag *src,
               Cmplx *dst,
               Size count,
               FourierOpt opt)

{
  Fourier *fou;
  Status status, stat;

  fou = FourierInit( dim, len, opt, FourierForward | FourierImagSeq | FourierMulti );
  status = testcondition( fou == NULL );
  if ( popexception( status ) ) return status;

  status = FourierTransf( fou, src, dst, count );
  logexception( status );

  stat = FourierFinal( fou );
  logexception( stat );
  if ( !status ) status = stat;

  return status;

}


extern Status FourierImagEven
              (Size dim,
               const Size *len,
               const Imag *src,
               Imag *dst,
               Size count,
               FourierOpt opt)

{
  Fourier *fou;
  Status status, stat;

  fou = FourierInit( dim, len, opt, FourierForward | FourierImagSeq | FourierEven | FourierMulti );
  status = testcondition( fou == NULL );
  if ( popexception( status ) ) return status;

  status = FourierTransf( fou, src, dst, count );
  logexception( status );

  stat = FourierFinal( fou );
  logexception( stat );
  if ( !status ) status = stat;

  return status;

}


extern Status FourierImagOdd
              (Size dim,
               const Size *len,
               const Imag *src,
               Real *dst,
               Size count,
               FourierOpt opt)

{
  Fourier *fou;
  Status status, stat;

  fou = FourierInit( dim, len, opt, FourierForward | FourierImagSeq | FourierOdd | FourierMulti );
  status = testcondition( fou == NULL );
  if ( popexception( status ) ) return status;

  status = FourierTransf( fou, src, dst, count );
  logexception( status );

  stat = FourierFinal( fou );
  logexception( stat );
  if ( !status ) status = stat;

  return status;

}
