/*----------------------------------------------------------------------------*
*
*  fourierrealinit.c  -  fourier: Fourier transforms
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

extern Fourier *FourierRealInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt)

{
  Fourier *fou;

  fou = FourierInit( dim, len, opt, FourierForward | FourierRealSeq );
  testcondition( fou == NULL );

  return fou;

}


extern Fourier *FourierRealEvenInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt)

{
  Fourier *fou;

  fou = FourierInit( dim, len, opt, FourierForward | FourierRealSeq | FourierEven );
  testcondition( fou == NULL );

  return fou;

}


extern Fourier *FourierRealOddInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt)

{
  Fourier *fou;

  fou = FourierInit( dim, len, opt, FourierForward | FourierRealSeq | FourierOdd );
  testcondition( fou == NULL );

  return fou;

}
