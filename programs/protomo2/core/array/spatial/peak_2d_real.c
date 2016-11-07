/*----------------------------------------------------------------------------*
*
*  peak_2d_real.c  -  array: spatial operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "spatial.h"
#include "exception.h"
#include "mathdefs.h"


/* functions */

extern Status Peak2dReal
              (const Size *srclen,
               const void *srcaddr,
               Size *ipos,
               Coord *pos,
               void *pk,
               const PeakParam *param)

{
  const Real *src = srcaddr;
  Status status = E_NONE;

  if ( argcheck( srclen == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( src    == NULL ) ) return exception( E_ARGVAL );

  Size nx = srclen[0];
  Size ny = srclen[1];

  Coord cx = 0;
  Coord cy = 0;

  const Coord *ctr = ( param == NULL ) ? NULL : param->ctr;
  const Coord *rad = ( param == NULL ) ? NULL : param->rad;

  PeakFlags flags = ( param == NULL ) ? PeakOriginCentered : param->flags;

  Size ipx, ipy;
  Real max = -RealMax;

  if ( ( ctr == NULL ) && ( rad == NULL ) ) {

    Size imax = 0;
    for ( Size i = 0; i < nx * ny; i++ ) {
      if ( src[i] > max ) {
        max = src[i]; imax = i;
      }
    }

    ipx = imax % nx; imax /= nx;
    ipy = imax;

  } else {

    Coord rx = -1, x2 = 0;
    Coord ry = -1, y2 = 0;

    if ( rad != NULL ) {
      rx = rad[0]; if ( rx < 0 ) rx = nx / 2;
      ry = rad[1]; if ( ry < 0 ) ry = ny / 2;
    }

    if ( ctr != NULL ) {
      cx = ctr[0];
      cy = ctr[1];
    } else if ( flags & PeakOriginCentered ) {
      cx = nx / 2;
      cy = ny / 2;
    }
    if ( flags & PeakModeCyc ) {
      cx = Fmod( cx, nx ); if ( cx < 0 ) cx += nx;
      cy = Fmod( cy, ny ); if ( cy < 0 ) cy += ny;
    }
    if ( ( cx < 0 ) || ( cy < 0 ) || ( cx >= nx ) || ( cy >= ny ) ) {
      cx = 0; cy = 0;
      status = E_SPATIAL_PEAK; /* indicates error later */
    }
    ipx = cx;
    ipy = cy;

    if ( !status ) {

      const Real *s = src;

      max = s[ipx+nx*ipy];

      for ( Size iy = 0; iy < ny; iy++ ) {
        Coord y = iy - cy;
        if ( flags & PeakModeCyc ) {
          if ( y >= ny / 2 ) y -= ny;
        }
        if ( ry > 0 ) {
          y2 = y / ry; y2 *= y2;
        }

        for ( Size ix = 0; ix < nx; ix++ ) {
          Coord x = ix - cx;
          if ( flags & PeakModeCyc ) {
            if ( x >= nx / 2 ) x -= nx;
          }
          if ( rx > 0 ) {
            x2 = x / rx; x2 *= x2;
          }

          if ( x2 + y2 <= 1 ) {
            if ( *s > max ) {
              max = *s;
              ipx = ix;
              ipy = iy;
            }
          }
          s++;

        } /* end for ix */

      } /* end for iy */

    } /* end if !status */

  } /* end if ctr */

  Coord px = ipx;
  Coord py = ipy;

  if ( max == -RealMax ) {

    status = E_SPATIAL_PEAK;

  } else if ( pos != NULL ) {

    Real min = max;
    Coord m0 = 0;
    Coord mx = 0;
    Coord my = 0;

    const Coord *cmrad = ( param == NULL ) ? NULL : param->cmrad;

    Coord cmrx = ( cmrad == NULL ) ? 0 : cmrad[0];
    Coord cmry = ( cmrad == NULL ) ? 0 : cmrad[1];

    Size dx = ( cmrx < nx / 2 ) ? ( ( cmrx > 1 ) ? Ceil( cmrx ) : 1 ) : ( ( nx - 1 ) / 2 );
    Size dy = ( cmry < ny / 2 ) ? ( ( cmry > 1 ) ? Ceil( cmry ) : 1 ) : ( ( ny - 1 ) / 2 );

    Coord x0 = dx; Size bx0, bx1, ix0;
    Coord y0 = dy; Size by0, by1, iy0;

    if ( flags & PeakModeCyc ) {
      ix0 = ( ipx < dx ) ? ( nx - dx ) : ( ipx - dx );
      iy0 = ( ipy < dy ) ? ( ny - dy ) : ( ipy - dy );
      bx0 = 0; bx1 = dx + dx;
      by0 = 0; by1 = dy + dy;
    } else {
      Size ix1 = ( ipx < nx - 1 - dx ) ? ( ipx + dx ) : ( nx - 1 );
      Size iy1 = ( ipy < ny - 1 - dy ) ? ( ipy + dy ) : ( ny - 1 );
      ix0 = ( ipx < dx ) ? 0 : ( ipx - dx );
      iy0 = ( ipy < dy ) ? 0 : ( ipy - dy );
      bx0 = ( ipx < dx ) ? ( dx - ipx ) : 0;
      by0 = ( ipy < dy ) ? ( dy - ipy ) : 0;
      bx1 = bx0 + ix1 - ix0;
      by1 = by0 + iy1 - iy0;
    }

    if ( ( bx0 > bx1 ) || ( by0 > by1 ) ) {

      status = E_SPATIAL_PEAK;

    } else if ( ( cmrx > 1 ) && ( cmry > 1 ) && ( flags & PeakCMEllips ) ) {

      /* search minimum within box */
      Size by = by0, iy = iy0;
      while ( by <= by1 ) {
        Size bx = bx0, ix = ix0;
        const Real *sy = src + iy * nx;
        Coord y = by - y0;
        Coord y2 = y / cmry; y2 *= y2;
        while ( bx <= bx1 ) {
          const Real *sx = sy + ix;
          Coord x = bx - x0;
          Coord x2 = x / cmrx; x2 *= x2;
          if ( x2 + y2 <= 1 ) {
            if ( *sx < min ) {
              min = *sx;
            }
          }
          bx++; ix++; if ( ix >= nx ) ix = 0;
        } /* end while bx */
        by++; iy++; if ( iy >= ny ) iy = 0;
      } /* end while by */
      /* center of mass */
      by = by0, iy = iy0;
      while ( by <= by1 ) {
        Size bx = bx0, ix = ix0;
        const Real *sy = src + iy * nx;
        Coord y = by - y0;
        Coord y2 = y / cmry; y2 *= y2;
        while ( bx <= bx1 ) {
          const Real *sx = sy + ix;
          Coord x = bx - x0;
          Coord x2 = x / cmrx; x2 *= x2;
          if ( x2 + y2 <= 1 ) {
            Coord s = (*sx) - min;
            m0 += s;
            mx += x * s;
            my += y * s;
          }
          bx++; ix++; if ( ix >= nx ) ix = 0;
        } /* end while bx */
        by++; iy++; if ( iy >= ny ) iy = 0;
      } /* end while by */

    } else {

      /* search minimum within box */
      Size by = by0, iy = iy0;
      while ( by <= by1 ) {
        Size bx = bx0, ix = ix0;
        const Real *sy = src + iy * nx;
        while ( bx <= bx1 ) {
          const Real *sx = sy + ix;
          if ( *sx < min ) {
            min = *sx;
          }
          bx++; ix++; if ( ix >= nx ) ix = 0;
        } /* end while bx */
        by++; iy++; if ( iy >= ny ) iy = 0;
      } /* end while by */
      /* center of mass */
      by = by0, iy = iy0;
      while ( by <= by1 ) {
        Size bx = bx0, ix = ix0;
        const Real *sy = src + iy * nx;
        Coord y = by - y0;
        while ( bx <= bx1 ) {
          const Real *sx = sy + ix;
          Coord x = bx - x0;
          Coord s = (*sx) - min;
          m0 += s;
          mx += x * s;
          my += y * s;
          bx++; ix++; if ( ix >= nx ) ix = 0;
        } /* end while bx */
        by++; iy++; if ( iy >= ny ) iy = 0;
      } /* end while by */

    }

    if ( m0 != 0 ) {

      px += mx / m0; if ( px < 0 ) { px += nx; } else if ( px >= nx ) { px -= nx; }
      py += my / m0; if ( py < 0 ) { py += ny; } else if ( py >= ny ) { py -= ny; }

      if ( flags & PeakHeightInterp ) {

        Coord px0 = Floor( px ); Size jx0 = px, jx1 = jx0 + 1;
        Coord py0 = Floor( py ); Size jy0 = py, jy1 = jy0 + 1;

        if ( flags & PeakModeCyc ) {
          if ( jx1 == nx ) jx1 = 0;
          if ( jy1 == ny ) jy1 = 0;
        } else {
          if ( jx1 == nx ) jx1 = jx0;
          if ( jy1 == ny ) jy1 = jy0;
        }

        Size Jy0 = nx * jy0;
        Size Jy1 = nx * jy1;

        Coord dx1 = px - px0, dx0 = 1 - dx1;
        Coord dy1 = py - py0, dy0 = 1 - dy1;

        Coord src0 = src[jx0+Jy0], src1 = src[jx0+Jy1];
        Coord src2 = src[jx1+Jy0], src3 = src[jx1+Jy1];

        max = dx0 * ( dy0 * src0 + dy1 * src1 )
            + dx1 * ( dy0 * src2 + dy1 * src3 );

      } /* end if flags */

    } /* end if m0 */

  } /* end if pos */

  if ( ipos != NULL ) {
    ipos[0] = ipx;
    ipos[1] = ipy;
  }
  if ( pos != NULL ) {
    if ( flags & PeakOriginRelative ) {
      pos[0] = px - cx;
      pos[1] = py - cy;
      if ( flags & PeakModeCyc ) {
        pos[0] = Fmod( pos[0], nx ) + nx;
        pos[1] = Fmod( pos[1], ny ) + ny;
        if ( pos[0] >= nx ) pos[0] -= nx;
        if ( pos[1] >= ny ) pos[1] -= ny;
        if ( pos[0] >= nx / 2 ) pos[0] -= nx;
        if ( pos[1] >= ny / 2 ) pos[1] -= ny;
      }
    } else {
      pos[0] = px;
      pos[1] = py;
    }
  }
  if ( pk != NULL ) {
    Real *p = pk; *p = max;
  }

  return status;

}
