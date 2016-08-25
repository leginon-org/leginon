/*----------------------------------------------------------------------------*
*
*  ccp4ionew.c  -  imageio: CCP4 files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "ccp4io.h"
#include "imageiocommon.h"
#include "imageiodefault.h"
#include "exception.h"
#include "array.h"
#include "baselib.h"
#include <stdlib.h>
#include <string.h>


/* constants */

/* machine architecture */

/* class info codes for int */
#define DFNTI_MBO       1       /* Motorola byte order 2's compl */
#define DFNTI_IBO       4       /* Intel byte order 2's compl */

/* class info codes for float */
#define DFNTF_BEIEEE    1       /* big endian IEEE (canonical) */
#define DFNTF_VAX       2       /* Vax format */
#define DFNTF_CONVEXNATIVE 5    /* Convex native floats */
#define DFNTF_LEIEEE    4       /* little-endian IEEE format */


/* functions */

static Status CCP4MetaInit
              (Imageio *imageio)

{
  CCP4Meta *meta = imageio->meta;
  CCP4Header *hdr = &meta->header;
  void (*cvt)( Size, const void *, void * );
  ImageAttr attr;
  Size dim, len;

  /* clear all fields */
  memset( meta, 0, sizeof(CCP4Meta) );
  meta->mode = CCP4_UNDEF;
  meta->ilab = UINT32_MAX;

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
    case TypeInt8:    meta->mode = CCP4_BYTE;  attr = ImageRealspc; cvt = NULL; break;
    case TypeInt16:   meta->mode = CCP4_INT16; attr = ImageRealspc; cvt = Swap16; break;
    case TypeReal32:  meta->mode = CCP4_REAL;  attr = ImageRealspc; cvt = Swap32; break;
    case TypeCmplx32: meta->mode = CCP4_CMPLX; attr = ImageFourspc | ImageSymHerm; cvt = Swap32; break;
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

  /* CCP4 header */

  hdr->nx = hdr->mx = meta->len[0];
  hdr->ny = hdr->my = meta->len[1];
  hdr->nz = hdr->mz = meta->len[2];
  if ( attr & ImageSymSym ) {
    hdr->mx = 2 * ( hdr->mx - 1 );
    if ( attr & ImageNodd ) {
      hdr->mx++;
    }
  }
  hdr->mode = meta->mode;
  hdr->nxstart = meta->low[0];
  hdr->nystart = meta->low[1];
  hdr->nzstart = meta->low[2];

  /* fill some other header fields */
  /* cell */
  hdr->a = hdr->mx; 
  hdr->b = hdr->my;
  hdr->c = hdr->mz;
  hdr->alpha = hdr->beta = hdr->gamma = 90;
  /* axis order */
  hdr->mapc = 1;
  hdr->mapr = 2;
  hdr->maps = 3;
  /* space group */
  hdr->ispg = 1;
  hdr->nsymbt = 0;
  /* map identifier */
  if ( *imageio->format->version.ident == 'C' ) {
    hdr->map[0] = 'M'; hdr->map[1] = 'A'; hdr->map[2] = 'P'; hdr->map[3] = ' ';
  }
  /* machine stamp */
  if ( *imageio->format->version.ident == 'C' ) {
    unsigned char *machst = (unsigned char *)&hdr->machst;
    uint16_t nativeIT, nativeFT;
    if ( imageio->iostat & ImageioBigNative ) {
      /* big endian, 2's complement, IEEE float */
      nativeIT = DFNTI_MBO;
      nativeFT = DFNTF_BEIEEE;
    } else {
      /* little endian, 2's complement, IEEE float */
      nativeIT = DFNTI_IBO;
      nativeFT = DFNTF_LEIEEE;
    }
    machst[0] = nativeFT | ( nativeFT << 4 );
    machst[1] = 1 | ( nativeIT << 4 );
    machst[2] = machst[3] = 0;
  }
  /* label */
  len = sizeof( hdr->label[0] );
  ImageioGetVersion( " created  by ", CCP4ioVers, &len, hdr->label[0] );
  hdr->nlab = 1;

  /* file offset */
  imageio->offset = CCP4HeaderSize + hdr->nsymbt;

  return E_NONE;

}


extern Status CCP4New
              (Imageio *imageio)

{
  CCP4Meta *meta;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( ~imageio->iostat & ImageioModeCre ) ) return pushexception( E_CCP4IO );
  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_CCP4IO );
  if ( runcheck && ( imageio->format == NULL ) ) return pushexception( E_CCP4IO );
  if ( runcheck && ( imageio->format->syn == NULL ) ) return pushexception( E_CCP4IO );

  /* meta data buffer */
  meta = malloc( sizeof(CCP4Meta) );
  if ( meta == NULL ) return pushexception( E_MALLOC );
  imageio->meta = meta;
  imageio->iostat |= ImageioAllocMeta;

  /* initialize meta data */
  status = CCP4MetaInit( imageio );
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
