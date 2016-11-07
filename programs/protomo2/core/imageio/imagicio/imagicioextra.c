/*----------------------------------------------------------------------------*
*
*  imagicioextra.c  -  imageio: CCP4 files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagicio.h"
#include "imagicioconfig.h"
#include "imageiocommon.h"
#include "imageioextra.h"
#include "imageiochecksum.h"
#include "fileiochecksum.h"
#include "statistics.h"
#include "exception.h"
#include <string.h>


/* functions */


static Status ImagicExtraRead
              (const I3data *data,
               int code,
               Size *count,
               void *buf)

{
  Size cnt = 1;
  Status status = E_NONE;

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( buf == NULL ) ) return exception( E_ARGVAL );

  Imageio *imageio = data->handle;
  if ( imageio == NULL ) return exception( E_IMAGICIO );

  ImagicMeta *meta = imageio->meta;
  ImagicHeader *hdr = &meta->header;

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

    case I3dataStat: {
      Stat *dst = buf;
      *dst = StatInitializer;
      dst->min  = hdr->densmin;
      dst->max  = hdr->densmax;
      dst->mean = hdr->avdens;
      dst->sd = hdr->sigma;
      cnt = 4;
      break;
    }

    default: return E_I3DATA_IMPL;

  }

  if ( count != NULL ) *count = cnt;

  return status;

}


static Status ImagicExtraWrite
              (const I3data *data,
               int code,
               Size count,
               const void *buf)

{
  Status status;

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( buf == NULL ) ) return exception( E_ARGVAL );

  Imageio *imageio = data->handle;
  if ( imageio == NULL ) return exception( E_IMAGICIO );

  ImagicMeta *meta = imageio->meta;
  ImagicHeader *hdr = &meta->header;

  switch ( code ) {

    case I3dataStat: {
      const Stat *src = buf;
      hdr->densmin = src->min;
      hdr->densmax = src->max;
      hdr->avdens = src->mean;
      hdr->sigma = src->sd;
      break;
    }

    default: status = E_I3DATA_IMPL;

  }

  return status;

}


extern Status ImagicExtra
              (Imageio *imageio,
               IOMode mode,
               void *extra)

{

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( extra == NULL ) ) return pushexception( E_ARGVAL );

  I3data *data = extra;
  data->init  = NULL;
  data->final = NULL;
  data->read    = ImagicExtraRead;
  data->readbuf = NULL;
  data->finalbuf = NULL;
  data->unpack   = NULL;
  data->pack     = NULL;
  data->write    = ImagicExtraWrite;
  data->writenew = ImagicExtraWrite;
  data->handle   = imageio;

  return E_NONE;

}
