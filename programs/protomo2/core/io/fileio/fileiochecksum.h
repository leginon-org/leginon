/*----------------------------------------------------------------------------*
*
*  fileiochecksum.h  -  io: file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef fileiochecksum_h_
#define fileiochecksum_h_

#include "fileio.h"
#include "checksum.h"


/* prototypes */

extern Status FileioChecksum
              (const Fileio *fileio,
               ChecksumType type,
               Size buflen,
               uint8_t *buf);



#endif
