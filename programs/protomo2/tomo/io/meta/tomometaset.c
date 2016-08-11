/*----------------------------------------------------------------------------*
*
*  tomometaset.c  -  series: tomography: tilt series
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


/* functions */

static Status TomometaWriteGlobal
              (Tomometa *meta)

{
  Status status;

  Size cycle = ( meta->cycle < 0 ) ? 0 : meta->cycle;

  status = I3ioWrite( meta->handle, OFFS + cycle * BLOCK + GLOBL, 0, sizeof(TomometaGlobal), meta->global );
  if ( exception( status ) ) return status;

  status = I3ioFlush( meta->handle );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern Status TomometaSetEuler
              (Tomometa *meta,
               Tomotilt *tilt,
               const Coord euler[3])

{
  Status status;

  if ( argcheck( meta == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( euler == NULL ) ) return pushexception( E_ARGVAL );

  Real64 *global = (Real64 *)meta->global;
  global[GLBEUL0] = tilt->param.euler[0] = euler[0];
  global[GLBEUL1] = tilt->param.euler[1] = euler[1];
  global[GLBEUL2] = tilt->param.euler[2] = euler[2];

  status = TomometaWriteGlobal( meta );
  if ( pushexception( status ) ) return status;

  return E_NONE;

}


extern Status TomometaSetOrigin
              (Tomometa *meta,
               Tomotilt *tilt,
               const Coord origin[3])

{
  Status status;

  if ( argcheck( meta == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( origin == NULL ) ) return pushexception( E_ARGVAL );

  Real64 *global = (Real64 *)meta->global;
  global[GLBORIX] = tilt->param.origin[0] = origin[0];
  global[GLBORIY] = tilt->param.origin[1] = origin[1];
  global[GLBORIZ] = tilt->param.origin[2] = origin[2];

  status = TomometaWriteGlobal( meta );
  if ( pushexception( status ) ) return status;

  return E_NONE;

}
