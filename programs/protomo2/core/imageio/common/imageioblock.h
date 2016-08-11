/*----------------------------------------------------------------------------*
*
*  imageioblock.h  -  imageio: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imageioblock_h_
#define imageioblock_h_

#include "imageio.h"


/* prototypes */

extern Status ImageioBlockCheck
              (Imageio *imageio,
               Offset offset,
               Size length,
               Size *count);

extern Status ImageioRdBlock
              (Imageio *imageio,
               Status (*rd)( Imageio *, Offset, Size, void * ),
               Offset offset,
               Size length,
               Size count,
               void *addr);

extern Status ImageioWrBlock
              (Imageio *imageio,
               Status (*wr)( Imageio *, Offset, Size, const void * ),
               Offset offset,
               Size length,
               Size count,
               const void *addr);


#endif
