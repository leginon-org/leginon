/*----------------------------------------------------------------------------*
*
*  fffiosiz.c  -  imageio: FFF files
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
#include "baselib.h"
#include "exception.h"


/* functions */

extern Status FFFSiz
              (Imageio *imageio,
               Offset size,
               Size length)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( size < 0 ) ) return pushexception( E_ARGVAL );

  FFFMeta *meta = imageio->meta;
  Fileio *fileio = imageio->fileio;
  if ( runcheck && ( fileio == NULL ) ) return pushexception( E_FFFIO );

  Offset filesize = size * TypeGetSize( imageio->eltype );
  if ( ( OffsetMax - filesize ) < imageio->offset ) return pushexception( E_INTOVFL );
  filesize += imageio->offset;

  if ( meta->i3meta ) {

    if ( size < imageio->arrsize ) {
      if ( meta->attr < 0 ) {
        status = FileioTruncate( fileio, filesize );
        if ( pushexception( status ) ) return status;
      }
    } else if ( size > imageio->arrsize ) {
      if ( meta->attr < 0 ) {
        status = FileioAllocate( fileio, filesize );
        if ( pushexception( status ) ) return status;
      } else {
        return pushexception( E_IMAGEIO_SZ );
      }
    }

  } else {

    if ( size < imageio->arrsize ) {
      status = FileioTruncate( fileio, filesize );
      if ( pushexception( status ) ) return status;
    } else if ( size > imageio->arrsize ) {
      status = FileioAllocate( fileio, filesize );
      if ( pushexception( status ) ) return status;
    }

  }

  return E_NONE;

}
