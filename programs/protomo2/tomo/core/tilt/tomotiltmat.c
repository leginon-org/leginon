/*----------------------------------------------------------------------------*
*
*  tomotiltmat.c  -  tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomotilt.h"
#include "base.h"
#include "exception.h"
#include "mat2.h"
#include "mat3.h"
#include "mathdefs.h"


/* functions */

extern Status TomotiltMat
              (const Coord euler[3],
               const TomotiltAxis *axis,
               const TomotiltOrient *orient,
               const TomotiltGeom *geom,
               Coord A0[3][3],
               Coord A[3][3],
               Coord Am[3][3],
               Coord Af[2][2],
               Bool usecorr)

{
  Coord degtorad = Pi/180;
  Status status = E_NONE;

  if ( argcheck( euler  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( axis   == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( orient == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( geom   == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( A      == NULL ) ) return exception( E_ARGVAL );

  /* compute transformation without in plane rotation first */
  {
    Coord Q[3][3], R[3][3];
    Coord phi = axis->phi * degtorad;
    Coord elev = -axis->theta * degtorad; /* elevation: clockwise rotation */
    Coord theta = ( geom->theta + axis->offset ) * degtorad;
    Mat3RotZ( phi, Q );
    Mat3RotY( elev, R );
    Mat3Mul( R, Q, Q );
    Mat3RotX( theta, R );
    Mat3Mul( R, Q, R );
    Mat3Transp( Q, Q );
    Mat3Mul( Q, R, A );
    TomotiltMatOrient( orient->euler, R );
    Mat3Mul( R, A, A );
    TomotiltMatOrient( euler, R );
    Mat3Mul( R, A, A );
  }
  if ( A0 != NULL ) {
    Mat3Mul( A0, A, A );
  }
  if ( geom->scale > 0 ) {
    Coord scale = geom->scale;
    A[0][0] *= scale; A[0][1] *= scale; A[0][2] *= scale;
    A[1][0] *= scale; A[1][1] *= scale; A[1][2] *= scale;
    A[2][0] *= scale; A[2][1] *= scale; A[2][2] *= scale;
  }

  /* transformation to object basis */
  if ( Am != NULL ) {
    Am[0][0] = A[0][0]; Am[0][1] = A[0][1]; Am[0][2] = A[0][2];
    Am[1][0] = A[1][0]; Am[1][1] = A[1][1]; Am[1][2] = A[1][2];
    Am[2][0] = A[2][0]; Am[2][1] = A[2][1]; Am[2][2] = A[2][2];
  }

  /* Fourier space transformation to object basis for filter */
  if ( Af != NULL ) {
    Af[0][0] = A[0][0]; Af[0][1] = A[1][0]; /* assign transp */
    Af[1][0] = A[0][1]; Af[1][1] = A[1][1];
    status = Mat2Inv( Af, Af, NULL );
  }

  /* in plane rotation */
  {
    Coord R[3][3];
    Mat3RotZ( geom->alpha * degtorad, R );
    Mat3Mul( A, R, A );
  }

  /* 2D correction */
  if ( ( geom->corr[0] > 0 ) && usecorr ) {
    Coord B[2][2], S[2][2], C[3][3];
    Coord beta = geom->beta * degtorad;
    Mat2Rot( &beta, B );
    S[0][0] = B[0][0] * geom->corr[0];
    S[0][1] = B[0][1] * geom->corr[0];
    S[1][0] = B[1][0] * geom->corr[1];
    S[1][1] = B[1][1] * geom->corr[1];
    Mat2TranspMul( B, S, S );
    C[0][0] = S[0][0]; C[0][1] = S[0][1]; C[0][2] = 0;
    C[1][0] = S[1][0]; C[1][1] = S[1][1]; C[1][2] = 0;
    C[2][0] = 0;       C[2][1] = 0;       C[2][2] = 1;
    /* total transformation */
    Mat3Mul( A, C, A );
  }

  return status;

}
