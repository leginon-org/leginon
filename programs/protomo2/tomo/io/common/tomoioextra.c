/*----------------------------------------------------------------------------*
*
*  tomoioextra.c  -  core: tomography
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
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern const I3data *TomoioGetExtra
                     (const Tomoio *tomoio)

{

  if ( tomoio == NULL ) return NULL;

  return &tomoio->extra;

}


extern Status TomoioExtraSetSampling
              (Tomoio *tomoio,
               Coord sampling)

{

  if ( argcheck( tomoio == NULL ) ) return exception( E_ARGVAL );

  if ( sampling <= 0 ) return exception( E_ARGVAL );

  tomoio->sampling = sampling;

  return E_NONE;

}


