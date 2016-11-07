/*----------------------------------------------------------------------------*
*
*  mcfmod.c  -  array: mutual correlation function
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

extern Status MCFmodReal
              (Size count,
               Real *dst)

{

  while ( count-- ) {

    Real re = *dst;
    Real dstabs = FnSqrt( FnFabs( re ) );

    if ( dstabs > 0 ) {

      *dst /= dstabs;

    } else {

      *dst = 0;

    }

    dst++;

  }

  return E_NONE;

}


extern Status MCFmodCmplx
              (Size count,
               Cmplx *dst)

{

  while ( count-- ) {

    Real re = Re( *dst ), im = Im( *dst );
    Real dstabs = FnSqrt( FnSqrt( re * re + im * im ) );

    if ( dstabs > 0 ) {

      Cset( *dst, re / dstabs, im / dstabs );

    } else {

      Cset( *dst, 0, 0 );

    }

    dst++;

  }

  return E_NONE;

}
