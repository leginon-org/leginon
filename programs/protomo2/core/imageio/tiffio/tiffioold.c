/*----------------------------------------------------------------------------*
*
*  tiffioold.c  -  imageio: TIFF files
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
#include "stringparse.h"
#include "exception.h"
#include "array.h"
#include "baselib.h"
#include <stdlib.h>
#include <string.h>


/* functions */

static Status TiffioMetaCopy
              (Imageio *imageio)

{
  TiffioMeta *meta = imageio->meta;
  TIFF *handle = meta->handle;
  uint16_t compr = COMPRESSION_NONE;
  uint16_t photo = PHOTOMETRIC_MINISBLACK; /* when undefined */
  uint16_t fillo = 0; /* when undefined */
  uint16_t runit = 0; /* when undefined */
  uint16_t orient = ORIENTATION_TOPLEFT;
  uint16_t planar = PLANARCONFIG_CONTIG;
  float xres = 0, yres = 0;
  uint32_t nx = 0, ny = 0;
  uint32_t tx = 0, ty = 0;
  uint32_t rps = 0;
  char *timestr=NULL;
  Type type = 0;
  int flags = 0;
  int iostat = 0;

  /* number of samples */
  meta->tags.sampnum = 1;
  TIFFGetField( handle, TIFFTAG_SAMPLESPERPIXEL, &meta->tags.sampnum );
  if ( !meta->tags.sampnum  || ( meta->tags.sampnum > 3 ) ) {
    return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_FMTERR ) );
  }

  /* sample size and format */
  meta->tags.sampsiz[0] = 8;
  meta->tags.sampsiz[1] = 8;
  meta->tags.sampsiz[2] = 8;
  TIFFGetField( handle, TIFFTAG_BITSPERSAMPLE, meta->tags.sampsiz );
  meta->tags.sampfmt = SAMPLEFORMAT_UINT;
  TIFFGetField( handle, TIFFTAG_SAMPLEFORMAT, &meta->tags.sampfmt );
  switch ( meta->tags.sampfmt ) {
    case SAMPLEFORMAT_INT: {
      if ( TiffioOpt.flags & TIFFIO_SMP_UINT ) {
        flags |= TIFFIO_SMP_UINT;
      } else {
        flags |= TIFFIO_SMP_INT;
      }
    }
    case SAMPLEFORMAT_VOID:
    case SAMPLEFORMAT_UINT: {
      if ( TiffioOpt.flags & TIFFIO_SMP_SGN ) {
        flags |= TIFFIO_SMP_SGN;
      }
      if ( TiffioOpt.flags & TIFFIO_SMP_INT ) {
        flags |= TIFFIO_SMP_INT;
      }
      /* read regardless */
      if ( meta->tags.sampnum == 1 ) {
        if ( meta->tags.sampsiz[0] == 8 ) {
          if ( flags & TIFFIO_SMP_INT ) {
            type = TypeInt8;
          } else {
            type = TypeUint8;
          }
        } else if ( meta->tags.sampsiz[0] == 16 ) {
          if ( flags & TIFFIO_SMP_INT ) {
            type = TypeInt16;
          } else {
            type = TypeUint16;
          }
        } else if ( meta->tags.sampsiz[0] == 32 ) {
          if ( flags & TIFFIO_SMP_INT ) {
            type = TypeInt32;
          } else {
            type = TypeUint32;
          }
        }
      } else if ( meta->tags.sampnum == 3 ) {
        /* only sampsiz[0] seems to be used */
        /* if ( ( meta->tags.sampsiz[0] == 8 ) && ( meta->tags.sampsiz[1] == 8 ) && ( meta->tags.sampsiz[2] == 8 ) ) { */
        if ( meta->tags.sampsiz[0] == 8 ) {
          type = TypeRGB;
        }
      }
      break;
    }
    case SAMPLEFORMAT_IEEEFP: {
      if ( meta->tags.sampnum == 1 ) {
        if ( meta->tags.sampsiz[0] == 32 ) {
          type = TypeReal32;
        }
      } else if ( meta->tags.sampnum == 2 ) {
        if ( meta->tags.sampsiz[0] == 32 ) {
          type = TypeCmplx32;
        }
      }
      break;
    }
  }
  if ( !type ) return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_TYPE ) );
  imageio->eltype = type;
  imageio->attr = ImageRealspc;

  /* read other tags */
  TIFFGetField( handle, TIFFTAG_COMPRESSION, &compr );
  meta->tags.compression = compr;

  TIFFGetField( handle, TIFFTAG_PHOTOMETRIC, &photo );
  meta->tags.photometric = photo;

  TIFFGetField( handle, TIFFTAG_FILLORDER, &fillo );
  meta->tags.fillorder = fillo;

  TIFFGetField( handle, TIFFTAG_RESOLUTIONUNIT, &runit );
  meta->tags.resolutionunit = runit;

  TIFFGetField( handle, TIFFTAG_XRESOLUTION, &xres );
  meta->tags.xresolution = xres;

  TIFFGetField( handle, TIFFTAG_YRESOLUTION, &yres );
  meta->tags.yresolution = yres;

  TIFFGetField( handle, TIFFTAG_PLANARCONFIG, &planar );
  meta->tags.planarconfig = planar;

  if ( TIFFGetField( handle, TIFFTAG_DATETIME, &timestr ) == 1 ) {
    char *ptr = timestr; Size i;
    for ( i = 0; ( i < 20 ) && timestr[i]; i++ ) {
      if ( ( timestr[i] >= '0' ) && ( timestr[i] <= '9' ) ) *ptr++ = timestr[i];
    }
    *ptr = 0;
    if ( StringParseDateTime( timestr, NULL, &meta->cre, NULL ) ) {
      memset( &meta->cre, 0, sizeof(Time) );
    }
  }

  if ( TIFFGetField( handle, TIFFTAG_TILEWIDTH, &tx ) == 1 ) {
    if ( TIFFGetField( handle, TIFFTAG_TILELENGTH, &ty ) == 1 ) {
      meta->tags.tilewidth = tx;
      meta->tags.tilelength = ty;
      flags |= TIFFIO_TILED;
    } else {
      return pushexception( E_TIFFIO );
    }
  }

  TIFFGetField( handle, TIFFTAG_ROWSPERSTRIP, &rps );
  meta->tags.rowsperstrip = rps;

  TIFFGetField( handle, TIFFTAG_ORIENTATION, &orient );
  meta->tags.orientation = orient;
  switch ( orient ) {
    case ORIENTATION_LEFTTOP:  flags |= TIFFIO_TRNSP | TIFFIO_ORI_TOP;                  iostat |= ImageioBlkTrnsp | ImageioBlkFlipY;                   break;
    case ORIENTATION_RIGHTTOP: flags |= TIFFIO_TRNSP | TIFFIO_ORI_TOP | TIFFIO_ORI_RIG; iostat |= ImageioBlkTrnsp | ImageioBlkFlipY | ImageioBlkFlipX; break;
    case ORIENTATION_RIGHTBOT: flags |= TIFFIO_TRNSP |                  TIFFIO_ORI_RIG; iostat |= ImageioBlkTrnsp |                   ImageioBlkFlipX; break;
    case ORIENTATION_LEFTBOT:  flags |= TIFFIO_TRNSP;                                   iostat |= ImageioBlkTrnsp;                                     break;
    case ORIENTATION_TOPLEFT:  flags |=                TIFFIO_ORI_TOP;                  iostat |=                   ImageioBlkFlipY;                   break;
    case ORIENTATION_TOPRIGHT: flags |=                TIFFIO_ORI_TOP | TIFFIO_ORI_RIG; iostat |=                   ImageioBlkFlipY | ImageioBlkFlipX; break;
    case ORIENTATION_BOTRIGHT: flags |=                                 TIFFIO_ORI_RIG; iostat |=                                     ImageioBlkFlipX; break;
    case ORIENTATION_BOTLEFT:  break;
    default: return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_FMTERR ) );
  }

  meta->flags = flags;
  if ( flags & TIFFIO_TILED ) {
    if ( flags & TIFFIO_TRNSP ) return pushexception( E_TIFFIO_IMPL );
    imageio->iostat |= iostat;
  } else {
    imageio->iostat |= iostat | ImageioBlk;
  }

  /* image size */
  imageio->dim = 2;
  if ( ( TIFFGetField( handle, TIFFTAG_IMAGEWIDTH, &nx )  != 1 )
    || ( TIFFGetField( handle, TIFFTAG_IMAGELENGTH, &ny ) != 1 ) ) {
    return ImageioErrFmt( imageio, pushexception( E_IMAGEIO_FMTERR ) );
  }
  if ( flags & TIFFIO_TRNSP ) {
    meta->len[0] = ny;
    meta->len[1] = nx;
  } else {
    meta->len[0] = nx;
    meta->len[1] = ny;
  }
  meta->low[0] = 0;
  meta->low[1] = 0;
  imageio->len = meta->len;
  imageio->low = meta->low;

  if ( ArrayOffset( imageio->dim, imageio->len, TypeGetSize( imageio->eltype ), &imageio->arrsize ) ) {
    return pushexception( E_IMAGEIO_BIG );
  }

  /* file offset */
  imageio->offset = 0;

  return E_NONE;

}


extern Status TiffioOld
              (Imageio *imageio)

{
  TiffioMeta *meta;
  Size buflen;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  if ( runcheck && ( imageio->fileio == NULL ) ) return pushexception( E_TIFFIO );
  if ( runcheck && ( imageio->iostat & ImageioModeCre ) ) return pushexception( E_TIFFIO );

  /* meta data buffer */
  meta = malloc( sizeof(TiffioMeta) );
  if ( meta == NULL ) return pushexception( E_MALLOC );
  imageio->meta = meta;
  imageio->iostat |= ImageioAllocMeta;

  /* error handling */
  TIFFSetWarningHandler( NULL ); /* no warning messages */
  TIFFSetErrorHandler( TiffioError );

  /* reopen tiff file */
  status = TiffioOpen( imageio );
  if ( exception( status ) ) return status;

  /* copy meta data */
  status=TiffioMetaCopy( imageio );
  if ( exception( status ) ) return status;

  /* temp buffer */
  if ( meta->flags & TIFFIO_TILED ) {
    buflen = TIFFTileSize( meta->handle );
  } else {
    buflen = TIFFScanlineSize( meta->handle );
  }
  status = ImageioBufAlloc( imageio, buflen );
  if ( pushexception( status ) ) return status;

  /* set i/o modes */
  imageio->rd = TiffioRd;
  imageio->wr = TiffioWr;
  status = ImageioModeInit( imageio );
  if ( exception( status ) ) return status;
  switch ( imageio->iocap ) {
    case ImageioCapLib: break;
    default: imageio->rd = NULL; imageio->wr = NULL;
  }

  return E_NONE;

}
