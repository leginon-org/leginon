/*----------------------------------------------------------------------------*
*
*  mulint32.c  -  core: multiply
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "baselib.h"
#include "exception.h"


/* functions */

extern Status MulInt32
              (int32_t src1,
               int32_t src2,
               int32_t *dst)

#define TYPE     int32_t
#define TYPEMIN  INT32_MIN
#define TYPEMAX  INT32_MAX
#define UTYPE    uint32_t
#define BITS     32

#include "mulint.h"
