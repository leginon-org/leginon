/*----------------------------------------------------------------------------*
*
*  tomoimage.h  -  align: image geometry
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoimage_h_
#define tomoimage_h_

#include "tomoaligndefs.h"
#include "tomoseries.h"

#define TomoimageName   "tomoimage"
#define TomoimageVers   TOMOALIGNVERS"."TOMOALIGNBUILD
#define TomoimageCopy   TOMOALIGNCOPY


/* exception codes */

enum {
  E_TOMOIMAGE = TomoimageModuleCode,
  E_TOMOIMAGE_MAXCODE
};


/* data structures */

typedef enum {
  TomoimageSel  = 0x01,
  TomoimageAli  = 0x02,
  TomoimageRef  = 0x04,
  TomoimageDone = 0x10,
  TomoimageFull = 0x20,
} TomoimageFlags;

typedef struct {
  Coord origin[3];
  Coord A[3][3];
  Coord A1[3][3];
  Coord Am[3][3];
  Coord Af[2][2];
  Coord Ap[3][2];
  Coord S[3][3];
  TomoimageFlags flags;
} TomoimageList;

typedef struct {
  TomoimageList *list;
  Size cooref;
  Size count;
  Size *min;
  Size *max;
} Tomoimage;


/* constants */

#define TomoimageInitializer  (Tomoimage){ NULL, SizeMax, 0, NULL, NULL }


/* prototypes */

extern Tomoimage *TomoimageCreate
                  (const Tomoseries *series,
                   const Size *selection,
                   const Size *exclusion,
                   Coord startangle);

extern Status TomoimageDestroy
              (Tomoimage *image);

extern Status TomoimageSet
              (TomoimageList *list,
               Coord Ap[3][2],
               TomoimageFlags full);

extern Status TomoimageGet
              (const Tomoseries *series,
               TomoimageList *list,
               Size index,
               Bool fulltransf);


#endif
