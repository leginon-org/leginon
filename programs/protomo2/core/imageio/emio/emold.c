/*----------------------------------------------------------------------------*
*
*  emioold.c  -  imageio: em files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "emio.h"
#include "imageiocommon.h"
#include "imageiodefault.h"
#include "exception.h"
#include "array.h"
#include "baselib.h"
#include <stdlib.h>
#include <string.h>


/* functions */

static Status EMMetaCopy
              (Imageio *imageio)

{
  EMMeta *meta = imageio->meta;
  EMHeader *hdr = &meta->header;
  void (*cvt)( Size, const void *, void * );
  ImageAttr attr;
  Type type;

  /* consistency and feature checks */
  if ( !hdr->nx && !hdr->ny && !hdr->nz ) {
    /* file was not closed properly */
    return pushexception( E_IMAGEIO_DATA );
  }
  if ( !hdr->nx ) {
    return pushexception(E_EMIO_HDR);
  }

  /* init */
  meta->headersize = EMHeaderSize;

  /* set data type */
  switch ( hdr->datatype ) {
    case EMbyte:   type = TypeUint8;   cvt = NULL; break;
    case EMint16:  type = TypeInt16;   cvt = Swap16; break;
    case EMint32:  type = TypeInt32;   cvt = Swap32; break;
    case EMfloat:  type = TypeReal32;  cvt = Swap32; break;
    case EMcmplx:  type = TypeCmplx32; cvt = Swap32; break;
    case EMdouble: type = TypeReal64;  cvt = Swap64; break;
    default: return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_FMTERR ) );
  }
  imageio->eltype = type;

  if ( ( cvt != NULL ) && ( imageio->iostat & ImageioByteSwap ) ) {
    imageio->cvtcount = TypeGetCount( type );
    imageio->rdcvt = cvt;
    imageio->wrcvt = cvt;
  }

  /* set size */
  meta->len[1] = 1; meta->low[1] = 0;
  meta->len[2] = 1; meta->low[2] = 0;
  imageio->dim = 1;
  meta->len[0] = hdr->nx;
  meta->low[0] = 0;
  if ( hdr->ny > 1 ) {
    imageio->dim = 2;
    meta->len[1] = hdr->ny;
    if ( hdr->nz > 1 ) {
      imageio->dim = 3;
      meta->len[2] = hdr->nz;
    }
  }
  imageio->len = meta->len;
  imageio->low = meta->low;

  if ( type == TypeCmplx32 ) {
    attr = ImageFourspc; /* Fourier space */
    attr |= ImageSymHerm;
    if ( meta->len[0] % 2 ) attr |= ImageNodd;
    meta->len[0] = meta->len[0] / 2 + 1;
  } else {
    attr = ImageRealspc; /* real space */
  }
  imageio->attr = attr;

  if ( ArrayOffset( imageio->dim, imageio->len, TypeGetSize( imageio->eltype ), &imageio->arrsize ) ) {
    return pushexception( E_IMAGEIO_BIG );
  }

  /* file offset */
  imageio->offset = meta->headersize;

  return E_NONE;

}


extern Status EMOld
              (Imageio *imageio)

{
  EMMeta *meta;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_EMIO );
  if ( runcheck && ( imageio->iostat & ImageioModeCre ) ) return pushexception( E_EMIO );
  if ( runcheck && ( imageio->format == NULL ) ) return pushexception( E_EMIO );
  if ( runcheck && ( imageio->format->syn == NULL ) ) return pushexception( E_EMIO );

  /* meta data buffer */
  meta = malloc( sizeof(EMMeta) );
  if ( meta == NULL ) return pushexception( E_MALLOC );
  imageio->meta = meta;
  imageio->iostat |= ImageioAllocMeta;

  /* read header */
  status = EMHeaderRead( imageio, &meta->header );
  if ( exception( status ) ) return status;

  /* copy meta data */
  status = EMMetaCopy( imageio );
  if ( exception( status ) ) return status;

  /* set i/o modes */
  imageio->rd = ImageioRdAmap;
  imageio->wr = ImageioWrAmap;
  status = ImageioModeInit( imageio );
  if ( exception( status ) ) return status;
  switch ( imageio->iocap ) {
    case ImageioCapUnix: imageio->rd = ImageioRd;    imageio->wr = ImageioWr;    break;
    case ImageioCapStd:  imageio->rd = ImageioRdStd; imageio->wr = ImageioWrStd; break;
    default: imageio->rd = NULL; imageio->wr = NULL;
  }

  /* set open flag when writing */
  if ( imageio->iostat & ImageioModeWr ) {
    status = imageio->format->syn( imageio );
    if ( exception( status ) ) return status;
  }

  return E_NONE;

}
