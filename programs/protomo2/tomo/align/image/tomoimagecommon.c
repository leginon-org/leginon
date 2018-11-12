/*----------------------------------------------------------------------------*
*
*  tomoimagecommon.c  -  align: image geometry
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoimage.h"
#include "exception.h"
#include <stdlib.h>
#include <stdio.h>


/* functions */

static Status TomoimageSortAlloc
              (Tomoimage *image,
               Size images)

{

  image->min = malloc( 2 * images * sizeof(Size) );
  if ( image->min == NULL ) return pushexception( E_MALLOC );
  image->max = image->min + images;

  for ( Size i = 0; i < 2 * images; i++ ) {
    image->min[i] = SizeMax;
  }

  return E_NONE;

}


static void TomoimageSort
            (const TomotiltGeom *geom,
             Size images,
             Size axisindex,
             Size *sort,
             Size *count)

{

  Size cnt = 0;
  for ( Size i = 0; i < images; i++ ) {
    if ( geom[i].axisindex == axisindex ) {
      sort[cnt++] = i;
    }
  }

  for ( Size i = 0; i < cnt; i++ ) {
    for ( Size j = i + 1; j < cnt; j++ ) {
      if ( geom[sort[j]].theta < geom[sort[i]].theta ) {
        Size k = sort[j]; sort[j] = sort[i]; sort[i] = k;
      }
    }
  }

  *count = cnt;

}


static Status TomoimageSortAxes
              (const Tomotilt *tilt,
               Tomoimage *image,
               Size *start)

{
  const TomotiltGeom *geom = tilt->tiltgeom;
  Size a0 = geom[image->cooref].axisindex;
  Size images = tilt->images;
  Size min = 0, max = 0;

  Size *sort = malloc( images * sizeof(*sort) );
  if ( sort == NULL ) return exception( E_MALLOC );

  Size c0;
  TomoimageSort( geom, images, a0, sort, &c0 );

  Size r0 = SizeMax;
  for ( Size i = 0; i < c0; i++ ) {
    if ( sort[i] == image->cooref ) r0 = i;
  }
  if ( r0 == SizeMax ) return exception( E_TOMOIMAGE );

  Size i = r0;
  while ( i-- > 0 ) {
    image->min[min++] = sort[i];
  }
  i = r0;
  while ( ++i < c0 ) {
    image->max[max++] = sort[i];
  }
  if ( min > max ) {
    max = min;
  } else {
    min = max;
  }
  if ( start != NULL ) {
    *start++ = 0;
    *start++ = min;
  }

  Coord t0 = geom[sort[r0]].theta;
  Coord t1 = r0 ? geom[sort[r0-1]].theta : CoordMax;
  Coord t2 = ( r0 + 1 < c0 ) ? geom[sort[r0+1]].theta : CoordMax;

  for ( Size a = 0; a < tilt->axes; a++ ) {

    if ( a != a0 ) {

      Size c;
      TomoimageSort( geom, images, a, sort, &c );

      Size r = SizeMax; Coord d0 = CoordMax;
      for ( Size i = 0; i < c; i++ ) {
        Coord d = geom[sort[i]].theta - t0;
        if ( d * d < d0 ) {
          d0 = d * d; r = i;
        }
      }
      if ( r == SizeMax ) return exception( E_TOMOIMAGE );

      Size r1 = r;
      if ( t1 < CoordMax ) {
        Coord d1 = d0;
        for ( Size i = 0; i < c; i++ ) {
          Coord d = geom[sort[i]].theta - t1;
          if ( d * d < d1 ) {
            d1 = d * d; r1 = i;
          }
        }
      }

      Size r2 = r;
      if ( t2 < CoordMax ) {
        Coord d2 = d0;
        for ( Size i = 0; i < c; i++ ) {
          Coord d = geom[sort[i]].theta - t2;
          if ( d * d < d2 ) {
            d2 = d * d; r2 = i;
          }
        }
      }

      if ( start != NULL ) *start++ = min;

      if ( r1 < r ) {
        r2 = ++r1;
      } else if ( r2 > r ) {
        r1 = r2;
      } else {
        r1 = r;
        r2 = r + 1;
        image->min[min++] = sort[r];
        max = min;
      }

      while ( r1-- ) {
        image->min[min++] = sort[r1];
      }
      while ( r2 < c ) {
        image->max[max++] = sort[r2++];
      }
      if ( min > max ) {
        max = min;
      } else {
        min = max;
      }

      if ( start != NULL ) *start++ = min;

    }

  }

  image->count = min;

  free( sort );

  return E_NONE;

}


extern Status TomoimageSortSeparate
              (const Tomotilt *tilt,
               Tomoimage *image)

{
  Status status;

  status = TomoimageSortAlloc( image, tilt->images );
  if ( exception( status ) ) return status;

  status = TomoimageSortAxes( tilt, image, NULL );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern Status TomoimageSortSimultaneous
              (const Tomotilt *tilt,
               Tomoimage *image,
               Coord startangle)

{
  const TomotiltGeom *geom = tilt->tiltgeom;
  Status status;

  Size *start = malloc( 2 * tilt->axes * sizeof(*start) );
  if ( start == NULL ) return exception( E_MALLOC );

  Coord *angle = malloc( tilt->images * sizeof(*angle) );
  if ( angle == NULL ) { status = exception( E_MALLOC ); goto exit1; }

  status = TomoimageSortAlloc( image, tilt->images );
  if ( exception( status ) ) goto exit2;

  status = TomoimageSortAxes( tilt, image, start );
  if ( exception( status ) ) goto exit2;

  Size *imagemin = image->min;
  Size *imagemax = image->max;

  status = TomoimageSortAlloc( image, tilt->images );
  if ( exception( status ) ) goto exit3;

  for ( Size i = 0; i < start[1]; i++ ) {
    Coord tmin = ( imagemin[i] < SizeMax ) ? Fabs( geom[imagemin[i]].theta ) : CoordMax;
    Coord tmax = ( imagemax[i] < SizeMax ) ? Fabs( geom[imagemax[i]].theta ) : CoordMax;
    if ( tmin == CoordMax ) {
      angle[i] = tmax;
    } else if ( tmax == CoordMax ) {
      angle[i] = tmin;
    } else if ( tmin > tmax ) {
      angle[i] = tmin;
    } else {
      angle[i] = tmax;
    }
    if ( angle[i] == CoordMax ) { status = exception( E_TOMOIMAGE ); goto exit3; }
    if ( startangle > 0 ) {
      if ( ( tmin <= startangle ) && ( tmax <= startangle ) ) start[0] = i;
    }
  }

  for ( Size i = 1; i < start[1]; i++ ) {
    angle[i-1] = ( angle[i-1] + angle[i] ) / 2;
  }
  angle[start[1]-1] = CoordMax;

  Bool loop = True;
  Size index = 0;

  for ( Size i = 0; i < start[0]; i++ ) {
    image->min[index] = imagemin[i];
    image->max[index] = imagemax[i];
    index++;
  }

  for ( Size i = 0; loop; i++ ) {

    loop = False;

    if ( ( i >= start[0] ) && ( i < start[1] ) ) {
      image->min[index] = imagemin[i];
      image->max[index] = imagemax[i];
      index++;
      loop = True;
    }

    Coord t0 = ( i < start[1] ) ? angle[i] : CoordMax;

    Bool loop2;

    do {

      loop2 = False;

      for ( Size k = 2; k < 2 * tilt->axes; k += 2 ) {

        if ( start[k] < start[k+1] ) {
          Coord tmin = ( imagemin[start[k]] < SizeMax ) ? Fabs( geom[imagemin[start[k]]].theta ) : CoordMax;
          Coord tmax = ( imagemax[start[k]] < SizeMax ) ? Fabs( geom[imagemax[start[k]]].theta ) : CoordMax;
          Coord t;
          if ( tmin == CoordMax ) {
            t = tmax;
          } else if ( tmax == CoordMax ) {
            t = tmin;
          } else if ( tmin > tmax ) {
            t = tmin;
          } else {
            t = tmax;
          }
          if ( t < t0 ) {
            image->min[index] = imagemin[start[k]];
            image->max[index] = imagemax[start[k]];
            index++; start[k]++;
            loop = loop2 = True;
          }
        }

      }

    } while ( loop2 );

  }

  exit3: free( imagemin );
  exit2: free( angle );
  exit1: free( start );

  return status;

}
