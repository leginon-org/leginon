/*----------------------------------------------------------------------------*
*
*  imageioblock.c  -  imageio: image files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imageioblock.h"
#include "imageiocommon.h"
#include "exception.h"
#include <string.h>


/* functions */

static Status ImageioSetY
              (Size count,
               Size length,
               Size elsize,
               const void *src,
               void *dst)
{

  if ( !count ) return E_NONE;

  switch ( elsize ) {

    case 1: {
      const uint8_t *s = src;
      uint8_t *d = dst;
      while ( count-- ) {
        *d = *s++; d += length;
      }
      break;
    }

    case 2: {
      const uint16_t *s = src;
      uint16_t *d = dst;
      while ( count-- ) {
        *d = *s++; d += length;
      }
      break;
    }

    case 3: {
      const uint8_t *s = src;
      uint8_t *d = dst;
      while ( count-- ) {
        d[0] = *s++;
        d[1] = *s++;
        d[2] = *s++;
        d += 3 * length;
      }
      break;
    }

    case 4: {
      const uint32_t *s = src;
      uint32_t *d = dst;
      while ( count-- ) {
        *d = *s++; d += length;
      }
      break;
    }

    case 8: {
      const uint64_t *s = src;
      uint64_t *d = dst;
      while ( count-- ) {
        *d = *s++; d += length;
      }
      break;
    }

    case 16: {
      const uint64_t *s = src;
      uint64_t *d = dst;
      while ( count-- ) {
        d[0] = *s++;
        d[1] = *s++;
        d += 2 * length;
      }
      break;
    }

    default: return exception( E_IMAGEIO );

  }

  return E_NONE;

}


static Status ImageioSetYf
              (Size count,
               Size length,
               Size elsize,
               const void *src,
               void *dst)
{

  if ( !count ) return E_NONE;

  switch ( elsize ) {

    case 1: {
      const uint8_t *s = src; s += count;
      uint8_t *d = dst;
      while ( count-- ) {
        *d = *--s; d += length;
      }
      break;
    }

    case 2: {
      const uint16_t *s = src; s += count;
      uint16_t *d = dst;
      while ( count-- ) {
        *d = *--s; d += length;
      }
      break;
    }

    case 3: {
      const uint8_t *s = src; s += 3 * count;
      uint8_t *d = dst;
      while ( count-- ) {
        d[2] = *--s;
        d[1] = *--s;
        d[0] = *--s;
        d += 3 * length;
      }
      break;
    }

    case 4: {
      const uint32_t *s = src; s += count;
      uint32_t *d = dst;
      while ( count-- ) {
        *d = *--s; d += length;
      }
      break;
    }

    case 8: {
      const uint64_t *s = src; s += count;
      uint64_t *d = dst;
      while ( count-- ) {
        *d = *--s; d += length;
      }
      break;
    }

    case 16: {
      const uint64_t *s = src; s += 2 * count;
      uint64_t *d = dst;
      while ( count-- ) {
        d[1] = *--s;
        d[0] = *--s;
        d += 2 * length;
      }
      break;
    }

    default: return exception( E_IMAGEIO );

  }

  return E_NONE;

}


static Status ImageioGetY
              (Size count,
               Size length,
               Size elsize,
               const void *src,
               void *dst)
{

  if ( !count ) return E_NONE;

  switch ( elsize ) {

    case 1: {
      const uint8_t *s = src;
      uint8_t *d = dst;
      while ( count-- ) {
        *d++ = *s; s += length;
      }
      break;
    }

    case 2: {
      const uint16_t *s = src;
      uint16_t *d = dst;
      while ( count-- ) {
        *d++ = *s; s += length;
      }
      break;
    }

    case 3: {
      const uint8_t *s = src;
      uint8_t *d = dst;
      while ( count-- ) {
        *d++ = s[0];
        *d++ = s[1];
        *d++ = s[2];
        s += 3 * length;
      }
      break;
    }

    case 4: {
      const uint32_t *s = src;
      uint32_t *d = dst;
      while ( count-- ) {
        *d++ = *s; s += length;
      }
      break;
    }

    case 8: {
      const uint64_t *s = src;
      uint64_t *d = dst;
      while ( count-- ) {
        *d++ = *s; s += length;
      }
      break;
    }

    case 16: {
      const uint64_t *s = src;
      uint64_t *d = dst;
      while ( count-- ) {
        *d++ = s[0];
        *d++ = s[1];
        s += 2 * length;
      }
      break;
    }

    default: return exception( E_IMAGEIO );

  }

  return E_NONE;

}


static Status ImageioGetYf
              (Size count,
               Size length,
               Size elsize,
               const void *src,
               void *dst)
{

  if ( !count ) return E_NONE;

  switch ( elsize ) {

    case 1: {
      const uint8_t *s = src;
      uint8_t *d = dst; d += count;
      while ( count-- ) {
        *--d = *s; s += length;
      }
      break;
    }

    case 2: {
      const uint16_t *s = src;
      uint16_t *d = dst; d += count;
      while ( count-- ) {
        *--d = *s; s += length;
      }
      break;
    }

    case 3: {
      const uint8_t *s = src;
      uint8_t *d = dst; d += 3 * count;
      while ( count-- ) {
        *--d = s[2];
        *--d = s[1];
        *--d = s[0];
        s += 3 * length;
      }
      break;
    }

    case 4: {
      const uint32_t *s = src;
      uint32_t *d = dst; d += count;
      while ( count-- ) {
        *--d = *s; s += length;
      }
      break;
    }

    case 8: {
      const uint64_t *s = src;
      uint64_t *d = dst; d += count;
      while ( count-- ) {
        *--d = *s; s += length;
      }
      break;
    }

    case 16: {
      const uint64_t *s = src;
      uint64_t *d = dst; d += 2 * count;
      while ( count-- ) {
        *--d = s[1];
        *--d = s[0];
        s += 2 * length;
      }
      break;
    }

    default: return exception( E_IMAGEIO );

  }

  return E_NONE;

}


extern Status ImageioBlockCheck
              (Imageio *imageio,
               Offset offset,
               Size length,
               Size *count)

{

  if ( offset < 0 ) return exception( E_ARGVAL );

  if ( count == NULL ) return exception( E_IMAGEIO_OFFS );

  if ( imageio->dim < 2 ) {

    *count = 0;

  } else {

    Size len0 = imageio->len[0];
    Size len1 = imageio->len[1];

    if ( offset % len0 ) return exception( E_IMAGEIO_OFFS );
    if ( length % len0 ) return exception( E_IMAGEIO_OFFS );

    offset /= len0;
    length /= len0;

    if ( offset % len1 ) return exception( E_IMAGEIO_OFFS );
    if ( length % len1 ) return exception( E_IMAGEIO_OFFS );

    *count = length / len1;

  }

  return E_NONE;

}


extern Status ImageioRdBlock
              (Imageio *imageio,
               Status (*rd)( Imageio *, Offset, Size, void * ),
               Offset offset,
               Size length,
               Size count,
               void *addr)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( rd == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( !count ) ) return pushexception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return pushexception( E_ARGVAL );

  Size elsize = TypeGetSize( imageio->eltype );

  Size siz = length / count;
  Size len = siz / elsize;
  Size len0 = imageio->len[0];
  Size len1 = imageio->len[1];
  Size siz0 = len0 * elsize;
  Size siz1 = len1 * elsize;

  uint8_t *dst = addr;

  if ( imageio->iostat & ImageioBlkTrnsp ) {

    status = ImageioBufAlloc( imageio, siz1 );
    if ( pushexception( status ) ) return status;

    uint8_t *ptr = imageio->buf;

    if ( imageio->iostat & ImageioBlkFlipX ) {

      while ( count-- ) {

        uint8_t *d = dst + siz0;

        for ( Size i = 0; i < len0; i++ ) {

          d -= elsize;

          status = rd( imageio, offset, siz1, ptr );
          if ( exception( status ) ) return status;

          if ( imageio->cvtcount && ( imageio->rdcvt != NULL ) ) {
            imageio->rdcvt( imageio->cvtcount * len1, ptr, ptr );
          }

          if ( imageio->iostat & ImageioBlkFlipY ) {
            status = ImageioSetYf( len1, len0, elsize, ptr, d );
            if ( pushexception( status ) ) return status;
          } else {
            status = ImageioSetY( len1, len0, elsize, ptr, d );
            if ( pushexception( status ) ) return status;
          }

          offset += siz1;

        }

        dst += siz;

      }

    } else {

      while ( count-- ) {

        uint8_t *d = dst;

        for ( Size i = 0; i < len0; i++ ) {

          status = rd( imageio, offset, siz1, ptr );
          if ( exception( status ) ) return status;

          if ( imageio->cvtcount && ( imageio->rdcvt != NULL ) ) {
            imageio->rdcvt( imageio->cvtcount * len1, ptr, ptr );
          }

          if ( imageio->iostat & ImageioBlkFlipY ) {
            status = ImageioSetYf( len1, len0, elsize, ptr, d );
            if ( pushexception( status ) ) return status;
          } else {
            status = ImageioSetY( len1, len0, elsize, ptr, d );
            if ( pushexception( status ) ) return status;
          }

          d += elsize;

          offset += siz1;

        }

        dst += siz;

      }

    }

  } else {

    if ( imageio->iostat & ImageioBlkFlipY ) {

      while ( count-- ) {

        dst += siz;

        uint8_t *d = dst;

        for ( Size i = 0; i < len1; i++ ) {

          d -= siz0;

          status = rd( imageio, offset, siz0, d );
          if ( exception( status ) ) return status;

          if ( imageio->cvtcount && ( imageio->rdcvt != NULL ) ) {
            imageio->rdcvt( imageio->cvtcount * len0, d, d );
          }

          if ( imageio->iostat & ImageioBlkFlipX ) {
            status = ImageioFlip( len0, elsize, d );
            if ( pushexception( status ) ) return status;
          }

          offset += siz0;

        }

      }

    } else {

      while ( count-- ) {

        status = rd( imageio, offset, siz, dst );
        if ( exception( status ) ) return status;

        if ( imageio->cvtcount && ( imageio->rdcvt != NULL ) ) {
          imageio->rdcvt( imageio->cvtcount * len, dst, dst );
        }

        if ( imageio->iostat & ImageioBlkFlipX ) {
          uint8_t *d = dst;
          for ( Size i = 0; i < len1; i++, d += siz0 ) {
            status = ImageioFlip( len0, elsize, d );
            if ( pushexception( status ) ) return status;
          }
        }

        dst += siz;

        offset += siz;

      }

    }

  }

  return E_NONE;

}


extern Status ImageioWrBlock
              (Imageio *imageio,
               Status (*wr)( Imageio *, Offset, Size, const void * ),
               Offset offset,
               Size length,
               Size count,
               const void *addr)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( wr == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( !count ) ) return pushexception( E_ARGVAL );
  if ( argcheck( addr == NULL ) ) return pushexception( E_ARGVAL );

  Size elsize = TypeGetSize( imageio->eltype );

  Size siz = length / count;
  Size len0 = imageio->len[0];
  Size len1 = imageio->len[1];
  Size siz0 = len0 * elsize;
  Size siz1 = len1 * elsize;

  const uint8_t *src = addr;

  if ( imageio->iostat & ImageioBlkTrnsp ) {

    status = ImageioBufAlloc( imageio, siz1 );
    if ( pushexception( status ) ) return status;

    uint8_t *ptr = imageio->buf;

    if ( imageio->iostat & ImageioBlkFlipX ) {

      while ( count-- ) {

        const uint8_t *s = src + siz0;

        for ( Size i = 0; i < len0; i++ ) {

          s -= elsize;

          if ( imageio->iostat & ImageioBlkFlipY ) {
            status = ImageioGetYf( len1, len0, elsize, s, ptr );
            if ( pushexception( status ) ) return status;
          } else {
            status = ImageioGetY( len1, len0, elsize, s, ptr );
            if ( pushexception( status ) ) return status;
          }

          if ( imageio->cvtcount && ( imageio->wrcvt != NULL ) ) {
            imageio->wrcvt( imageio->cvtcount * len1, ptr, ptr );
          }

          status = wr( imageio, offset, siz1, ptr );
          if ( exception( status ) ) return status;

          offset += siz1;

        }

        src += siz;

      }

    } else {

      while ( count-- ) {

        const uint8_t *s = src;

        for ( Size i = 0; i < len0; i++ ) {

          if ( imageio->iostat & ImageioBlkFlipY ) {
            status = ImageioGetYf( len1, len0, elsize, s, ptr );
            if ( pushexception( status ) ) return status;
          } else {
            status = ImageioGetY( len1, len0, elsize, s, ptr );
            if ( pushexception( status ) ) return status;
          }

          if ( imageio->cvtcount && ( imageio->wrcvt != NULL ) ) {
            imageio->wrcvt( imageio->cvtcount * len1, ptr, ptr );
            ptr = imageio->buf;
          }

          status = wr( imageio, offset, siz1, ptr );
          if ( exception( status ) ) return status;

          s += elsize;

          offset += siz1;

        }

        src += siz;

      }

    }

  } else {

    if ( ( imageio->iostat & ImageioBlkFlipX ) || ( imageio->cvtcount && ( imageio->wrcvt != NULL ) ) ) {
      status = ImageioBufAlloc( imageio, siz0 );
      if ( pushexception( status ) ) return status;
    }

    if ( imageio->iostat & ImageioBlkFlipY ) {

      while ( count-- ) {

        src += siz;

        const uint8_t *s = src;

        for ( Size i = 0; i < len1; i++ ) {

          s -= siz0;

          const uint8_t *p = s;

          if ( imageio->iostat & ImageioBlkFlipX ) {
            memcpy( imageio->buf, s, siz0 );
            status = ImageioFlip( len0, elsize, imageio->buf );
            if ( pushexception( status ) ) return status;
            p = imageio->buf;
          }

          if ( imageio->cvtcount && ( imageio->wrcvt != NULL ) ) {
            imageio->wrcvt( imageio->cvtcount * len0, p, imageio->buf );
            p = imageio->buf;
          }

          status = wr( imageio, offset, siz0, p );
          if ( exception( status ) ) return status;

          src += siz0;

          offset += siz0;

        }

      }

    } else {

      while ( count-- ) {

        for ( Size i = 0; i < len1; i++ ) {

          const uint8_t *ptr = src;

          if ( imageio->iostat & ImageioBlkFlipX ) {
            memcpy( imageio->buf, src, siz0 );
            status = ImageioFlip( len0, elsize, imageio->buf );
            if ( pushexception( status ) ) return status;
            ptr = imageio->buf;
          }

          if ( imageio->cvtcount && ( imageio->wrcvt != NULL ) ) {
            imageio->wrcvt( imageio->cvtcount * len0, ptr, imageio->buf );
            ptr = imageio->buf;
          }

          status = wr( imageio, offset, siz0, ptr );
          if ( exception( status ) ) return status;

          src += siz0;

          offset += siz0;

        }

      }

    }

  }

  return E_NONE;

}
