/*----------------------------------------------------------------------------*
*
*  imageio.c  -  imageio: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imageio.h"


/* variables */

ImageioParam ImageioParamDefault = { NULL, NULL, 0, ImageioCapRdWr | ImageioCapMmap | ImageioCapLoad | ImageioCapAuto };
