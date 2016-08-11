/*----------------------------------------------------------------------------*
*
*  fouriercenter.c  -  fourier: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "fouriercommon.h"
#include "exception.h"
#include "mathdefs.h"
#include "macros.h"
#include <stdlib.h>
#include <string.h>


/* functions */

#undef TYPE
#define TYPE Real
#include "fouriercenter.h"

#undef TYPE
#define TYPE Cmplx
#include "fouriercenter.h"
