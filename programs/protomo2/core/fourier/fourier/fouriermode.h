/*----------------------------------------------------------------------------*
*
*  fouriermode.h  -  fourier: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef fouriermode_h_
#define fouriermode_h_


/* types */

typedef enum {
  FourierAsym     = 0x00,
  FourierSym      = 0x01,
  FourierNeg      = 0x02,
  FourierConj     = 0x04,
  FourierEven     = FourierSym,
  FourierOdd      = FourierSym | FourierNeg,
  FourierHerm     = FourierSym | FourierConj,
  FourierAHerm    = FourierSym | FourierConj | FourierNeg,
  FourierSymMask  = FourierSym | FourierConj | FourierNeg,
  FourierCmplxSeq = 0x000,
  FourierRealSeq  = 0x010,
  FourierImagSeq  = 0x020,
  FourierSeqMask  = FourierCmplxSeq | FourierRealSeq | FourierImagSeq,
  FourierForward  = 0x0000,
  FourierBackward = 0x0100,
  FourierModeMask = FourierSeqMask | FourierForward | FourierBackward,
  FourierMulti    = 0x1000,
  FourierInvalid  = 0x8000
} FourierMode;


/* prototypes */

extern Fourier *FourierInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt,
                 FourierMode mode);


#endif
