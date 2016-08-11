/*----------------------------------------------------------------------------*
*
*  imageiobeginend.c  -  imageio: image files
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
#include "imageioblock.h"
#include "array.h"
#include "baselib.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern void *ImageioBeginRead
             (Imageio *imageio,
              Offset offset,
              Size length)

{
  void *addr;
  Size size, count;
  Status status;

  if ( argcheck( imageio == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( offset < 0 ) { pushexception( E_ARGVAL ); return NULL; }

  if ( runcheck && ( imageio->fileio == NULL ) ) { pushexception( E_IMAGEIO ); return NULL; }
  if ( runcheck && ( imageio->offset  < 0 ) ) { pushexception( E_IMAGEIO ); return NULL; }

  if ( ~imageio->iostat & ImageioModeOpen ) {
    pushexception( E_IMAGEIO ); return NULL;
  }

  if ( ~imageio->iostat & ImageioModeRd ) {
    pushexception( E_IMAGEIO_RD ); return NULL;
  }

  if ( ( imageio->rd == NULL ) && !( imageio->iocap & ( ImageioCapMmap | ImageioCapAmap ) ) ) {
    pushexception( E_IMAGEIO_IOP ); return NULL;
  }

  if ( !length ) {
    status = ArraySize( imageio->dim, imageio->len, TypeGetSize( imageio->eltype ), &length );
    if ( pushexception( status ) ) return NULL;
  }

  if ( imageio->iocap & ( ImageioCapMmap | ImageioCapAmap ) ) {

    status = ImageioAddr( imageio, offset, length, &addr );
    if ( exception( status ) ) return NULL;

  } else {

    status = ImageioSizeSet( imageio, &offset, length, &size, &count );
    if ( pushexception( status ) ) return NULL;

    addr = malloc( size );
    if ( addr == NULL ) {
      pushexception( E_MALLOC ); return NULL;
    }

    if ( count ) {

      status = ImageioRdBlock( imageio, imageio->rd, offset, size, count, addr );
      if ( exception( status ) ) { free( addr ); return NULL; }

    } else {

      status = imageio->rd( imageio, offset, size, addr );
      if ( exception( status ) ) { free( addr ); return NULL; }

      if ( imageio->cvtcount && ( imageio->rdcvt != NULL ) ) {
        imageio->rdcvt( imageio->cvtcount * length, addr, addr );
      }

    }

  }

  return addr;

}


extern void *ImageioBeginWrite
             (Imageio *imageio,
              Offset offset,
              Size length)

{
  void *addr;
  Size size, count;
  Status status;

  if ( argcheck( imageio == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }
  if ( offset < 0 ) { pushexception( E_ARGVAL ); return NULL; }

  if ( runcheck && ( imageio->fileio == NULL ) ) { pushexception( E_IMAGEIO ); return NULL; }
  if ( runcheck && ( imageio->offset  < 0 ) ) { pushexception( E_IMAGEIO ); return NULL; }

  if ( ~imageio->iostat & ImageioModeOpen ) {
    pushexception( E_IMAGEIO ); return NULL;
  }

  if ( ~imageio->iostat & ImageioModeWr ) {
    pushexception( E_IMAGEIO_WR ); return NULL;
  }

  if ( ( imageio->wr == NULL ) && !( imageio->iocap & ( ImageioCapMmap | ImageioCapAmap ) ) ) {
    pushexception( E_IMAGEIO_IOP ); return NULL;
  }

  if ( !length ) {
    status = ArraySize( imageio->dim, imageio->len, TypeGetSize( imageio->eltype ), &length );
    if ( pushexception( status ) ) return NULL;
  }

  if ( imageio->iocap & ( ImageioCapMmap | ImageioCapAmap ) ) {

    status = ImageioAddr( imageio, offset, length, &addr );
    if ( exception( status ) ) return NULL;

  } else {

    status = ImageioSizeSet( imageio, &offset, length, &size, &count );
    if ( pushexception( status ) ) return NULL;

    addr = malloc( size );
    if ( addr == NULL ) {
      pushexception( E_MALLOC ); return NULL;
    }

  }

  imageio->iostat |= ImageioModData | ImageioFinMod;

  return addr;

}


extern Status ImageioEndRead
              (Imageio *imageio,
               Offset offset,
               Size length,
               void *addr)

{

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( offset < 0 ) return pushexception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );
  if ( runcheck && ( imageio->offset  < 0 ) ) return pushexception( E_IMAGEIO );

  if ( ~imageio->iostat & ImageioModeOpen ) {
    return pushexception( E_IMAGEIO );
  }

  if ( ~imageio->iostat & ImageioModeRd ) {
    return pushexception( E_IMAGEIO_RD );
  }

  if ( ( imageio->rd == NULL ) && !( imageio->iocap & ( ImageioCapMmap | ImageioCapAmap ) ) ) {
    return pushexception( E_IMAGEIO_IOP );
  }

  if ( !( imageio->iocap & ( ImageioCapMmap | ImageioCapAmap ) ) ) {

    free( addr );

  }

  return E_NONE;

}


extern Status ImageioEndWrite
              (Imageio *imageio,
               Offset offset,
               Size length,
               void *addr)

{
  Size size, count;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( offset < 0 ) return pushexception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );
  if ( runcheck && ( imageio->offset  < 0 ) ) return pushexception( E_IMAGEIO );

  if ( ~imageio->iostat & ImageioModeOpen ) {
    return pushexception( E_IMAGEIO );
  }

  if ( ~imageio->iostat & ImageioModeWr ) {
    return pushexception( E_IMAGEIO_WR );
  }

  if ( ( imageio->wr == NULL ) && !( imageio->iocap & ( ImageioCapMmap | ImageioCapAmap ) ) ) {
    return pushexception( E_IMAGEIO_IOP );
  }

  if ( !length ) {
    status = ArraySize( imageio->dim, imageio->len, TypeGetSize( imageio->eltype ), &length );
    if ( pushexception( status ) ) return status;
  }

  if ( !( imageio->iocap & ( ImageioCapMmap | ImageioCapAmap ) ) ) {

    status = ImageioSizeSet( imageio, &offset, length, &size, &count );
    if ( pushexception( status ) ) return status;

    if ( count ) {

      status = ImageioWrBlock( imageio, imageio->wr, offset, size, count, addr );
      if ( exception( status ) ) return status;

    } else {

      if ( imageio->cvtcount && ( imageio->wrcvt != NULL ) ) {
        imageio->wrcvt( imageio->cvtcount * length, addr, addr );
      }

      status = imageio->wr( imageio, offset, size, addr );
      if ( exception( status ) ) return status;

    }

    free( addr );

  }

  imageio->iostat |= ImageioModData | ImageioFinMod;

  return E_NONE;

}
