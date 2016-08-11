/*----------------------------------------------------------------------------*
*
*  imageiodefault.c  -  imageio: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imageiocommon.h"
#include "exception.h"
#include "macros.h"


/* functions */

extern Status ImageioRd
              (Imageio *imageio,
               Offset offset,
               Size length,
               void *addr)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );
  if ( runcheck && ( imageio->iocap != ImageioCapUnix ) ) return pushexception( E_IMAGEIO );

  if ( ( ~imageio->iostat & ( ImageioModeOpen | ImageioModeRd ) ) || ( imageio->iostat & ImageioFinClose ) ) {
    return pushexception( E_IMAGEIO );
  }

  status = FileioRead( imageio->fileio, offset, length, addr );
  if ( pushexception( status ) ) return status;

  return status;

}


extern Status ImageioRdStd
              (Imageio *imageio,
               Offset offset,
               Size length,
               void *addr)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );
  if ( runcheck && ( imageio->iocap != ImageioCapStd ) ) return pushexception( E_IMAGEIO );

  if ( ( ~imageio->iostat & ( ImageioModeOpen | ImageioModeRd ) ) || ( imageio->iostat & ImageioFinClose ) ) {
    return pushexception( E_IMAGEIO );
  }

  status = FileioReadStd( imageio->fileio, offset, length, addr );
  if ( pushexception( status ) ) return status;

  return status;

}


extern Status ImageioRdAmap
              (Imageio *imageio,
               Offset offset,
               Size length,
               void *addr)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );
  if ( runcheck && ( imageio->iocap != ImageioCapAmap ) ) return pushexception( E_IMAGEIO );

  if ( ( imageio->iostat & ImageioModeOpen ) || ( ~imageio->iostat & ImageioModeRd ) ) {
    return pushexception( E_IMAGEIO );
  }

  status = FileioRead( imageio->fileio, offset, length, addr );
  if ( pushexception( status ) ) return status;

  return status;

}


extern Status ImageioWr
              (Imageio *imageio,
               Offset offset,
               Size length,
               const void *addr)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );
  if ( runcheck && ( imageio->iocap != ImageioCapUnix ) ) return pushexception( E_IMAGEIO );

  if ( ( ~imageio->iostat & ( ImageioModeOpen | ImageioModeWr ) ) || ( imageio->iostat & ImageioFinClose ) ) {
    return pushexception( E_IMAGEIO );
  }

  status = FileioWrite( imageio->fileio, offset, length, addr );
  if ( pushexception( status ) ) return status;

  return status;

}


extern Status ImageioWrStd
              (Imageio *imageio,
               Offset offset,
               Size length,
               const void *addr)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );
  if ( runcheck && ( imageio->iocap != ImageioCapStd ) ) return pushexception( E_IMAGEIO );

  if ( ( ~imageio->iostat & ( ImageioModeOpen | ImageioModeWr ) ) || ( imageio->iostat & ImageioFinClose ) ) {
    return pushexception( E_IMAGEIO );
  }

  status = FileioWriteStd( imageio->fileio, offset, length, addr );
  if ( pushexception( status ) ) return status;

  return status;

}


extern Status ImageioWrAmap
              (Imageio *imageio,
               Offset offset,
               Size length,
               void *addr)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );
  if ( runcheck && ( imageio->iocap != ImageioCapAmap ) ) return pushexception( E_IMAGEIO );

  if ( ~imageio->iostat & ( ImageioModeOpen | ImageioModeWr | ImageioFinClose ) ) {
    return pushexception( E_IMAGEIO );
  }

  status = FileioWrite( imageio->fileio, offset, length, addr );
  if ( pushexception( status ) ) return status;

  return status;

}


extern Status ImageioMmapAdr
              (Imageio *imageio,
               Offset offset,
               Size length,
               void **addr)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( imageio->offset < 0 ) ) return pushexception( E_IMAGEIO );
  if ( argcheck( addr == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );
  if ( runcheck && ( imageio->iocap != ImageioCapMmap ) ) return pushexception( E_IMAGEIO );

  if ( ( ~imageio->iostat & ImageioModeOpen ) || ( imageio->iostat & ImageioFinClose ) ) {
    return pushexception( E_IMAGEIO );
  }

  status = ImageioMmapSet( imageio, offset, length, addr );
  if ( pushexception( status ) ) return status;

  return E_NONE;

}


extern Status ImageioSiz
              (Imageio *imageio,
               Offset size,
               Size length)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( size < 0 ) ) return pushexception( E_ARGVAL );

  Fileio *fileio = imageio->fileio;
  if ( runcheck && ( fileio == NULL ) ) return pushexception( E_IMAGEIO );

  Offset elsize = TypeGetSize( imageio->eltype );
  if ( size > OffsetMax / elsize ) return exception( E_INTOVFL );
  Offset filesize = size * elsize;

  if ( OFFSETADDOVFL( filesize, imageio->offset ) ) return exception( E_INTOVFL );
  filesize += imageio->offset;

  if ( size < imageio->arrsize ) {
    status = FileioTruncate( fileio, filesize );
    if ( pushexception( status ) ) return status;
  } else {
    status = FileioAllocate( fileio, filesize );
    if ( pushexception( status ) ) return status;
  }

  return E_NONE;

}


extern Status ImageioFls
              (Imageio *imageio)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );

  if ( ~imageio->iostat & ( ImageioModeOpen | ImageioModeWr ) ) {
    return pushexception( E_IMAGEIO );
  }

  switch ( imageio->iocap ) {

    case ImageioCapMmap:
    case ImageioCapStd:
    case ImageioCapUnix: {
      status = FileioFlush( imageio->fileio );
      if ( pushexception( status ) ) return status;
      break;
    }

    case ImageioCapAmap: {
      status = ImageioAmapSync( imageio );
      if ( exception( status ) ) return status;
      break;
    }

    default: {
      return pushexception( E_IMAGEIO );
    }

  }

  return E_NONE; 

}


extern Status ImageioFin
              (Imageio *imageio)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );

  if ( ~imageio->iostat & ( ImageioModeOpen | ImageioFinClose ) ) {
    return pushexception( E_IMAGEIO );
  }

  switch ( imageio->iocap ) {

    case ImageioCapMmap:
    case ImageioCapStd:
    case ImageioCapUnix: {
      break;
    }

    case ImageioCapAmap: {
      status = ImageioAmapFinal( imageio );
      if ( exception( status ) ) return status;
      break;
    }

    default: {
      return pushexception( E_IMAGEIO );
    }

  }

  if ( imageio->iostat & ImageioModeDel ) {
    status = ImageioDel( imageio );
    if ( exception( status ) ) return status;
  }

  status = FileioClose( imageio->fileio );
  if ( pushexception( status ) ) return status;
  imageio->fileio = NULL;

  return status;

}
