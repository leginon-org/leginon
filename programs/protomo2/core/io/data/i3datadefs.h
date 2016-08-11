/*----------------------------------------------------------------------------*
*
*  i3datadefs.h  -  io: i3 file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef i3datadefs_h_
#define i3datadefs_h_

#include "image.h"


/* types */

typedef enum {
  I3dataSampling,
  I3dataBinning,
  I3dataTransf,
  I3dataStat,
  I3dataCenters,
  I3dataCount,
  I3dataImage,
  I3dataWindow2,
  I3dataWindow3,
  I3dataAlign,
  I3dataMax,
  I3dataUndef = -1
} I3dataCode;

typedef struct {
  Size count;
  Size dim;
} I3Count;

typedef struct {
  Image image;
  Size len[4];
  Index low[4];
  Size size;
  Size elsize;
} I3Image;

typedef struct {
  Size fileindex;
  Size windowindex;
  Coord A[3][2];
} I3Window2;

typedef struct {
  Size fileindex;
  Size windowindex;
  Coord A[4][3];
} I3Window3;

typedef struct {
  Size fileindex;
  Size windowindex;
  Size reference;
  Real ccc;
} I3Align;


/* constants */

#define I3ImageInitializer    (I3Image){ ImageInitializer, { 1, 1, 1, 0 }, { 0, 0, 0, 0 }, 0, 0 }

#define I3Window2Initializer  (I3Window2){ SizeMax, SizeMax, { { 0, 0 }, { 0, 0 }, { 0, 0 } } }

#define I3Window3Initializer  (I3Window3){ SizeMax, SizeMax, { { 0, 0, 0 }, { 0, 0, 0 }, { 0, 0, 0 }, { 0, 0, 0 } } }

#define I3AlignInitializer    (I3Align){ SizeMax, SizeMax, SizeMax, -RealMax }


#endif
