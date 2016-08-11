/*----------------------------------------------------------------------------*
*
*  matinv.h  -  matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

/* template */

{
  Coord d = 1;
  Coord tol = 3 * CoordEPS;

  if ( !n ) {
    return E_ARGVAL;
  }

  Coord C0[n], C[n][2*n]; Size I[n];

  const Coord *Ai = (const Coord *)A;
  Coord *Ci = (Coord *)C;
  for ( Size i = 0; i < n; i++ ) {
    C0[i] = fabs( Ai[0] );
    for ( Size j = 1; j < n; j++ ) {
      if ( fabs( Ai[j] ) > C0[i] ) C0[i] = fabs( Ai[j] );
    }
    if ( C0[i] == 0 ) return E_MATSING;
    for ( Size j = 0; j < n; j++ ) {
      *Ci++ = *Ai++ / C0[i];
    }
    for ( Size j = 0; j < n; j++ ) {
      *Ci++ = ( i == j ) ? 1 : 0;
    }
    I[i] = i;
  }

  for ( Size j0 = 0; j0 < n; j0++ ) {

    Size i0 = j0, ii0 = I[i0]; 
    Coord c0 = C[ii0][j0], c0a = fabs( c0 );

    for ( Size i = j0+1; i < n; i++ ) {
      Size ii = I[i];
      Coord c = C[ii][j0];
      Coord ca = fabs( c );
      if ( ca > c0a ) {
        i0 = i;
        ii0 = ii;
        c0 = c;
        c0a = ca;
      }
    }

    if ( c0a < tol ) return E_MATSING;

    if ( i0 != j0 ) {
      I[i0] = I[j0];
      I[j0] = ii0;
      d = -d;
    }
    d *= c0 * C0[ii0];

    for ( Size j = 0; j < 2*n; j++ ) {
      C[ii0][j] /= c0;
    }

    for ( Size i = 0; i < n; i++ ) {
      if ( i != ii0 ) {
        Coord c = C[i][j0];
        for ( Size j = 0; j < 2*n; j++ ) {
          C[i][j] -= c * C[ii0][j];
        }
      }
    }

  }

  if ( B != NULL ) {
    Coord *Bi = (Coord *)B;
    for ( Size i = 0; i < n; i++ ) {
      Ci = (Coord *)C; Ci += 2*n * I[i] + n;
      for ( Size j = 0; j < n; j++ ) {
        *Bi++ = *Ci++ / C0[j];
      }
    }
  }
  if ( det != NULL ) {
    *det = d;
  }

  return E_NONE;

}
