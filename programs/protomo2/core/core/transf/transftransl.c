/*----------------------------------------------------------------------------*
*
*  transftransl.c  -  core: linear transformations: unit matrix
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "transfn.h"


/* functions */

extern Status TransfTransl
              (Size n,
               const Coord *A,
               Coord *B)

{

  B += n * n;
  for ( Size j = 0; j < n; j++ ) {
    *B++ = *A++;
  }

  return E_NONE;

}
