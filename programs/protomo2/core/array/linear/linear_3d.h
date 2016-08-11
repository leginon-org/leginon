/*----------------------------------------------------------------------------*
*
*  linear_3d.h  -  array: spatial linear transformations
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
  Coord tol = ArrayCoordTol / 2;
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
    Coord a02 = ( A == NULL ) ? 0 : *A++;
    Coord a10 = ( A == NULL ) ? 0 : *A++;
    Coord a11 = ( A == NULL ) ? 1 : *A++;
    Coord a12 = ( A == NULL ) ? 0 : *A++;
    Coord a20 = ( A == NULL ) ? 0 : *A++;
    Coord a21 = ( A == NULL ) ? 0 : *A++;
    Coord a22 = ( A == NULL ) ? 1 : *A++;
    Coord b0 = ( b == NULL ) ? srclen[0] / 2 : b[0];
    Coord b1 = ( b == NULL ) ? srclen[1] / 2 : b[1];
    Coord b2 = ( b == NULL ) ? srclen[2] / 2 : b[2];
    Coord c0 = ( c == NULL ) ? dstlen[0] / 2 : c[0];
    Coord c1 = ( c == NULL ) ? dstlen[1] / 2 : c[1];
    Coord c2 = ( c == NULL ) ? dstlen[2] / 2 : c[2];

    for ( Size iz = 0; iz < dstlen[2]; iz++ ) {

      Coord z = iz - c2; 
      Coord z0 = a20 * z + b0;
      Coord z1 = a21 * z + b1;
      Coord z2 = a22 * z + b2;

      for ( Size iy = 0; iy < dstlen[1]; iy++ ) {

        Coord y = iy - c1;
        Coord y0 = a10 * y + z0;
        Coord y1 = a11 * y + z1;
        Coord y2 = a12 * y + z2;

        for ( Size ix = 0; ix < dstlen[0]; ix++ ) {

          Coord x = ix - c0;
          Coord x0 = a00 * x + y0;
          Coord x1 = a01 * x + y1;
          Coord x2 = a02 * x + y2;

          Coord x0i = Floor( x0 );
          Coord x0d = x0 - x0i;

          Coord x1i = Floor( x1 );
          Coord x1d = x1 - x1i;

          Coord x2i = Floor( x2 );
          Coord x2d = x2 - x2i;

          Size i0, i1, i2;
          Size j0, j1, j2;

          if ( flags & TransformCyc ) {

            if ( x0i < 0 ) {
              i0 = -x0i;
              i0 %= srclen[0];
              if ( i0 ) i0 = srclen[0] - i0;
            } else {
              i0 = x0i;
              i0 %= srclen[0];
            }
            if ( x0d < tol ) {
              j0 = i0;
              x0d = 0;
            } else {
              j0 = i0 + 1;
              if ( j0 == srclen[0] ) j0 = 0;
            }

            if ( x1i < 0 ) {
              i1 = -x1i;
              i1 %= srclen[1];
              if ( i1 ) i1 = srclen[1] - i1;
            } else {
              i1 = x1i;
              i1 %= srclen[1];
            }
            if ( x1d < tol ) {
              j1 = i1;
              x1d = 0;
            } else {
              j1 = i1 + 1;
              if ( j1 == srclen[1] ) j1 = 0;
            }

            if ( x2i < 0 ) {
              i2 = -x2i;
              i2 %= srclen[2];
              if ( i2 ) i2 = srclen[2] - i2;
            } else {
              i2 = x2i;
              i2 %= srclen[2];
            }
            if ( x2d < tol ) {
              j2 = i2;
              x2d = 0;
            } else {
              j2 = i2 + 1;
              if ( j2 == srclen[2] ) j2 = 0;
            }

          } else {

            if ( x0i < 0 ) goto clip;
            i0 = x0i;
            if ( x0d < tol ) {
              j0 = i0;
              x0d = 0;
            } else {
              j0 = i0 + 1;
            }
            if ( j0 >= srclen[0] ) goto clip;

            if ( x1i < 0 ) goto clip;
            i1 = x1i;
            if ( x1d < tol ) {
              j1 = i1;
              x1d = 0;
            } else {
              j1 = i1 + 1;
            }
            if ( j1 >= srclen[1] ) goto clip;

            if ( x2i < 0 ) goto clip;
            i2 = x2i;
            if ( x2d < tol ) {
              j2 = i2;
              x2d = 0;
            } else {
              j2 = i2 + 1;
            }
            if ( j2 >= srclen[2] ) goto clip;

          }

          Size kii = srclen[0] * ( i1 + srclen[1] * i2 );
          Size kij = srclen[0] * ( i1 + srclen[1] * j2 );
          Size kji = srclen[0] * ( j1 + srclen[1] * i2 );
          Size kjj = srclen[0] * ( j1 + srclen[1] * j2 );

          Coord dstval = ( 1 - x0d ) * ( ( 1 - x1d ) * ( ( 1 - x2d ) * src[i0+kii] + x2d * src[i0+kij] ) + x1d * ( ( 1 - x2d ) * src[i0+kji] + x2d * src[i0+kjj] ) )
                       +       x0d   * ( ( 1 - x1d ) * ( ( 1 - x2d ) * src[j0+kii] + x2d * src[j0+kij] ) + x1d * ( ( 1 - x2d ) * src[j0+kji] + x2d * src[j0+kjj] ) );

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
          *dst++ = dstval;
          continue;

          clip:
          *dst++ = fill;
          status = E_TRANSFORM_CLIP;

        } /* end for ix */

      } /* end for iy */

    } /* end for iz */

  }

  if ( stat != NULL ) {
    stat->count = nstat;
    stat->min = min;
    stat->max = max;
    stat->mean = sum / nstat;
    stat->sd = sum2;
    stat->sd = nstat * sum2 - sum * sum;
    stat->sd = ( ( stat->sd > 0 ) && nstat ) ? ( Sqrt( stat->sd ) / nstat ) : 0;
  }

  return status;

}
