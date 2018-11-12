/*----------------------------------------------------------------------------*
*
*  matsvd.c  -  matrix operations: singular value decomposition
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
#include "mathdefs.h"
#include <string.h>


/* functions */

/*
   Ref: J.C.Nash, Compact numerical methods for computers:
   linear algebra and function minimisation, Bristol, 1979
*/

extern Status MatSvd
              (Size m,
               Size n,
               const Coord *A,
               Coord *U,
               Coord *S,
               Coord *V)
{
  Coord p, q, r, u, v, c, s;
  Size i, j, k, J, K, count;
  Coord tol;

  tol = CoordEPS; tol *= n; tol *= tol;
  /* U is m by n */
  memcpy( U, A, m*n*sizeof(Coord) );
  /* V is n by n */
  for ( J = 0; J < n*n; J++) {
    V[J] = 0;
  }
  for ( J = 0; J < n*n; J += n+1 ) {
    V[J] = 1;
  }
  do {
    count = n*(n-1)/2;
    for ( j = 0; j < n-1; j++ ) {
      for ( k = j+1; k < n; k++ ) {
        p = q = r = 0;
        for ( i = 0, J = j, K = k; i < m; i++, J += n, K += n ) {
          p += U[J] * U[K];
          q += U[J] * U[J];
          r += U[K] * U[K];
        }
        if ( q < r ) {
          /* interchange columns here directly to save some multiplications */
          for ( i = 0, J = j, K = k; i < m; i++, J += n, K += n ) {
            u = U[J]; U[J] = U[K]; U[K] = -u;
          }
          for (i=0,J=j,K=k; i < n; i++,J+=n,K+=n) {
            u = V[J]; V[J] = V[K]; V[K] = -u;
          }
        } else if ( ( q*r == 0 ) || ( ( p*p ) / ( q*r ) < tol ) ) {
          count--;
        } else {
          q -= r;
          v = sqrt( 4*p*p + q*q );
          c = sqrt( (v+q) / (2*v) );
          s = p / (v*c);
          for ( i = 0, J = j, K = k; i < m; i++, J += n, K += n ) {
            u = U[J];
            U[J] = u*c + U[K]*s;
            U[K] = U[K]*c - u*s;
          }
          for ( i = 0, J = j, K = k; i < n; i++, J += n, K += n ) {
            u = V[J];
            V[J] = u*c + V[K]*s;
            V[K] = V[K]*c - u*s;
          }
        } 
      } 
    } 
  } while (count > 0);
  for ( j = 0; j < n; j++ ) {
    u = 0;
    for ( i = 0, J = j; i < m; i++, J += n ) {
      u += U[J]*U[J];
    }
    S[j] = sqrt(u);
    if ( S[j] >= tol ) {
      for ( i = 0, J = j; i < m; i++, J += n ) {
        U[J] /= S[j];
      }
    }
  }
  return E_NONE;

}
