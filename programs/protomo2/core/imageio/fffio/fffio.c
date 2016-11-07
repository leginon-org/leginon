/*----------------------------------------------------------------------------*
*
*  fffio.c  -  imageio: FFF files
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
#include "exception.h"
#include "baselib.h"
#include <string.h>


/* variables */

#define NUL 0
const uint8_t FFFbigmagic[16] = {'I','3','P',NUL,'0','1','0','8',NUL,NUL,NUL,NUL,NUL,NUL,NUL,NUL};
const uint8_t FFFltlmagic[16] = {'3','I',NUL,'P','1','0','8','0',NUL,NUL,NUL,NUL,NUL,NUL,NUL,NUL};


/* header layout

  nr offs size  type name
   0    0   16  uint8_t magic[16]
   1   16    2  uint16_t kind
   2   18    2  uint16_t type
   3   20    2  uint16_t tsize
   4   22    2  uint16_t dim
   5   24    4  uint32_t data
   6   28    4  uint32_t attr
   7   32   16  char cre[16]
   8   48   16  char mod[16]
   9        64  FFFHdr
*/


static void FFFHeaderPack
            (FFFHeader *hdr)

{
  char *f,*h=(char *)hdr;

  f=(char *)hdr->magic;
  if (f != h+0) { size_t i=0; while (i < 16) { h[i+0]=f[i]; i++; } }

  f=(char *)&hdr->kind;
  if (f != h+16) { h[16]=f[0]; h[17]=f[1]; }

  f=(char *)&hdr->type;
  if (f != h+18) { h[18]=f[0]; h[19]=f[1]; }

  f=(char *)&hdr->tsize;
  if (f != h+20) { h[20]=f[0]; h[21]=f[1]; }

  f=(char *)&hdr->dim;
  if (f != h+22) { h[22]=f[0]; h[23]=f[1]; }

  f=(char *)&hdr->data;
  if (f != h+24) { h[24]=f[0]; h[25]=f[1]; h[26]=f[2]; h[27]=f[3]; }

  f=(char *)&hdr->attr;
  if (f != h+28) { h[28]=f[0]; h[29]=f[1]; h[30]=f[2]; h[31]=f[3]; }

  f=(char *)hdr->cre;
  if (f != h+32) { size_t i=0; while (i < 16) { h[i+32]=f[i]; i++; } }

  f=(char *)hdr->mod;
  if (f != h+48) { size_t i=0; while (i < 16) { h[i+48]=f[i]; i++; } }

}


static void FFFHeaderUnpack
            (FFFHeader *hdr)

{
  char *f,*h=(char *)hdr;

  f=(char *)hdr->mod;
  if (f != h+48) { size_t i=16; while (i) { --i; f[i]=h[i+48]; } }

  f=(char *)hdr->cre;
  if (f != h+32) { size_t i=16; while (i) { --i; f[i]=h[i+32]; } }

  f=(char *)&hdr->attr;
  if (f != h+28) { f[3]=h[31]; f[2]=h[30]; f[1]=h[29]; f[0]=h[28]; }

  f=(char *)&hdr->data;
  if (f != h+24) { f[3]=h[27]; f[2]=h[26]; f[1]=h[25]; f[0]=h[24]; }

  f=(char *)&hdr->dim;
  if (f != h+22) { f[1]=h[23]; f[0]=h[22]; }

  f=(char *)&hdr->tsize;
  if (f != h+20) { f[1]=h[21]; f[0]=h[20]; }

  f=(char *)&hdr->type;
  if (f != h+18) { f[1]=h[19]; f[0]=h[18]; }

  f=(char *)&hdr->kind;
  if (f != h+16) { f[1]=h[17]; f[0]=h[16]; }

  f=(char *)hdr->magic;
  if (f != h+0) { size_t i=16; while (i) { --i; f[i]=h[i+0]; } }

}


extern void FFFMetaInit
            (FFFMeta *meta)

{

  memset( meta, 0, sizeof(*meta) );
  meta->attr = -1;
  meta->extra = I3dataInitializer;
  meta->i3meta = True;

}


static void FFFHeaderSwap
            (FFFHeader *hdr)

{
  char *h = (char *)hdr;

  Swap16( 12, h, h );
  Swap32( 2, h+24, h+24 );

}


extern Status FFFMetaRead
              (Imageio *imageio,
               FFFMeta *meta)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( meta == NULL ) ) return pushexception( E_ARGVAL );

  /* read header into buffer */
  FFFHeader *hdr = &meta->hdr;
  status = FileioRead( imageio->fileio, 0, FFFHeaderSize, hdr );
  if ( pushexception( status ) ) return status;

  /* swap if non-native byte order */
  if ( imageio->iostat & ImageioByteSwap ) {
    FFFHeaderSwap( hdr );
  }

  /* unpack header, code may be removed by optimization */
  if ( sizeof(FFFHeader) > FFFHeaderSize ) {
    FFFHeaderUnpack( hdr );
  }

  /* check and set meta */
  if ( !hdr->dim ) return pushexception( E_IMAGEIO_FMTERR );
  meta->dscrlen = hdr->dim * FFFdscrsize;
  meta->dscrsize = hdr->dim * sizeof(FFFArrayDscr);

  /* read attr */
  uint16_t major = imageio->format->version.major;
  uint16_t minor = imageio->format->version.minor;
  if ( !major ) return pushexception( E_IMAGEIO_FMTERR );
  if ( !hdr->attr || ( ( major == 1 ) && ( minor < 8 ) ) ) {
    meta->i3meta = False;
  } else {
    if ( hdr->attr != FFFHeaderSize + meta->dscrsize ) return pushexception( E_IMAGEIO_FMTERR );
    if ( hdr->attr + sizeof(meta->attr) != hdr->data ) return pushexception( E_IMAGEIO_FMTERR );
    status = FileioRead( imageio->fileio, hdr->attr, sizeof(meta->attr), &meta->attr );
    if ( pushexception( status ) ) return status;
    if ( imageio->iostat & ImageioByteSwap ) {
      Swap64( 1, &meta->attr, &meta->attr );
    }
    if ( ( meta->attr != -1 ) && ( meta->attr <= (int64_t)hdr->data ) ) return pushexception( E_IMAGEIO_FMTERR );
  }

  return E_NONE;

}


static Offset FFFSetDscr
              (Size dim,
               const Size *len,
               const Index *low,
               int32_t *fffdscr)

{
  Offset size = 0;

  if ( dim ) {
    size = 1;
    fffdscr += 4 * dim;
    while ( dim-- ) {
      Index high = *low + *len - 1;
      if ( high < *low ) return 0;
      *--fffdscr = size;
      *--fffdscr = *len;
      *--fffdscr = high;
      *--fffdscr = *low;
      if ( MulOffset( size, *len, NULL ) ) return 0;
      size *= *len;
      len++; low++;
    }
  }
  return size;

}


extern Status FFFMetaWrite
              (Imageio *imageio)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  FFFMeta *meta = imageio->meta;
  FFFHeader *hdr = &meta->hdr;

  /* modification time */
  Time tm = TimeGet();
  FFFSetTime( &tm, hdr->mod, sizeof(hdr->mod) );

  /* temp copy */
  FFFMeta buf = *meta;

  /* set open flag */
  if ( ~imageio->iostat & ImageioFinClose ) {
    buf.hdr.magic[8] = 1;
    buf.hdr.magic[9] = 1;
  }

  /* pack header, code may be removed by optimization */
  if ( sizeof(FFFHeader) > FFFHeaderSize ) {
    FFFHeaderPack( &buf.hdr );
  }

  /* get descriptor */
  if ( !FFFSetDscr( imageio->dim, imageio->len, imageio->low, imageio->buf ) ) {
    return pushexception( E_FFFIO );
  }

  /* swap if non-native byte order */
  if ( imageio->iostat & ImageioByteSwap ) {
    FFFHeaderSwap( &buf.hdr );
    Swap32( buf.dscrlen, imageio->buf, imageio->buf ); /* array descriptor */
    Swap64( 1, &buf.attr, &buf.attr );
  }

  /* write header and dscr to file */
  if ( imageio->iocap == ImageioCapStd ) {
    status = FileioWriteStd( imageio->fileio, 0, FFFHeaderSize, &buf.hdr );
    if ( pushexception( status ) ) return status;
    status = FileioWriteStd( imageio->fileio, FFFHeaderSize, meta->dscrsize, imageio->buf );
    if ( pushexception( status ) ) return status;
  } else {
    status = FileioWrite( imageio->fileio, 0, FFFHeaderSize, &buf.hdr );
    if ( pushexception( status ) ) return status;
    status = FileioWrite( imageio->fileio, FFFHeaderSize, meta->dscrsize, imageio->buf );
    if ( pushexception( status ) ) return status;
  }

  /* write attr */
  if ( meta->i3meta ) {
    if ( imageio->iocap == ImageioCapStd ) {
      status = FileioWriteStd( imageio->fileio, hdr->attr, sizeof(meta->attr), &buf.attr );
      if ( pushexception( status ) ) return status;
    } else {
      status = FileioWrite( imageio->fileio, hdr->attr, sizeof(meta->attr), &buf.attr );
      if ( pushexception( status ) ) return status;
    }
  }

  /* flush buffers */
  status = FileioFlush( imageio->fileio );
  if ( pushexception( status ) ) return status;

  return E_NONE;

}
