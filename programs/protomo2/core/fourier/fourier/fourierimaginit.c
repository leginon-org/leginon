/*----------------------------------------------------------------------------*
*
*  fourierimaginit.c  -  fourier: Fourier transforms
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

extern Fourier *FourierImagInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt)

{
  Fourier *fou;

  fou = FourierInit( dim, len, opt, FourierForward | FourierImagSeq );
  testcondition( fou == NULL );

  return fou;

}


extern Fourier *FourierImagEvenInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt)

{
  Fourier *fou;

  fou = FourierInit( dim, len, opt, FourierForward | FourierImagSeq | FourierEven );
  testcondition( fou == NULL );

  return fou;

}


extern Fourier *FourierImagOddInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt)

{
  Fourier *fou;

  fou = FourierInit( dim, len, opt, FourierForward | FourierImagSeq | FourierOdd );
  testcondition( fou == NULL );

  return fou;

}
