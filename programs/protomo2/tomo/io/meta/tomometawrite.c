/*----------------------------------------------------------------------------*
*
*  tomometawrite.c  -  series: tomography: tilt series
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
#include "exception.h"
#include <string.h>


/* functions */

static Status TomometaCycleUpdate
              (Tomometa *meta,
               const Size cycle,
               const Tomotilt *tilt)

{
  I3io *handle = meta->handle;
  uint32_t *hdr = meta->header;
  Status status;

  Real64 *global = (Real64 *)meta->global;
  meta->global[GLBREF] = tilt->param.cooref;
  global[GLBEUL0] = tilt->param.euler[0];
  global[GLBEUL1] = tilt->param.euler[1];
  global[GLBEUL2] = tilt->param.euler[2];
  global[GLBORIX] = tilt->param.origin[0];
  global[GLBORIY] = tilt->param.origin[1];
  global[GLBORIZ] = tilt->param.origin[2];
  status = I3ioWrite( handle, OFFS + cycle * BLOCK + GLOBL, 0, sizeof(TomometaGlobal), meta->global );
  if ( exception( status ) ) return status;

  for ( Size i = 0; i < hdr[HDRAXS]; i++ ) {
    TomometaAxis axis; Real64 *raxis = (Real64 *)axis;
    axis[AXSREF]  = tilt->tiltaxis[i].cooref;
    raxis[AXSPHI] = tilt->tiltaxis[i].phi;
    raxis[AXSTHE] = tilt->tiltaxis[i].theta;
    raxis[AXSOFF] = tilt->tiltaxis[i].offset;
    status = I3ioWrite( handle, OFFS + cycle * BLOCK + AXIS, i * sizeof(TomometaAxis), sizeof(TomometaAxis), axis );
    if ( exception( status ) ) return status;
  }

  for ( Size i = 0; i < hdr[HDRORN]; i++ ) {
    TomometaOrient orn; Real64 *rorn = (Real64 *)orn;
    orn[ORNAXS]   = tilt->tiltorient[i].axisindex;
    rorn[ORNEUL0] = tilt->tiltorient[i].euler[0];
    rorn[ORNEUL1] = tilt->tiltorient[i].euler[1];
    rorn[ORNEUL2] = tilt->tiltorient[i].euler[2];
    status = I3ioWrite( handle, OFFS + cycle * BLOCK + ORIEN, i * sizeof(TomometaOrient), sizeof(TomometaOrient), orn );
    if ( exception( status ) ) return status;
  }

  for ( Size i = 0; i < hdr[HDRIMG]; i++ ) {
    TomometaGeom geom; Real64 *rgeom = (Real64 *)geom;
    geom[GEOAXS] = tilt->tiltgeom[i].axisindex;
    geom[GEOORN] = tilt->tiltgeom[i].orientindex;
    rgeom[GEOORIX] = tilt->tiltgeom[i].origin[0];
    rgeom[GEOORIY] = tilt->tiltgeom[i].origin[1];
    rgeom[GEOTHET] = tilt->tiltgeom[i].theta;
    rgeom[GEOALPH] = tilt->tiltgeom[i].alpha;
    rgeom[GEOBETA] = tilt->tiltgeom[i].beta;
    rgeom[GEOCORX] = tilt->tiltgeom[i].corr[0];
    rgeom[GEOCORY] = tilt->tiltgeom[i].corr[1];
    rgeom[GEOSCAL] = tilt->tiltgeom[i].scale;
    status = I3ioWrite( handle, OFFS + cycle * BLOCK + GEOM, i * sizeof(TomometaGeom), sizeof(TomometaGeom), geom );
    if ( exception( status ) ) return status;
  }

  return E_NONE;

}


extern Status TomometaWrite
              (Tomometa *meta,
               const Tomotilt *tilt,
               const Tomofile *file)

{
  Status status;

  if ( argcheck( meta == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( tilt == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( file == NULL ) ) return pushexception( E_ARGVAL );

  if ( ~file->flags & TomoflagInit ) return pushexception( E_TOMOMETA );

  I3io *handle = meta->handle;
  uint32_t *hdr = meta->header;

  status = TomometaCycleUpdate( meta, ( meta->cycle < 0 ) ? 0 : meta->cycle, tilt );
  if ( pushexception( status ) ) return status;

  if ( !meta->hdrwr ) {

    Real64 *rpar = (Real64 *)meta->param;
    meta->param[PARVRS] = tilt->param.version;
    rpar[PARPIX] = tilt->param.pixel;
    rpar[PARLMB] = tilt->param.emparam.lambda;
    rpar[PARCS]  = tilt->param.emparam.cs;
    rpar[PARFS]  = tilt->param.emparam.fs;
    rpar[PARBET] = tilt->param.emparam.beta;
    meta->param[PARRESERVED]  = 0;
    meta->param[PARRESERVED2] = 0;
    status = I3ioWrite( handle, PAR, 0, sizeof(TomometaParam), meta->param );
    if ( pushexception( status ) ) return status;

    TomofileDscr *dscr = file->dscr;
    for ( Size i = 0; i < hdr[HDRFIL]; i++ ) {
      TomometaTiltfile tf;
      tf[FILIND]  = dscr[i].nameindex;
      tf[FILDIM]  = dscr[i].dim;
      tf[FILLEN0] = dscr[i].len[0];
      tf[FILLEN1] = dscr[i].len[1];
      tf[FILLEN2] = dscr[i].len[2];
      tf[FILLOW0] = dscr[i].low[0];
      tf[FILLOW1] = dscr[i].low[1];
      tf[FILLOW2] = dscr[i].low[2];
      tf[FILTYPE] = dscr[i].type;
      tf[FILATTR] = dscr[i].attr;
      memcpy( &tf[FILCHKS], dscr[i].checksum, sizeof(dscr[i].checksum) );
      status = I3ioWrite( handle, FIL, i * sizeof(TomometaTiltfile), sizeof(TomometaTiltfile), tf );
      if ( pushexception( status ) ) return status;
    }

    for ( Size i = 0; i < hdr[HDRIMG]; i++ ) {
      TomometaImage img; Real64 *rimg = (Real64 *)img;
      img[IMGNUM] = tilt->tiltimage[i].number;
      img[IMGIND] = tilt->tiltimage[i].fileindex;
      img[IMGOFF] = tilt->tiltimage[i].fileoffset;
      rimg[IMGPIX]  = tilt->tiltimage[i].pixel;
      rimg[IMGLOCX] = tilt->tiltimage[i].loc[0];
      rimg[IMGLOCY] = tilt->tiltimage[i].loc[1];
      rimg[IMGFOC]  = tilt->tiltimage[i].defocus;
      rimg[IMGCAST] = tilt->tiltimage[i].ca;
      rimg[IMGPAST] = tilt->tiltimage[i].phia;
      rimg[IMGAMPC] = tilt->tiltimage[i].ampcon;
      status = I3ioWrite( handle, IMG, i * sizeof(TomometaImage), sizeof(TomometaImage), img );
      if ( pushexception( status ) ) return status;
    }

    meta->hdrwr = True;

  }

  status = I3ioFlush( handle );
  if ( pushexception( status ) ) return status;

  return E_NONE;

}


extern Status TomometaUpdate
              (Tomometa *meta,
               const Tomotilt *tilt)

{
  Status status;

  if ( argcheck( meta == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( tilt == NULL ) ) return pushexception( E_ARGVAL );

  I3io *handle = meta->handle;
  int32_t cycle = meta->cycle;

  if ( cycle++ >= 0 ) {

    status = TomometaCycleInit( meta, cycle );
    if ( pushexception( status ) ) return status;

    status = TomometaCycleUpdate( meta, cycle, tilt );
    if ( pushexception( status ) ) return status;

    status = TomometaInitTransf( meta );
    if ( pushexception( status ) ) return status;

    status = I3ioWrite( handle, CYC, 0, sizeof(meta->cycle), &cycle );
    if ( pushexception( status ) ) return status;

    meta->cycle = cycle;

  } else {

    status = TomometaInitTransf( meta );
    if ( pushexception( status ) ) return status;

  }

  status = I3ioFlush( handle );
  if ( pushexception( status ) ) return status;

  return E_NONE;

}
