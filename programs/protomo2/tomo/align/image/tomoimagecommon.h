/*----------------------------------------------------------------------------*
*
*  tomoimagecommon.h  -  align: image geometry
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoimagecommon_h_
#define tomoimagecommon_h_

#include "tomoimage.h"


/* prototypes */

extern Status TomoimageSortSeparate
              (const Tomotilt *tilt,
               Tomoimage *image);

extern Status TomoimageSortSimultaneous
              (const Tomotilt *tilt,
               Tomoimage *image,
               Coord startangle);


#endif
