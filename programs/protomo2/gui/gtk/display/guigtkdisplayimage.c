/*----------------------------------------------------------------------------*
*
*  guigtkdisplayimage.c  -  guigtk: EM image viewer
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "guigtkdisplaycommon.h"
#include "imagearray.h"
#include "imageio.h"
#include "exception.h"
#include "mathdefs.h"
#include <stdlib.h>
#include <string.h>


/* functions */

static Status GuigtkDisplayImageExtend
              (const Image *srcdscr,
               const void *srcaddr,
               GuigtkDisplayImage *dstimg)

{
  Image src = *srcdscr;
  Image dst = dstimg->dscr;
  Size dstsize = dstimg->size;
  Status status;

  Size srcsize;
  status = ArraySize( src.dim, src.len, TypeGetSize( src.type ), &srcsize );
  if ( exception( status ) ) return status;

  Size count = 1;
  for ( Size d = src.dim; d > 1; d-- ) {
    Size len =  src.len[d-1];
    if ( src.low[d-1] == -(Index)( len / 2 ) ) break;
    srcsize /= len;
    dstsize /= len;
    count *= len;
    src.dim--;
    dst.dim--;
  }

  const char *srcptr = srcaddr;
  char *dstptr = dstimg->addr;

  while ( count-- ) {

    status = ImageExtend( &src, srcptr, &dst, dstptr, 0 );
    if ( exception( status ) ) return status;

    srcptr += srcsize * TypeGetSize( src.type );
    dstptr += dstsize * TypeGetSize( dst.type );

  }

  return E_NONE;

}


extern Status GuigtkDisplayLoadImage
              (GuigtkDisplay *display,
               const Image *src,
               const void *addr)

{
  GuigtkDisplayImage *img = &display->img;
  GuigtkDisplayImage *dsp = &display->dsp;
  GuigtkDisplayImage new;
  Status status;

  display->status &= ~GuigtkDisplayDisp;

  if ( src != NULL ) {

    Bool sym = src->attr & ImageSymSym;
    Bool cpy = display->status & GuigtkDisplayDupl;
    Bool set = True;

    new.dscr.len = new.len;
    new.dscr.low = new.low;

    status = ImageMetaCopy( src, &new.dscr, sym ? ImageModeSym : 0 );
    if ( status ) return status;

    status = ArraySize( new.dscr.dim, new.dscr.len, TypeGetSize( new.dscr.type ), &new.size );
    if ( status ) return status;

    if ( sym || cpy ) {
      new.addr = malloc( new.size * TypeGetSize( new.dscr.type ) );
      if ( new.addr == NULL ) return E_MALLOC;
      new.alloc = True;
    } else if ( src != &img->dscr ) {
      if ( addr == NULL ) return E_GUIGTKDISPLAY;
      new.addr = (void *)addr;
      new.alloc = False;
    } else {
      if ( img->addr == NULL ) return E_GUIGTKDISPLAY;
      set = False;
    }

    if ( sym ) {
      status = GuigtkDisplayImageExtend( src, addr, &new );
      if ( status ) { free( new.addr ); return status; }
    } else if ( cpy ) {
      memcpy( new.addr, addr, new.size * TypeGetSize( new.dscr.type ) );
    }

    if ( sym || cpy ) {
      if ( display->handle != NULL ) {
        status = GuigtkDisplayClose( display );
        if ( status ) ExceptionClear();
      }
      if ( img->alloc ) free( img->addr );
    }

    if ( set ) {
      img->dscr.dim = new.dscr.dim;
      img->dscr.len = img->len;
      img->dscr.low = img->low;
      img->dscr.type = new.dscr.type;
      img->dscr.attr = new.dscr.attr;
      for ( Size d = 0; d < new.dscr.dim; d++ ) {
        img->len[d] = new.len[d];
        img->low[d] = new.low[d];
      }
      for ( Size d = new.dscr.dim; d < 3; d++ ) {
        img->len[d] = 0;
        img->low[d] = 0;
      }
      img->size = new.size;
      img->addr = new.addr;
      img->alloc = new.alloc;
    }

    if ( dsp->alloc ) free( dsp->addr );
    *dsp = *img;
    dsp->alloc = False;

    if ( img->dscr.type == TypeCmplx ) {

      dsp->addr = malloc( dsp->size * sizeof(Real) );
      if ( dsp->addr == NULL ) return E_MALLOC;
      dsp->alloc = True;
      dsp->dscr.type = TypeReal;

    }

    display->z = dsp->dscr.len[2] / 2; /* origin is 0 */

    display->dx = dsp->dscr.len[0] / 2;
    display->dy = dsp->dscr.len[1] / 2;

    display->fmt = GraphDataFormat( dsp->dscr.type );
    display->glt = GraphDataType( dsp->dscr.type );
    if ( !display->fmt || !display->glt ) return E_IMAGEIO_TYPE;

  }

  if ( display->func >= GuigtkDisplayFuncMax ) {
    display->func = TypeIsCmplx( img->dscr.type ) ? GuigtkDisplayAbs : GuigtkDisplayRe;
  }

  if ( img->dscr.type == TypeCmplx ) {

    Real *src = img->addr;
    Real *dst = dsp->addr;

    switch ( display->func ) {
      case GuigtkDisplayIm: src++;
      case GuigtkDisplayRe: {
        for ( Size i = 0; i < img->size; i++ ) {
          *dst++ = *src++; src++;
        }
        break;
      }
      case GuigtkDisplayAbs: {
        for ( Size i = 0; i < img->size; i++ ) {
          Real re = *src++;
          Real im = *src++;
          *dst++ = FnSqrt( re * re + im * im );
        }
        break;
      }
      case GuigtkDisplayLogAbs: {
        for ( Size i = 0; i < img->size; i++ ) {
          Real re = *src++;
          Real im = *src++;
          Real abs = FnSqrt( re * re + im * im );
          *dst++ = FnLog( abs + 1E-5 );
        }
        break;
      }
      default: return E_GUIGTKDISPLAY;
    }

  }

  status = GuigtkDisplayStat( display );
  if ( status ) return status;

  status = GuigtkDisplayHistogram( display );
  if ( status ) return status;

  display->status |= GuigtkDisplayDisp;

  return E_NONE;

}


extern Status GuigtkDisplayUnloadImage
              (GuigtkDisplay *display)

{
  GuigtkDisplayImage *img = &display->img;
  GuigtkDisplayImage *dsp = &display->dsp;
  Status status;

  display->status &= ~GuigtkDisplayDisp;
  display->func = GuigtkDisplayFuncMax;

  if ( display->handle != NULL ) {
    status = GuigtkDisplayClose( display );
    if ( status ) ExceptionClear();
  }

  if ( img->alloc ) free( img->addr );
  if ( dsp->alloc ) free( dsp->addr );

  img->alloc = False; img->addr = NULL;
  dsp->alloc = False; dsp->addr = NULL;

  return E_NONE;

}


extern Status GuigtkDisplayOpen
              (const char *path,
               GuigtkDisplay *display)

{
  Image src;
  Size srcsize;
  Status status;

  Imageio *handle = ImageioOpenReadOnly( path, &src, &display->iopar );
  status = testcondition( handle == NULL );
  if ( status ) return status;

  if ( ( src.dim < 2 ) || ( src.dim > 3 ) ) {
    status = ImageioErrPath( handle, E_IMAGEIO_DIM ); goto error1;
  }

  status = ArraySize( src.dim, src.len, TypeGetSize( src.type ), &srcsize );
  if ( exception( status ) ) {
    status = ImageioErrPath( handle, E_IMAGEIO_BIG ); goto error1;
  }

  const char *name = ImageioGetPath( handle );
  const char *ptr = strrchr( name, DIRSEP ) + 1;
  if ( ( ptr != NULL ) && *ptr ) name = ptr;
  name = strdup( name );
  if ( name == NULL ) { pushexception( E_MALLOC ); goto error1; }

  void *addr = ImageioBeginRead( handle, 0, 0 );
  status = testcondition( addr == NULL );
  if ( status ) goto error2;

  if ( display->handle != NULL ) {
    status = GuigtkDisplayClose( display );
    if ( exception( status ) ) ExceptionClear();
  }

  if ( display->img.alloc && ( display->img.addr != NULL ) ) {
    free( display->img.addr );
  }

  display->name = name;
  display->handle = handle;
  display->img.dscr.dim = src.dim;
  display->img.dscr.len = display->img.len;
  display->img.dscr.low = display->img.low;
  display->img.dscr.type = src.type;
  display->img.dscr.attr = src.attr;
  display->img.size = srcsize;
  display->img.addr = addr;
  display->img.alloc = False;
  for ( Size d = 0; d < src.dim; d++ ) {
    display->img.len[d] = src.len[d];
    display->img.low[d] = src.low[d];
  }
  for ( Size d = src.dim; d < 3; d++ ) {
    display->img.len[d] = 0;
    display->img.low[d] = 0;
  }

  display->status |= GuigtkDisplayRead;

  return E_NONE;

  error2: free( (char *)name );
  error1: ImageioClose( handle );

  return status;

}


extern Status GuigtkDisplayClose
              (GuigtkDisplay *display)

{
  Status stat, status = E_NONE;

  if ( display->handle != NULL ) {

    if ( display->status & GuigtkDisplayRead ) {
      status = ImageioEndRead( display->handle, 0, 0, display->img.addr );
      logexception( status );
    }

    stat = ImageioClose( display->handle );
    if ( exception( stat ) ) status = stat;

    if ( display->name != NULL ) free( (char *)display->name );

    display->name = NULL;
    display->handle = NULL;
    display->img.addr = NULL;
    display->img.alloc = False;

    display->status &= ~( GuigtkDisplayRead | GuigtkDisplayDisp );

  }

  return status;

}
