/*----------------------------------------------------------------------------*
*
*  imageiodefault.h  -  imageio: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imageiodefault_h_
#define imageiodefault_h_

#include "imageiocommon.h"


/* prototypes */

extern Status ImageioRd
              (Imageio *imageio,
               Offset offset,
               Size length,
               void *addr);

extern Status ImageioRdStd
              (Imageio *imageio,
               Offset offset,
               Size length,
               void *addr);

extern Status ImageioRdAmap
              (Imageio *imageio,
               Offset offset,
               Size length,
               void *addr);

extern Status ImageioWr
              (Imageio *imageio,
               Offset offset,
               Size length,
               const void *addr);

extern Status ImageioWrStd
              (Imageio *imageio,
               Offset offset,
               Size length,
               const void *addr);

extern Status ImageioWrAmap
              (Imageio *imageio,
               Offset offset,
               Size length,
               const void *addr);

extern Status ImageioMmapAdr
              (Imageio *imageio,
               Offset offset,
               Size length,
               void **addr);

extern Status ImageioSiz
              (Imageio *imageio,
               Offset size,
               Size length);

extern Status ImageioFls
              (Imageio *imageio);

extern Status ImageioFin
              (Imageio *imageio);


#endif
