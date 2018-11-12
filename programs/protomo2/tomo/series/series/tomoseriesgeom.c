/*----------------------------------------------------------------------------*
*
*  tomoseriesgeom.c  -  series: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoseries.h"
#include "transf2.h"
#include "mat2.h"
#include "mat3.h"
#include "exception.h"


/* functions */

extern void TomoseriesResampleGeom
            (const TomodataDscr *dscr,
             Coord sampling,
             Coord Ap[3][2],
             Coord Bp[3][2])

{

  Mat2Mul( Ap, (void *)dscr->B1, Bp );

  Bp[0][0] *= sampling; Bp[0][1] *= sampling;
  Bp[1][0] *= sampling; Bp[1][1] *= sampling;

  Transf2TranspMulVec( (void *)dscr->B1, Ap[2], Bp[2] );

  Bp[2][0] -= dscr->img.low[0]; Bp[2][1] -= dscr->img.low[1];

}


extern void TomoseriesResampleGeom3
            (const TomodataDscr *dscr,
             Coord sampling,
             Coord A[3][3],
             Coord a[2],
             Coord B[3][3],
             Coord b[2])

{

  B[0][0] = dscr->B1[0][0] * sampling; B[0][1] = dscr->B1[0][1] * sampling; B[0][2] = 0; 
  B[1][0] = dscr->B1[1][0] * sampling; B[1][1] = dscr->B1[1][1] * sampling; B[1][2] = 0; 
  B[2][0] = 0;                         B[2][1] = 0;                         B[2][2] = sampling; 

  Mat3Mul( A, B, B );

  Transf2TranspMulVec( (void *)dscr->B1, a, b );

  b[0] -= dscr->img.low[0]; b[1] -= dscr->img.low[1];

}


extern void TomoseriesResampleTransform
            (const Tomoseries *series,
             const Size index,
             Coord Ap[3][2],
             Coord Bp[3][2])

{

  TomodataDscr *dscr = series->data->dscr + index;

  TomoseriesResampleGeom( dscr, series->sampling, Ap, Bp );

}
