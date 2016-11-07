/*----------------------------------------------------------------------------*
*
*  emionew.c  -  imageio: em files
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
/* for user name */
#include <pwd.h>
#include <unistd.h>
#include <sys/types.h>


/* functions */

static void EMgetusername
            (char *buf,
             Size buflen)

{
#define pwbuflen 256
  char pwbuf[pwbuflen];
  struct passwd pw;
  struct passwd *ptr;

  if ( getpwuid_r( getuid(), &pw, pwbuf, pwbuflen, &ptr ) ) {
    pw.pw_name = "noname";
  }
  strncpy( buf, pw.pw_name, buflen );
  buf[buflen-1] = 0;

}


static Status EMMetaInit
              (Imageio *imageio)

{
  EMMeta *meta = imageio->meta;
  EMHeader *hdr = &meta->header;
  void (*cvt)( Size, const void *, void * );
  EMType type;
  ImageAttr attr;
  Size dim, len;

  /* clear all fields */
  memset( meta, 0, sizeof(EMMeta) );
  meta->headersize = EMHeaderSize;

  /* check and set array dimension and size */
  dim = imageio->dim;
  if ( !dim || ( dim > 3 ) ) {
    return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_DIM ) );
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
    case TypeUint8:   type = EMbyte;   attr = ImageRealspc; cvt = NULL; break;
    case TypeInt16:   type = EMint16;  attr = ImageRealspc; cvt = Swap16; break;
    case TypeInt32:   type = EMint32;  attr = ImageRealspc; cvt = Swap32; break;
    case TypeReal32:  type = EMfloat;  attr = ImageRealspc; cvt = Swap32; break;
    case TypeReal64:  type = EMdouble; attr = ImageRealspc; cvt = Swap64; break;
    case TypeCmplx32: type = EMcmplx;  attr = ImageFourspc | ImageSymHerm; cvt = Swap32; break;
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

  /* EM header */

  hdr->machine = ( imageio->iostat & ImageioBigNative ) ? EMSGI : EMPC;
  hdr->datatype = type;
  if ( imageio->attr & ImageSymSym ) {
    hdr->nx = 2 * ( meta->len[0] - 1 );
    if ( attr & ImageNodd ) {
      hdr->nx++;
    }
  } else {
    hdr->nx = meta->len[0];
  }
  hdr->ny = meta->len[1];
  hdr->nz = meta->len[2];
  len = sizeof( hdr->username );
  EMgetusername( hdr->username, len );
  len = sizeof( hdr->extra );
  ImageioGetVersion( " created  by ", EMioVers, &len, hdr->extra );

  /* file offset */
  imageio->offset = meta->headersize;

  return E_NONE;

}



extern Status EMNew
              (Imageio *imageio)

{
  EMMeta *meta;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( ~imageio->iostat & ImageioModeCre ) ) return pushexception( E_EMIO );
  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_EMIO );
  if ( runcheck && ( imageio->format == NULL ) ) return pushexception( E_EMIO );
  if ( runcheck && ( imageio->format->syn == NULL ) ) return pushexception( E_EMIO );

  /* meta data buffer */
  meta = malloc( sizeof(EMMeta) );
  if ( meta == NULL ) return pushexception( E_MALLOC );
  imageio->meta = meta;
  imageio->iostat |= ImageioAllocMeta;

  /* initialize meta data */
  status = EMMetaInit( imageio );
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
