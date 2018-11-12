/*----------------------------------------------------------------------------*
*
*  imagemaskcommon.h  -  image: mask operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imagemaskcommon_h_
#define imagemaskcommon_h_

#include "imagemask.h"


/* prototypes */

extern Status ImageMaskSetParam
              (const Image *image,
               const MaskParam *src,
               MaskParam *dst,
               Coord *b,
               Size bsize);


#endif
