/*----------------------------------------------------------------------------*
*
*  fffiofmt.c  -  imageio: FFF files
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


/* functions */

#ifdef FFFSupportVersion100

static Bool FFFHeaderCompat
            (FFFHeader *hdr)

{
  uint32_t *magic32 = (uint32_t *)hdr->magic;
  uint8_t magic3 = 0;
  Bool reset = False;

  /* compatibility with version 1.00, big endian only */
  /* magic[3]      was 255                            */
  /* magic[4..7]   were 0                             */
  /* magic[8..11]  contained string "I3P "            */
  /* magic[12..15] contained version                  */

  if ( magic32[1] == 0 ) {
    magic3 = hdr->magic[3];
    magic32[1] = magic32[3];
    magic32[2] = 0;
    magic32[3] = 0;
  }

  if ( ( hdr->magic[4] == '0' ) && ( hdr->magic[5] == '1' ) ) {
    /* for major version 1 */
    if ( hdr->magic[6] == '0' ) {
      if ( hdr->magic[7] < '3' ) {
        /* for minor versions < 3 */
        static const uint16_t FFF_K_tab[8] = { K_ASYM, K_UNDEF, K_EVEN, K_ODD, K_HERMEVEN, K_HERMODD, K_ANTIHERM, K_ANTIHERM|K_MOD2 };
        uint16_t kind = hdr->kind;
        kind = ( kind & ~0x7 ) | FFF_K_tab[kind & 0x7];
        if ( ( kind == 0 ) && ( hdr->type == T_CMPLX ) ) {
          kind = K_FOU|K_HERMEVEN; /* assume even number of samples */
        }
        hdr->kind = kind;
        reset = ( magic3 == 255 );
      } else if ( hdr->magic[7] < '4' ) {
        /* for minor versions < 4 */
        hdr->attr = 0; /* no attributes */
      }
    }
  }

  return reset;

}

#endif


static Status FFFFmtCheck
              (FFFHeader *hdr,
               ImageioStatus iostat,
               uint16_t major,
               uint16_t minor)

{
  uint8_t *magic = hdr->magic;

  if ( ~iostat & ImageioBigNative ) Swap16( 8, magic, magic );
#ifdef FFFSupportVersion100
  /* rearrange header fields for old versions */
  if ( FFFHeaderCompat( hdr ) ) {
    if ( ( major == 1 ) && ( minor == 0 ) ) hdr->magic[3] = 0;
  }
#endif

  /* check magic bytes */
  const uint8_t *ref = FFFbigmagic;
  if ( magic[0] != ref[0] ) return E_IMAGEIO_FORMAT;
  if ( magic[1] != ref[1] ) return E_IMAGEIO_FORMAT;
  if ( magic[2] != ref[2] ) return E_IMAGEIO_FORMAT;
  if ( magic[3] != ref[3] ) return E_IMAGEIO_FORMAT;

  /* check version */
  if ( magic[4] != ref[4] ) return E_IMAGEIO_VERS;
  if ( magic[5] != ref[5] ) return E_IMAGEIO_VERS;
  if ( magic[6] != ref[6] ) return E_IMAGEIO_VERS;
  if ( magic[7] >  ref[7] ) return E_IMAGEIO_VERS;
  if ( magic[7] < '4' ) {
    if ( iostat & ImageioModeWr ) return E_IMAGEIO_VERS;
  }

  /* check header data */
  if ( hdr->kind & ~K_MASK ) return E_IMAGEIO_FORMAT;
  if ( hdr->type >= T_MAXTYPE ) return E_IMAGEIO_FORMAT;
  if ( !hdr->tsize ) return E_IMAGEIO_FORMAT;
  if ( !hdr->dim ) return E_IMAGEIO_FORMAT;
  if ( !major ) return E_IMAGEIO_FORMAT;
  Size hdrsize = FFFHeaderSize + hdr->dim * sizeof(FFFArrayDscr);
  if ( !hdr->attr || ( ( major == 1 ) && ( minor < 8 ) ) ) {
    if ( hdr->data < hdrsize ) return E_IMAGEIO_FORMAT;
    if ( hdr->attr ) {
      if ( ( hdr->attr < hdrsize ) || ( hdr->attr == hdr->data ) ) return E_IMAGEIO_FORMAT;
    }
  } else {
    if ( hdr->attr != hdrsize ) return E_IMAGEIO_FORMAT;
    if ( hdr->attr + sizeof(int64_t) != hdr->data ) return E_IMAGEIO_FORMAT;
  }

  return E_NONE;

}


extern Status FFFFmt
              (Imageio *imageio)

{
  FFFMeta meta;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  Fileio *fileio = imageio->fileio;
  if ( runcheck && ( fileio == NULL ) ) return pushexception( E_FFFIO );
  if ( runcheck && ( FileioGetMode( fileio ) & IOCre ) ) return pushexception( E_FFFIO );

  uint16_t major = imageio->format->version.major;
  uint16_t minor = imageio->format->version.minor;

  /* read header in native byte order and check */
  ImageioSetEndian( &imageio->iostat, ~ImageioByteSwap );
  status = FFFMetaRead( imageio, &meta );
  if ( exception( status ) ) return status;
  status = FFFFmtCheck( &meta.hdr, imageio->iostat, major, minor );
  if ( !status ) return E_NONE;

  /* non-native check */
  ImageioSetEndian( &imageio->iostat, ImageioByteSwap );
  status = FFFMetaRead( imageio, &meta );
  if ( exception( status ) ) return status;
  status = FFFFmtCheck( &meta.hdr, imageio->iostat, major, minor );
  if ( !status ) return E_NONE;

  /* checks failed */
  pushexception( status );

  return status;

}
