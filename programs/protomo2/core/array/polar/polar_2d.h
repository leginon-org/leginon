/*----------------------------------------------------------------------------*
*
*  polar_2d.h  -  array: spatial polar transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

/* template */

{
  Coord thrmin = -RealMax;
  Coord thrmax = +RealMax;
  Coord bias = 0, scale = 1;
  Coord fill = 0;
  Size nstat = 0;
  Coord min = +RealMax;
  Coord max = -RealMax;
  Coord sum = 0, sum2 = 0;
  TransformFlags flags = 0;
  Stat *stat = NULL;
  Status status = E_NONE;

  if ( argcheck( srclen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( srcaddr == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstlen  == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstaddr == NULL ) ) return exception( E_ARGVAL );

  if ( param != NULL ) {
    TransferParam *transf =  param->transf;
    if ( transf != NULL ) {
      if ( transf->flags & TransferThr ) {
        thrmin = transf->thrmin;
        thrmax = transf->thrmax;
        if ( thrmax > DSTTYPEMAX ) thrmax = DSTTYPEMAX;
        if ( thrmin < DSTTYPEMIN ) thrmin = DSTTYPEMIN;
      }
      if ( transf->flags & TransferBias)  bias  = transf->bias;
      if ( transf->flags & TransferScale) scale = transf->scale;
    }
    flags = param->flags;
    if ( flags & TransformFill ) fill = param->fill;
    if ( fill > DSTTYPEMAX ) fill = DSTTYPEMAX;
    if ( fill < DSTTYPEMIN ) fill = DSTTYPEMIN;
    stat = param->stat;
  }

  {
    const SRCTYPE *src = srcaddr;
    DSTTYPE *dst = dstaddr;
    Coord a00 = ( A == NULL ) ? 1 : *A++;
    Coord a01 = ( A == NULL ) ? 0 : *A++;
    Coord a10 = ( A == NULL ) ? 0 : *A++;
    Coord a11 = ( A == NULL ) ? 1 : *A++;
    Coord b0 = ( b == NULL ) ? srclen[0] / 2 : b[0];
    Coord b1 = ( b == NULL ) ? srclen[1] / 2 : b[1];
    Coord c0 = 2.0 * Pi / ( ( c == NULL ) ? dstlen[0] : c[0] );
    Coord c1 = ( c == NULL ) ? 1.0 : c[1];
    Size ip, dp;

    for ( ip = 0, dp = 0; ip < dstlen[0]; ip++, dp++ ) {
      Coord p = c0 * ip;
      Coord xp = cos( p ); 
      Coord yp = sin( p );
      Size ir, dr;

      for ( ir = 0, dr = dp; ir < dstlen[1]; ir++, dr += dstlen[0] ) {
        Coord r = c1 * ir;
        Coord x = r * xp;
        Coord y = r * yp;
        Coord x0 = a00 * x + a10 * y + b0;
        Coord x1 = a01 * x + a11 * y + b1;

        Coord x0a = fabs( x0 );
        Coord x0i = floor( x0a );
        Coord x0d = x0a - x0i;

        Coord x1a = fabs( x1 );
        Coord x1i = floor( x1a );
        Coord x1d = x1a - x1i;

        Size i0, i1;
        Size j0, j1;
        Coord dstval;

        if ( flags & TransformCyc ) {

          if ( x0d < CoordEPS ) {
            i0 = x0a;
            i0 %= srclen[0];
            j0 = i0;
          } else if ( x0 < 0 ) {
            j0 = x0i;
            j0 %= srclen[0];
            i0 = j0 ? j0 - 1 : srclen[0] - 1;
          } else {
            i0 = x0i;
            i0 %= srclen[0];
            j0 = i0 + 1;
            if ( j0 == srclen[0] ) j0 = 0;
          }

          if ( x1d < CoordEPS ) {
            i1 = x1a;
            i1 %= srclen[1];
            j1 = i1;
          } else if ( x1 < 0 ) {
            j1 = x1i;
            j1 %= srclen[1];
            i1 = j1 ? j1 - 1 : srclen[1] - 1;
          } else {
            i1 = x1i;
            i1 %= srclen[1];
            j1 = i1 + 1;
            if ( j1 == srclen[1] ) j1 = 1;
          }

        } else {

          if ( x0d < CoordEPS ) {
            i0 = x0a;
            j0 = i0;
          } else if ( x0 < 0 ) {
            goto clip;
          } else {
            i0 = x0a;
            j0 = i0 + 1;
            if ( j0 == srclen[0] ) goto clip;
          }

          if ( x1d < CoordEPS ) {
            i1 = x1a;
            j1 = i1;
          } else if ( x1 < 0 ) {
            goto clip;
          } else {
            i1 = x1a;
            j1 = i1 + 1;
            if ( j1 == srclen[1] ) goto clip;
          }

        }

        dstval = ( 1 - x0d ) * ( ( 1 - x1d ) * src[ i0 + i1 * srclen[0] ] + x1d * src[ i0 + j1 * srclen[0] ] )
               +       x0d   * ( ( 1 - x1d ) * src[ j0 + i1 * srclen[0] ] + x1d * src[ j0 + j1 * srclen[0] ] );

        dstval = ( dstval - bias ) * scale;
        if ( dstval < thrmin ) {
          dstval = thrmin;
        } else if ( dstval > thrmax ) {
          dstval = thrmax;
        }
        if ( stat != NULL ) {
          if ( dstval < min ) min = dstval;
          if ( dstval > max ) max = dstval;
          sum += dstval;
          sum2 += dstval * dstval;
          nstat++;
        }
        dst[dr] = dstval;
        continue;

        clip:
        dst[dr] = fill;
        status = E_TRANSFORM_CLIP;

      } /* end for ix */

    } /* end for iy */

  }

  if ( stat != NULL ) {
    stat->count = nstat;
    stat->min = min;
    stat->max = max;
    stat->mean = sum / nstat;
    stat->sd = sum2;
    stat->sd = nstat * sum2 - sum * sum;
    stat->sd = ( (stat->sd > 0 ) && nstat ) ? ( sqrt( stat->sd ) / nstat ) : 0;
  }

  return status;

}
