/*----------------------------------------------------------------------------*
*
*  fffioold.c  -  imageio: FFF files
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
#include "exception.h"
#include "array.h"
#include "baselib.h"
#include <stdlib.h>
#include <string.h>


/* functions */

static Offset FFFGetDscr
              (Size dim,
               Size *len,
               Index *low,
               const int32_t *fffdscr)

{
  Offset size = 0;

  if ( dim ) {
    size = 1;
    fffdscr += 4 * dim;
    while ( dim-- ) {
      --fffdscr;
      *len = *--fffdscr;
      --fffdscr;
      *low = *--fffdscr;
      if ( MulOffset( size, *len, NULL ) ) {
        size = 0;
      } else {
        size *= *len;
      }
      len++; low++;
    }
  }
  return size;

}


static Status FFFMetaCopy
              (Imageio *imageio)

{
  uint16_t major = imageio->format->version.major;
  uint16_t minor = imageio->format->version.minor;
  FFFMeta *meta = imageio->meta;
  FFFHeader *hdr = &meta->hdr;
  uint8_t *magic = hdr->magic;
  void (*cvt)( Size, const void *, void * );
  Type type;
  Status status;

  /* consistency and feature checks */
  if ( ( magic[8] || magic[9] ) && major && minor ) {
    /* file was not closed properly */
    return pushexception( E_IMAGEIO_DATA );
  }

  /* check data type */
  switch ( hdr->type ) {
    case T_LOGIC:
    case T_BYTE:   type = TypeUint8;   cvt = NULL;   break;
    case T_WORD_U: type = TypeUint16;  cvt = Swap16; break;
    case T_INT_U:  type = TypeUint32;  cvt = Swap32; break;
    case T_BYTE_S: type = TypeInt8;    cvt = NULL;   break;
    case T_WORD:   type = TypeInt16;   cvt = Swap16; break;
    case T_INT:    type = TypeInt32;   cvt = Swap32; break;
    case T_REAL:   type = TypeReal32;  cvt = Swap32; break;
    case T_IMAG:   type = TypeImag32;  cvt = Swap32; break;
    case T_CMPLX:  type = TypeCmplx32; cvt = Swap32; break;
    case T_RGB:    type = TypeRGB;     cvt = NULL;   break;
    default: return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_TYPE ) );
  }
  Size elsize = TypeGetSize( type );
  if ( elsize != hdr->tsize ) {
    return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_FMTERR ) );
  }
  imageio->eltype = type;

  if ( ( cvt != NULL ) && ( imageio->iostat & ImageioByteSwap ) ) {
    imageio->cvtcount = TypeGetCount( type );
    imageio->rdcvt = cvt;
    imageio->wrcvt = cvt;
  }

  /* real or Fourier space */
  ImageAttr attr = ( hdr->kind & K_FOU ) ? ImageFourspc : ImageRealspc;

  /* storage mode */
  if ( hdr->kind & K_SYM ) {
    /* symmetric */
    attr |= ImageSymSym;
    if ( hdr->kind & K_CC ) {
      /* hermitian */
      attr |= ImageSymConj;
    }
    if ( hdr->kind & K_NEG ) {
      /* odd or antiherm */
      attr |= ImageSymNeg;
    }
    if ( hdr->kind & K_MOD2 ) {
      /* uneven number of samples in x */
      attr |= ImageNodd;
    }
  }
  imageio->attr = attr;

  /* dimension and size */
  imageio->dim = hdr->dim;

  status = ImageioImageAlloc( imageio, NULL, NULL );
  if ( pushexception( status ) ) return status;

  if ( !FFFGetDscr( imageio->dim, imageio->len, imageio->low, imageio->buf ) ) {
    return pushexception( E_IMAGEIO_FMTERR );
  }

  if ( ArrayOffset( imageio->dim, imageio->len, elsize, &imageio->arrsize ) ) {
    return pushexception( E_IMAGEIO_BIG );
  }

  /* file offsets */
  Offset filesize = imageio->arrsize * elsize;
  if ( ( OffsetMax - filesize ) < hdr->data ) return pushexception( E_INTOVFL );
  filesize += hdr->data;
  if ( meta->i3meta ) {
    if ( meta->attr > 0 ) {
      if ( ( meta->attr % 8 ) || ( meta->attr < filesize ) ) {
        return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_FMTERR ) );
      }
    }
  } else {
    if ( hdr->attr && ( hdr->attr > hdr->data ) ) {
      if ( hdr->attr < filesize ) return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_FMTERR ) );
    }
  }
  imageio->offset = hdr->data;

  return E_NONE;

}


extern Status FFFOld
              (Imageio *imageio)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_FFFIO );
  if ( runcheck && ( imageio->iostat & ImageioModeCre ) ) return pushexception( E_FFFIO );
  if ( runcheck && ( imageio->iostat & ImageioModeWr ) && ( imageio->format->syn == NULL ) ) return pushexception( E_FFFIO );
  if ( runcheck && ( imageio->format == NULL ) ) return pushexception( E_FFFIO );

  /* header buffer */
  FFFMeta *meta = malloc( sizeof(FFFMeta) );
  if ( meta == NULL ) return pushexception( E_MALLOC );
  FFFMetaInit( meta );

  imageio->meta = meta;
  imageio->iostat |= ImageioAllocMeta;

  /* read header */
  status = FFFMetaRead( imageio, meta );
  if ( exception( status ) ) return status;

  /* dscr buffer */
  status = ImageioBufAlloc( imageio, meta->dscrsize );
  if ( pushexception( status ) ) return status;

  /* read dscr */
  status = FileioRead( imageio->fileio, FFFHeaderSize, meta->dscrsize, imageio->buf );
  if ( pushexception( status ) ) return status;

  /* swap if non-native byte order */
  if ( imageio->iostat & ImageioByteSwap ) {
    Swap32( meta->dscrlen , imageio->buf, imageio->buf );
  }

  /* copy meta data */
  status = FFFMetaCopy( imageio );
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
