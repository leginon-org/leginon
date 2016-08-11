/*----------------------------------------------------------------------------*
*
*  ccp4ioold.c  -  imageio: CCP4 files
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


/* functions */

static Status CCP4MetaCopy
              (Imageio *imageio)

{
  CCP4Meta *meta = imageio->meta;
  CCP4Header *hdr = &meta->header;
  void (*cvt)( Size, const void *, void * );
  ImageAttr attr;
  Type type;

  /* consistency and feature checks */
  if ( hdr->mode == CCP4_OPENFLAG ) {
    /* file was not closed properly */
    return pushexception( E_IMAGEIO_DATA );
  }
  if ( ( hdr->mapc != 1 ) || ( hdr->mapr != 2 ) || ( hdr->maps != 3 ) ) {
    return pushexception( E_CCP4IO_AXIS );
  }

  /* new label index */
  meta->ilab = hdr->nlab;

  /* set data type */
  switch ( hdr->mode ) {
    case CCP4_BYTE:   type = TypeInt8;    cvt = NULL; break;
    case CCP4_INT16:  type = TypeInt16;   cvt = Swap16; break;
    case CCP4_REAL:   type = TypeReal32;  cvt = Swap32; break;
    case CCP4_CMPLX:  type = TypeCmplx32; cvt = Swap32; break;
    case CCP4_UINT16: type = TypeUint16;  cvt = Swap16; break;
    default: return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_FMTERR ) );
  }
  meta->mode = hdr->mode;
  imageio->eltype = type;

  if ( ( cvt != NULL ) && ( imageio->iostat & ImageioByteSwap ) ) {
    imageio->cvtcount = TypeGetCount( type );
    imageio->rdcvt = cvt;
    imageio->wrcvt = cvt;
  }

  if ( ( type == TypeCmplx32 ) && ( hdr->nx != hdr->mx ) ) {
    attr = ImageFourspc; /* Fourier space */
    if ( hdr->mx / 2 + 1 == hdr->nx ) {
      /* start values may not be set properly
      hdr->nxstart = 0;
      hdr->nystart = -(int32_t)hdr->ny/2;
      hdr->nzstart = -(int32_t)hdr->nz/2;
      end comment */
      attr |= ImageSymHerm;
      if ( hdr->mx % 2 ) attr |= ImageNodd;
    } else {
      return pushexception( E_CCP4IO_FOU );
    }
  } else {
    attr = ImageRealspc; /* real space */
  }
  imageio->attr = attr;

  /* set size after type */
  meta->len[1] = 1; meta->low[1] = 0;
  meta->len[2] = 1; meta->low[2] = 0;
  imageio->dim = 1;
  meta->len[0] = hdr->nx;
  meta->low[0] = hdr->nxstart;
  if ( hdr->ny > 1 ) {
    imageio->dim = 2;
    meta->len[1] = hdr->ny;
    meta->low[1] = hdr->nystart;
    if ( hdr->nz > 1 ) {
      imageio->dim = 3;
      meta->len[2] = hdr->nz;
      meta->low[2] = hdr->nzstart;
    }
  }
  imageio->len = meta->len;
  imageio->low = meta->low;

  if ( ArrayOffset( imageio->dim, imageio->len, TypeGetSize( imageio->eltype ), &imageio->arrsize ) ) {
    return pushexception( E_IMAGEIO_BIG );
  }

  /* file offset */
  imageio->offset = CCP4HeaderSize + hdr->nsymbt;

  return E_NONE;

}


extern Status CCP4Old
              (Imageio *imageio)

{
  CCP4Meta *meta;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_CCP4IO );
  if ( runcheck && ( imageio->iostat & ImageioModeCre ) ) return pushexception( E_CCP4IO );
  if ( runcheck && ( imageio->format == NULL ) ) return pushexception( E_CCP4IO );
  if ( runcheck && ( imageio->format->syn == NULL ) ) return pushexception( E_CCP4IO );

  /* meta data buffer */
  meta = malloc( sizeof(CCP4Meta) );
  if ( meta == NULL ) return pushexception( E_MALLOC );
  imageio->meta = meta;
  imageio->iostat |= ImageioAllocMeta;

  /* read header */
  status = CCP4HeaderRead( imageio, &meta->header );
  if ( exception( status ) ) return status;

  /* copy meta data */
  status=CCP4MetaCopy( imageio );
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
