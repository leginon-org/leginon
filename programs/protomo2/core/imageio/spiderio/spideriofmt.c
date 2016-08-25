/*----------------------------------------------------------------------------*
*
*  spideriofmt.c  -  imageio: spider files
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
#include "exception.h"
#include "baselib.h"
#include <math.h>


/* functions */

static Status SpiderFmtCheck
              (const SpiderHeader *hdr,
               const Imageio *imageio)

{
  Size dim = 0;
  Type type;

  Size nz = hdr->nslice;
  Size ny = hdr->nrow;
  Size nx = hdr->nsam;
  Size iform = hdr->iform;

  if ( ( hdr->nslice != nz ) || ( hdr->nslice < 0 ) ) return E_IMAGEIO_FORMAT;
  if ( ( hdr->nrow   != ny ) || ( hdr->nrow   < 0 ) ) return E_IMAGEIO_FORMAT;
  if ( ( hdr->nsam   != nx ) || ( hdr->nsam   < 0 ) ) return E_IMAGEIO_FORMAT;
  if ( hdr->iform  != iform ) return E_IMAGEIO_FORMAT;
  switch ( iform ) {
    case SPIDER_OPENFLAG:                 type = TypeUndef;  break;
    case SPIDER_FMT_2D:          dim = 2; type = TypeReal32; break;
    case SPIDER_FMT_3D:          dim = 3; type = TypeReal32; break;
    case SPIDER_FMT_2D_FOU_ODD:
    case SPIDER_FMT_2D_FOU_EVEN: dim = 2; type = TypeCmplx32; break;
    case SPIDER_FMT_3D_FOU_ODD:
    case SPIDER_FMT_3D_FOU_EVEN: dim = 3; type = TypeCmplx32; break;
    default: return E_IMAGEIO_FORMAT;
  }

  if ( imageio->iostat & ImageioFmtAuto ) {

    Size nrec, reclen, hdrlen;
    if ( ( hdr->labrec != floorf( hdr->labrec ) ) || ( hdr->labrec <= 0 ) ) return E_IMAGEIO_FORMAT;
    if ( ( hdr->labbyt != floorf( hdr->labbyt ) ) || ( hdr->labbyt <= 0 ) ) return E_IMAGEIO_FORMAT;
    if ( ( hdr->lenbyt != floorf( hdr->lenbyt ) ) || ( hdr->lenbyt <= 0 ) ) return E_IMAGEIO_FORMAT;
    nrec = hdr->labrec;
    reclen = hdr->lenbyt;
    hdrlen = hdr->labbyt;
    if ( hdrlen != nrec * reclen ) return E_IMAGEIO_FORMAT;

    Offset size = nx * TypeGetSize( type );
    if ( dim > 1 ) size *= ny;
    if ( dim > 2 ) size *= nz;
    if ( size <= 0 ) return E_IMAGEIO_FORMAT;
    size += hdrlen;
    if ( size < 0 ) return E_IMAGEIO_FORMAT;
    if ( dim && ( FileioGetSize( imageio->fileio ) < size ) ) return E_IMAGEIO_FORMAT;

  }

  return E_NONE;

}


extern Status SpiderFmt
              (Imageio *imageio)

{
  Fileio *fileio;
  SpiderHeader hdr;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  fileio = imageio->fileio;
  if ( runcheck && ( fileio == NULL ) ) return pushexception( E_SPIDERIO );
  if ( runcheck && ( FileioGetMode( fileio ) & IOCre ) ) return pushexception( E_SPIDERIO );

  /* read header in native byte order and check */
  ImageioSetEndian( &imageio->iostat, ~ImageioByteSwap );
  status = SpiderHeaderRead( imageio, &hdr );
  if ( exception( status ) ) return status;
  status = SpiderFmtCheck( &hdr, imageio );
  if ( !status ) return E_NONE;

  /* non-native check */
  ImageioSetEndian( &imageio->iostat, ImageioByteSwap );
  status = SpiderHeaderRead( imageio, &hdr );
  if ( exception( status ) ) return status;
  status = SpiderFmtCheck( &hdr, imageio );
  if ( !status ) return E_NONE;

  /* checks failed */
  pushexception( status );

  return status;

}
