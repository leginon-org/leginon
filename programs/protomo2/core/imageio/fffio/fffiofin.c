/*----------------------------------------------------------------------------*
*
*  fffiofin.c  -  imageio: FFF files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "fffio.h"
#include "imageiocommon.h"
#include "imageiodefault.h"
#include "exception.h"


/* functions */

extern Status FFFFin
              (Imageio *imageio)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  FFFMeta *meta = imageio->meta;
  if ( runcheck && ( meta == NULL ) ) return pushexception( E_FFFIO );

  if ( runcheck && ( ~imageio->iostat & ImageioFinClose ) ) return pushexception( E_FFFIO );

  if ( meta->extra.final != NULL ) {
    status = meta->extra.final( &meta->extra, E_NONE );
    if ( pushexception( status ) ) {
      if ( imageio->iostat & ImageioModeCre ) imageio->iostat |= ImageioModeDel;
    }
  }

  status = ImageioFin( imageio );
  logexception( status );

  return status;

}
