/*----------------------------------------------------------------------------*
*
*  tomometaget.c  -  series: tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomometacommon.h"
#include "strings.h"
#include "exception.h"
#include <stdlib.h>


/* functions */

extern IOMode TomometaGetMode
              (const Tomometa *meta)

{

  if ( meta == NULL ) return 0;

  return meta->mode;

}


extern int TomometaGetCycle
           (const Tomometa *meta)

{

  return ( meta == NULL ) ? -2 : meta->cycle;

}


extern Size TomometaGetImages
            (const Tomometa *meta)

{

  return ( meta == NULL ) ? 0 : meta->header[HDRIMG];

}


extern Tomotilt *TomometaGetTilt
                 (Tomometa *meta)

{
  Status status;

  if ( argcheck( meta == NULL ) ) { pushexception( E_ARGVAL ); return NULL; }

  I3io *handle = meta->handle;
  uint32_t *hdr = meta->header;

  Tomotilt *tilt = TomotiltCreate( "dummy", hdr[HDRIMG], hdr[HDRAXS], hdr[HDRORN], hdr[HDRFIL], NULL );
  status = testcondition( tilt == NULL );
  if ( status ) return NULL;

  Size offs = OFFS + ( ( meta->cycle < 0 ) ? 0 : meta->cycle ) * BLOCK;

  status = I3ioRead( handle, PAR, 0, sizeof(TomometaParam), meta->param );
  if ( exception( status ) ) goto error;
  Real64 *rpar = (Real64 *)meta->param;
  tilt->param.version = meta->param[PARVRS];
  tilt->param.pixel = rpar[PARPIX];
  tilt->param.emparam.lambda = rpar[PARLMB];
  tilt->param.emparam.cs = rpar[PARCS];
  tilt->param.emparam.fs = rpar[PARFS];
  tilt->param.emparam.beta = rpar[PARBET];

  for ( Size i = 0; i < hdr[HDRIMG]; i++ ) {
    TomometaImage img; Real64 *rimg = (Real64 *)img;
    status = I3ioRead( handle, IMG, i * sizeof(TomometaImage), sizeof(TomometaImage), img );
    if ( exception( status ) ) goto error;
    tilt->tiltimage[i].number = img[IMGNUM];
    tilt->tiltimage[i].fileindex = img[IMGIND];
    tilt->tiltimage[i].fileoffset = img[IMGOFF];
    tilt->tiltimage[i].pixel   = rimg[IMGPIX];
    tilt->tiltimage[i].loc[0]  = rimg[IMGLOCX];
    tilt->tiltimage[i].loc[1]  = rimg[IMGLOCY];
    tilt->tiltimage[i].defocus = rimg[IMGFOC];
    tilt->tiltimage[i].ca      = rimg[IMGCAST];
    tilt->tiltimage[i].phia    = rimg[IMGPAST];
    tilt->tiltimage[i].ampcon  = rimg[IMGAMPC];
    TomometaGeom geom; Real64 *rgeom = (Real64 *)geom;
    status = I3ioRead( handle, offs + GEOM, i * sizeof(TomometaGeom), sizeof(TomometaGeom), geom );
    if ( exception( status ) ) goto error;
    tilt->tiltgeom[i].axisindex = geom[GEOAXS];
    tilt->tiltgeom[i].orientindex = geom[GEOORN];
    tilt->tiltgeom[i].origin[0] = rgeom[GEOORIX];
    tilt->tiltgeom[i].origin[1] = rgeom[GEOORIY];
    tilt->tiltgeom[i].theta     = rgeom[GEOTHET];
    tilt->tiltgeom[i].alpha     = rgeom[GEOALPH];
    tilt->tiltgeom[i].beta      = rgeom[GEOBETA];
    tilt->tiltgeom[i].corr[0]   = rgeom[GEOCORX];
    tilt->tiltgeom[i].corr[1]   = rgeom[GEOCORY];
    tilt->tiltgeom[i].scale     = rgeom[GEOSCAL];
  }

  for ( Size i = 0; i < hdr[HDRFIL]; i++ ) {
    TomometaTiltfile file;
    status = I3ioRead( handle, FIL, i * sizeof(TomometaTiltfile), sizeof(TomometaTiltfile), file );
    if ( exception( status ) ) goto error;
    tilt->tiltfile[i].nameindex = file[FILIND];
    tilt->tiltfile[i].dim = file[FILDIM];
  }

  status = I3ioRead( handle, offs + GLOBL, 0, sizeof(TomometaGlobal), meta->global );
  if ( exception( status ) ) goto error;
  Real64 *global = (Real64 *)meta->global;
  tilt->param.cooref = meta->global[GLBREF];
  tilt->param.euler[0] = global[GLBEUL0];
  tilt->param.euler[1] = global[GLBEUL1];
  tilt->param.euler[2] = global[GLBEUL2];
  tilt->param.origin[0] = global[GLBORIX];
  tilt->param.origin[1] = global[GLBORIY];
  tilt->param.origin[2] = global[GLBORIZ];

  for ( Size i = 0; i < hdr[HDRAXS]; i++ ) {
    TomometaAxis axis; Real64 *raxis = (Real64 *)axis;
    status = I3ioRead( handle, offs + AXIS, i * sizeof(TomometaAxis), sizeof(TomometaAxis), axis );
    if ( exception( status ) ) goto error;
    tilt->tiltaxis[i].cooref = axis[AXSREF];
    tilt->tiltaxis[i].phi    = raxis[AXSPHI];
    tilt->tiltaxis[i].theta  = raxis[AXSTHE];
    tilt->tiltaxis[i].offset = raxis[AXSOFF];
  }

  for ( Size i = 0; i < hdr[HDRORN]; i++ ) {
    TomometaOrient orn; Real64 *rorn = (Real64 *)orn;
    status = I3ioRead( handle, offs + ORIEN, i * sizeof(TomometaOrient), sizeof(TomometaOrient), orn );
    if ( exception( status ) ) goto error;
    tilt->tiltorient[i].axisindex = orn[ORNAXS];
    tilt->tiltorient[i].euler[0] = rorn[ORNEUL0];
    tilt->tiltorient[i].euler[1] = rorn[ORNEUL1];
    tilt->tiltorient[i].euler[2] = rorn[ORNEUL2];
  }

  char *string = I3ioReadBuf( handle, STR, 0, hdr[HDRSTR] );
  status = testcondition( string == NULL );
  if ( status ) goto error;

  free( tilt->tiltstrings );
  tilt->tiltstrings = string;
  tilt->strings = hdr[HDRSTR];

  return tilt;

  error: free( tilt );

  return NULL;

}
