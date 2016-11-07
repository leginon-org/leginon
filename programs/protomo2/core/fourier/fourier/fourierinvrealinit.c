/*----------------------------------------------------------------------------*
*
*  fourierinvrealinit.c  -  fourier: Fourier transforms
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

extern Fourier *FourierInvRealInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt)

{
  Fourier *fou;

  fou = FourierInit( dim, len, opt, FourierBackward | FourierRealSeq );
  testcondition( fou == NULL );

  return fou;

}


extern Fourier *FourierInvRealEvenInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt)

{
  Fourier *fou;

  fou = FourierInit( dim, len, opt, FourierBackward | FourierRealSeq | FourierEven );
  testcondition( fou == NULL );

  return fou;

}


extern Fourier *FourierInvRealOddInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt)

{
  Fourier *fou;

  fou = FourierInit( dim, len, opt, FourierBackward | FourierRealSeq | FourierOdd );
  testcondition( fou == NULL );

  return fou;

}
