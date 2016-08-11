/*----------------------------------------------------------------------------*
*
*  suprimioold.c  -  imageio: suprim files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "suprimio.h"
#include "imageiocommon.h"
#include "imageiodefault.h"
#include "exception.h"
#include "array.h"
#include "baselib.h"
#include <stdlib.h>
#include <string.h>


static Status SuprimMetaCopy
              (Imageio *imageio)

{
  SuprimMeta *meta = imageio->meta;
  SuprimHeader *hdr = &meta->header;
  void (*cvt)( Size, const void *, void * );
  ImageAttr attr;
  Type type;
  int32_t nz;

  /* consistency and feature checks */
  if ( hdr->intern == SuprimOpenFlag ) {
    /* file was not closed properly */
    return pushexception( E_IMAGEIO_DATA );
  }
  nz = hdr->reg[NSLICES].l;
  if ( ( hdr->nrow  <= 0 ) || ( hdr->ncol  <= 0 ) || ( hdr->reg[NSLICES].l < 0 )
    || ( hdr->format < 0 ) || ( hdr->intern < 0 ) ) {
    return pushexception( E_SUPRIMIO_HDR );
  }

  /* set data type */
  switch ( hdr->intern ) {
    case SuprimUint8:   type = TypeUint8;   cvt = NULL; break;
    case SuprimInt16:   type = TypeInt16;   cvt = Swap16; break;
    case SuprimInt32:   type = TypeInt32;   cvt = Swap32; break;
    case SuprimReal32:  type = TypeReal32;  cvt = Swap32; break;
    case SuprimCmplx32: type = TypeCmplx32; cvt = Swap32; break;
    case SuprimRGB:     type = TypeRGB;     cvt = NULL; break;
    default: return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_FMTERR ) );
  }
  imageio->eltype = type;

  if ( ( cvt != NULL ) && ( imageio->iostat & ImageioByteSwap ) ) {
    imageio->cvtcount = TypeGetCount( type );
    imageio->rdcvt = cvt;
    imageio->wrcvt = cvt;
  }

  if ( type == TypeCmplx32 ) {
    attr = ImageFourspc; /* Fourier space */
  } else {
    attr = ImageRealspc; /* real space */
  }
  imageio->attr = attr;

  /* set size after type */
  if ( nz > 1 ) {
    imageio->dim = 3;
    meta->len[2] = nz;
    meta->low[2] = 0; /* not defined */
  } else {
    imageio->dim = 2;
  }
  meta->len[0] = hdr->ncol;
  meta->len[1] = hdr->nrow;
  meta->low[0] = 0; /* hdr->reg[COL_ORG].f is float */;
  meta->low[1] = 0; /* hdr->reg[ROW_ORG].f is float */;
  imageio->len = meta->len;
  imageio->low = meta->low;

  if ( ArrayOffset( imageio->dim, imageio->len, TypeGetSize( imageio->eltype ), &imageio->arrsize ) ) {
    return pushexception( E_IMAGEIO_BIG );
  }

  /* file offset */
  imageio->offset = meta->headersize;

  return E_NONE;

}


extern Status SuprimOld
              (Imageio *imageio)

{
  SuprimMeta *meta;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_SUPRIMIO );
  if ( runcheck && ( imageio->iostat & ImageioModeCre ) ) return pushexception( E_SUPRIMIO );
  if ( runcheck && ( imageio->format == NULL ) ) return pushexception( E_SUPRIMIO );
  if ( runcheck && ( imageio->format->syn == NULL ) ) return pushexception( E_SUPRIMIO );

  /* meta data buffer */
  meta = malloc( sizeof(SuprimMeta) );
  if ( meta == NULL ) return pushexception( E_MALLOC );
  imageio->meta = meta;
  imageio->iostat |= ImageioAllocMeta;

  /* read header */
  status = SuprimHeaderRead( imageio, &meta->header );
  if ( exception( status ) ) return status;

  /* copy meta data */
  status=SuprimMetaCopy( imageio );
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
