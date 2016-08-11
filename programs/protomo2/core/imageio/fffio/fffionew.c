/*----------------------------------------------------------------------------*
*
*  fffionew.c  -  imageio: FFF files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "fffio.h"
#include "imageiocommon.h"
#include "imageiodefault.h"
#include "stringformat.h"
#include "exception.h"
#include "array.h"
#include "baselib.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern void FFFSetTime
            (const Time *tm,
             char *buf,
             Size len)

{
  const char sep[] = { 0, 0, 0, 0, '2' };

  if ( tm->date ) {
    StringFormatDateTime( tm, sep, &len, buf );
  } else {
    memset( buf, 0, len );
  }

}


static Status FFFMetaSet
              (Imageio *imageio)

{
  FFFMeta *meta = imageio->meta;
  FFFHeader *hdr = &meta->hdr;
  void (*cvt)( Size, const void *, void * );
  FFFImagetype type;
  Status status;

  /* init in native byte order in this implementation */
  memcpy( hdr->magic, ( imageio->iostat & ImageioBigNative ) ? FFFbigmagic : FFFltlmagic, sizeof(hdr->magic) );

  /* storage modes */
  ImageAttr attr = imageio->attr;
  hdr->kind = 0;
  if ( attr & ImageFourspc ) hdr->kind |= K_FOU;
  if ( attr & ImageSymSym ) {
    hdr->kind |= K_SYM;
    if ( attr & ImageSymConj ) hdr->kind |= K_CC;
    if ( attr & ImageSymNeg  ) hdr->kind |= K_NEG;
    if ( attr & ImageNodd    ) hdr->kind |= K_MOD2;
  } else if ( attr & ( ImageSymMask | ImageNodd ) ) {
    return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_ATTR ) );
  }

  /* check data type */
  switch ( imageio->eltype ) {
    case TypeUint8:   type = T_BYTE;   cvt = NULL;   attr = ImageSymSym; break;
    case TypeUint16:  type = T_WORD_U; cvt = Swap16; attr = ImageSymSym; break;
    case TypeUint32:  type = T_INT_U;  cvt = Swap32; attr = ImageSymSym; break;
    case TypeInt8:    type = T_BYTE_S; cvt = NULL;   attr = ImageSymSym; break;
    case TypeInt16:   type = T_WORD;   cvt = Swap16; attr = ImageSymSym; break;
    case TypeInt32:   type = T_INT;    cvt = Swap32; attr = ImageSymSym; break;
    case TypeReal32:  type = T_REAL;   cvt = Swap32; attr = ImageSymMask; break;
    case TypeImag32:  type = T_IMAG;   cvt = Swap32; attr = ImageSymMask; break;
    case TypeCmplx32: type = T_CMPLX;  cvt = Swap32; attr = ImageSymMask; break;
    case TypeRGB:     type = T_RGB;    cvt = NULL;   attr = 0; break;
    default: return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_TYPE ) );
  }
  if ( imageio->attr & ~attr & ImageSymMask ) {
    return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_ATTR ) );
  }
  hdr->type = type;
  hdr->tsize = TypeGetSize( imageio->eltype );

  if ( ( cvt != NULL ) && ( imageio->iostat & ImageioByteSwap ) ) {
    imageio->cvtcount = TypeGetCount( imageio->eltype );
    imageio->rdcvt = cvt;
    imageio->wrcvt = cvt;
  }

  /* check, allocate, and set size */
  hdr->dim = imageio->dim;
  if ( !hdr->dim ) {
    return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_DIM ) );
  }
  if ( ArrayOffset( hdr->dim, imageio->len, hdr->tsize, &imageio->arrsize ) ) {
    return pushexception( E_IMAGEIO_BIG );
  }

  status = ImageioImageAlloc( imageio, imageio->len, imageio->low );
  if ( pushexception( status ) ) return status;

  meta->dscrlen = hdr->dim * FFFdscrsize;
  meta->dscrsize = hdr->dim * sizeof(FFFArrayDscr);

  status = ImageioBufAlloc( imageio, meta->dscrsize );
  if ( pushexception( status ) ) return status;

  /* creation time */
  Time tm = TimeGet();
  FFFSetTime( &tm, hdr->cre, sizeof( hdr->cre ) );

  /* offsets */
  hdr->attr = FFFHeaderSize + meta->dscrsize;
  hdr->data = hdr->attr + sizeof(meta->attr);
  imageio->offset = hdr->data;

  return E_NONE;

}


extern Status FFFNew
              (Imageio *imageio)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( ~imageio->iostat & ImageioModeCre ) ) return pushexception( E_FFFIO );
  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_FFFIO );
  if ( runcheck && ( imageio->format == NULL ) ) return pushexception( E_FFFIO );
  if ( runcheck && ( imageio->format->syn == NULL ) ) return pushexception( E_FFFIO );

  /* meta data buffer */
  FFFMeta *meta = malloc( sizeof(FFFMeta) );
  if ( meta == NULL ) return pushexception( E_MALLOC );
  FFFMetaInit( meta );

  imageio->meta = meta;
  imageio->iostat |= ImageioAllocMeta;

  /* initialize meta data */
  status = FFFMetaSet( imageio );
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
