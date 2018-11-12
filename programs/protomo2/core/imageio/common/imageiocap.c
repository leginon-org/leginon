/*----------------------------------------------------------------------------*
*
*  imageiocap.c  -  imageio: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imageiocommon.h"
#include "exception.h"
#include <string.h>


/* variables */

static const char *ImageioCapStr[] = {
  "all",
  "lib",
  "unix",
  "std",
  "mmap",
  "amap",
  "load",
  "rdwr",
  NULL,
};

static const ImageioCap ImageioCapVal[] = {
  ImageioCapAll | ImageioCapAuto,
  ImageioCapLib,
  ImageioCapUnix,
  ImageioCapStd,
  ImageioCapMmap,
  ImageioCapAmap,
  ImageioCapLoad,
  ImageioCapRdWr,
};


/* functions */

extern ImageioCap ImageioCapCheck
                  (const char *cap)

{

  const char **str = ImageioCapStr;
  const ImageioCap *val = ImageioCapVal;

  while ( *str != NULL ) {
    if ( !strcasecmp( *str, cap ) ) {
      return *val;
    }
    str++; val++;
  }

  return 0;

}
