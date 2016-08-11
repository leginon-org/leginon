/*----------------------------------------------------------------------------*
*
*  mat3euler.c  -  3 x 3 matrix operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "mat3.h"
#include "mathdefs.h"


/* functions */

extern Status Mat3Euler
              (Coord A[3][3],
               Coord eul[3])

{
  Coord x, y, c, s, t;
  Coord b00, b01, b12, b22;

  if ( A[2][2] == 1.0 ) {

    eul[0] = atan2( A[0][1], A[0][0] );
    eul[1] = 0;
    eul[2] = 0;

  } else if ( A[2][2] == -1.0 ) {

    eul[0] = atan2( A[0][1], A[0][0] );
    eul[1] = Pi;
    eul[2] = 0;

  } else {

    x = A[1][2];
    y = A[0][2];
    if ( y == 0 ) {
      c = ( x < 0 ) ? -1 : 1;
      s = 0;
    } else if ( x == 0 ) {
      c = 0;
      s = ( y < 0 ) ? -1 : 1;
    } else if ( fabs( y ) > fabs( x ) ) {
      t = x / y;
      s = 1 / sqrt( 1 + t*t ); if ( y < 0 ) s = -s;
      c = s * t;
    } else {
      t = y / x;
      c = 1 / sqrt( 1 + t*t ); if ( x < 0 ) c = -c;
      s = c * t;
    }

    /*
    G[0][0] = c; G[0][1] = -s; G[0][2] = 0;
    G[1][0] = s; G[1][1] =  c; G[1][2] = 0;
    G[2][0] = 0; G[2][1] =  0; G[2][2] = 1;
    Mat3Mul( G, A, B );
    */

    b00  =  c * A[0][0]  -  s * A[1][0];
    b01  =  c * A[0][1]  -  s * A[1][1];
    b12  =  s * A[0][2]  +  c * A[1][2];
    b22  =  A[2][2];

    eul[0] = atan2( b01, b00 );
    eul[1] = atan2( b12, b22 );
    eul[2] = atan2( s, c );

  }

  return E_NONE;

}
