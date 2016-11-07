/*----------------------------------------------------------------------------*
*
*  pcfmod.c  -  array: phase-only cross-correlation function
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
#include "mathdefs.h"


/* functions */

extern Status PCFmodReal
              (Size count,
               Real *dst)

{

  while ( count-- ) {

    if ( *dst > 0 ) {

      *dst = 1;

    } else if ( *dst < 0 ) {

      *dst = -1;

    }

    dst++;

  }

  return E_NONE;

}


extern Status PCFmodCmplx
              (Size count,
               Cmplx *dst)

{

  while ( count-- ) {

    Real re = Re( *dst ), im = Im( *dst );
    Real dstabs = FnSqrt( re * re + im * im );

    if ( dstabs > 0 ) {

      Cset( *dst, re / dstabs, im / dstabs );

    } else {

      Cset( *dst, 0, 0 );

    }

    dst++;

  }

  return E_NONE;

}
