/*----------------------------------------------------------------------------*
*
*  i3dataprint.c  -  io: i3 data
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "i3data.h"
#include "statistics.h"
#include "exception.h"
#include "message.h"
#include <stdio.h>
#include <stdlib.h>


/* functions */

static void I3dataPrintSampling
            (const Coord *buf)

{

  MessageFormat( "sampling %"CoordG"\n", *buf );

}


static void I3dataPrintBinning
            (const Size *buf)

{

  MessageFormat( "binnig %"SizeU"\n", *buf );

}


static void I3dataPrintTransf
            (Size count,
             const Coord *buf)

{

  MessageStringBegin( "trf", NULL );

  while ( count-- ) {
    MessageFormatPrint( " %"CoordG, *buf++ );
  }

  MessageStringEnd( "\n", NULL );

}


static void I3dataPrintStat
            (const Stat *buf)

{

  MessageFormat( "min %"CoordG"  max %"CoordG"  mean %"CoordG"  sd %"CoordG"\n", buf->min, buf->max, buf->mean, buf->sd );

}


static void I3dataPrintCenters
            (Size count,
             const Index *buf)

{

  MessageFormat( "centers count %"SizeU"\n", count );

}


static void I3dataPrintCount
            (const Size *buf)

{

  MessageFormat( "count %"OffsetD"\n", *buf );

}


static void I3dataPrintImage
            (const I3Image *buf)

{
  const char *s = "  size";

  const Image *img = &buf->image;

  Size dim = img->dim;
  const Size *len = buf->len;
  const Index *low = buf->low;

  MessageFormatBegin( "dim %-4"SizeU, dim );

  for ( Size d = 0; d < dim; d++ ) {
    MessageFormatPrint( "%s %"SizeU, s, len[d] );
    s = " x";
  }

  s = "  [";
  for ( Size d = 0; d < dim; d++ ) {
  double high = low[d]; high += len[d] - 1;
    MessageFormatPrint( "%s%"IndexD"..%.0f]", s, low[d], high );
    s = " [";
  }

  if ( len[3] ) {
    MessageFormatPrint( "[%"SizeU"]", len[3] );
  }

  MessageString( "\n", NULL );

  MessageFormat( "data type %s", TypeIdent( img->type ) );

  if ( img->attr & ImageSymMask ) {
    const char *sym, *n;
    if ( img->attr & ImageSymConj) {
      if ( img->attr & ImageSymNeg) {
        sym = " antihermitian";
      } else {
        sym = " hermitian";
      }
    } else {
      if ( img->attr & ImageSymNeg ) {
        sym = " odd";
      } else {
        sym = " even";
      }
    }
    if ( img->attr & ImageNodd ) {
      n = " 2N+1";
    } else {
      n = " 2N";
    }
    MessageFormat( "\nsymmetry%s%s", sym, n );
  }

  MessageStringEnd( "\n", NULL );

}


extern void I3dataPrint
            (int code,
             Size count,
             const void *buf)

{

  switch ( code ) {

    case I3dataSampling: I3dataPrintSampling( buf ); break;

    case I3dataBinning: I3dataPrintBinning( buf ); break;

    case I3dataTransf: I3dataPrintTransf( count, buf ); break;

    case I3dataStat: I3dataPrintStat( buf ); break;

    case I3dataCenters: I3dataPrintCenters( count, buf ); break;

    case I3dataCount: I3dataPrintCount( buf ); break;

    case I3dataImage: I3dataPrintImage( buf ); break;

    default: return;

  }

}
