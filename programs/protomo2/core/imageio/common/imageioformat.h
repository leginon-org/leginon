/*----------------------------------------------------------------------------*
*
*  imageioformat.h  -  imageio: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imageioformat_h_
#define imageioformat_h_

#include "imageiocommon.h"


/* prototypes */

extern Status ImageioFormatRegister
              (const ImageioFormat *format);

extern const ImageioFormat *ImageioFormatNew
                            (const ImageioParam *param);

extern Status ImageioFormatOld
              (const ImageioParam *param,
               Imageio *imageio);


#endif
