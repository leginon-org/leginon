/*----------------------------------------------------------------------------*
*
*  tomo.h  -  core: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomo_h_
#define tomo_h_

#include "tomodefs.h"

#define TomoName   "tomo"
#define TomoVers   TOMOVERS"."TOMOBUILD
#define TomoCopy   TOMOCOPY


/* exception codes */

enum {
  E_TOMO = TomoModuleCode,
  E_TOMO_MAXCODE
};


#endif
