/*----------------------------------------------------------------------------*
*
*  tiffionew.c  -  imageio: TIFF files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tiffiocommon.h"
#include "imageiocommon.h"
#include "exception.h"
#include "array.h"
#include "baselib.h"
#include <stdlib.h>
#include <string.h>


/* functions */

static Status TiffioMetaInit
              (Imageio *imageio)

{
  TiffioMeta *meta = imageio->meta;
  uint16_t smp, bit, cnt;
  uint16_t photo = PHOTOMETRIC_MINISBLACK;
  Size dim;

  /* clear all fields */
  memset( meta, 0, sizeof(TiffioMeta) );
  meta->handle = NULL;
  meta->flags = TiffioOpt.flags & TIFFIO_DATE;

  /* check array dimension and size */
  dim = imageio->dim;
  if ( dim != 2 ) {
    return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_DIM ) );
  }
  if ( ( imageio->len[0] > INT32_MAX ) || ( imageio->len[1] > INT32_MAX ) ) {
    return pushexception( E_IMAGEIO_BIG );
  }
  if ( ArrayOffset( dim, imageio->len, TypeGetSize( imageio->eltype ), &imageio->arrsize ) ) {
    return pushexception( E_IMAGEIO_BIG );
  }
  meta->len[0] = imageio->len[0];
  meta->len[1] = imageio->len[1];
  imageio->len = meta->len;
  imageio->low = meta->low;

  /* check data type */
  switch ( imageio->eltype ) {
    case TypeUint8:   smp = SAMPLEFORMAT_UINT;   bit =  8; cnt = 1; break;
    case TypeUint16:  smp = SAMPLEFORMAT_UINT;   bit = 16; cnt = 1; break;
    case TypeUint32:  smp = SAMPLEFORMAT_UINT;   bit = 32; cnt = 1; break;
    case TypeInt8:    smp = SAMPLEFORMAT_INT;    bit =  8; cnt = 1; break;
    case TypeInt16:   smp = SAMPLEFORMAT_INT;    bit = 16; cnt = 1; break;
    case TypeInt32:   smp = SAMPLEFORMAT_INT;    bit = 32; cnt = 1; break;
    case TypeReal32:  smp = SAMPLEFORMAT_IEEEFP; bit = 32; cnt = 1; break;
    case TypeCmplx32: smp = SAMPLEFORMAT_IEEEFP; bit = 32; cnt = 2; break;
    case TypeRGB:     smp = SAMPLEFORMAT_UINT;   bit =  8; cnt = 3; photo = PHOTOMETRIC_RGB; break;
    default: return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_TYPE ) );
  }
  if ( imageio->attr & ImageFourspc ) {
    return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_DOMAIN ) );
  }
  if ( imageio->attr & ImageSymMask ) {
    return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_ATTR ) );
  }
  meta->tags.sampfmt = smp;
  meta->tags.sampsiz[0] = bit;
  meta->tags.sampsiz[1] = bit;
  meta->tags.sampsiz[2] = bit;
  meta->tags.sampnum = cnt;

  /* tiff parameters */
  if ( meta->tags.rowsperstrip == 0 ) {
    meta->tags.rowsperstrip = 1;
  }
  meta->tags.planarconfig = PLANARCONFIG_CONTIG;
  meta->tags.compression = TiffioOpt.compression;
  meta->tags.photometric = photo;
  meta->tags.resolutionunit = RESUNIT_INCH;
  meta->tags.xresolution = TiffioOpt.DPI;
  meta->tags.yresolution = TiffioOpt.DPI;

  /* orientation */
  if ( TiffioOpt.flags & TIFFIO_TRNSP ) {
    if ( TiffioOpt.flags & TIFFIO_ORI_TOP ) {
      if ( TiffioOpt.flags & TIFFIO_ORI_RIG ) {
        meta->tags.orientation = ORIENTATION_RIGHTTOP;
        meta->flags |= TIFFIO_TRNSP | TIFFIO_ORI_TOP | TIFFIO_ORI_RIG;
        imageio->iostat |= ImageioBlk | ImageioBlkTrnsp | ImageioBlkFlipY | ImageioBlkFlipX;
      } else {
        meta->tags.orientation = ORIENTATION_LEFTTOP;
        meta->flags |= TIFFIO_TRNSP | TIFFIO_ORI_TOP;
        imageio->iostat |= ImageioBlk | ImageioBlkTrnsp | ImageioBlkFlipY;
      }
    } else {
      if ( TiffioOpt.flags & TIFFIO_ORI_RIG ) {
        meta->tags.orientation = ORIENTATION_RIGHTBOT;
        meta->flags |= TIFFIO_TRNSP | TIFFIO_ORI_RIG;
        imageio->iostat |= ImageioBlk | ImageioBlkTrnsp | ImageioBlkFlipX;
      } else {
        meta->tags.orientation = ORIENTATION_LEFTBOT;
        meta->flags |= TIFFIO_TRNSP;
        imageio->iostat |= ImageioBlk | ImageioBlkTrnsp;
      }
    }
  } else {
    if ( TiffioOpt.flags & TIFFIO_ORI_TOP ) {
      if ( TiffioOpt.flags & TIFFIO_ORI_RIG ) {
        meta->tags.orientation = ORIENTATION_TOPRIGHT;
        meta->flags |= TIFFIO_ORI_TOP | TIFFIO_ORI_RIG;
        imageio->iostat |= ImageioBlk | ImageioBlkFlipY | ImageioBlkFlipX;
      } else {
        meta->tags.orientation = ORIENTATION_TOPLEFT;
        meta->flags |= TIFFIO_ORI_TOP;
        imageio->iostat |= ImageioBlk | ImageioBlkFlipY;
      }
    } else {
      if ( TiffioOpt.flags & TIFFIO_ORI_RIG ) {
        meta->tags.orientation = ORIENTATION_BOTRIGHT;
        meta->flags |= TIFFIO_ORI_RIG;
        imageio->iostat |= ImageioBlk | ImageioBlkFlipX;
      } else {
        meta->tags.orientation = ORIENTATION_BOTLEFT;
        imageio->iostat |= ImageioBlk;
      }
    }
  }

  /* creation time */
  meta->cre = TimeGet();
  meta->mod = meta->cre;

  /* file offset */
  imageio->offset = 0;

  return E_NONE;

}


extern Status TiffioNew
              (Imageio *imageio)

{
  TiffioMeta *meta;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( ~imageio->iostat & ImageioModeCre ) ) return pushexception( E_TIFFIO );
  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_TIFFIO );
  if ( runcheck && ( imageio->format == NULL ) ) return pushexception( E_TIFFIO );
  if ( runcheck && ( imageio->format->syn == NULL ) ) return pushexception( E_TIFFIO );

  /* meta data buffer */
  meta = malloc( sizeof(TiffioMeta) );
  if ( meta == NULL ) return pushexception( E_MALLOC );
  imageio->meta = meta;
  imageio->iostat |= ImageioAllocMeta;

  /* initialize meta data */
  status = TiffioMetaInit( imageio );
  if ( exception( status ) ) return status;

  /* temp buffer */
  status = ImageioBufAlloc( imageio, imageio->len[0] * TypeGetSize( imageio->eltype ) );
  if ( pushexception( status ) ) return status;

  /* error handling */
  TIFFSetWarningHandler( NULL ); /* no warning messages */
  TIFFSetErrorHandler( TiffioError );

  /* reopen tiff file */
  status = TiffioOpen( imageio );
  if ( exception( status ) ) return status;

  /* set i/o modes */
  imageio->rd = TiffioRd;
  imageio->wr = TiffioWr;
  status = ImageioModeInit( imageio );
  if ( exception( status ) ) return status;
  switch ( imageio->iocap ) {
    case ImageioCapLib: break;
    default: imageio->rd = NULL; imageio->wr = NULL;
  }

  /* write header */
  status = imageio->format->syn( imageio );
  if ( exception( status ) ) return status;

  return E_NONE;

}
