/*----------------------------------------------------------------------------*
*
*  tomopygtk.h  -  gtk wrapper library
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomopygtk_h_
#define tomopygtk_h_

#include "image.h"

#define TomoPyGtkName   TOMOPYNAME"gtk"
#define TomoPyGtkVers   TOMOPYVERS"."TOMOPYBUILD
#define TomoPyGtkCopy   TOMOPYCOPY


/* types */

typedef struct {
  Status (*display)(const Image *, const void *);
} TomoPyGtkFn;


#endif
