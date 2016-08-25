/*----------------------------------------------------------------------------*
*
*  imagestatprint.c  -  image: statistics
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagestat.h"
#include "exception.h"
#include "message.h"


/* functions */

extern Status ImageStatPrint
              (const char *hdr,
               const Image *src,
               const void *srcaddr,
               const ImageStatParam *param)

{
  Stat stat;
  ImageStatParam par;
  Status status;

  if ( src  == NULL ) return exception( E_ARGVAL );

  par = ImageStatParamInitializer;
  if ( param == NULL ) {
    par.stat.flags = StatAll;
    par.flags = ImageStatAll;
  } else {
    par.stat.flags = param->stat.flags;
    par.flags = param->flags;
  }

  if ( ( srcaddr != NULL ) && ( par.stat.flags & StatAll ) ) {
    status = ImageStat( src, srcaddr, &stat, &par );
    if ( exception( status ) ) return status;
  }

  MessageLock;

  if ( hdr != NULL ) {
    MessageStringHeadr( hdr, "\n", NULL );
  }

  if ( par.flags & ImageStatType ) {
    MessageStringHeadr( "data type ", TypeIdent( src->type ), "\n", NULL );
  }

  if ( ( par.flags & ImageStatSym ) && ( src->attr & ImageSymMask ) ) {
    MessageStringHeadr( "symmetry ", NULL );
    if ( src->attr & ImageSymConj ) {
      MessageStringPrint( ( src->attr & ImageSymNeg ) ? " antihermitian" : " hermitian", NULL );
    } else {
      MessageStringPrint( ( src->attr & ImageSymNeg ) ? " odd" : " even", NULL );
    }
    MessageStringPrint( ( src->attr & ImageNodd ) ? " 2N+1" : " 2N", "\n", NULL );
  }

  if ( ( par.flags & ImageStatDom ) && ( src->attr & ImageFourspc ) ) {
    MessageStringHeadr( "domain    Fourier\n", NULL );
  }

  if ( par.flags & ImageStatSize ) {
    const char *s="  size";
    MessageFormatHeadr( "dim %-4"SizeU, src->dim );
    for ( Size d = 0; d < src->dim; d++ ) {
      MessageFormatPrint( "%s %"SizeU, s, src->len[d] );
      s = " x";
    }
    s = "  [";
    for ( Size d = 0; d < src->dim; d++ ) {
      double high = src->low[d]; high += src->len[d] - 1;
      MessageFormatPrint( "%s%"IndexD"..%.0f]", s, src->low[d], high );
      s = " [";
    }
    MessageStringPrint( "\n", NULL );
  }

  if ( par.stat.flags & StatAll ) {
    const char *i = TypeIsImag( src->type ) ? "i" : "";
    MessageStringHeadr( NULL );
    if ( par.stat.flags & StatMin ) {
      MessageFormatPrint( "min %"CoordG"%s  ", stat.min, i );
    }
    if ( par.stat.flags & StatMax ) {
      MessageFormatPrint( "max %"CoordG"%s  ", stat.max, i );
    }
    if ( par.stat.flags & StatMean ) {
      MessageFormatPrint( "mean %"CoordG"%s  ", stat.mean, i );
    }
    if ( par.stat.flags & StatSd ) {
      MessageFormatPrint( "sd %"CoordG"%s  ", stat.sd, i );
    }
    MessageStringPrint( "\n", NULL );
  }

  MessageUnlock;

  return E_NONE;

}
