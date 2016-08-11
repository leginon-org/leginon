/*----------------------------------------------------------------------------*
*
*  maskcommon.c  -  array: mask operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "maskcommon.h"


/* functions */

extern void MaskSetupParam
            (Size dim,
             const Size *len,
             const Coord *b,
             const Coord *w,
             Coord *c,
             Coord *p,
             MaskFlags flags)

{

  if ( b == NULL ) {

    c[0] = ( flags & MaskModeSym ) ? 0 : len[0] / 2;
    for ( Size d = 1; d < dim; d++ ) {
      c[d] = len[d] / 2;
    }

  } else {

    for ( Size d = 0; d < dim; d++ ) {
      c[d] = b[d];
    }

  }

  if ( w == NULL ) {

    for ( Size d = 0; d < dim; d++ ) {
      p[d] = 1;
    }

  } else if ( flags & MaskModeFract ) {

    if ( w[0] > 0 ) {
      if ( ( flags & MaskModeSym ) && ( len[0] > 1 ) ) {
        p[0] = ( flags & MaskModeNodd ) ? ( 2 * len[0] - 1 ) : ( 2 * ( len[0] - 1 ) );
      } else {
        p[0] = len[0];
      }
      p[0] = 2.0 / ( w[0] * p[0] );
    } else {
      p[0] = 0;
    }

    for ( Size d = 1; d < dim; d++ ) {
      p[d] = ( w[d] > 0 ) ? ( 2.0 / ( w[d] * len[d] ) ) : 0;
    }

  } else {

    for ( Size d = 0; d < dim; d++ ) {
      p[d] = ( w[d] > 0 ) ? ( 2.0 / w[d] ) : 0;
    }

  }

}


extern void MaskSetupParamApod
            (Size dim,
             const Size *len,
             const Coord *b,
             const Coord *w,
             const Coord *s,
             Coord *c,
             Coord *p,
             Coord *t,
             MaskFlags flags)

{

  if ( b == NULL ) {

    c[0] = ( flags & MaskModeSym ) ? 0 : len[0] / 2;
    for ( Size d = 1; d < dim; d++ ) {
      c[d] = len[d] / 2;
    }

  } else {

    for ( Size d = 0; d < dim; d++ ) {
      c[d] = b[d];
    }

  }

  if ( w == NULL ) {

    for ( Size d = 0; d < dim; d++ ) {
      p[d] = 1;
      t[d] = 0;
    }

  } else if ( flags & MaskModeFract ) {

    if ( w[0] > 0 ) {
      if ( ( flags & MaskModeSym ) && ( len[0] > 1 ) ) {
        p[0] = ( flags & MaskModeNodd ) ? ( 2 * len[0] - 1 ) : ( 2 * ( len[0] - 1 ) );
      } else {
        p[0] = len[0];
      }
      p[0] = 2.0 / ( w[0] * p[0] );
      t[0] = ( s[0] > 0 ) ? ( 2.0 * s[0] / w[0] ) : 0;
    } else {
      p[0] = 0;
      t[0] = 0;
    }

    for ( Size d = 1; d < dim; d++ ) {
      if ( w[d] > 0 ) {
        p[d] = 2.0 / ( w[d] * len[d] );
        t[d] = ( s[d] > 0 ) ? ( 2.0 * s[d] / w[d] ) : 0;
      } else {
        p[d] = 0;
        t[d] = 0;
      }
    }

  } else {

    for ( Size d = 0; d < dim; d++ ) {
      if ( w[d] > 0 ) {
        p[d] = 2.0 / w[d];
        t[d] = ( s[d] > 0 ) ? ( 2.0 * s[d] / w[d] ) : 0;
      } else {
        p[d] = 0;
        t[d] = 0;
      }
    }

  }

}


/* A is basis transformation of principal axes of mask to image */
/* B = diag(c)*AT;  AT is the coo transformation from image to mask */
/* p = principal axes */

extern void MaskSetupMat
            (Size dim,
             const Coord *A,
             const Coord *p,
             Coord *B)

{
  Coord *Bij = B;

  for ( Size i = 0; i < dim; i++ ) {

    const Coord *Aij = A + i;
    for ( Size j = 0; j < dim; j++ ) {
      *Bij++ = p[i] * *Aij;
      Aij += dim;
    }

  }

}
