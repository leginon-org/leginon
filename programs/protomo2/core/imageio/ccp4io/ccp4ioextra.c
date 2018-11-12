/*----------------------------------------------------------------------------*
*
*  ccp4ioextra.c  -  imageio: CCP4 files
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
#include "imageioextra.h"
#include "imageiochecksum.h"
#include "statistics.h"
#include "exception.h"
#include <string.h>


/* functions */

static Status CCP4ExtraRead
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
  if ( imageio == NULL ) return exception( E_CCP4IO );

  CCP4Meta *meta = imageio->meta;
  CCP4Header *hdr = &meta->header;
  Bool isccp4 = ( *imageio->format->version.ident == 'C' ) ? True : False;

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
      dst->min  = hdr->amin;
      dst->max  = hdr->amax;
      dst->mean = hdr->amean;
      if ( isccp4 ) dst->sd = hdr->arms;
      cnt = 4;
      break;
    }

    default: return E_I3DATA_IMPL;

  }

  if ( count != NULL ) *count = cnt;

  return status;

}


static Status CCP4ExtraWrite
              (const I3data *data,
               int code,
               Size count,
               const void *buf)

{
  Status status;

  if ( argcheck( data == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( buf == NULL ) ) return exception( E_ARGVAL );

  Imageio *imageio = data->handle;
  if ( imageio == NULL ) return exception( E_CCP4IO );

  CCP4Meta *meta = imageio->meta;
  CCP4Header *hdr = &meta->header;
  Bool isccp4 = ( *imageio->format->version.ident == 'C' ) ? True : False;

  switch ( code ) {

    case I3dataStat: {
      const Stat *src = buf;
      hdr->amin = src->min;
      hdr->amax = src->max;
      hdr->amean = src->mean;
      if ( isccp4 ) hdr->arms = src->sd;
      break;
    }

    default: status = E_I3DATA_IMPL;

  }

  return status;

}


extern Status CCP4Extra
              (Imageio *imageio,
               IOMode mode,
               void *extra)

{

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( extra == NULL ) ) return pushexception( E_ARGVAL );

  I3data *data = extra;
  data->init  = NULL;
  data->final = NULL;
  data->read    = CCP4ExtraRead;
  data->readbuf = NULL;
  data->finalbuf = NULL;
  data->unpack   = NULL;
  data->pack     = NULL;
  data->write    = CCP4ExtraWrite;
  data->writenew = CCP4ExtraWrite;
  data->handle   = imageio;

  return E_NONE;

}
