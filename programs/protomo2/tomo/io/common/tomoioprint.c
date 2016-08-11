/*----------------------------------------------------------------------------*
*
*  tomoioprint.c  -  core: tomography
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoiocommon.h"
#include "statistics.h"
#include "exception.h"
#include "message.h"
#include <stdlib.h>


/* functions */

extern void TomoioPrintImage
            (const Tomoio *tomoio)

{

  I3dataPrint( I3dataImage, 0, tomoio->metadata );

}


