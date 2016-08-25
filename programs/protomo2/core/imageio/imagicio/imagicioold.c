/*----------------------------------------------------------------------------*
*
*  imagicioold.c  -  imageio: imagic files
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
#include "imagicioconfig.h"
#include "imageiodefault.h"
#include "stringparse.h"
#include "exception.h"
#include "array.h"
#include "baselib.h"
#include <stdlib.h>
#include <string.h>


/* functions */

static void ImagicToTime
            (ImagicHeader *hdr,
             Time *time)

{
  int y = hdr->nyear;
  char buf[20];
  Size i;

  if ( y < 1970 ) {
    if ( y < 70 ) {
      y += 2000;
    } else {
      y += 1900;
    }
  }
  buf[3]  = y % 10; y /= 10;
  buf[2]  = y % 10; y /= 10;
  buf[1]  = y % 10; y /= 10;
  buf[0]  = y % 10; y /= 10;
  buf[4]  = hdr->nmonth / 10;
  buf[5]  = hdr->nmonth % 10;
  buf[6]  = hdr->nday / 10;
  buf[7]  = hdr->nday % 10;
  buf[8]  = hdr->nhour / 10;
  buf[9]  = hdr->nhour % 10;
  buf[10] = hdr->nminut / 10;
  buf[11] = hdr->nminut % 10;
  buf[12] = hdr->nsec / 10;
  buf[13] = hdr->nsec % 10;
  buf[14] = 0;
  for ( i = 0; i < 14; i++ ) {
    buf[i] += '0';
  }

  if ( StringParseDateTime( buf, NULL, time, NULL ) ) {
    memset( time, 0, sizeof(Time) );
  }

}


static Status ImagicMetaCopy
              (Imageio *imageio)

{
  ImagicMeta *meta = imageio->meta;
  ImagicHeader *hdr = &meta->header;
  void (*cvt)( Size, const void *, void * );
  Status status;

  /* consistency and feature checks */
  if ( hdr->ierror ) {
    if ( !imageio->format->version.ident[6] || ( hdr->ierror != IMAGICUSER2RAW ) ) {
      /* file was not closed properly */
      return pushexception( E_IMAGEIO_DATA );
    }
  }
  ImagicToTime( hdr, &meta->cre );

  /* set data type */
  status = ImagicGetType( hdr, &imageio->eltype, &imageio->attr );
  if ( status ) return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_FMTERR ) );
  switch ( imageio->eltype ) {
    case TypeUint8:   cvt = NULL; break;
    case TypeInt16:   cvt = Swap16; break;
    case TypeInt32:   cvt = Swap32; break;
    case TypeReal32:  cvt = Swap32; break;
    case TypeCmplx32: cvt = Swap32; break;
    default: return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_TYPE ) );
  }

  if ( ( cvt != NULL ) && ( imageio->iostat & ImageioByteSwap ) ) {
    imageio->cvtcount = TypeGetCount( imageio->eltype );
    imageio->rdcvt = cvt;
    imageio->wrcvt = cvt;
  }

  /* size */
  Index ni = hdr->ifol + 1;
  if ( ni % hdr->izlp ) return pushexception( E_IMAGEIO_FMTERR );
  ni /= hdr->izlp;
  if ( hdr->i4lp > 0 ) {
    if ( ni % hdr->i4lp ) return pushexception( E_IMAGEIO_FMTERR );
    if ( ni != hdr->i4lp ) return pushexception( E_IMAGICIO_FEAT );
  }
  if ( ( hdr->i5lp > 1 ) || ( hdr->i6lp > 1 ) ) {
    return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_DIM ) );
  }

  if ( imageio->format->version.ident[6] ) {

    meta->len[0] = hdr->iylp; /* IMAGIC-RAW */
    meta->len[1] = hdr->ixlp;

    meta->low[0] = hdr->iyold;
    meta->low[1] = hdr->ixold;

  } else {

    meta->len[0] = hdr->ixlp;/* IMAGIC proper */
    meta->len[1] = hdr->iylp;

    meta->low[0] = hdr->ixold;
    meta->low[1] = hdr->iyold;

    imageio->iostat |= ImageioBlk | ImageioBlkTrnsp;

  }

  meta->len[2] = hdr->izlp;
  meta->len[3] = ni;

  meta->low[2] = hdr->izold;
  meta->low[3] = hdr->locold;

  imageio->dim = 3;
  if ( meta->len[2] <= 1 ) {
    imageio->dim--;
    meta->len[2] = 1;
    meta->low[2] = 0;
    if ( meta->len[1] <= 1 ) {
      imageio->dim--;
      meta->len[1] = 1;
      meta->low[1] = 0;
      if ( meta->low[0] <= 1 ) {
        meta->len[0] = 1;
        meta->low[0] = 0;
      }
    }
  }

  if ( meta->len[3] <= 1 ) {
    meta->len[3] = 1;
    meta->low[3] = 0;
  } else {
    imageio->dim = 4;
  }

  imageio->len = meta->len;
  imageio->low = meta->low;

  if ( ArrayOffset( imageio->dim, imageio->len, TypeGetSize( imageio->eltype ), &imageio->arrsize ) ) {
    return pushexception( E_IMAGEIO_BIG );
  }

  /* file offset */
  imageio->offset = 0;

  return E_NONE;

}


extern Status ImagicOld
              (Imageio *imageio)

{
  ImagicMeta *meta;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGICIO );
  if ( runcheck && ( imageio->iostat & ImageioModeCre ) ) return pushexception( E_IMAGICIO );
  if ( runcheck && ( imageio->format == NULL ) ) return pushexception( E_IMAGICIO );
  if ( runcheck && ( imageio->format->syn == NULL ) ) return pushexception( E_IMAGICIO );

  /* meta data buffer */
  meta = malloc( sizeof(ImagicMeta) );
  if ( meta == NULL ) return pushexception( E_MALLOC );
  imageio->meta = meta;
  imageio->iostat |= ImageioAllocMeta;

  /* read header */
  status = ImagicHeaderRead( imageio, &meta->header );
  if ( exception( status ) ) return status;

  /* copy meta data */
  status=ImagicMetaCopy( imageio );
  if ( exception( status ) ) return status;

  /* set open flag when writing */
  if ( imageio->iostat & ImageioModeWr ) {
    status = imageio->format->syn( imageio );
    if ( exception( status ) ) return status;
  }

  /* open image data file now */
  status = ImagicImageFileOpen( imageio );
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

  return E_NONE;

}
