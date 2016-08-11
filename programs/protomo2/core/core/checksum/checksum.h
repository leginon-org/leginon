/*----------------------------------------------------------------------------*
*
*  checksum.h  -  core: checksums
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef checksum_h_
#define checksum_h_

#include "defs.h"

#define ChecksumName   "checksum"
#define ChecksumVers   COREVERS"."COREBUILD
#define ChecksumCopy   CORECOPY


/* exception codes */

enum {
  E_CHECKSUM=ChecksumModuleCode,
  E_CHECKSUM_TYPE,
  E_CHECKSUM_MAXCODE
};


/* types */

typedef enum {
  ChecksumTypeUndef,
  ChecksumTypeXor,
  ChecksumTypeMax
} ChecksumType;


/* prototypes */

extern Status Checksum
              (ChecksumType type,
               Size count,
               const void *addr,
               Size sumlen,
               uint8_t *sumaddr);

extern Status ChecksumCalc
              (ChecksumType type,
               Size count,
               const void *addr,
               Size sumlen,
               uint8_t *sumaddr);

extern void ChecksumXor
            (Size count,
             const void *addr,
             Size sumlen,
             uint8_t *sumaddr);

extern void ChecksumXorCalc
            (Size count,
             const void *addr,
             Size sumlen,
             uint8_t *sumaddr);


#endif
