/*----------------------------------------------------------------------------*
*
*  imagicionew.c  -  imageio: imagic files
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
#include "imagicioconfig.h"
#include "imageiocommon.h"
#include "imageiodefault.h"
#include "stringformat.h"
#include "exception.h"
#include "array.h"
#include "baselib.h"
#include <stdlib.h>
#include <string.h>


/* functions */

static void TimeToImagic
            (Time *time,
             ImagicHeader *hdr)

{
  const char sep[] = { 0, 0, 0, 0, 0 };
  char buf[32];
  Size len = sizeof( buf );
  int y0, y1, y2, y3;

  StringFormatDateTime( time, sep, &len, buf );

  y0 = buf[0] - '0';
  y1 = buf[1] - '0';
  y2 = buf[2] - '0';
  y3 = buf[3] - '0';

  hdr->nyear  = 10 * ( 10 * ( 10 * y0 + y1 ) + y2 ) + y3;
  hdr->nmonth = 10 * ( buf[4]  - '0' ) + ( buf[5]  - '0' );
  hdr->nday   = 10 * ( buf[6]  - '0' ) + ( buf[7]  - '0' );
  hdr->nhour  = 10 * ( buf[8]  - '0' ) + ( buf[9]  - '0' );
  hdr->nminut = 10 * ( buf[10] - '0' ) + ( buf[11] - '0' );
  hdr->nsec   = 10 * ( buf[12] - '0' ) + ( buf[13] - '0' );

}


static Status ImagicMetaInit
              (Imageio *imageio)

{
  ImagicMeta *meta = imageio->meta;
  ImagicHeader *hdr = &meta->header;
  void (*cvt)( Size, const void *, void * );
  Size npixel;
  uint32_t user2;
  Status status;

  /* clear all fields */
  memset( meta, 0, sizeof(ImagicMeta) );
  meta->hdrfile = NULL;

  /* check and set array dimension and size */
  Size dim = imageio->dim;
  if ( !dim || ( dim > ImagicImageMaxDim ) ) {
    return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_DIM ) );
  }
  Size elsize = TypeGetSize( imageio->eltype );
  if ( ArrayOffset( dim, imageio->len, elsize, &imageio->arrsize ) ) {
    return pushexception( E_IMAGEIO_BIG );
  }
  for ( dim = 0; dim < imageio->dim; dim++ ) {
    meta->len[dim] = imageio->len[dim];
    if ( meta->len[dim] > (Size)INT32_MAX ) return pushexception( E_INTOVFL );
  }
  imageio->len = meta->len;
  if ( imageio->low != NULL ) {
    for ( dim = 0; dim < imageio->dim; dim++ ) {
      meta->low[dim] = imageio->low[dim];
      if ( meta->low[dim] < INT32_MIN ) return pushexception( E_INTOVFL );
      if ( meta->low[dim] > INT32_MAX ) return pushexception( E_INTOVFL );
    }
  }
  imageio->low = meta->low;

  hdr->i6lp = hdr->i5lp = 1;
  hdr->i4lp = hdr->izlp = hdr->iylp = hdr->ixlp = 1;
  hdr->ifol = 1;

  if ( imageio->format->version.ident[6] ) {

    /* IMAGIC-RAW, ixlp is y-coo, iylp is x-coo */

    switch ( imageio->dim ) {
      case 4: {
        hdr->i4lp = meta->len[3];
        hdr->ifol *= meta->len[3];
        hdr->locold = meta->low[3];
      }
      case 3: {
        hdr->izlp = meta->len[2];
        hdr->ifol *= meta->len[2];
        hdr->izold = meta->low[2];
      }
      case 2: {
        hdr->ixlp = meta->len[1];
        hdr->ixold = meta->low[1];
      }
      case 1: {
        hdr->iylp = meta->len[0];
        hdr->iyold = meta->low[0];
        break;
      }
      default: return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_DIM ) );
    }

    user2 = IMAGICUSER2RAW;

    hdr->ierror = IMAGICUSER2RAW;

  } else {

    /* IMAGIC proper, image data must be transposed in x-y */

    switch ( imageio->dim ) {
      case 4: {
        hdr->i4lp = meta->len[3];
        hdr->ifol *= meta->len[3];
        hdr->locold = meta->low[3];
      }
      case 3: {
        hdr->izlp = meta->len[2];
        hdr->ifol *= meta->len[2];
        hdr->izold = meta->low[2];
      }
      case 2: {
        hdr->iylp = meta->len[1];
        hdr->iyold = meta->low[0];
      }
      case 1: {
        hdr->ixlp = meta->len[0];
        hdr->ixold = meta->low[1];
        break;
      }
      default: return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_DIM ) );
    }

    user2 = IMAGICUSER2;

    imageio->iostat |= ImageioBlk | ImageioBlkTrnsp;

  }

  hdr->ifol--;

  /* data type */
  if ( imageio->attr & ImageSymMask ) {
    return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_ATTR ) );
  }
  status = ImagicSetType( imageio->eltype, imageio->attr, hdr );
  if ( status ) return ImageioErrFmt( imageio, pushexception( status ) );

  switch ( imageio->eltype ) {
    case TypeUint8:   cvt = NULL; break;
    case TypeInt16:   cvt = Swap16; break;
    case TypeInt32:   cvt = Swap32; break;
    case TypeReal32:  cvt = Swap32; break;
    case TypeCmplx32: cvt = Swap32; break;
    default: return pushexception( E_IMAGICIO );
  }

  if ( ( cvt != NULL ) && ( imageio->iostat & ImageioByteSwap ) ) {
    imageio->cvtcount = TypeGetCount( imageio->eltype );
    imageio->rdcvt = cvt;
    imageio->wrcvt = cvt;
  }

  /* Imagic header */

  hdr->imn = 1;
  meta->ifol = hdr->ifol; /* for first time hdr write */
  hdr->nblocks = 1;
  if ( ArraySize( 3, meta->len, elsize, &npixel ) || ( npixel > INT32_MAX ) ) {
    hdr->rsize = INT32_MAX;
  } else {
    hdr->rsize = npixel;
  }

  strcpy( hdr->name, "i3 did it with no magic" );
  hdr->imavers = 19999999;
  /* IEEE floating point only */
  if ( imageio->iostat & ImageioBigNative ) {
    hdr->realtype = 0x04040404;
  } else {
    hdr->realtype = 0x02020202;
  }

  /* set time and comment label */
  meta->cre = TimeGet();
  TimeToImagic( &meta->cre, hdr );
  Size len = sizeof( hdr->history );
  ImageioGetVersion( " created  by ", ImagicioVers, &len, hdr->history );

  /* identifier */
  *((int32_t *)&hdr->user1) = IMAGICUSER1;
  *((int32_t *)&hdr->user2) = user2;

  /* file offset */
  imageio->offset = 0;

  return E_NONE;

}


extern Status ImagicNew
              (Imageio *imageio)

{
  ImagicMeta *meta;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( ~imageio->iostat & ImageioModeCre ) ) return pushexception( E_IMAGICIO );
  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_IMAGICIO );
  if ( runcheck && ( imageio->format == NULL ) ) return pushexception( E_IMAGICIO );
  if ( runcheck && ( imageio->format->syn == NULL ) ) return pushexception( E_IMAGICIO );

  /* meta data buffer */
  meta = malloc( sizeof(ImagicMeta) );
  if ( meta == NULL ) return pushexception( E_MALLOC );
  imageio->meta = meta;
  imageio->iostat |= ImageioAllocMeta;

  /* initialize meta data */
  status = ImagicMetaInit( imageio );
  if ( exception( status ) ) return status;

  /* write header */
  status = imageio->format->syn( imageio );
  if ( exception( status ) ) return status;

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
