/*----------------------------------------------------------------------------*
*
*  tomometacommon.c  -  series: tomography: tilt series
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
#include <string.h>


/* variables */

static const char TomometaIdent[8] = "TOMO";


/* functions */

extern char *TomometaPath
             (const char *path,
              const char *prfx)

{
  char *metapath;

  if ( ( path == NULL ) || !*path ) {
    metapath = StringConcat( prfx, ".i3t", NULL );
  } else {
    metapath = strdup( path );
  }
  if ( metapath == NULL ) pushexception( E_MALLOC );

  return metapath;

}


extern Status TomometaCycleInit
              (Tomometa *meta,
               const Size cycle)

{
  I3io *handle = meta->handle;
  uint32_t *hdr = meta->header;
  Status status;

  status = I3ioAlloc( handle, OFFS + cycle * BLOCK + GLOBL, sizeof(TomometaGlobal), 0 );
  if ( exception( status ) ) return status;

  status = I3ioAlloc( handle, OFFS + cycle * BLOCK + AXIS, hdr[HDRAXS] * sizeof(TomometaAxis), 0 );
  if ( exception( status ) ) return status;

  status = I3ioAlloc( handle, OFFS + cycle * BLOCK + ORIEN, hdr[HDRORN] * sizeof(TomometaOrient), 0 );
  if ( exception( status ) ) return status;

  status = I3ioAlloc( handle, OFFS + cycle * BLOCK + GEOM, hdr[HDRIMG] * sizeof(TomometaGeom), 0 );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern Status TomometaInit
              (Tomometa *meta,
               const Tomotilt *tilt)

{
  I3io *handle = meta->handle;
  uint32_t *hdr = meta->header;
  Status status;

  meta->ident = TomometaIdent;

  hdr[HDRVRS] = 4;
  hdr[HDRSTR] = tilt->strings;
  hdr[HDRAXS] = tilt->axes;
  hdr[HDRORN] = tilt->orients;
  hdr[HDRIMG] = tilt->images;
  hdr[HDRFIL] = tilt->files;

  status = I3ioWriteAlloc( handle, CYC, sizeof(meta->cycle), &meta->cycle, 0 );
  if ( exception( status ) ) return status;

  status = I3ioWriteAlloc( handle, HDR, sizeof(TomometaHeader), hdr, 0 );
  if ( exception( status ) ) return status;

  status = I3ioWriteAlloc( handle, STR, hdr[HDRSTR], tilt->tiltstrings, 0 );
  if ( exception( status ) ) return status;

  status = I3ioAlloc( handle, PAR, sizeof(TomometaParam), 0 );
  if ( exception( status ) ) return status;

  status = I3ioAlloc( handle, FIL, hdr[HDRFIL] * sizeof(TomometaTiltfile), 0 );
  if ( exception( status ) ) return status;

  status = I3ioAlloc( handle, IMG, hdr[HDRIMG] * sizeof(TomometaImage), 0 );
  if ( exception( status ) ) return status;

  status = I3ioAlloc( handle, TRF, hdr[HDRIMG] * sizeof(TomometaTransf), 0 );
  if ( exception( status ) ) return status;

  status = TomometaInitTransf( meta );
  if ( exception( status ) ) return status;

  status = TomometaCycleInit( meta, 0 );
  if ( exception( status ) ) return status;

  return E_NONE;

}


static Status TomometaHeaderCheck
              (const uint32_t *hdr)

{

  if ( hdr[HDRVRS] != 4 ) return exception( E_TOMOMETA_FMT );

  if ( !hdr[HDRSTR] ) return exception( E_TOMOMETA_FMT );
  if ( !hdr[HDRAXS] ) return exception( E_TOMOMETA_FMT );
  if ( !hdr[HDRORN] ) return exception( E_TOMOMETA_FMT );
  if ( !hdr[HDRIMG] ) return exception( E_TOMOMETA_FMT );
  if ( !hdr[HDRFIL] ) return exception( E_TOMOMETA_FMT );

  return E_NONE;

}


extern Status TomometaSetup
              (Tomometa *meta,
               Tomotilt **tiltptr,
               Tomofile **fileptr,
               Tomoflags flags)

{
  Tomotilt *tilt;
  Tomofile *file;
  Status status;

  if ( argcheck( meta == NULL ) ) return pushexception( E_ARGVAL );

  I3io *handle = meta->handle;
  uint32_t *hdr = meta->header;

  meta->ident = TomometaIdent;

  I3ioMeta iometa;
  status = I3ioMetaGet( handle, 4, &iometa );
  if ( pushexception( status ) ) return status;
  if ( memcmp( &iometa, TomometaIdent, sizeof(iometa) ) ) return pushexception( E_TOMOMETA_FMT );

  status = I3ioRead( handle, HDR, 0, sizeof(uint32_t), hdr + HDRVRS );
  if ( pushexception( status ) ) return status;
  if ( hdr[HDRVRS] < 4 ) return userexceptionmsg( "need protomo-2.2.2 to read file ", I3ioGetPath( handle ) );
  status = I3ioRead( handle, HDR, 0, sizeof(TomometaHeader), hdr );
  if ( pushexception( status ) ) return status;

  status = TomometaHeaderCheck( hdr );
  if ( pushexception( status ) ) return status;

  status = I3ioRead( handle, CYC, 0, sizeof(int32_t), &meta->cycle );
  if ( pushexception( status ) ) return status;
  if ( ( flags & TomoCycle ) && ( meta->cycle < 0 ) ) {
    meta->cycle = 0;
    status = I3ioWrite( handle, CYC, 0, sizeof(int32_t), &meta->cycle );
    if ( pushexception( status ) ) return status;
  }

  if ( tiltptr != NULL ) {

    tilt = TomometaGetTilt( meta );
    status = testcondition( tilt == NULL );
    if ( status ) return status;

  }

  if ( fileptr != NULL ) {

    if ( tiltptr == NULL ) return pushexception( E_TOMOMETA );

    file = TomofileCreate( tilt );
    status = testcondition( file == NULL );
    if ( status ) goto error1;

    TomofileDscr *dscr = file->dscr;
    for ( Size i = 0; i < hdr[HDRFIL]; i++ ) {
      TomometaTiltfile file;
      status = I3ioRead( handle, FIL, i * sizeof(TomometaTiltfile), sizeof(TomometaTiltfile), file );
      if ( exception( status ) ) goto error2;
      dscr[i].nameindex = file[FILIND];
      dscr[i].dim = file[FILDIM];
      dscr[i].len[0] = file[FILLEN0];
      dscr[i].len[1] = file[FILLEN1];
      dscr[i].len[2] = file[FILLEN2];
      dscr[i].low[0] = file[FILLOW0];
      dscr[i].low[1] = file[FILLOW1];
      dscr[i].low[2] = file[FILLOW2];
      dscr[i].type = file[FILTYPE];
      dscr[i].attr = file[FILATTR];
      memcpy( dscr[i].checksum, &file[FILCHKS], sizeof(dscr[i].checksum) );
    }

    file->flags = TomoflagInit;

    *fileptr = file;

  }

  if ( tiltptr != NULL ) *tiltptr = tilt;

  return E_NONE;

  /* error handling */

  error2: TomofileDestroy( file );
  error1: TomotiltDestroy( tilt );

  return status;

}
