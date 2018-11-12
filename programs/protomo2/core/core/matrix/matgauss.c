/*----------------------------------------------------------------------------*
*
*  matgauss.c  -  matrix operations: linear equations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "matmn.h"
#include "exception.h"
#include "mathdefs.h"
#include <string.h>


/* functions */

extern Status MatGauss
              (Size m,
               Size n,
               Size l,
               Coord *A,
               Coord *B,
               Size *r)

{
  Size p = n + l;
  Size n0 = ( m < n ) ? m : n;
  Coord *Ai, *Bi, *Ci;
  Size rnk = 0;
  Coord tol = 3 * CoordEPS;

  if ( !m || !n || !l ) {
    return E_ARGVAL;
  }

  Coord C0[m], C[m*p]; Size I[m];

  Ai = A; Bi = B; Ci = C;
  for ( Size i = 0; i < m; i++ ) {
    C0[i] = fabs( Ai[0] );
    for ( Size j = 1; j < n; j++ ) {
      if ( fabs( Ai[j] ) > C0[i] ) C0[i] = fabs( Ai[j] );
    }
    if ( C0[i] == 0 ) return E_MATSING;
    for ( Size j = 0; j < n; j++ ) {
      *Ci++ = *Ai++ / C0[i];
    }
    for ( Size j = n; j < p; j++ ) {
      *Ci++ = *Bi++ / C0[i];
    }
    I[i] = i;
  }

  for ( Size j0 = 0; j0 < n0; j0++ ) {

    Size i0 = j0, ii0 = I[i0];
    Coord *Ci0 = C + ii0 * p;
    Coord c0 = Ci0[j0], c0a = fabs( c0 );

    for ( Size i = j0+1; i < n; i++ ) {
      Size ii = I[i];
      Coord c = C[ ii * p + j0 ];
      Coord ca = fabs( c );
      if ( ca > c0a ) {
        i0 = i;
        ii0 = ii;
        c0 = c;
        c0a = ca;
      }
    }

    if ( c0a < tol ) continue;

    if ( i0 != j0 ) {
      I[i0] = I[j0];
      I[j0] = ii0;
    }

    Ci0 = C + ii0 * p;
    for ( Size j = 0; j < p; j++ ) {
      Ci0[j] /= c0;
    }

    Ci = C;
    for ( Size i = 0; i < m; i++ ) {
      if ( i != ii0 ) {
        Coord c0 = Ci[j0];
        for ( Size j = 0; j < p; j++ ) {
          Ci[j] -= c0 * Ci0[j];
        }
      }
      Ci += p;
    }

    rnk++;

  }

  Ai = A; Bi = B;
  for ( Size i = 0; i < m; i++ ) {
    Ci = C + I[i] * p;
    for ( Size j = 0; j < n; j++ ) {
      *Ai++ = *Ci++;
    }
    for ( Size j = n; j < p; j++ ) {
      *Bi++ = *Ci++;
    }
  }

  if ( r != NULL ) {
    *r = rnk;
  }

  return E_NONE;

}
