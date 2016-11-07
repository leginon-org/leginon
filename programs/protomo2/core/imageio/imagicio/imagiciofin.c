/*----------------------------------------------------------------------------*
*
*  imagiciofin.c  -  imageio: imagic files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagicio.h"
#include "imageiocommon.h"
#include "imageiodefault.h"
#include "exception.h"


/* functions */

extern Status ImagicFin
              (Imageio *imageio)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  ImagicMeta *meta = imageio->meta;
  if ( runcheck && ( meta == NULL ) ) return pushexception( E_IMAGICIO );

  if ( runcheck && ( ~imageio->iostat & ImageioFinClose ) ) return pushexception( E_IMAGICIO );

  status = ImageioFin( imageio );
  logexception( status );

  if ( meta->hdrfile != NULL ) {

    IOMode mode = FileioGetMode( imageio->fileio );

    if ( mode & IODel ) {
      status = FileioSetMode( meta->hdrfile, IODel );
      logexception( status );
    } else {
      status = FileioClearMode( meta->hdrfile, IODel );
      logexception( status );
    }

    Status stat = FileioClose( meta->hdrfile );
    if ( stat ) {
      if ( !status ) status = pushexception( stat );
    } else {
      meta->hdrfile = NULL;
    }

  }

  return status;

}
