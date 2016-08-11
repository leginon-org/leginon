/*----------------------------------------------------------------------------*
*
*  maskparam.h  -  array: mask operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef maskparam_h_
#define maskparam_h_

#include "mask.h"


/* prototypes */

extern MaskParam *MaskParamNew
                  (MaskParam **param);

extern MaskParam *MaskParamStd
                  (Coord *A,
                   Coord *b,
                   Coord *width,
                   Coord *sigma,
                   Coord val,
                   Size rectdef,
                   Size ellipsdef,
                   Size sigmadef,
                   MaskFlags flags,
                   MaskParam *param);

extern MaskParam *MaskParamWedge
                  (Coord *A,
                   Coord *b,
                   Coord *wedge,
                   Coord val,
                   Size wedgedef,
                   MaskFlags flags,
                   MaskParam *param);


#endif
