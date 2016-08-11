/*----------------------------------------------------------------------------*
*
*  tomotiltnew.c  -  tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomotiltnew.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern Status TomotiltNewImage
              (Tomotilt *tomotilt,
               Size axisindex,
               Size orientindex,
               Size fileindex,
               Size *imageindex)

{
  TomotiltImage *image;
  TomotiltGeom *geom;
  Size index;
  Status status;

  if ( argcheck( tomotilt == NULL ) ) return exception( E_ARGVAL );

  if ( axisindex   >= tomotilt->axes )    return exception( E_ARGVAL );
  if ( orientindex >= tomotilt->orients ) return exception( E_ARGVAL );
  if ( ( fileindex >= tomotilt->files ) && ( fileindex < TomotiltImageMax ) ) return exception( E_ARGVAL );
  if ( imageindex  == NULL) return exception( E_ARGVAL );

  image = malloc( ( tomotilt->images + 1 ) * sizeof(TomotiltImage) );
  if ( image == NULL ) {
    status = exception( E_MALLOC ); goto error2;
  }

  geom = malloc( ( tomotilt->images + 1 ) * sizeof(TomotiltGeom) );
  if ( geom == NULL ) {
    status = exception( E_MALLOC ); goto error1;
  }

  if ( tomotilt->images ) {
    memcpy( image, tomotilt->tiltimage, tomotilt->images * sizeof(TomotiltImage) );
    memcpy( geom,  tomotilt->tiltgeom,  tomotilt->images * sizeof(TomotiltGeom) );
  }

  free( tomotilt->tiltimage );
  free( tomotilt->tiltgeom );

  tomotilt->tiltimage = image;
  tomotilt->tiltgeom  = geom;

  index = tomotilt->images++;

  image[index].number = TomotiltImageMax;
  image[index].fileindex = fileindex;
  image[index].fileoffset = INT64_MAX;
  image[index].pixel = 0;
  image[index].loc[0] = CoordMax;
  image[index].loc[1] = CoordMax;
  image[index].defocus = CoordMax;
  image[index].ca = 0;
  image[index].phia = CoordMax;
  image[index].ampcon = CoordMax;

  geom[index].axisindex = axisindex;
  geom[index].orientindex = orientindex;
  geom[index].origin[0] = CoordMax;
  geom[index].origin[1] = CoordMax;
  geom[index].theta = CoordMax;
  geom[index].alpha = CoordMax;
  geom[index].beta = CoordMax;
  geom[index].corr[0] = 0;
  geom[index].corr[1] = 0;
  geom[index].scale = 0;

  *imageindex = index;

  return E_NONE;

  error1: free( image );
  error2: return status;

}


extern Status TomotiltNewAxis
              (Tomotilt *tomotilt,
               Size *axisindex)

{
  TomotiltAxis *axis;
  Size index;

  if ( argcheck( tomotilt == NULL ) ) return exception( E_ARGVAL );

  if ( axisindex == NULL ) return exception( E_ARGVAL );

  axis = malloc( ( tomotilt->axes + 1 ) * sizeof(TomotiltAxis) );
  if ( axis == NULL ) {
    return exception( E_MALLOC );
  }

  if ( tomotilt->axes ) {
    memcpy( axis, tomotilt->tiltaxis, tomotilt->axes * sizeof(TomotiltAxis) );
  }
  free( tomotilt->tiltaxis );
  tomotilt->tiltaxis = axis;

  index = tomotilt->axes++;

  axis[index].cooref = TomotiltImageMax;
  axis[index].reserved = TomotiltImageMax;
  axis[index].phi = CoordMax;
  axis[index].theta = CoordMax;
  axis[index].offset = CoordMax;

  *axisindex = index;

  return E_NONE;

}


extern Status TomotiltNewOrient
              (Tomotilt *tomotilt,
               Size axisindex,
               Size *orientindex)

{
  TomotiltOrient *orient;
  Size index;

  if ( argcheck( tomotilt == NULL ) ) return exception( E_ARGVAL );

  if ( axisindex >= tomotilt->axes ) return exception( E_ARGVAL );
  if ( orientindex == NULL ) return exception( E_ARGVAL );

  orient = malloc( ( tomotilt->orients + 1 ) * sizeof(TomotiltOrient) );
  if ( orient == NULL ) {
    return exception( E_MALLOC );
  }

  if ( tomotilt->orients ) {
    memcpy( orient, tomotilt->tiltorient, tomotilt->orients * sizeof(TomotiltOrient) );
  }
  free( tomotilt->tiltorient );
  tomotilt->tiltorient = orient;

  index = tomotilt->orients++;

  orient[index].axisindex = axisindex;
  orient[index].reserved = TomotiltImageMax;
  orient[index].euler[0] = CoordMax;
  orient[index].euler[1] = CoordMax;
  orient[index].euler[2] = CoordMax;

  *orientindex = index;

  return E_NONE;

}



extern Status TomotiltNewFile
              (Tomotilt *tomotilt,
               const char *name,
               Size *fileindex)

{
  TomotiltFile *file;
  char *tiltstrings;
  Size length;
  Size index;
  Status status;

  if ( argcheck( tomotilt == NULL ) ) return exception( E_ARGVAL );

  if ( ( name == NULL ) || !*name ) return exception( E_ARGVAL );
  if ( fileindex == NULL ) return exception( E_ARGVAL );

  file = malloc( ( tomotilt->files + 1 ) * sizeof(TomotiltFile) );
  if ( file == NULL ) {
    status = exception( E_MALLOC ); goto error2;
  }

  length = strlen(name) + 1;

  tiltstrings = malloc( tomotilt->strings + length );
  if ( tiltstrings == NULL ) {
    status = exception( E_MALLOC ); goto error1;
  }

  if ( tomotilt->files ) {
    memcpy( file, tomotilt->tiltfile, tomotilt->files * sizeof(TomotiltFile) );
  }
  free( tomotilt->tiltfile );
  tomotilt->tiltfile = file;

  if ( tomotilt->strings ) {
    memcpy( tiltstrings, tomotilt->tiltstrings, tomotilt->strings );
  }
  memcpy( tiltstrings + tomotilt->strings, name, length );
  free( tomotilt->tiltstrings );
  tomotilt->tiltstrings = tiltstrings;

  index = tomotilt->files++;

  memset( file + index, 0, sizeof(TomotiltFile) );
  file[index].nameindex = tomotilt->strings;

  tomotilt->strings += length;

  *fileindex = index;

  return E_NONE;

  error1: free( file );
  error2: return status;

}
