/*----------------------------------------------------------------------------*
*
*  imageiocommon.c  -  imageio: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imageiocommon.h"
#include "imageioblock.h"
#include "baselib.h"
#include "module.h"
#include "stringformat.h"
#include "exception.h"
#include "macros.h"
#include <stdlib.h>
#include <string.h>


/* variables */

Size ImageioLoadSize = 128 * 1024 * 1024;


/* functions */

extern ImageioStatus ImageioGetEndian()

{
  const uint8_t magic[4] = { 'A', 'B', 'C', 'D' };
  const uint32_t *big = (uint32_t *)magic;
  const uint32_t big0 = magic[0];
  const uint32_t big1 = magic[1];
  const uint32_t big2 = magic[2];
  const uint32_t big3 = magic[3];

  if ( *big == ( ( big0 << 24 ) | ( big1 << 16 ) | ( big2 << 8 ) | big3 ) ) {
    return ImageioBigNative;  /* native big endian */
  } else {
    return 0; /* native little endian */
  }

}


extern void ImageioSetEndian
            (ImageioStatus *iostat,
             ImageioStatus swap)

{

  if ( swap & ImageioByteSwap ) {

    *iostat |= ImageioByteSwap;

    if ( *iostat & ImageioBigNative ) {
      *iostat &= ~ImageioBigFile;
    } else {
      *iostat |= ImageioBigFile;
    }

  } else {

    *iostat &= ~ImageioByteSwap;

    if ( *iostat & ImageioBigNative ) {
      *iostat |= ImageioBigFile;
    } else {
      *iostat &= ~ImageioBigFile;
    }

  }

}


extern char *ImageioGetVersion
             (const char *txt,
              const char *vers,
              Size *len,
              char *buf)

{
  char *ptr = buf;

  if ( *len ) {
    if ( ( txt != NULL ) && *txt ) {
      Time tm = TimeGet();
      ptr = StringFormatDateTime( &tm, ImageDateTimeSep, len, ptr );
      ptr = StringFormatString( *len, txt, len, ptr );
    }
    ptr = CoreCopyVersion( len, ptr );
    if ( ( *len > 2 ) && ( vers != NULL ) && *vers ) {
      *ptr++ = ' '; (*len)--;
      *ptr++ = '('; (*len)--;
      ptr = StringFormatString( *len, vers, len, ptr );
      if ( *len ) {
        *ptr++ = ')'; (*len)--;
      }
    }
    if ( *len ) {
      Size n = *len;
      char *p = ptr;
      while ( n-- ) *p++ = 0;
    }
  }
  return ptr;

}


extern Status ImageioErrPath
              (Imageio *imageio,
               Status status)

{
  const char *path;

  if ( imageio == NULL ) return pushexception( E_ARGVAL );
  if ( imageio->fileio == NULL ) return pushexception( E_ARGVAL );

  path = FileioGetPath( imageio->fileio );
  if ( path != NULL ) {
    appendexception( ", file " );
    appendexception( path );
  }

  return status;

}


extern Status ImageioErrFmt
              (Imageio *imageio,
               Status status)

{

  if ( imageio == NULL ) return pushexception( E_ARGVAL );

  if ( imageio->format != NULL ) {

    const char *ident = imageio->format->version.ident;
    if ( ( ident != NULL ) && *ident ) {
      appendexception( " for " );
      appendexception( ident );
      appendexception( " format");
    }

  }

  return status;
}


extern Status ImageioImageAlloc
              (Imageio *imageio,
               const Size *len,
               const Index *low)

{

  if ( imageio == NULL ) return exception( E_ARGVAL );

  Size dim = imageio->dim;
  if ( dim == 0 ) return exception( E_IMAGEIO );

  Size *dstlen = malloc( dim * sizeof(Size) );
  if ( dstlen == NULL ) {
    return exception( E_MALLOC );
  }

  Index *dstlow = malloc( dim * sizeof(Index) );
  if ( dstlow == NULL ) {
    free( dstlen ); return exception( E_MALLOC );
  }

  if ( len == NULL ) {
    memset( dstlen, 0, dim * sizeof(Size) );
  } else {
    memcpy( dstlen, imageio->len, dim * sizeof(Size) );
  }
  imageio->len = dstlen;

  if ( low == NULL ) {
    memset( dstlow, 0, dim * sizeof(Size) );
  } else {
    memcpy( dstlow, imageio->low, dim * sizeof(Index) );
  }
  imageio->low = dstlow;

  imageio->iostat |= ImageioAllocLen | ImageioAllocLow;

  return E_NONE;

}


extern Status ImageioBufAlloc
              (Imageio *imageio,
               Size size)

{

  if ( ( ~imageio->iostat & ImageioAllocBuf ) || ( imageio->buflen < size ) ) {
    void *buf = malloc( size );
    if ( buf == NULL ) return exception( E_MALLOC );
    if ( imageio->buf != NULL ) free( imageio->buf );
    imageio->buf = buf;
    imageio->buflen = size;
    imageio->iostat |= ImageioAllocBuf;
  }

  return E_NONE;

}


extern Status ImageioSizeSet
              (Imageio *imageio,
               Offset *offset,
               Size length,
               Size *size,
               Size *count)

{
  Status status;

  if ( imageio->iostat & ImageioBlk ) {
    status = ImageioBlockCheck( imageio, *offset, length, count );
    if ( exception( status ) ) return status;
  } else {
    if ( count != NULL ) *count = 0;
  }

  Size elsize = TypeGetSize( imageio->eltype );

  status = MulOffset( *offset, elsize, offset );
  if ( exception( status ) ) return status;

  if ( OFFSETADDOVFL( *offset, imageio->offset ) ) return exception( E_INTOVFL );
  *offset += imageio->offset;

  status = MulSize( length, elsize, size );
  if ( exception( status ) ) return status;

  if ( *size > (Size)OffsetMaxSize ) return exception( E_INTOVFL );

  if ( OFFSETADDOVFL( *offset, (Offset)*size ) ) return exception( E_INTOVFL );

  return E_NONE;

}


extern void ImageioCleanup
            (Imageio *imageio)

{
  ImageioStatus iostat = imageio->iostat;

  if ( iostat & ImageioAllocBuf  ) free( imageio->buf );
  if ( iostat & ImageioAllocMeta ) free( imageio->meta );
  if ( iostat & ImageioAllocLow  ) free( imageio->low );
  if ( iostat & ImageioAllocLen  ) free( imageio->len );

  free( imageio );

}


extern Status ImageioFlip
              (Size length,
               Size elsize,
               void *dst)

{

  if ( !elsize ) return exception( E_ARGVAL );

  if ( !length ) return E_NONE;

  switch ( elsize ) {

    case 1: {
      uint8_t *d = dst;
      uint8_t *e = d + length - 1;
      while ( d < e ) {
        uint8_t v = *d;
        *d++ = *e;
        *e-- = v;
      }
      break;
    }

    case 2: {
      uint16_t *d = dst;
      uint16_t *e = d + length - 1;
      while ( d < e ) {
        uint16_t v = *d;
        *d++ = *e;
        *e-- = v;
      }
      break;
    }

    case 3: {
      uint8_t *d = dst;
      uint8_t *e = d + 3 * ( length - 1 );
      while ( d < e ) {
        uint8_t v0 = d[0];
        uint8_t v1 = d[1];
        uint8_t v2 = d[2];
        *d++ = e[0];
        *d++ = e[1];
        *d++ = e[2];
        e[0] = v0;
        e[1] = v1;
        e[2] = v2;
        e -= 3;
      }
      break;
    }

    case 4: {
      uint32_t *d = dst;
      uint32_t *e = d + length - 1;
      while ( d < e ) {
        uint32_t v = *d;
        *d++ = *e;
        *e-- = v;
      }
      break;
    }

    case 8: {
      uint64_t *d = dst;
      uint64_t *e = d + length - 1;
      while ( d < e ) {
        uint64_t v = *d;
        *d++ = *e;
        *e-- = v;
      }
      break;
    }

    case 16: {
      uint64_t *d = dst;
      uint64_t *e = d + 2 * ( length - 1 );
      while ( d < e ) {
        uint64_t v0 = d[0];
        uint64_t v1 = d[1];
        *d++ = e[0];
        *d++ = e[1];
        e[0] = v0;
        e[1] = v1;
        e -= 2;
      }
      break;
    }

    default: return exception( E_IMAGEIO );

  }

  return E_NONE;

}
