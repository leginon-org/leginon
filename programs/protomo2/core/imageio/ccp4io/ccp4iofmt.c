/*----------------------------------------------------------------------------*
*
*  ccp4iofmt.c  -  imageio: CCP4 files
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
#include "exception.h"

/* macros */

#define MAXTYPE  ( CCP4_MAXTYPE - 1 )
#define MAXSIZE  0x0fffffff
#define HBITS    0xffff0000


/* functions */

static Status CCP4FmtCheck
              (CCP4Header *hdr,
               ImageioStatus iostat,
               Bool isccp4)

{

  if ( ( hdr->nx == 0 ) || ( hdr->nx > MAXSIZE ) ) return E_IMAGEIO_FORMAT;
  if ( ( hdr->ny == 0 ) || ( hdr->ny > MAXSIZE ) ) return E_IMAGEIO_FORMAT;
  if ( ( hdr->nz == 0 ) || ( hdr->nz > MAXSIZE ) ) return E_IMAGEIO_FORMAT;

  if ( ( hdr->mode > MAXTYPE ) && ( hdr->mode != CCP4_OPENFLAG ) ) return E_IMAGEIO_FORMAT;

  if ( hdr->nlab > 10 ) return E_IMAGEIO_FORMAT;

  if ( iostat & ImageioFmtAuto ) {

    if ( ( hdr->mx == 0 ) || ( hdr->mx > MAXSIZE ) ) return E_IMAGEIO_FORMAT;
    if ( ( hdr->my == 0 ) || ( hdr->my > MAXSIZE ) ) return E_IMAGEIO_FORMAT;
    if ( ( hdr->mz == 0 ) || ( hdr->mz > MAXSIZE ) ) return E_IMAGEIO_FORMAT;

    if ( ( hdr->a < 0 ) || ( hdr->a > MAXSIZE ) || ( ( hdr->a > 0 ) && ( hdr->a < 1e-6 ) ) ) return E_IMAGEIO_FORMAT;
    if ( ( hdr->b < 0 ) || ( hdr->b > MAXSIZE ) || ( ( hdr->b > 0 ) && ( hdr->b < 1e-6 ) ) ) return E_IMAGEIO_FORMAT;
    if ( ( hdr->c < 0 ) || ( hdr->c > MAXSIZE ) || ( ( hdr->c > 0 ) && ( hdr->c < 1e-6 ) ) ) return E_IMAGEIO_FORMAT;

    if ( ( hdr->alpha < 0 ) || ( hdr->alpha >= 180 ) ) return E_IMAGEIO_FORMAT;
    if ( ( hdr->beta  < 0 ) || ( hdr->beta  >= 180 ) ) return E_IMAGEIO_FORMAT;
    if ( ( hdr->gamma < 0 ) || ( hdr->gamma >= 180 ) ) return E_IMAGEIO_FORMAT;

    if ( !( ( ( hdr->mapc == 1 ) && ( hdr->mapr == 2 ) && ( hdr->maps == 3 ) )
         || ( ( hdr->mapc == 1 ) && ( hdr->mapr == 3 ) && ( hdr->maps == 2 ) )
         || ( ( hdr->mapc == 2 ) && ( hdr->mapr == 1 ) && ( hdr->maps == 3 ) )
         || ( ( hdr->mapc == 2 ) && ( hdr->mapr == 3 ) && ( hdr->maps == 1 ) )
         || ( ( hdr->mapc == 3 ) && ( hdr->mapr == 1 ) && ( hdr->maps == 2 ) )
         || ( ( hdr->mapc == 3 ) && ( hdr->mapr == 2 ) && ( hdr->maps == 1 ) ) ) ) {
         return E_IMAGEIO_FORMAT;
    }

    if ( hdr->ispg & HBITS ) return E_IMAGEIO_FORMAT;

  }

  if ( isccp4 ) {

    if ( ( hdr->map[0] != 'M' ) || ( hdr->map[1] != 'A' ) || ( hdr->map[2] != 'P' ) ) return E_IMAGEIO_FORMAT;
    if ( hdr->arms < 0 ) return E_IMAGEIO_FORMAT;

  }

  return E_NONE;

}


extern Status CCP4Fmt
              (Imageio *imageio)

{
  Fileio *fileio;
  CCP4Header hdr;
  Bool isccp4;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  fileio = imageio->fileio;
  if ( runcheck && ( fileio == NULL ) ) return pushexception( E_CCP4IO );
  if ( runcheck && ( FileioGetMode( fileio ) & IOCre ) ) return pushexception( E_CCP4IO );

  isccp4 = ( *imageio->format->version.ident == 'C' );

  /* read header in native byte order and check */
  ImageioSetEndian( &imageio->iostat, ~ImageioByteSwap );
  status = CCP4HeaderRead( imageio, &hdr );
  if ( exception( status ) ) return status;
  status = CCP4FmtCheck( &hdr, imageio->iostat, isccp4 );
  if ( !status ) return E_NONE;

  /* non-native check */
  ImageioSetEndian( &imageio->iostat, ImageioByteSwap );
  status = CCP4HeaderRead( imageio, &hdr );
  if ( exception( status ) ) return status;
  status = CCP4FmtCheck( &hdr, imageio->iostat, isccp4 );
  if ( !status ) return E_NONE;

  /* checks failed */
  pushexception( status );

  return status;

}
