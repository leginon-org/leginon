/*----------------------------------------------------------------------------*
*
*  tomopyimage.h  -  tomopy: image handling
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomopyimage_h_
#define tomopyimage_h_

#ifdef __cplusplus
extern "C" {
#endif

#include "tomopy.h"

#define TomoPyImageName   "tomopyimage"
#define TomoPyImageVers   TOMOPYVERS"."TOMOPYBUILD
#define TomoPyImageCopy   TOMOPYCOPY


/* exception codes */

enum {
  E_TOMOPYIMAGE = TomoPyImageModuleCode,
  E_TOMOPYIMAGE_GTK,
  E_TOMOPYIMAGE_EMAN,
  E_TOMOPYIMAGE_MAXCODE
};


/* data types */

enum {
  TomoPyUndef,
  TomoPyUint8,
  TomoPyUint16,
  TomoPyUint32,
  TomoPyInt8,
  TomoPyInt16,
  TomoPyInt32,
  TomoPyReal32,
  TomoPyCmplx32
};

enum {
  TomoPyRealspace,
  TomoPyFourier
};


/* variables */

extern PyTypeObject *TomoPyImageTypeObject;


/* prototypes */

extern void TomoPyImageInit
            (TomoPy *mod);

extern PyObject *TomoPyImageCreate();

extern void TomoPyImageSet
            (const void *dscr,
             void *buf,
             PyObject *image);

extern int TomoPyToImage
           (const int dim,
            const int *len,
            const int *low,
            const int type,
            const int attr,
            const void *buf,
            PyObject *image);

extern int TomoPyFromImage
           (int *dim,
            int *len,
            int *low,
            int *type,
            int *attr,
            void **buf,
            const PyObject *image);


#ifdef __cplusplus
}
#endif

#endif
