/*----------------------------------------------------------------------------*
*
*  tomotransfercalc.c  -  tomography: transfer functions
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomotransfer.h"
#include "mat3.h"
#include <string.h>


/* functions */

static void TomotransferAddSinc
            (const Size len[2],
             const Index low[2],
             Real *H,
             Coord A[3][3],
             const TomotransferParam *param)

{
  Coord f = param->bfsh;
  Coord b = f * param->body;
  Coord a = Pi * b;
  Coord w = b * param->bwid;

  if ( w > 0 ) {

    /* w = d*(apod.width)                          */
    /* psf h(x): rect(x/d) conv exp(-pi*x*x/(w*w)  */
    /* tf  H(s): w*sinc(d*s)*exp(-pi*w*w*s*s)      */
    for ( Size iy = 0; iy < len[1]; iy++ ) {
      Coord y = iy; y += low[1];
      Coord ry = A[2][1] * y;
      for ( Size ix = 0; ix < len[0]; ix++ ) {
        Coord x = ix; x += low[0];
        Coord rx = A[2][0] * x;
        Coord r = rx + ry;
        Coord arg = a * r;
        Coord sig = r * w;
        Coord e = f * Exp( -Pi * sig * sig );
        if ( arg == 0 ) {
          *H++ += e;
        } else {
          *H++ += e * Sin( arg ) / arg;
        }
      } /* end for x */
    } /* end for y */

  } else { /* if w */

    /* psf h(x): rect(x/d)                             */
    /* tf  H(s): d*sinc(d*s) = d*sin(pi*d*s)/(pi*d*s)  */
    for ( Size iy = 0; iy < len[1]; iy++ ) {
      Coord y = iy; y += low[1];
      Coord ry = A[2][1] * y;
      for ( Size ix = 0; ix < len[0]; ix++ ) {
        Coord x = ix; x += low[0];
        Coord rx = A[2][0] * x;
        Coord r = rx + ry;
        Coord arg = a * r;
        if ( arg == 0 ) {
          *H++ += f;
        } else {
          *H++ += f * Sin( arg ) / arg;
        }
      } /* end for x */
    } /* end for y */

  } /* end if w */

}


extern void TomotransferAdd
            (const Size len[2],
             const Index low[2],
             Coord Ai[3][3],
             Coord A1j[3][3],
             Real *Hi,
             const TomotransferParam *param)

{
  Coord AjAi[3][3];

  /* reciprocal space transformation: I* -> O*  */
  /* basis: A-1T; coordinates: A                */

  /* reciprocal space transformation: O* -> J*  */
  /* basis: AT; coordinates: A-1                */

  Mat3Mul( A1j, Ai, AjAi );
  TomotransferAddSinc( len, low, Hi, AjAi, param );

}


extern void TomotransferCalc
            (const Size len[2],
             const Index low[2],
             Tomotransfer *trans,
             Size count,
             Coord Ai[3][3],
             Real *Hi,
             const TomotransferParam *param)

{

  /* reciprocal space transformation: I* -> O*  */
  /* basis: A-1T; coordinates: A                */

  memset( Hi, 0, len[1] * len[0] * sizeof(*Hi) );

  for ( Size j = 0; j < count; j++ ) {

    if ( trans[j].A1[0][0] != CoordMax ) {

      TomotransferAdd( len, low, Ai, trans[j].A1, Hi, param );

    }

  }

}
