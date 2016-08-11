/*----------------------------------------------------------------------------*
*
*  suprimionew.c  -  imageio: suprim files
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


static Status SuprimMetaInit
              (Imageio *imageio)

{
  SuprimMeta *meta = imageio->meta;
  SuprimHeader *hdr = &meta->header;
  void (*cvt)( Size, const void *, void * );
  char *tr, *trnew, trend[] = "none";
  Size ntr, ntrend = strlen( trend ) + 1;
  const char cremsg[] = " created  by ";
  const char modmsg[] = " modified by ";
  int32_t *nr, *count;
  int32_t intern;
  Size dim, len;
  ImageAttr attr;

  /* clear all fields */
  memset( meta, 0, sizeof(SuprimMeta) );
  meta->mod = NULL;

  /* check and set array dimension and size */
  dim = imageio->dim;
  if ( ( dim < 2 ) || ( dim > 3 ) ) {
    return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_DIM ) );
  }
  if ( ArrayOffset( dim, imageio->len, TypeGetSize( imageio->eltype ), &imageio->arrsize ) ) {
    return pushexception( E_IMAGEIO_BIG );
  }
  meta->len[2] = 1;
  meta->low[2] = 0;
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
    case TypeUint8:   intern = SuprimUint8;   attr = ImageRealspc; cvt = NULL; break;
    case TypeInt16:   intern = SuprimInt16;   attr = ImageRealspc; cvt = Swap16; break;
    case TypeInt32:   intern = SuprimInt32;   attr = ImageRealspc; cvt = Swap32; break;
    case TypeReal32:  intern = SuprimReal32;  attr = ImageRealspc; cvt = Swap32; break;
    case TypeCmplx32: intern = SuprimCmplx32; attr = ImageFourspc | ImageSymHerm; cvt = Swap32; break;
    case TypeRGB:     intern = SuprimRGB;     attr = ImageRealspc; cvt = NULL; break;
    default: return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_TYPE ) );
  }
  if ( ( attr ^ imageio->attr ) & ImageFourspc ) {
    return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_DOMAIN ) );
  }
  if ( ( imageio->attr & ImageSymMask ) != ( attr & ImageSymMask ) ) {
    return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_ATTR ) );
  }
  attr = imageio->attr;

  if ( ( cvt != NULL ) && ( imageio->iostat & ImageioByteSwap ) ) {
    imageio->cvtcount = TypeGetCount( imageio->eltype );
    imageio->rdcvt = cvt;
    imageio->wrcvt = cvt;
  }

  /* Suprim header */

  hdr->version = 0;
  hdr->nrow = meta->len[1];
  hdr->ncol = meta->len[0];
  hdr->format = TypeGetSize( imageio->eltype );
  hdr->intern = intern;
  /* hdr->filetype */
  /* hdr->min */
  /* hdr->max */
  /* hdr->mean */
  /* hdr->sd */
  hdr->reg[NSLICES].l = meta->len[2];

  /* trace is not swapped because new file is always written in native byte order */
  tr = hdr->trace;
  ntr = sizeof( hdr->trace ) - 1;
  /* trace count */
  nr = (int32_t *)tr;
  tr += sizeof( int32_t ); ntr -= sizeof( int32_t );
  /* 1st */
  count = (int32_t *)tr;
  tr += sizeof( int32_t ); ntr -= sizeof( int32_t );
  trnew = ImageioGetVersion( cremsg, SuprimioVers, &ntr, tr );
  *trnew++ = 0; ntr--;
  *count = trnew-tr; tr = trnew;
  if ( ntr < sizeof( int32_t ) + 20 + 13 + 16 + ntrend ) {
    return pushexception( E_SUPRIMIO );
  }
  /* 2nd */
  count = (int32_t *)tr;
  tr += sizeof( int32_t ); ntr -= sizeof( int32_t );
  meta->mod = tr;
  trnew = ImageioGetVersion( modmsg, SuprimioVers, &ntr, tr );
  *trnew++ = 0; ntr--;
  *count = trnew - tr; tr = trnew;
  len = strstr( meta->mod, modmsg ) - meta->mod;
  meta->nmod = ( len > 1 ) ? ( len - 1 ) : 0;
  /* 3rd */
  count = (int32_t *)tr; *count = ntrend;
  tr += sizeof( int32_t ); ntr -= sizeof( int32_t );
  strcpy( tr, trend );
  tr += ntrend; ntr -= ntrend;
  /* set number (minus 2) */
  *nr = 1;
  /* end marker 0 */
  nr = (int32_t *)tr;
  tr += sizeof( int32_t ); ntr -= sizeof( int32_t );
  *nr = 0;

  /* file offset */
  meta->headersize = SuprimTraceOffs + ( tr - hdr->trace );
  imageio->offset = meta->headersize;

  return E_NONE;

}


extern Status SuprimNew
              (Imageio *imageio)

{
  SuprimMeta *meta;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( ~imageio->iostat & ImageioModeCre ) ) return pushexception( E_SUPRIMIO );
  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_SUPRIMIO );
  if ( runcheck && ( imageio->format == NULL ) ) return pushexception( E_SUPRIMIO );
  if ( runcheck && ( imageio->format->syn == NULL ) ) return pushexception( E_SUPRIMIO );

  /* meta data buffer */
  meta = malloc( sizeof(SuprimMeta) );
  if ( meta == NULL ) return pushexception( E_MALLOC );
  imageio->meta = meta;
  imageio->iostat |= ImageioAllocMeta;

  /* initialize meta data */
  status = SuprimMetaInit( imageio );
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
