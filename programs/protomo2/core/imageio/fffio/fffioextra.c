/*----------------------------------------------------------------------------*
*
*  fffioextra.c  -  imageio: FFF files
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
#include "imageioextra.h"
#include "exception.h"
#include "macros.h"


/* functions */


static Status FFFExtraRead
              (const I3data *data,
               int code,
               Size *count,
               void *buf)

{
  Size cnt = 1;
  Status status = E_NONE;

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( buf == NULL ) ) return exception( E_ARGVAL );

  switch ( code ) {

    case I3dataSampling: {
      Coord *dst = buf;
      *dst = 1;
      break;
    }

    case I3dataBinning: {
      Size *dst = buf;
      *dst = 1;
      break;
    }

    default: return E_I3DATA_IMPL;

  }

  if ( count != NULL ) *count = cnt;

  return status;

}


static Status FFFExtraWrite
              (const I3data *data,
               int code,
               Size count,
               const void *buf)

{
  Status status;

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( buf == NULL ) ) return exception( E_ARGVAL );

  switch ( code ) {

    default: status = E_I3DATA_IMPL;

  }

  return status;

}


extern Status FFFExtra
              (Imageio *imageio,
               IOMode mode,
               void *extra)

{

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( extra == NULL ) ) return pushexception( E_ARGVAL );

  FFFMeta *meta = imageio->meta;
  if ( !meta->i3meta ) return pushexception( E_IMAGEIOEXTRA_IMPL );

  if ( mode & ( IONew | IOCre | IOWr ) ) {

    if ( ( meta->attr >= 0 ) && ( mode & ( IONew | IOCre ) ) ) {
      return pushexception( E_FFFIO );
    }

    if ( meta->attr < 0 ) {

      Offset arrsize = imageio->arrsize * meta->hdr.tsize;
      if ( arrsize > OffsetMax - 7 ) return pushexception( E_INTOVFL );
      arrsize = 8 * ( ( arrsize + 7 ) / 8 );
      if ( OFFSETADDOVFL( imageio->offset, arrsize ) ) return pushexception( E_INTOVFL );

      meta->attr = imageio->offset + arrsize;

    }

  } else {

    if ( meta->attr < 0 ) return pushexception( E_IMAGEIOEXTRA_IMPL );

  }


  I3data *data = extra;
  data->init  = NULL;
  data->final = NULL;
  data->read    = FFFExtraRead;
  data->readbuf = NULL;
  data->finalbuf = NULL;
  data->unpack   = NULL;
  data->pack     = NULL;
  data->write    = FFFExtraWrite;
  data->writenew = FFFExtraWrite;

  return E_NONE;

}
