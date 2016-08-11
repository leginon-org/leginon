/*----------------------------------------------------------------------------*
*
*  peak_1d_real.c  -  array: spatial operations
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

extern Status Peak1dReal
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

  Coord cx = 0;

  const Coord *ctr = ( param == NULL ) ? NULL : param->ctr;
  const Coord *rad = ( param == NULL ) ? NULL : param->rad;

  PeakFlags flags = ( param == NULL ) ? PeakOriginCentered : param->flags;

  Size ipx;
  Real max = -RealMax;

  if ( ( ctr == NULL ) && ( rad == NULL ) ) {

    Size imax = 0;
    for ( Size i = 0; i < nx; i++ ) {
      if ( src[i] > max ) {
        max = src[i]; imax = i;
      }
    }

    ipx = imax;

  } else {

    Coord rx = -1, x2 = 0;

    if ( rad != NULL ) {
      rx = rad[0]; if ( rx < 0 ) rx = nx / 2;
    }

    if ( ctr != NULL ) {
      cx = ctr[0];
    } else if ( flags & PeakOriginCentered ) {
      cx = nx / 2;
    }
    if ( flags & PeakModeCyc ) {
      cx = Fmod( cx, nx ); if ( cx < 0 ) cx += nx;
    }
    if ( ( cx < 0 ) || ( cx >= nx ) ) {
      cx = 0;
      status = E_SPATIAL_PEAK; /* indicates error later */
    }
    ipx = cx;

    if ( !status ) {

      const Real *s = src;

      max = s[ipx];

      for ( Size ix = 0; ix < nx; ix++ ) {
        Coord x = ix - cx;
        if ( flags & PeakModeCyc ) {
          if ( x >= nx / 2 ) x -= nx;
        }
        if ( rx > 0 ) {
          x2 = x / rx; x2 *= x2;
        }

        if ( x2 <= 1 ) {
          if ( *s > max ) {
            max = *s;
            ipx = ix;
          }
        }
        s++;

      } /* end for ix */

    } /* end if !status */

  } /* end if ctr */

  Coord px = ipx;

  if ( max == -RealMax ) {

    status = E_SPATIAL_PEAK;

  } else if ( pos != NULL ) {

    Real min = max;
    Coord m0 = 0;
    Coord mx = 0;

    const Coord *cmrad = ( param == NULL ) ? NULL : param->cmrad;

    Coord cmrx = ( cmrad == NULL ) ? 0 : cmrad[0];

    Size dx = ( cmrx < nx / 2 ) ? ( ( cmrx > 1 ) ? Ceil( cmrx ) : 1 ) : ( ( nx - 1 ) / 2 );

    Coord x0 = dx; Size bx0, bx1, ix0;

    if ( flags & PeakModeCyc ) {
      ix0 = ( ipx < dx ) ? ( nx - dx ) : ( ipx - dx );
      bx0 = 0; bx1 = dx + dx;
    } else {
      Size ix1 = ( ipx < nx - 1 - dx ) ? ( ipx + dx ) : ( nx - 1 );
      ix0 = ( ipx < dx ) ? 0 : ( ipx - dx );
      bx0 = ( ipx < dx ) ? ( dx - ipx ) : 0;
      bx1 = bx0 + ix1 - ix0;
    }

    if ( bx0 > bx1 ) {

      status = E_SPATIAL_PEAK;

    } else if ( ( cmrx > 1 ) && ( flags & PeakCMEllips ) ) {

      /* search minimum within box */
      Size bx = bx0, ix = ix0;
      while ( bx <= bx1 ) {
        const Real *sx = src + ix;
        Coord x = bx - x0;
        Coord x2 = x / cmrx; x2 *= x2;
        if ( x2 <= 1 ) {
          if ( *sx < min ) {
            min = *sx;
          }
        }
        bx++; ix++; if ( ix >= nx ) ix = 0;
      } /* end while bx */
      /* center of mass */
      bx = bx0, ix = ix0;
      while ( bx <= bx1 ) {
        const Real *sx = src + ix;
        Coord x = bx - x0;
        Coord x2 = x / cmrx; x2 *= x2;
        if ( x2 <= 1 ) {
          Coord s = (*sx) - min;
          m0 += s;
          mx += x * s;
        }
        bx++; ix++; if ( ix >= nx ) ix = 0;
      } /* end while bx */

    } else {

      /* search minimum within box */
      Size bx = bx0, ix = ix0;
      while ( bx <= bx1 ) {
        const Real *sx = src + ix;
        if ( *sx < min ) {
          min = *sx;
        }
        bx++; ix++; if ( ix >= nx ) ix = 0;
      } /* end while bx */
      /* center of mass */
      bx = bx0, ix = ix0;
      while ( bx <= bx1 ) {
        const Real *sx = src + ix;
        Coord x = bx - x0;
        Coord s = (*sx) - min;
        m0 += s;
        mx += x * s;
        bx++; ix++; if ( ix >= nx ) ix = 0;
      } /* end while bx */

    }

    if ( m0 != 0 ) {

      px += mx / m0; if ( px < 0 ) { px += nx; } else if ( px >= nx ) { px -= nx; }

      if ( flags & PeakHeightInterp ) {

        Coord px0 = Floor( px ); Size jx0 = px, jx1 = jx0 + 1;

        if ( flags & PeakModeCyc ) {
          if ( jx1 == nx ) jx1 = 0;
        } else {
          if ( jx1 == nx ) jx1 = jx0;
        }

        Coord dx1 = px - px0, dx0 = 1 - dx1;

        Coord src0 = src[jx0], src1 = src[jx1];

        max = dx0 * src0 + dx1 * src1;

      } /* end if flags */

    } /* end if m0 */

  } /* end if pos */

  if ( ipos != NULL ) {
    ipos[0] = ipx;
  }
  if ( pos != NULL ) {
    if ( flags & PeakOriginRelative ) {
      pos[0] = px - cx;
      if ( flags & PeakModeCyc ) {
        pos[0] = Fmod( pos[0], nx ) + nx;
        if ( pos[0] >= nx ) pos[0] -= nx;
        if ( pos[0] >= nx / 2 ) pos[0] -= nx;
      }
    } else {
      pos[0] = px;
    }
  }
  if ( pk != NULL ) {
    Real *p = pk; *p = max;
  }

  return status;

}
