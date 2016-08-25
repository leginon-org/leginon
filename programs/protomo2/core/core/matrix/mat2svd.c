/*----------------------------------------------------------------------------*
*
*  mat2svd.c  -  2 x 2 matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "mat2.h"
#include "mathdefs.h"


/* functions */

/*
   Ref: J.C.Nash, Compact numerical methods for computers:
   linear algebra and function minimisation, Bristol, 1979
*/

extern Status Mat2Svd
              (Coord A[2][2],
               Coord U[2][2],
               Coord S[2],
               Coord V[2][2])
{
  Coord tol = 4*CoordEPS*CoordEPS;
  Coord p, q, r, u, v, c, s;

  U[0][0] = A[0][0]; U[0][1] = A[0][1];
  U[1][0] = A[1][0]; U[1][1] = A[1][1];
  V[0][0] = 1; V[0][1] = 0;
  V[1][0] = 0; V[1][1] = 1;
  while (True) {
    p = U[0][0] * U[0][1] + U[1][0] * U[1][1];
    q = U[0][0] * U[0][0] + U[1][0] * U[1][0];
    r = U[0][1] * U[0][1] + U[1][1] * U[1][1];
    if ( (q*r == 0) || ((p*p)/(q*r) < tol) ) break;
    /* change to algor.1: keep ordering of columns */
    q = q-r;
    v = sqrt( 4*p*p + q*q );
    if (q < 0) {
      s=sqrt( (v-q) / (2*v) );
      if (p < 0) s = -s;
      c = p / (v*s);
    } else {
      c = sqrt( (v+q) / (2*v) );
      s = p / (v*c);
    }
    u = U[0][0]; 
    U[0][0] = u*c + U[0][1]*s;
    U[0][1] = U[0][1]*c - u*s;
    u = U[1][0]; 
    U[1][0] = u*c + U[1][1]*s;
    U[1][1] = U[1][1]*c - u*s;
    u = V[0][0]; 
    V[0][0] = u*c + V[0][1]*s;
    V[0][1] = V[0][1]*c - u*s;
    u = V[1][0]; 
    V[1][0] = u*c + V[1][1]*s;
    V[1][1] = V[1][1]*c - u*s;
  }
  S[0] = sqrt( U[0][0] * U[0][0] + U[1][0] * U[1][0] );
  if (S[0] >= tol) {
    U[0][0] /= S[0]; U[1][0] /= S[0];
  }
  S[1] = sqrt( U[0][1] * U[0][1] + U[1][1] * U[1][1] );
  if (S[1] >= tol) {
    U[0][1] /= S[1]; U[1][1] /= S[1];
  }
  return E_NONE;

}
