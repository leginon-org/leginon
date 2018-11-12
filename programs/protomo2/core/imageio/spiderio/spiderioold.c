/*----------------------------------------------------------------------------*
*
*  spiderioold.c  -  imageio: spider files
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
#include "stringparse.h"
#include "exception.h"
#include "array.h"
#include "baselib.h"
#include <math.h>
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

static Bool checkval
            (char c0,
             char c1,
             unsigned int min,
             unsigned int max)

{
  unsigned int v, v0, v1;

  if ( c0 < '0' ) return True;
  v0 = c0 - '0';
  if ( v0 >  9  ) return True;

  if ( c1 < '0' ) return True;
  v1 = c1 - '0';
  if ( v1 >  9  ) return True;

  v = 10 * v0 + v1;
  if ( v < min ) return True;
  if ( v > max ) return True;

  return False;

}


static void SpiderToTime
            (char spdrdate[12],
             char spdrtime[8],
             Time *time)

{
  unsigned int i;
  unsigned int m = 0;
  char buf[16];

  for ( i = 0; i < 12; i++ ) {
    if ( ( spdrdate[3] == SpiderMonth[i][0] )
      && ( ( spdrdate[4] == SpiderMonth[i][1] ) || ( spdrdate[4] == SpiderMonth[i][3] ) )
      && ( ( spdrdate[5] == SpiderMonth[i][2] ) || ( spdrdate[5] == SpiderMonth[i][4] ) ) ) {
      if ( checkval( spdrdate[0], spdrdate[1], 1, SpiderMonth[i][5] ) ) break;
      m = i + 1; break;
    }
  }
  if ( ( m == 0 )
    || checkval( spdrtime[0], spdrtime[1], 1, 23 )
    || checkval( spdrtime[3], spdrtime[4], 1, 59 )
    || checkval( spdrtime[6], spdrtime[7], 1, 59 ) ) {
    return;
  }

  if ( ( spdrdate[9]  < '0' ) || ( spdrdate[9]  > '9' )
    || ( spdrdate[10] < '0' ) || ( spdrdate[10] > '9' ) ) {
    if ( spdrdate[7]  < '7' ) {
      buf[0] = '2';
      buf[1] = '0';
    } else {
      buf[0] = '1';
      buf[1] = '9';
    }
    buf[2] = spdrdate[7];
    buf[3] = spdrdate[8];
  } else {
    buf[0] = spdrdate[7];
    buf[1] = spdrdate[8];
    buf[2] = spdrdate[9];
    buf[3] = spdrdate[10];
  }
  buf[4] = '0' + m / 10;
  buf[5] = '0' + m % 10;
  buf[6] = spdrdate[0];
  buf[7] = spdrdate[1];

  buf[8]  = spdrtime[0];
  buf[9]  = spdrtime[1];
  buf[10] = spdrtime[3];
  buf[11] = spdrtime[4];
  buf[12] = spdrtime[6];
  buf[13] = spdrtime[7];
  buf[14] = 0;

  if ( StringParseDateTime( buf, NULL, time, NULL ) ) {
    memset( time, 0, sizeof(Time) );
  }

}


static Status SpiderMetaCopy
              (Imageio *imageio)

{
  SpiderMeta *meta = imageio->meta;
  SpiderHeader *hdr = &meta->header;
  void (*cvt)( Size, const void *, void * );
  Index xlow = 0, ylow = 0, zlow = 0;
  Size nrec, reclen;

  /* consistency and feature checks */
  if ( hdr->istack != 0 ) {
    return pushexception( E_SPIDERIO_STACK );
  }
  switch ( (int)rint( hdr->iform ) ) {
    case SPIDER_OPENFLAG: {
      /* file was not closed properly */
      return pushexception( E_IMAGEIO_DATA );
    }
    case SPIDER_FMT_2D: {
      imageio->dim = 2;
      imageio->eltype = TypeReal32;
      imageio->attr = ImageRealspc;
      cvt = Swap32;
      break;
    }
    case SPIDER_FMT_3D: {
      imageio->dim = 3;
      imageio->eltype = TypeReal32;
      imageio->attr = ImageRealspc;
      cvt = Swap32;
      break;
    }
    case SPIDER_FMT_2D_FOU_ODD: {
      imageio->dim = 2;
      imageio->eltype = TypeCmplx32;
      imageio->attr = ImageFourspc | ImageSymHerm | ImageNodd;
      ylow = -(Index)( hdr->nrow / 2 );
      cvt = Swap32;
      break;
    }
    case SPIDER_FMT_2D_FOU_EVEN: {
      imageio->dim = 2;
      imageio->eltype = TypeCmplx32;
      imageio->attr = ImageFourspc | ImageSymHerm;
      ylow = -(Index)( hdr->nrow / 2 );
      cvt = Swap32;
      break;
    }
    case SPIDER_FMT_3D_FOU_ODD: {
      imageio->dim = 3;
      imageio->eltype = TypeCmplx32;
      imageio->attr = ImageFourspc | ImageSymHerm | ImageNodd;
      ylow = -(Index)( hdr->nrow / 2 );
      zlow = -(Index)( hdr->nslice / 2 );
      cvt = Swap32;
      break;
    }
    case SPIDER_FMT_3D_FOU_EVEN: {
      imageio->dim = 3;
      imageio->eltype = TypeCmplx32;
      imageio->attr = ImageFourspc | ImageSymHerm;
      ylow = -(Index)( hdr->nrow / 2 );
      zlow = -(Index)( hdr->nslice / 2 );
      cvt = Swap32;
      break;
    }
    default: return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_FMTERR ) );
  }

  if ( ( cvt != NULL ) && ( imageio->iostat & ImageioByteSwap ) ) {
    imageio->cvtcount = TypeGetCount( imageio->eltype );
    imageio->rdcvt = cvt;
    imageio->wrcvt = cvt;
  }

  /* set size after type */
  meta->len[1] = 1; meta->low[1] = 0;
  meta->len[2] = 1; meta->low[2] = 0;
  meta->len[0] = hdr->nsam;
  meta->low[0] = xlow;
  if ( imageio->dim > 1 ) {
    meta->len[1] = hdr->nrow;
    meta->low[1] = ylow;
    if ( imageio->dim > 2 ) {
      meta->len[2] = hdr->nslice;
      meta->low[2] = zlow;
    }
  }
  imageio->len = meta->len;
  imageio->low = meta->low;

  if ( ArrayOffset( imageio->dim, imageio->len, TypeGetSize( imageio->eltype ), &imageio->arrsize ) ) {
    return pushexception( E_IMAGEIO_BIG );
  }

  /* file offset */
  nrec = hdr->labrec;
  reclen = hdr->lenbyt;
  meta->headersize = hdr->labbyt;
  if ( meta->headersize != nrec * reclen ) {
    return exception( E_SPIDERIO_HDR );
  }
  imageio->offset = meta->headersize;

  SpiderToTime( hdr->cdat, hdr->ctim, &meta->cre );

  return E_NONE;

}


extern Status SpiderOld
              (Imageio *imageio)

{
  SpiderMeta *meta;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_SPIDERIO );
  if ( runcheck && ( imageio->iostat & ImageioModeCre ) ) return pushexception( E_SPIDERIO );
  if ( runcheck && ( imageio->format == NULL ) ) return pushexception( E_SPIDERIO );
  if ( runcheck && ( imageio->format->syn == NULL ) ) return pushexception( E_SPIDERIO );

  /* meta data buffer */
  meta = malloc( sizeof(SpiderMeta) );
  if ( meta == NULL ) return pushexception( E_MALLOC );
  imageio->meta = meta;
  imageio->iostat |= ImageioAllocMeta;

  /* read header */
  status = SpiderHeaderRead( imageio, &meta->header );
  if ( exception( status ) ) return status;

  /* copy meta data */
  status=SpiderMetaCopy( imageio );
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
