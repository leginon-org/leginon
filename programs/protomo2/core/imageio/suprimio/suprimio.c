/*----------------------------------------------------------------------------*
*
*  suprimio.c  -  imageio: suprim files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "suprimio.h"
#include "imageiocommon.h"
#include "stringformat.h"
#include "exception.h"
#include "baselib.h"
#include <string.h>


/* header layout

  nr offs size  type name
   0    0    1  uint8_t version
   1    1    4  uint32_t nrow
   2    5    4  uint32_t ncol
   3    9    4  int32_t format
   4   13    4  int32_t intern
   5   17    4  int32_t filetype
   6   21    4  Real32 min
   7   25    4  Real32 max
   8   29    4  Real32 mean
   9   33    4  Real32 sd
  10   37  512  SuprimRegister reg[SuprimRegisterMax]
  11  549 1024  char trace[1024]
  12      1573  SuprimHdr
*/


static void SuprimHeaderPack
            (SuprimHeader *hdr)

{
  char *f,*h=(char *)hdr;

  f=(char *)&hdr->version;
  if (f != h+0) { h[0]=f[0]; }

  f=(char *)&hdr->nrow;
  if (f != h+1) { h[1]=f[0]; h[2]=f[1]; h[3]=f[2]; h[4]=f[3]; }

  f=(char *)&hdr->ncol;
  if (f != h+5) { h[5]=f[0]; h[6]=f[1]; h[7]=f[2]; h[8]=f[3]; }

  f=(char *)&hdr->format;
  if (f != h+9) { h[9]=f[0]; h[10]=f[1]; h[11]=f[2]; h[12]=f[3]; }

  f=(char *)&hdr->intern;
  if (f != h+13) { h[13]=f[0]; h[14]=f[1]; h[15]=f[2]; h[16]=f[3]; }

  f=(char *)&hdr->filetype;
  if (f != h+17) { h[17]=f[0]; h[18]=f[1]; h[19]=f[2]; h[20]=f[3]; }

  f=(char *)&hdr->min;
  if (f != h+21) { h[21]=f[0]; h[22]=f[1]; h[23]=f[2]; h[24]=f[3]; }

  f=(char *)&hdr->max;
  if (f != h+25) { h[25]=f[0]; h[26]=f[1]; h[27]=f[2]; h[28]=f[3]; }

  f=(char *)&hdr->mean;
  if (f != h+29) { h[29]=f[0]; h[30]=f[1]; h[31]=f[2]; h[32]=f[3]; }

  f=(char *)&hdr->sd;
  if (f != h+33) { h[33]=f[0]; h[34]=f[1]; h[35]=f[2]; h[36]=f[3]; }

  f=(char *)hdr->reg;
  if (f != h+37) { size_t i=0; while (i < 512) { h[i+37]=f[i]; i++; } }

  f=(char *)hdr->trace;
  if (f != h+549) { size_t i=0; while (i < 1024) { h[i+549]=f[i]; i++; } }

}


static void SuprimHeaderUnpack
            (SuprimHeader *hdr)

{
  char *f,*h=(char *)hdr;

  f=(char *)hdr->reg;
  if (f != h+37) { size_t i=512; while (i) { --i; f[i]=h[i+37]; } }

  f=(char *)&hdr->sd;
  if (f != h+33) { f[3]=h[36]; f[2]=h[35]; f[1]=h[34]; f[0]=h[33]; }

  f=(char *)&hdr->mean;
  if (f != h+29) { f[3]=h[32]; f[2]=h[31]; f[1]=h[30]; f[0]=h[29]; }

  f=(char *)&hdr->max;
  if (f != h+25) { f[3]=h[28]; f[2]=h[27]; f[1]=h[26]; f[0]=h[25]; }

  f=(char *)&hdr->min;
  if (f != h+21) { f[3]=h[24]; f[2]=h[23]; f[1]=h[22]; f[0]=h[21]; }

  f=(char *)&hdr->filetype;
  if (f != h+17) { f[3]=h[20]; f[2]=h[19]; f[1]=h[18]; f[0]=h[17]; }

  f=(char *)&hdr->intern;
  if (f != h+13) { f[3]=h[16]; f[2]=h[15]; f[1]=h[14]; f[0]=h[13]; }

  f=(char *)&hdr->format;
  if (f != h+9) { f[3]=h[12]; f[2]=h[11]; f[1]=h[10]; f[0]=h[9]; }

  f=(char *)&hdr->ncol;
  if (f != h+5) { f[3]=h[8]; f[2]=h[7]; f[1]=h[6]; f[0]=h[5]; }

  f=(char *)&hdr->nrow;
  if (f != h+1) { f[3]=h[4]; f[2]=h[3]; f[1]=h[2]; f[0]=h[1]; }

  f=(char *)&hdr->version;
  if (f != h+0) { f[0]=h[0]; }

}


static void SuprimHeaderSwap
            (SuprimHeader *hdr)

{
  char *h = (char *)hdr;

  Swap32( 9, h+1, h+1 );
  Swap32( SuprimRegisterMax, h+37, h+37 );
  /* trace is not aligned to 4-byte, must be swapped at the time when read or written */

}


static Status SuprimHeaderReadTrace
              (Imageio *imageio,
               SuprimHeader *hdr)

{
  SuprimMeta *meta = imageio->meta;
  Size offs = SuprimTraceOffs;
  int32_t nr, len;
  Status status;

  do {
    status = FileioRead( imageio->fileio, offs, sizeof( int32_t ), &nr );
    if ( exception( status ) ) return status;
    offs += sizeof( int32_t );
    if ( imageio->iostat & ImageioByteSwap ) {
      Swap32( 1, &nr, &nr );
    }
    if ( !nr ) break;
    if ( nr < 0 ) return exception( E_SUPRIMIO_TRC );
    nr += 2;

    while ( nr-- ) {
      status = FileioRead( imageio->fileio, offs, sizeof( int32_t ), &len );
      if ( exception( status ) ) return status;
      offs += sizeof( int32_t );
      if ( imageio->iostat & ImageioByteSwap ) {
        Swap32( 1, &len, &len );
      }
      if ( len < 0 ) return exception( E_SUPRIMIO_TRC );
      offs += len;
    }

  } while ( True );

  /* before detecting format */
  if ( ~imageio->iostat & ImageioModeFmt ) return status;

  meta->headersize = offs;

  /* reread whole trace */
  status = FileioRead( imageio->fileio, SuprimTraceOffs, offs - SuprimTraceOffs, hdr->trace );
  if ( exception( status ) ) return status;

  return status;

}


extern Status SuprimHeaderRead
              (Imageio *imageio,
               SuprimHeader *hdr)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( hdr == NULL ) ) return pushexception( E_ARGVAL );

  /* read into buffer */
  status = FileioRead( imageio->fileio, 0, SuprimTraceOffs, hdr );
  if ( pushexception( status ) ) return status;

  /* swap if non-native byte order */
  if ( imageio->iostat & ImageioByteSwap ) {
    SuprimHeaderSwap( hdr );
  }

  /* unpack header, code may be removed by optimization, unless check is set */
  if ( sizeof(SuprimHeader) > SuprimHeaderSize) {
    SuprimHeaderUnpack( hdr );
  }

  status = SuprimHeaderReadTrace( imageio, hdr );
  if ( pushexception( status ) ) return status;

  return E_NONE;

}


extern Status SuprimHeaderWrite
              (Imageio *imageio)

{
  SuprimMeta *meta;
  SuprimHeader *hdr, buf;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  /* modification time */
  meta = imageio->meta;
  if ( ( meta->mod != NULL ) && meta->nmod ) {
    Time tm = TimeGet();
    Size tmlen = meta->nmod;
    char *tmbuf = meta->mod;
    StringFormatDateTime( &tm, ImageDateTimeSep, &tmlen, tmbuf );
  }

  /* temp copy of header */
  hdr = &meta->header;
  memcpy( &buf, hdr, sizeof( SuprimHeader ) - sizeof( hdr->trace ) );

  /* set open flag */
  if ( ~imageio->iostat & ImageioFinClose ) {
    buf.intern = SuprimOpenFlag;
  }

  /* pack header, code may be removed by optimization */
  if ( sizeof( SuprimHeader ) > SuprimHeaderSize ) {
    SuprimHeaderPack( &buf );
  }
  /* swap if non-native byte order */
  if ( imageio->iostat & ImageioByteSwap ) {
    SuprimHeaderSwap( &buf );
  }

  /* append trace */
  memcpy( SuprimTraceOffs + (char *)&buf, hdr->trace, meta->headersize - SuprimTraceOffs );

  /* write to file */
  if ( imageio->iocap == ImageioCapStd ) {
    status = FileioWriteStd( imageio->fileio, 0, meta->headersize, &buf );
    if ( pushexception( status ) ) return status; 
  } else {
    status = FileioWrite( imageio->fileio, 0, meta->headersize, &buf );
    if ( pushexception( status ) ) return status; 
  }

  /* flush buffers */
  status = FileioFlush( imageio->fileio );
  if ( pushexception( status ) ) return status; 

  return E_NONE;

}
