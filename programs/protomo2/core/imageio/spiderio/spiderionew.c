/*----------------------------------------------------------------------------*
*
*  spiderionew.c  -  imageio: spider files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "spiderio.h"
#include "imageiocommon.h"
#include "imageiodefault.h"
#include "stringformat.h"
#include "exception.h"
#include "array.h"
#include "baselib.h"
#include <stdlib.h>
#include <string.h>


/* variables */

static const char SpiderMonth[12][6]={
  { 'J','a','n','A','N',31 },
  { 'F','e','b','E','B',29 },
  { 'M','a','r','A','R',31 },
  { 'A','p','r','P','R',30 },
  { 'M','a','y','A','Y',31 },
  { 'J','u','n','U','N',30 },
  { 'J','u','l','U','L',31 },
  { 'A','u','g','U','G',31 },
  { 'S','e','p','E','P',30 },
  { 'O','c','t','C','T',31 },
  { 'N','o','v','O','V',30 },
  { 'D','e','c','E','C',31 }
};


/* functions */

static void TimeToSpider
            (Time *time,
             char spdrdate[12],
             char spdrtime[8])

{
  const char sep[] = { 0, 0, 0, 0, 0 };
  char buf[32];
  Size len = sizeof( buf );
  int m;

  StringFormatDateTime( time, sep, &len, buf );

  m = 10 * ( buf[4] - '0' ) + ( buf[5] - '0' ) - 1;
  spdrdate[0] = buf[6];
  spdrdate[1] = buf[7];
  spdrdate[2] = '-';
  spdrdate[3] = SpiderMonth[m][0];
  spdrdate[4] = SpiderMonth[m][1];
  spdrdate[5] = SpiderMonth[m][2];
  spdrdate[6] = '-';
  spdrdate[7] = buf[0];
  spdrdate[8] = buf[1];
  spdrdate[9] = buf[2];
  spdrdate[10] = buf[3];
  spdrdate[11] = ' ';

  spdrtime[0] = buf[8];
  spdrtime[1] = buf[9];
  spdrtime[2] = ':';
  spdrtime[3] = buf[10];
  spdrtime[4] = buf[11];
  spdrtime[5] = ':';
  spdrtime[6] = buf[12];
  spdrtime[7] = buf[13];

}


static Status SpiderMetaInit
              (Imageio *imageio)

{
  SpiderMeta *meta = imageio->meta;
  SpiderHeader *hdr = &meta->header;
  void (*cvt)( Size, const void *, void * );
  SpiderType spitype, foue, fouo;
  ImageAttr attr;
  Size dim, len;
  Size nrec, reclen;

  /* clear all fields */
  memset( meta, 0, sizeof(SpiderMeta) );

  /* check and set array dimension and size */
  dim = imageio->dim;
  switch ( dim ) {
    case 1:
    case 2: {
      dim = 2;
      spitype = SPIDER_FMT_2D;
      foue = SPIDER_FMT_2D_FOU_EVEN;
      fouo = SPIDER_FMT_2D_FOU_ODD;
      break;
    }
    case 3: {
      dim = 3;
      spitype = SPIDER_FMT_3D;
      foue = SPIDER_FMT_3D_FOU_EVEN;
      fouo = SPIDER_FMT_3D_FOU_ODD;
      break;
    }
    default: {
      return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_DIM ) );
    }
  }
  if ( ArrayOffset( dim, imageio->len, TypeGetSize( imageio->eltype ), &imageio->arrsize ) ) {
    return pushexception( E_IMAGEIO_BIG );
  }
  while ( dim < 3 ) {
    meta->len[dim] = 1;
    meta->low[dim] = 0;
    dim++;
  }
  for ( dim = 0; dim < imageio->dim; dim++ ) {
    meta->len[dim] = imageio->len[dim];
  }
  imageio->len = meta->len;
  if ( imageio->low != NULL ) {
    for ( dim = 0; dim < imageio->dim; dim++ ) {
      meta->low[dim] = imageio->low[dim];
    }
  }
  imageio->low = meta->low;

  /* check data type */
  switch ( imageio->eltype ) {
    case TypeReal32:  cvt = Swap32; break;
    case TypeCmplx32: cvt = Swap32; break;
    default: return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_TYPE ) );
  }
  attr = imageio->attr;
  if ( attr & ImageFourspc ) {
    if ( ( attr & ImageSymMask ) == ImageSymHerm ) {
      spitype = ( attr & ImageNodd ) ? fouo : foue;
    } else {
      return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_ATTR ) );
    }
  } else if ( attr & ( ImageSymMask | ImageNodd ) ) {
    return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_ATTR ) );
  }

  if ( ( cvt != NULL ) && ( imageio->iostat & ImageioByteSwap ) ) {
    imageio->cvtcount = TypeGetCount( imageio->eltype );
    imageio->rdcvt = cvt;
    imageio->wrcvt = cvt;
  }

  /* Spider header */

  hdr->nsam = meta->len[0];
  hdr->nrow = meta->len[1];
  hdr->nslice = meta->len[2];
  hdr->iform = spitype;
  hdr->sig = -1;
  hdr->scale = 1;
  nrec = ( 256 + meta->len[0] - 1 ) / meta->len[0];
  reclen = meta->len[0] * sizeof(Real32);
  meta->headersize = nrec * reclen;
  hdr->labrec = nrec;
  hdr->labbyt = meta->headersize;
  hdr->lenbyt = reclen;

  meta->cre = TimeGet();
  TimeToSpider( &meta->cre, hdr->cdat, hdr->ctim );
  len = sizeof(hdr->ctit);
  ImageioGetVersion( " created  by ", SpiderioVers, &len, hdr->ctit );

  /* file offset */
  imageio->offset = meta->headersize;

  return E_NONE;

}


extern Status SpiderNew
              (Imageio *imageio)

{
  SpiderMeta *meta;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( ~imageio->iostat & ImageioModeCre ) ) return pushexception( E_SPIDERIO );
  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_SPIDERIO );
  if ( runcheck && ( imageio->format == NULL ) ) return pushexception( E_SPIDERIO );
  if ( runcheck && ( imageio->format->syn == NULL ) ) return pushexception( E_SPIDERIO );

  /* meta data buffer */
  meta = malloc( sizeof(SpiderMeta) );
  if ( meta == NULL ) return pushexception( E_MALLOC );
  imageio->meta = meta;
  imageio->iostat |= ImageioAllocMeta;

  /* initialize meta data */
  status = SpiderMetaInit( imageio );
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

  /* write header */
  status = imageio->format->syn( imageio );
  if ( exception( status ) ) return status;

  return E_NONE;

}
