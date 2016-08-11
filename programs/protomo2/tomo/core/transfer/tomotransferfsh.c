/*----------------------------------------------------------------------------*
*
*  tomotransfer.c  -  tomography: transfer functions
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
#include "mathdefs.h"
#include "exception.h"


/* functions */

extern Coord TomotransferFsh
             (Coord A[3][3])

{
  Coord a02 = A[0][2];
  Coord a12 = A[1][2];
  Coord a22 = A[2][2];

  Coord a2 = Sqrt( a02 * a02 + a12 * a12 + a22 * a22 );

  return a2 / a22;

}
