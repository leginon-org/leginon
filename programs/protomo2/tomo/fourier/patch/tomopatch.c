/*----------------------------------------------------------------------------*
*
*  tomopatch.c  -  fourier: patch
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomopatch.h"
#include "imagearray.h"
#include "windowfourier.h"
#include "mat2.h"
#include "strings.h"
#include "exception.h"
#include "message.h"
#include <stdlib.h>
#include <string.h>


/* types */

typedef struct {
  Index iy;
  Cmplx *buf;
} Patch;


/* constants */

#define NP 127

#define logbuflen 96


/* functions */

static Status TomopatchResample
              (const Image *src,
               const void *srcaddr,
               Coord Ap[3][2],
               Coord rp[2],
               const Window *win,
               const WindowFourier *fouwin,
               const MaskParam *winmsk,
               Real *winaddr,
               Cmplx *fouaddr,
               Cmplx *sumaddr)

{
  Coord r[2];
  Status status;

  Mat2TranspMulVec( Ap, rp, r );
  r[0] += Ap[2][0];
  r[1] += Ap[2][1];

  status = WindowResample( src->len, src->type, srcaddr, Ap[0], r, win, winaddr, NULL, winmsk );
  if ( exception( status ) ) return status;

  status = FourierRealTransf( fouwin->forw, winaddr, fouaddr, 1 );
  if ( exception( status ) ) return status;

  Real *fou = (Real *)fouaddr;
  Real *sum = (Real *)sumaddr;
  for ( Size i = 0; i < fouwin->fousize; i++ ) {
    Real re = *fou++;
    Real im = *fou++;
    *sum++ += FnSqrt( re*re + im*im );
    *sum++ = 0;
  }

  return E_NONE;

}


static Status TomopatchAlloc
              (Size *np,
               Patch *p,
               Size ip,
               Index iy,
               Size size)

{

  if ( ip >= NP ) {
    return userexception( "dimension [NP] too small" );
  }

  while ( *np <= ip ) {
    p[*np].buf = NULL;
    (*np)++;
  }

  if ( p[ip].buf == NULL ) {
    p[ip].buf = malloc( size * sizeof(Cmplx) );
    if ( p[ip].buf == NULL ) return pushexception( E_MALLOC );
  }

  p[ip].iy = iy;
  memset( p[ip].buf, 0, size * sizeof(Cmplx) );

  return E_NONE;

}


static void TomopatchDealloc
            (Size np,
             Patch *p)

{

  while ( np-- ) {
    free( p->buf );
    p++;
  }

}


static Status TomopatchExtract
              (const Image *src,
               const void *srcaddr,
               Coord Ap[3][2],
               const Window *win,
               const WindowFourier *fouwin,
               Real *winaddr,
               Cmplx *fouaddr,
               Image *dst,
               Size *np,
               Patch *p,
               Size *ip,
               const char *logbuf,
               const TomopatchParam *param)

{
  Index iymin = 0, iymax = -1;
  Index ix1, ix2, iy;
  Coord rp[2];
  Real pwr;
  Status status;

  dst->len[2] = 0;
  dst->low[2] = 0;
  *ip = 0;

  if ( *logbuf ) {
    Message( logbuf, "\n" );
  }

  for ( iy = 0; iy <= param->maxy; ) {

    rp[1] = iy; rp[1] *= param->inc[1];

    if ( *logbuf ) {
      MessageFormatHeadr( "   y %4d", iy );
    }

    status = TomopatchAlloc( np, p, *ip, iy, fouwin->fousize );
    if ( exception( status ) ) return status;

    Cmplx *sum = p[*ip].buf;

    for ( ix1 = 0; ix1 <= param->maxx; ) {
      rp[0] = ix1; rp[0] *= param->inc[0];
      status = TomopatchResample( src, srcaddr, Ap, rp, win, fouwin, param->msk, winaddr, fouaddr, sum );
      if ( status == E_WINDOW_AREA ) break;
      if ( pushexception( status ) ) return status;
      ix1++;
    }
    if ( *logbuf ) {
      MessageFormatPrint( "   +x %3d", ix1 );
    }

    for ( ix2 = -1; ix2 >= param->minx; ) {
      rp[0] = ix2; rp[0] *= param->inc[0];
      status = TomopatchResample( src, srcaddr, Ap, rp, win, fouwin, param->msk, winaddr, fouaddr, sum );
      if ( status == E_WINDOW_AREA ) break;
      if ( pushexception( status ) ) return status;
      ix2--;
    }
    Index n = ix1 - ix2 - 1;
    if ( *logbuf ) {
      MessageFormatPrint( "   -x %3d   total %3d", n - ix1, n );
    }

    if ( n > 0 ) {
      status = ImageSumAbs2( &fouwin->fou, sum, &pwr );
      if ( pushexception( status ) ) return status;
      (*ip)++;
      if ( *logbuf ) {
        MessageFormatPrint( "    power %-13.5e\n", pwr );
      }
    } else {
      if ( *logbuf ) {
        MessageStringPrint( "\n", NULL );
      }
      break;
    }

    iymax = iy;
    iy++;

  } /* end for iy */

  for ( iy = -1; iy >= param->miny; ) {

    rp[1] = iy; rp[1] *= param->inc[1];

    if ( *logbuf ) {
      MessageFormatHeadr( "   y %4d", iy );
    }

    status = TomopatchAlloc( np, p, *ip, iy, fouwin->fousize );
    if ( exception( status ) ) return status;

    Cmplx *sum = p[*ip].buf;

    for ( ix1 = 0; ix1 <= param->maxx; ) {
      rp[0] = ix1; rp[0] *= param->inc[0];
      status = TomopatchResample( src, srcaddr, Ap, rp, win, fouwin, param->msk, winaddr, fouaddr, sum );
      if ( status == E_WINDOW_AREA ) break;
      if ( pushexception( status ) ) return status;
      ix1++;
    }
    if ( *logbuf ) {
      MessageFormatPrint( "   +x %3d", ix1 );
    }

    for ( ix2 = -1; ix2 >= param->minx; ) {
      rp[0] = ix2; rp[0] *= param->inc[0];
      status = TomopatchResample( src, srcaddr, Ap, rp, win, fouwin, param->msk, winaddr, fouaddr, sum );
      if ( status == E_WINDOW_AREA ) break;
      if ( pushexception( status ) ) return status;
      ix2--;
    }
    Index n = ix1 - ix2 - 1;
    if ( *logbuf ) {
      MessageFormatPrint( "   -x %3d   total %3d", n - ix1, n );
    }

    if ( n > 0 ) {
      status = ImageSumAbs2( &fouwin->fou, sum, &pwr );
      if ( pushexception( status ) ) return status;
      (*ip)++;
      if ( *logbuf ) {
        MessageFormatPrint( "    power %-13.5e\n", pwr );
      }
    } else {
      if ( *logbuf ) {
        MessageStringPrint( "\n", NULL );
      }
      break;
    }

    iymin = iy;
    iy--;

  } /* end while iy */

  if ( iymax >= iymin ) {
    dst->len[2] = iymax - iymin + 1;
    dst->low[2] = iymin;
  }

  return E_NONE;

}


static Status TomopatchFile
              (const char *path,
               const Size number,
               const Image *image,
               const Patch *p,
               const Size ip,
               const WindowFourier *fouwin,
               Cmplx *foubuf)

{
  char numbuf[64];
  Status status;

  sprintf( numbuf, "_patch_%"SizeU".img", number );
  char *filepath = StringConcat( path, numbuf, NULL );
  if ( filepath == NULL ) return exception( E_MALLOC );

  ImageioParam ioparam = ImageioParamDefault;
  ioparam.cap = ImageioCapUnix | ImageioCapLib;
  ioparam.mode |= ImageioModeDel;

  Imageio *imageio = ImageioCreate( filepath, image, &ioparam );
  status = testcondition( imageio == NULL );
  if ( status ) goto error1;

  Size imagesize = image->len[1] * image->len[0];

  Image fou = fouwin->fou;
  fou.type = image->type;

  Image img = *image;
  img.dim = fou.dim;

  for ( Size i = 0; i < ip; i++ ) {

    Cmplx *buf = p[i].buf;

    if ( image->type == TypeReal ) {
      Real *src = (Real *)buf, *dst = src;
      for ( Size j = 0; j < fouwin->fousize; j++ ) {
        *dst++ = *src++; src++;
      }
    }

    if ( imagesize > fouwin->fousize ) {
      status = ImageExtend( &fou, buf, &img, foubuf, 0 );
      if ( pushexception( status ) ) goto error2;
      buf = foubuf;
    }

    status = ImageioWrite( imageio, ( p[i].iy - image->low[2] ) * (Offset)imagesize, imagesize, buf );
    if ( exception( status ) ) goto error2;

  }

  status = ImageioUndel( imageio );
  if ( exception( status ) ) goto error2;

  status = ImageioClose( imageio );
  logexception( status );

  return status;

  error2: ImageioClose( imageio );
  error1: free( filepath );

  return status;

}


extern Status TomopatchWrite
              (const Tomoseries *series,
               const char *path,
               const TomopatchParam *param)

{
  Size isum, nsum = 0;
  Patch sum[NP];
  Coord Ap[3][2], Bp[3][2];
  Size index;
  void *addr;
  char logbuf[logbuflen];
  char *wpath = NULL;
  Status status;

  if ( argcheck( series == NULL ) ) return pushexception( E_ARGVAL );

  if ( param  == NULL ) return pushexception( E_ARGVAL );

  if ( ( path == NULL ) || !*path ) {
    wpath = TomoseriesOutName( series, NULL );
    status = testcondition( wpath == NULL );
    if ( status ) return status;
    path = wpath;
  }

  WindowParam winpar = WindowParamInitializer;
  winpar.area = param->area;

  Window win;
  status = WindowInit( 2, param->len, &win, &winpar );
  if ( pushexception( status ) ) goto error1;

  WindowFourierParam foupar = WindowFourierParamInitializer;
  foupar.opt = FourierZeromean;
  foupar.back = False;

  WindowFourier fouwin;
  status = WindowFourierInit( 2, param->len, NULL, NULL, NULL, &fouwin, &foupar );
  if ( pushexception( status ) ) goto error1;

  Real *buf = WindowAlloc( &win );
  if ( buf == NULL ) { status = pushexception( E_MALLOC ); goto error2; }

  Cmplx *foubuf = malloc( win.size * sizeof(Cmplx) );
  if ( foubuf == NULL ) { status = pushexception( E_MALLOC ); goto error3; }

  Image img; Size len[3]; Index low[3];
  img.len = len;
  img.low = low;

  status = ImageMetaCopy( &fouwin.fou, &img, param->extend ? ImageModeSym : 0 );
  if ( pushexception( status ) ) goto error4;

  img.dim = 3;
  if ( !param->complx ) {
    img.type = TypeReal;
    img.attr &= ~ImageSymConj;
  }

  const Tomodata *data = series->data;
  const TomodataDscr *dscr = data->dscr;
  const Tomogeom *geom = series->geom;
  const TomotiltGeom *tiltgeom = series->tilt->tiltgeom;

  for ( index = 0; index < series->tilt->images; index++, dscr++, geom++, tiltgeom++ ) {

    const TomotiltAxis *axis = series->tilt->tiltaxis + tiltgeom->axisindex;

    status = TomotiltMatAxis2( axis, tiltgeom, Ap );
    if ( pushexception( status ) ) goto error5;

    Ap[2][0] = geom->Ap[2][0];
    Ap[2][1] = geom->Ap[2][1];

    TomoseriesResampleGeom( dscr, series->sampling, Ap, Bp );

    addr = TomodataBeginRead( data->cache, dscr, index );
    status = testcondition( addr == NULL );
    if ( status ) goto error5;

    if ( series->flags & TomoLog ) {
      TomodataLogString( data, data->dscr, index, logbuf, logbuflen );
    } else {
      *logbuf = 0;
    }

    status = TomopatchExtract( &dscr->img, addr, Bp, &win, &fouwin, buf, foubuf, &img, &nsum, sum, &isum, logbuf, param );
    if ( exception( status ) ) goto error6;

    status = TomodataEndRead( data->cache, dscr, index, addr );
    if ( exception( status ) ) goto error5;

    Size number = series->tilt->tiltimage[index].number;
    status = TomopatchFile( wpath, number, &img, sum, isum, &fouwin, foubuf );
    if ( exception( status ) ) goto error5;

  }

  TomopatchDealloc( nsum, sum );
  free( foubuf );
  free( buf );

  status = WindowFourierFinal( &fouwin );
  logexception( status );

  if ( wpath != NULL ) free( wpath );

  return status;

  error6: TomodataEndRead( data->cache, dscr, index, addr );
  error5: TomopatchDealloc( nsum, sum );
  error4: free( foubuf );
  error3: free( buf );
  error2: WindowFourierFinal( &fouwin );
  error1: if ( wpath != NULL ) free( wpath );

  return status;

}
