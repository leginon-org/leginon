/*----------------------------------------------------------------------------*
*
*  stringformat.h  -  core: character string operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef stringformat_h_
#define stringformat_h_

#include "defs.h"

#define StringFormatName   "stringformat"
#define StringFormatVers   COREVERS"."COREBUILD
#define StringFormatCopy   CORECOPY


/* exception codes */

enum {
  E_STRINGFORMAT = StringFormatModuleCode,
  E_STRINGFORMAT_MAXCODE
};


/* prototypes */

extern char *StringFormatString
             (Size srclen,
              const char *src,
              Size *dstlen,
              char *dst);

extern char *StringFormatUint64
             (uint64_t src,
              uint64_t base,
              Size *dstlen,
              char *dst);

extern char *StringFormatDateTime
             (const Time *tm,
              const char sep[5],
              Size *dstlen,
              char *dst);


#endif
