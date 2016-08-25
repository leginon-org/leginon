/*----------------------------------------------------------------------------*
*
*  imagefouriercommon.h  -  fourierop: image transforms
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imagefouriercommon_h_
#define imagefouriercommon_h_

#include "imagefourier.h"
#include "fouriermode.h"


/* types */

struct _ImageFourier {
  Fourier *fou;
  FourierMode mode;
  Size seqdim;
  Size *seqlen;
  Type seqtype;
  void *cvt;
  Size size;
  Size count;
};


#endif
