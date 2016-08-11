/*----------------------------------------------------------------------------*
*
*  tomodiagn.h  -  align: diagnostic output
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomodiagn_h_
#define tomodiagn_h_

#include "tomoaligndefs.h"
#include "tomoseries.h"
#include "image.h"

#define TomodiagnName   "tomodiagn"
#define TomodiagnVers   TOMOALIGNVERS"."TOMOALIGNBUILD
#define TomodiagnCopy   TOMOALIGNCOPY


/* exception codes */

enum {
  E_TOMODIAGN = TomodiagnModuleCode,
  E_TOMODIAGN_MAXCODE
};


/* types */

struct _Tomodiagn;

typedef struct _Tomodiagn Tomodiagn;


/* prototypes */

extern Tomodiagn *TomodiagnCreate
                  (const Tomoseries *series,
                   const char *sffx,
                   const Image *image);


extern Status TomodiagnDestroy
              (Tomodiagn *diagn);


extern Status TomodiagnClose
              (Tomodiagn *diagn);

extern Status TomodiagnWrite
              (Tomodiagn *diagn,
               Size index,
               const void *addr);


#endif
