/*----------------------------------------------------------------------------*
*
*  imageioamap.c  -  imageio: image files
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
#include "baselib.h"
#include "exception.h"
#include "macros.h"
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/types.h>


/* functions */

static void *ImageioMapAnon
             (Size size)

{
  const char *anon = "/dev/zero";
  void *addr;
  int fd;

  if ( !size ) {
    pushexception( E_ARGVAL ); return NULL;
  }

  /* create anonymous memory mapping */
  fd = open( anon, O_RDWR );
  if ( fd < 0 ) {
    pushexception( E_ERRNO ); goto error1;
  }

  addr = mmap( 0, size, PROT_READ|PROT_WRITE, MAP_PRIVATE, fd, 0 );
  if ( addr == MAP_FAILED ) {
    pushexception( E_ERRNO ); goto error2;
  }
  if ( addr == NULL ) {
    pushexception( E_IMAGEIO ); goto error2;
  }

  close(fd);

  return addr;

  error2:
  close(fd);

  error1:
  appendexception( " (/dev/zero)" );

  return NULL;

}


static Status ImageioUnmapAnon
              (void *addr,
               Size size)

{
  Status status = E_NONE;

  if ( argcheck( addr == NULL ) ) return pushexception( E_ARGVAL );

  if ( !size ) return pushexception( E_ARGVAL );

  if ( munmap( addr, size ) < 0 ) {
    status = pushexception( E_ERRNO );
    appendexception( " (/dev/zero)" );
  }

  return status;

}


static Status ImageioAnonCheck
              (Imageio *imageio,
               Size *arrsize,
               Size *count)

{
  Offset arroffs;
  Status status;

  status = MulOffset( imageio->arrsize, TypeGetSize( imageio->eltype ), &arroffs );
  if ( exception( status ) || ( arroffs > OffsetMaxSize ) ) return exception( E_IMAGEIO_BIG );

  *arrsize = arroffs;

  if ( imageio->iostat & ImageioBlk ) {
    status = ImageioBlockCheck( imageio, 0, imageio->arrsize, count );
    if ( exception( status ) ) return status;
  } else {
    *count = 0;
  }

  return E_NONE;

}


extern Status ImageioAmap
              (Imageio *imageio)

{
  Size arrsize, count;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );
  if ( runcheck && ( imageio->offset < 0 ) ) return pushexception( E_IMAGEIO );

  if ( imageio->iocap || !( imageio->cap & ( ImageioCapAmap | ImageioCapLoad ) ) ) {
    return pushexception( E_IMAGEIO );
  }
  if ( ( ~imageio->iostat & ImageioModeRd ) || ( imageio->rd == NULL ) ) {
    return pushexception( E_IMAGEIO_IOP );
  }
  if ( ( imageio->iostat & ImageioModeWr ) && ( imageio->wr == NULL ) ) {
    return pushexception( E_IMAGEIO_IOP );
  }

  imageio->iocap = 0;

  status = ImageioAnonCheck( imageio, &arrsize, &count );
  if ( exception( status ) ) return E_NONE;

  if ( ( imageio->cap & ImageioCapLoad ) && ( arrsize > ImageioLoadSize ) ) {
    status = exception( E_IMAGEIO_BIG ); return E_NONE;
  }

  imageio->amap = ImageioMapAnon( arrsize );
  status = testcondition( imageio->amap == NULL );
  if ( status ) return status;

  imageio->iocap = ImageioCapAmap;
  imageio->amapsize = arrsize;

  if ( imageio->iostat & ImageioModeCre ) {

    imageio->iostat |= ImageioModData | ImageioFinMod;

  } else {

    if ( count ) {
      status = ImageioRdBlock( imageio, imageio->rd, imageio->offset, arrsize, count, imageio->amap );
      if ( exception( status ) ) goto error;
    } else {
      status = imageio->rd( imageio, imageio->offset, arrsize, imageio->amap );
      if ( exception( status ) ) goto error;
    }

    if ( imageio->cvtcount && ( imageio->rdcvt != NULL ) ) {
      imageio->rdcvt( imageio->cvtcount * imageio->arrsize, imageio->amap, imageio->amap );
    }

    if ( imageio->iostat & ImageioModeWr ) {
      imageio->iostat |= ImageioModData | ImageioFinMod;
    }

  }

  imageio->wra = imageio->wr;
  imageio->iostat |= ImageioModeLd;

  return E_NONE;

  error:

  popexception( ImageioUnmapAnon( imageio->amap, arrsize ) );
  imageio->iocap = 0;
  imageio->amap = NULL;
  imageio->amapsize = 0;
  return status;

}


extern Status ImageioAmapAddr
              (Imageio *imageio,
               Offset offset,
               Size length,
               void **addr)

{
  Size size, count;
  Status status;

  if ( argcheck( imageio == NULL ) ) return exception( E_ARGVAL );
  if ( offset < 0 ) return exception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return exception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return exception( E_IMAGEIO );
  if ( runcheck && ( imageio->offset < 0 ) ) return exception( E_IMAGEIO );

  if ( ( imageio->iocap && ( imageio->iocap != ImageioCapAmap ) ) || !( imageio->cap & ( ImageioCapAmap | ImageioCapLoad ) ) ) {
    return exception( E_IMAGEIO );
  }

  if ( ~imageio->iostat & ImageioModeLd ) return exception( E_IMAGEIO );

  status = ImageioSizeSet( imageio, &offset, length, &size, &count );
  if ( exception( status ) ) return status;

  char *amap = imageio->amap;
  if ( runcheck && ( amap == NULL ) ) return exception( E_IMAGEIO );
  char *ptr = amap + offset;
  if ( ptr < amap ) return exception( E_INTOVFL );

  *addr = ptr;

  return E_NONE;

}


static Status ImageioSyncAnon
              (Imageio *imageio)

{
  Size arrsize, count;
  Status status;

  if ( imageio->wra == NULL ) {
    return pushexception( E_IMAGEIO );
  }

  if ( imageio->iostat & ImageioModData ) {

    status = ImageioAnonCheck( imageio, &arrsize, &count );
    if ( pushexception( status ) ) return status;

    if ( imageio->cvtcount && ( imageio->wrcvt != NULL ) ) {
      imageio->wrcvt( imageio->cvtcount * imageio->arrsize, imageio->amap, imageio->amap );
    }

    if ( count ) {
      status = ImageioWrBlock( imageio, imageio->wra, imageio->offset, arrsize, count, imageio->amap );
      if ( exception( status ) ) return status;
    } else {
      status = imageio->wra( imageio, imageio->offset, arrsize, imageio->amap );
      if ( exception( status ) ) return status;
    }

    if ( imageio->iostat & ImageioFinClose ) {

      imageio->iostat &= ~ImageioModData;

    } else {

      if ( imageio->cvtcount && ( imageio->rdcvt != NULL ) ) {
        imageio->rdcvt( imageio->cvtcount * imageio->arrsize, imageio->amap, imageio->amap );
      }

    }


  }

  return E_NONE;

}


extern Status ImageioAmapSync
              (Imageio *imageio)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( imageio->iocap != ImageioCapAmap ) {
    return pushexception( E_IMAGEIO );
  }

  status = ImageioSyncAnon( imageio );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern Status ImageioAmapFinal
              (Imageio *imageio)

{
  Offset arrsize;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGEIO );
  if ( runcheck && ( imageio->offset < 0 ) ) return pushexception( E_IMAGEIO );

  if ( imageio->iocap != ImageioCapAmap ) {
    return pushexception( E_IMAGEIO );
  }

  status = ImageioSyncAnon( imageio );
  if ( exception( status ) ) return status;

  status = MulOffset( imageio->arrsize, TypeGetSize( imageio->eltype ), &arrsize );
  if ( pushexception( status ) ) return status;

  status = ImageioUnmapAnon( imageio->amap, arrsize );
  if ( exception( status ) ) return status;

  imageio->amap = NULL;
  imageio->amapsize = 0;
  imageio->iostat &= ~ImageioModeLd;

  return E_NONE;

}
