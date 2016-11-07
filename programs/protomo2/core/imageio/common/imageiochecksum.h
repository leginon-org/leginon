/*----------------------------------------------------------------------------*
*
*  imageiochecksum.h  -  imageio: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imageiochecksum_h_
#define imageiochecksum_h_

#include "imageio.h"
#include "checksum.h"


/* prototypes */

extern Status ImageioChecksum
              (const Imageio *imageio,
               ChecksumType type,
               Size buflen,
               uint8_t *buf);


#endif
