/*----------------------------------------------------------------------------*
*
*  imageioextra.h  -  imageioextra: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imageioextra_h_
#define imageioextra_h_

#include "imageio.h"
#include "i3data.h"

#define ImageioExtraName   "imageioextra"
#define ImageioExtraVers   IMAGEIOVERS"."IMAGEIOBUILD
#define ImageioExtraCopy   IMAGEIOCOPY


/* exception codes */

enum {
  E_IMAGEIOEXTRA = ImageioExtraModuleCode,
  E_IMAGEIOEXTRA_IMPL,
  E_IMAGEIOEXTRA_MAXCODE
};


/* prototypes */

extern Status ImageioExtraSetup
              (Imageio *imageio,
               IOMode mode,
               I3data *data);

extern Status ImageioExtraInit
              (Imageio *imageio,
               I3data *data);


#endif
