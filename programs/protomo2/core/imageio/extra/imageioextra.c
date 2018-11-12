/*----------------------------------------------------------------------------*
*
*  imageioextra.c  -  imageioextra: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imageioextra.h"
#include "imageiocommon.h"
#include "exception.h"


/* functions */

extern Status ImageioExtraSetup
              (Imageio *imageio,
               IOMode mode,
               I3data *data)

{
  I3data extra;
  Status status;

  if ( argcheck( imageio == NULL ) ) return exception( E_IMAGEIOEXTRA );
  if ( argcheck( data == NULL ) ) return exception( E_IMAGEIOEXTRA );

  if ( imageio->extraoffs > 0 ) return exception( E_IMAGEIOEXTRA );

  if ( imageio->format->ext == NULL ) return exception( E_IMAGEIOEXTRA_IMPL );

  status = imageio->format->ext( imageio, mode, &extra );
  if ( popexception( status ) ) return status;

  if ( ( extra.handle == NULL ) && ( extra.init == NULL ) ) return exception( E_IMAGEIOEXTRA );

  imageio->extraoffs = OffsetMax;

  *data = extra;

  return E_NONE;

}



extern Status ImageioExtraInit
              (Imageio *imageio,
               I3data *data)

{

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( data == NULL ) ) return pushexception( E_ARGVAL );

  data->handle = imageio;

  return E_NONE;

}

