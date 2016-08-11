/*----------------------------------------------------------------------------*
*
*  preproc.c  -  image: preprocessing
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "preproc.h"
#include "convol.h"
#include "mask.h"
#include "message.h"
#include "statistics.h"
#include "spatial.h"
#include "transfer.h"
#include "exception.h"
#include "macros.h"
#include <stdlib.h>
#include <string.h>


/* macros */

#define PreprocMessage( msg )  if ( flags & PreprocLog ) Message( msg, "\n" );


/* functions */

static Status PreprocCompstat
              (Size dim,
               const Size *len,
               const Real *addr,
               Size size,
               const Size *staori,
               const Size *stalen,
               Real *staaddr,
               Size stasize,
               Stat *stat,
               Coord grad[4],
               PreprocFlags flags)

{
  Status status;

  if ( stasize && ( stalen != len ) ) {
    status = ArrayCut( dim, len, addr, staori, stalen, staaddr, sizeof(Real) );
    if ( exception( status ) ) return status;
    len = stalen;
    addr = staaddr;
    size = stasize;
  }

  static const StatParam param = { StatAll };
  status = MinmaxmeanReal( size, addr, stat, &param );
  if ( exception( status ) ) return status;
  if ( flags & PreprocLog ) {
    MessageFormat( "  min %"CoordG",  max %"CoordG",  mean %"CoordG",  sd %"CoordG"\n", stat->min, stat->max, stat->mean, stat->sd );
  }

  switch ( dim ) {
    case 2:  status = exception( GradientLin2dReal( len, addr, grad ) ); break;
    case 3:  status = exception( GradientLin3dReal( len, addr, grad ) ); break;
    default: status = exception( E_INTERNAL );
  }
  if ( status ) return status;
  if ( flags & PreprocLog ) {
    MessageFormatBegin( "  grad %"CoordG"  %+"CoordG" x  %+"CoordG" y", grad[0], grad[1], grad[2] );
    if ( dim > 2 ) MessageFormat( "  %+"CoordG" z", grad[3] );
    MessageFormatEnd( "\n" );
  }

  return E_NONE;

}


static Status BoundsUint8
              (Size dim,
               const Size *srclen,
               const void *srcaddr,
               const Size *srcori,
               const Size *srcbox,
               Size *dstori,
               Size *dstbox)

{
  const uint8_t *src = srcaddr;

  if ( argcheck( srclen == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src    == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstori == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstbox == NULL ) ) return exception( E_ARGVAL );

  Size *o = dstori;
  Size *b = dstbox;

  Size siz = 1;
  for ( Size d = 0; d < dim; d++ ) {
    o[d] = ( srcori == NULL ) ? 0 : srcori[d];
    b[d] = ( srcbox == NULL ) ? srclen[d] : srcbox[d];
    siz *= srclen[d];
  }

  Size inc = 1;

  for ( Size d = 0; d < dim; d++ ) {

    Size stp = inc * srclen[d];

    Size i0, i1 = ( o[d] + b[d] ) * inc;
    while ( b[d] ) {
      i0 = i1 - inc;
      for ( Size j = 0; j < siz; j += stp ) {
        for ( Size i = i0 + j; i < i1 + j; i++ ) {
          if ( src[i] ) goto endloop1;
        }
      }
      i1 = i0;
      b[d]--;
    }
    endloop1:

    i0 = o[d] * inc;
    while ( b[d] && ( o[d] < srclen[d] ) ) {
      i1 = i0 + inc;
      for ( Size j = 0; j < siz; j += stp ) {
        for ( Size i = i0 + j; i < i1 + j; i++ ) {
          if ( src[i] ) goto endloop2;
        }
      }
      i0 = i1;
      o[d]++; b[d]--;
    }
    endloop2:

    inc = stp;

  }

  return E_NONE;

}


static Status Shrink2dUint8
              (const Size *srclen,
               const Size *srcori,
               const Size *srcbox,
               const Size *krnlen,
               void *dstaddr,
               Size *count)

{
  uint8_t *dst = dstaddr;

  if ( argcheck( srclen == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( krnlen == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dst    == NULL ) ) return exception( E_ARGVAL );

  if ( !krnlen[0] ) return exception( E_ARRAY_ZERO );
  if ( !krnlen[1] ) return exception( E_ARRAY_ZERO );

  if ( count != NULL ) *count = 0;

  Size nx = srclen[0];
  Size ny = srclen[1];

  Size ox = ( srcori == NULL ) ? 0 : srcori[0];
  Size oy = ( srcori == NULL ) ? 0 : srcori[1];

  if ( srcbox == NULL ) srcbox = srclen;
  Size px = ( ox + srcbox[0] < nx ) ? ox + srcbox[0] : nx;
  Size py = ( oy + srcbox[1] < ny ) ? oy + srcbox[1] : ny;

  Size mx = krnlen[0];
  Size my = krnlen[1];

  Size lx = mx / 2, hx = mx - lx;
  Size ly = my / 2, hy = my - ly;

  Size n = 0;

  for ( Size iy = oy; iy < py; iy++ ) {

    Size iy0 = ( iy > ly ) ? iy - ly : 0;
    Size iyn = ( iy < ny - hy ) ? iy + hy : ny;

    iy0 *= nx;
    iyn *= nx;

    for ( Size ix = ox; ix < px; ix++ ) {

      Size ix0 = ( ix > lx ) ? ix - lx : 0;
      Size ixn = ( ix < nx - hx ) ? ix + hx : nx;

      Size i = iy * nx + ix;

      if ( dst[i] == 1 ) {
        for ( Size y = iy0; y < iyn; y += nx ) {
          for ( Size x = ix0; x < ixn; x++ ) {
            if ( !dst[y+x] ) {
              dst[i] = 2; n++; goto endloop;
            }
          }
        }
      }
      endloop: continue;

    } /* end for ix */

  } /* end for iy */

  if ( count != NULL ) *count = n;

  return E_NONE;

}


static Status PreprocFill2d
              (const Size *msklen,
               void *mskaddr,
               const Size *krnlen,
               void *dstaddr,
               Size *count,
               Size *iter)

{
  uint8_t *msk = mskaddr;
  Real *dst = dstaddr;
  Status status;

  if ( argcheck( msklen == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( msk    == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( krnlen == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dst    == NULL ) ) return exception( E_ARGVAL );

  if ( !krnlen[0] ) return exception( E_ARRAY_ZERO );
  if ( !krnlen[1] ) return exception( E_ARRAY_ZERO );

  Size nx = msklen[0];
  Size ny = msklen[1];

  Size mx = krnlen[0];
  Size my = krnlen[1];

  if ( nx < mx ) return exception( E_CONVOL_SIZE );
  if ( ny < my ) return exception( E_CONVOL_SIZE );

  Size lx = mx / 2, hx = mx - lx;
  Size ly = my / 2, hy = my - ly;

  Size n = ny * nx;
  while ( n-- ) {
    if ( msk[n] ) msk[n] = 1;
  } 

  Index niter = 0, nfill = 0;

  Size ori[] = { 0, 0 };
  Size box[] = { nx, ny };

  while ( True ) {

    status = BoundsUint8( 2, msklen, msk, ori, box, ori, box );
    if ( exception( status ) ) return status;

    Size nshr = 0;
    Size shr[] = { 3, 3 };
    status = Shrink2dUint8( msklen, ori, box, shr, msk, &nshr );
    if ( exception( status ) ) return status;
    if ( !nshr ) break;
    niter++;

    for ( Size iy = ori[1]; iy < ori[1] + box[1]; iy++ ) {

      Size iy0 = ( iy > ly ) ? iy - ly : 0;
      Size iyn = ( iy < ny - hy ) ? iy + hy : ny;

      iy0 *= nx;
      iyn *= nx;

      for ( Size ix = ori[0]; ix < ori[0] + box[0]; ix++ ) {

        Size ix0 = ( ix > lx ) ? ix - lx : 0;
        Size ixn = ( ix < nx - hx ) ? ix + hx : nx;

        Size i = iy * nx + ix;

        if ( msk[i] == 2 ) {
          Real sum = 0; Size n = 0;
          for ( Size y = iy0; y < iyn; y += nx ) {
            for ( Size x = ix0; x < ixn; x++ ) {
              Size k = y + x;
              if ( !msk[k] ) {
                sum += dst[k]; n++;
              }
            }
          }
          if ( n ) {
            dst[i] = sum / n;
          }
          nfill++;
        }

      } /* end for ix */

    } /* end for iy */

    for ( Size iy = ori[1]; iy < ori[1] + box[1]; iy++ ) {

      for ( Size ix = ori[0]; ix < ori[0] + box[0]; ix++ ) {

        Size i = iy * nx + ix;
        if ( msk[i] == 2 ) msk[i] = 0;

      } /* end for ix */

    } /* end for iy */

  } /* end while */

  if ( count != NULL ) *count = nfill;
  if ( iter != NULL ) *iter = niter;

  return E_NONE;

}


static Status Grow2dUint8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr)

{
  const uint8_t *src = srcaddr;
  uint8_t *dst = dstaddr;

  if ( argcheck( srclen == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src    == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( krnlen == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dst    == NULL ) ) return exception( E_ARGVAL );

  if ( !krnlen[0] ) return exception( E_ARRAY_ZERO );
  if ( !krnlen[1] ) return exception( E_ARRAY_ZERO );

  Size nx = srclen[0];
  Size ny = srclen[1];

  Size mx = krnlen[0];
  Size my = krnlen[1];

  if ( nx < mx ) return exception( E_CONVOL_SIZE );
  if ( ny < my ) return exception( E_CONVOL_SIZE );

  Size lx = mx / 2, hx = mx - lx;
  Size ly = my / 2, hy = my - ly;

  Size n = ny * nx;
  while ( n-- ) {
    dst[n] = src[n] ? 2 : 0;
  } 

  for ( Size iy = 0; iy < ny; iy++ ) {

    Size ky0 = ( iy < ly ) ? 0 : iy - ly;
    Size kyn = ( iy > ny - hy ) ? ny : iy + hy;

    Size iy0 = ky0 * nx;
    Size iyn = kyn * nx;
    Size iyi = iy * nx;

    for ( Size ix = 0; ix < nx; ix++ ) {

      Size ix0 = ( ix < lx ) ? 0 : ix - lx;
      Size ixn = ( ix > nx - hx ) ? nx : ix + hx;

      if ( dst[iyi+ix] & 2 ) {
        for ( Size y = iy0; y < iyn; y += nx ) {
          for ( Size x = ix0; x < ixn; x++ ) {
            dst[y+x] |= 1;
          }
        }
      }

    } /* end for ix */

  }  /* end for iy */

  return E_NONE;

}


static Status Grow3dUint8
              (const Size *srclen,
               const void *srcaddr,
               const Size *krnlen,
               void *dstaddr)

{
  const uint8_t *src = srcaddr;
  uint8_t *dst = dstaddr;

  if ( argcheck( srclen == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src    == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( krnlen == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dst    == NULL ) ) return exception( E_ARGVAL );

  if ( !krnlen[0] ) return exception( E_ARRAY_ZERO );
  if ( !krnlen[1] ) return exception( E_ARRAY_ZERO );
  if ( !krnlen[2] ) return exception( E_ARRAY_ZERO );

  Size nx = srclen[0];
  Size ny = srclen[1];
  Size nz = srclen[2];

  Size mx = krnlen[0];
  Size my = krnlen[1];
  Size mz = krnlen[2];

  if ( nx < mx ) return exception( E_CONVOL_SIZE );
  if ( ny < my ) return exception( E_CONVOL_SIZE );
  if ( nz < mz ) return exception( E_CONVOL_SIZE );

  Size lx = mx / 2, hx = mx - lx;
  Size ly = my / 2, hy = my - ly;
  Size lz = mz / 2, hz = mz - lz;

  Size n = nz * ny * nx;
  while ( n-- ) {
    dst[n] = src[n] ? 2 : 0;
  } 

  for ( Size iz = 0; iz < nz; iz++ ) {

    Size kz0 = ( iz < lz ) ? 0 : iz - lz;
    Size kzn = ( iz > nz - hz ) ? nz : iz + hz;

    Size iz0 = kz0 * ny * nx;
    Size izn = kzn * ny * nx;
    Size izi = iz * ny * nx;

    for ( Size iy = 0; iy < ny; iy++ ) {

      Size ky0 = ( iy < ly ) ? 0 : iy - ly;
      Size kyn = ( iy > ny - hy ) ? ny : iy + hy;

      Size iy0 = ky0 * nx;
      Size iyn = kyn * nx;
      Size iyi = iy * nx;

      for ( Size ix = 0; ix < nx; ix++ ) {

        Size ix0 = ( ix < lx ) ? 0 : ix - lx;
        Size ixn = ( ix > nx - hx ) ? nx : ix + hx;

        if ( dst[izi+iyi+ix] & 2 ) {
          for ( Size z = iz0; z < izn; z += ny * nx ) {
            for ( Size y = iy0; y < iyn; y += nx ) {
              for ( Size x = ix0; x < ixn; x++ ) {
                dst[z+y+x] |= 1;
              }
            }
          }
        }

      } /* end for ix */

    } /* end for iy */

  } /* end for iz */

  return E_NONE;

}


static Status PreprocSub
              (Size dim,
               Type srctype,
               const Size *srclen,
               const void *srcaddr,
               Type msktype,
               const void *mskaddr,
               const Size *staori,
               const Size *stalen,
               Type dsttype,
               const Size *dstori,
               const Size *dstlen,
               void *dstaddr,
               const PreprocParam *param,
               PreprocFlags flags)

{
  Status status;

  if ( dim > 3 ) return exception( E_PREPROC_DIM );
  if ( flags & PreprocBin ) {
    if ( dsttype != TypeUint8 ) return exception( E_ARGVAL );
  } else if ( ( dsttype != srctype ) && ( dsttype != TypeReal ) ) {
    return exception( E_PREPROC_TYPE );
  }

  Size srcelsize = TypeGetSize( srctype );
  Size mskelsize = TypeGetSize( msktype );
  PreprocFlags func = flags & PreprocFunc;

  Size winlen[3], winsize;
  static const Size winoribuf[3] = { 0, 0, 0 };
  const Size *winori = ( dstori == NULL ) ? winoribuf : dstori;
  status = ArrayBox( dim, srclen, dstori, dstlen, winlen, &winsize );
  if ( exception( status ) ) return status;
  if ( !winsize ) return exception( E_ARRAY_ZERO );

  Size stalenbuf[3], stasize;
  if ( staori == NULL ) staori = winori;
  if ( stalen == NULL ) stalen = winlen;
  status = ArrayBox( dim, winlen, staori, stalen, stalenbuf, &stasize );
  logexception( status );
  if ( stalen != winlen ) stalen = stalenbuf;

  /* kernel */
  Size kerlen[3], kersize = 1;
  for ( Size d = 0; d < dim; d++ ) {
    kerlen[d] = ( param->kernel == NULL ) ? 3 : param->kernel[d];
    if ( !kerlen[d] ) kerlen[d] = 1;
    kersize *= kerlen[d];
  }

  /* buffers */
  Size cmpbuf = stasize * sizeof(Real);
  Size datbuf = winsize * sizeof(Real);
  Size fltbuf = winsize * MAX( srcelsize, sizeof(Real) );
  Size kerbuf = kersize * MAX( srcelsize, sizeof(Real) );
  Size winbuf = winsize * MAX( MAX( srcelsize, sizeof(Real) ), mskelsize );
  char *buf = malloc( cmpbuf + datbuf + fltbuf + kerbuf + winbuf );
  if ( buf == NULL ) return exception( E_MALLOC );
  Real *cmpaddr = stasize ? (Real *)buf : NULL;
  void *dataddr = buf + cmpbuf;
  void *fltaddr = buf + cmpbuf + datbuf;
  void *keraddr = buf + cmpbuf + datbuf + fltbuf;
  void *winaddr = buf + cmpbuf + datbuf + fltbuf + kerbuf;

  /* Gaussian kernel */
  if ( func == PreprocGauss ) {
    Real *ptr = keraddr;
    Size size = winsize;
    while ( size-- ) *ptr++ = 1;
    Coord rad[3];
    for ( Size d = 0; d < dim; d++ ) {
      rad[d] = ( param->rad == NULL ) ? 0.5 * kerlen[d] : 2 * param->rad[d];
    }
    MaskParam maskparam = MaskParamInitializer;
    maskparam.wid = rad;
    status = MaskGauss( dim, kerlen, TypeReal, keraddr, NULL, NULL, &maskparam );
    if ( exception( status ) ) goto exit;
  }

  /* preprocessing */

  if ( param->msg != NULL ) PreprocMessage( param->msg );

  status = ArrayCut( dim, srclen, srcaddr, winori, winlen, winaddr, srcelsize );
  if ( exception( status ) ) goto exit;
  void *wptr = winaddr;
  Type type = srctype;

  status = ScaleReal( type, winsize, winaddr, dataddr, NULL );
  if ( exception( status ) ) goto exit;
  void *fptr = dataddr;

  const Size *cmpori = staori, *cmplen = stalen; Size cmpsize = stasize;
  Stat st; Coord gr[4];
  status = PreprocCompstat( dim, winlen, dataddr, winsize, cmpori, cmplen, cmpaddr, cmpsize, &st, gr, flags );
  if ( exception( status ) ) goto exit;

  if ( ( flags & PreprocFunc ) || ( mskaddr != NULL ) ) {

    fptr = NULL;

    switch ( flags & PreprocFunc ) {

      case PreprocUndef: {
        memcpy( fltaddr, winaddr, winsize * srcelsize );
        break;
      }

      case PreprocMin: {
        PreprocMessage( " minimum filter" );
        switch ( dim ) {
          case 2: FilterMin2d( type, winlen, winaddr, kerlen, fltaddr ); break;
          case 3: FilterMin3d( type, winlen, winaddr, kerlen, fltaddr ); break;
          default: status = exception( E_PREPROC_DIM ); goto exit;
        }
        wptr = fltaddr;
        break;
      }

      case PreprocMax: {
        PreprocMessage( " maximum filter" );
        switch ( dim ) {
          case 2: FilterMax2d( type, winlen, winaddr, kerlen, fltaddr ); break;
          case 3: FilterMax3d( type, winlen, winaddr, kerlen, fltaddr ); break;
          default: status = exception( E_PREPROC_DIM ); goto exit;
        }
        wptr = fltaddr;
        break;
      }

      case PreprocMean: {
        PreprocMessage( " mean filter" );
        switch ( dim ) {
          case 2: FilterMean2dReal( winlen, dataddr, kerlen, fltaddr ); break;
          case 3: FilterMean3dReal( winlen, dataddr, kerlen, fltaddr ); break;
          default: status = exception( E_PREPROC_DIM ); goto exit;
        }
        wptr = fltaddr; type = TypeReal;
        fptr = fltaddr; cmplen = winlen; cmpsize = winsize; /* use whole image from here on for statistics */
        break;
      }

      case PreprocMedian: {
        PreprocMessage( " median filter" );
        switch ( dim ) {
          case 2: FilterMedian2d( type, winlen, winaddr, kerlen, keraddr, fltaddr ); break;
          case 3: FilterMedian3d( type, winlen, winaddr, kerlen, keraddr, fltaddr ); break;
          default: status = exception( E_PREPROC_DIM ); goto exit;
        }
        wptr = fltaddr;
        break;
      }

      case PreprocGauss: {
        PreprocMessage( " gaussian blur" );
        switch ( dim ) {
          case 2: Convol2dReal( winlen, dataddr, kerlen, keraddr, fltaddr ); break;
          case 3: Convol3dReal( winlen, dataddr, kerlen, keraddr, fltaddr ); break;
          default: status = exception( E_PREPROC_DIM ); goto exit;
        }
        wptr = fltaddr; type = TypeReal;
        fptr = fltaddr; cmplen = winlen; cmpsize = winsize; /* use whole image from here on for statistics */

        break;
      }

      default: status = exception( E_PREPROC_DIM ); goto exit;

    }

    if ( fptr == NULL ) {
      status = ScaleReal( type, winsize, wptr, dataddr, NULL );
      if ( exception( status ) ) goto exit;
      fptr = dataddr;
    }

    /* recompute statistics */
    if ( wptr == fltaddr ) {
      status = PreprocCompstat( dim, winlen, fptr, winsize, cmpori, cmplen, cmpaddr, cmpsize, &st, gr, flags );
      if ( exception( status ) ) goto exit;
    }

    if ( ( flags & PreprocMsk ) && ( mskaddr != NULL ) ) {

      /* cut out region of interest */
      status = ArrayCut( dim, srclen, mskaddr, winori, winlen, winaddr, mskelsize );
      if ( exception( status ) ) goto exit;

      status = ScaleReal( msktype, winsize, winaddr, winaddr, NULL );
      if ( exception( status ) ) goto exit;

      status = ScaleType( TypeUint8, winsize, winaddr, winaddr, NULL );
      if ( exception( status ) ) goto exit;

      PreprocMessage( " apply binary mask" );

      if ( param->grow ) {
        Size nsrc = 0;
        uint8_t *ptr = winaddr;
        if ( flags & PreprocLog ) {
          for ( Size i = 0; i < winsize; i++ ) {
            if ( ptr[i] ) nsrc++;
          }
        }
        Size g[] = { param->grow, param->grow, param->grow };
        switch ( dim ) {
          case 2: Grow2dUint8( winlen, winaddr, g, winaddr ); break;
          case 3: Grow3dUint8( winlen, winaddr, g, winaddr ); break;
          default: status = exception( E_PREPROC_DIM ); goto exit;
        }
        Size ndst = 0;
        if ( flags & PreprocLog ) {
          for ( Size i = 0; i < winsize; i++ ) {
            if ( ptr[i] ) ndst++;
          }
          MessageFormat( "  grow %"SizeU" + %"SizeU" = %"SizeU"\n", ndst - nsrc, nsrc, ndst );
        }
      }

      Size count = 0, iter = 0;
      switch ( dim ) {
        case 2: PreprocFill2d( winlen, winaddr, kerlen, fptr, &count, &iter ); break;
        case 3: status = exception( E_IMPL ); goto exit;
        default: status = exception( E_PREPROC_DIM ); goto exit;
      }
      if ( flags & PreprocLog ) {
        MessageFormat( "  iter %"SizeU", filled %"SizeU"\n", iter, count );
      }
      status = PreprocCompstat( dim, winlen, fptr, winsize, cmpori, cmplen, cmpaddr, cmpsize, &st, gr, flags );
      if ( exception( status ) ) goto exit;

    }

  } /* end if flags & PreprocFunc */

  /* correct gradient */

  if ( flags & PreprocGrad ) {

    Size iter = ( flags & PreprocIter ) ? 2 : 1;

    while ( iter-- ) {

      PreprocMessage( " correcting linear gradient" );

      switch ( dim ) {
        case 2: GradcorrLin2dReal( winlen, fptr, gr ); break;
        case 3: GradcorrLin3dReal( winlen, fptr, gr ); break;
        default: status = exception( E_PREPROC_DIM ); goto exit;
      }
      type = TypeReal;
      status = PreprocCompstat( dim, winlen, fptr, winsize, cmpori, cmplen, cmpaddr, cmpsize, &st, gr, flags );
      if ( exception( status ) ) goto exit;

    }

    if ( ( flags & PreprocLog ) && ( cmplen != winlen ) ) {
      PreprocMessage( "  full image statistics" );
      status = PreprocCompstat( dim, winlen, fptr, winsize, NULL, NULL, NULL, 0, &st, gr, flags );
      if ( exception( status ) ) goto exit;
    }
    cmplen = winlen;

  } /* end if flags & PreprocGrad */

  TransferParam transfer = TransferParamInitializer;
  Coord thrmin = -CoordMax;
  Coord thrmax = +CoordMax;

  /* clip outliers */

  if ( flags & ( PreprocClip | PreprocThr ) ) {

    if ( ( flags & PreprocClip ) && ( ( param->clipmin > 0 ) || ( param->clipmax > 0 ) ) ) {

      if ( param->clipmin > 0 ) thrmin = st.mean - param->clipmin * st.sd;
      if ( param->clipmax > 0 ) thrmax = st.mean + param->clipmax * st.sd;

      if ( flags & PreprocLog ) {
        if ( ( thrmin <= st.min ) && ( thrmax >= st.max ) ) {
          PreprocMessage( " no clipping" );
        } else {
          MessageBegin( " clipping", NULL );
          if ( thrmin > st.min ) MessageFormatPrint( " below s = %"CoordG" (%"CoordG")", param->clipmin, thrmin );
          if ( thrmax < st.max ) MessageFormatPrint( " above s = %"CoordG" (%"CoordG")", param->clipmax, thrmax );
          MessageEnd( "\n", NULL );
        }
      }

    }

    if ( ( flags & PreprocThr ) && ( param->thrmin < param->thrmax ) ) {
      if ( ( thrmin == -CoordMax ) || ( param->thrmin > thrmin ) ) thrmin = param->thrmin;
      if ( ( thrmax == +CoordMax ) || ( param->thrmax < thrmax ) ) thrmax = param->thrmax;
    }

    if ( ( thrmin > -CoordMax ) || ( thrmax < +CoordMax ) ) {

      if ( flags & PreprocLog ) {
        MessageFormat( " clipping at %"CoordG" and %"CoordG"\n", thrmin, thrmax );
      }
      transfer.thrmin = thrmin;
      transfer.thrmax = thrmax;
      transfer.flags = TransferThr;

    }

  }

  /* output */

  if ( flags & PreprocBin ) {

    Real *win = fptr; uint8_t *dst = dstaddr;
    for ( Size i = 0; i < winsize; i++ ) {
      if ( ( win[i] < thrmin ) || ( win[i] > thrmax ) ) {
        dst[i] = 1;
      } else {
        dst[i] = 0;
      }
    }

  } else {

    if ( ( flags & PreprocLog ) && ( cmplen != winlen ) ) {
      PreprocMessage( "  full image statistics" );
      status = PreprocCompstat( dim, winlen, fptr, winsize, NULL, NULL, NULL, 0, &st, gr, flags );
      if ( exception( status ) ) goto exit;
    }

    status = ScaleType( dsttype, winsize, fptr, dstaddr, &transfer );
    if ( exception( status ) ) goto exit;

  }

  exit:

  free( buf );

  return status;

}


extern Status Preproc
              (Size dim,
               Type srctype,
               const Size *srclen,
               const void *srcaddr,
               Type msktype,
               const void *mskaddr,
               const Size *statori,
               const Size *statlen,
               Type dsttype,
               const Size *dstori,
               const Size *dstlen,
               void *dstaddr,
               const PreprocParam *param)

{

  if ( param == NULL ) param = &PreprocParamInitializer;

  if ( param->flags & PreprocBin ) return exception( E_ARGVAL );

  return PreprocSub( dim, srctype, srclen, srcaddr, msktype, mskaddr, statori, statlen, dsttype, dstori, dstlen, dstaddr, param, param->flags );

}


extern Status PreprocBinary
              (Size dim,
               Type srctype,
               const Size *srclen,
               const void *srcaddr,
               const Size *statori,
               const Size *statlen,
               const Size *dstori,
               const Size *dstlen,
               uint8_t *dstaddr,
               const PreprocParam *param)

{

  if ( param == NULL ) param = &PreprocParamInitializer;

  PreprocFlags flags = 0;
  flags |= ( ( param->flags & PreprocThr ) && ( param->thrmin < param->thrmax ) ) ? PreprocBin : 0;
  flags |= ( ( param->flags & PreprocClip ) && ( ( param->clipmin > 0 ) || ( param->clipmax > 0 ) ) ) ? PreprocBin : 0;
  if ( !flags ) return exception( E_ARGVAL );

  return PreprocSub( dim, srctype, srclen, srcaddr, 0, NULL, statori, statlen, TypeUint8, dstori, dstlen, dstaddr, param, param->flags | flags );

}
