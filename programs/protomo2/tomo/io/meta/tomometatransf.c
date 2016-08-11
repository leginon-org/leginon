/*----------------------------------------------------------------------------*
*
*  tomometatransf.c  -  series: tomography: tilt series
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

extern Status TomometaInitTransf
              (Tomometa *meta)

{
  TomometaTransf transf;
  Status status;

  memset( &transf, 0, sizeof(TomometaTransf) );

  for ( Size i = 0; i < meta->header[HDRIMG]; i++ ) {
    status = I3ioWrite( meta->handle, TRF, i * sizeof(TomometaTransf), sizeof(TomometaTransf), &transf );
    if ( exception( status ) ) return status;
  }

  return E_NONE;

}


extern Status TomometaResetTransf
              (Tomometa *meta)

{
  Status status;

  status = TomometaInitTransf( meta );
  if ( pushexception( status ) ) return status;

  status = I3ioFlush( meta->handle );
  if ( pushexception( status ) ) return status;

  return E_NONE;

}


extern Status TomometaSetTransf
              (Tomometa *meta,
               Size index,
               Coord Ap[3][2],
               Bool fulltransf)

{
  TomometaTransf transf;
  Status status;

  transf[TRFHDR] = ( index << 2 ) | 2;
  if ( fulltransf ) transf[TRFHDR] |= 1;
  Real64 *trf = (Real64 *)( transf + TRFTRF );
  *trf++ = Ap[0][0];
  *trf++ = Ap[0][1];
  *trf++ = Ap[1][0];
  *trf++ = Ap[1][1];
  *trf++ = Ap[2][0];
  *trf++ = Ap[2][1];

  meta->mode |= IOMod;

  status = I3ioWrite( meta->handle, TRF, index * sizeof(TomometaTransf),sizeof(TomometaTransf), transf );
  if ( pushexception( status ) ) return status;

  status = I3ioFlush( meta->handle );
  if ( pushexception( status ) ) return status;

  return E_NONE;

}


extern Status TomometaGetTransf
              (Tomometa *meta,
               Size index,
               Coord Ap[3][2],
               Bool *fulltransf)

{
  TomometaTransf transf;
  Status status;

  status = I3ioRead( meta->handle, TRF, index * sizeof(TomometaTransf),sizeof(TomometaTransf), transf );
  if ( pushexception( status ) ) return status;

  Size ind = transf[TRFHDR] >> 2;
  if ( transf[TRFHDR] & 2 ) {
    if ( ind != index ) return pushexception( E_TOMOMETA );
    Real64 *trf = (Real64 *)( transf + TRFTRF );
    Ap[0][0] = *trf++; Ap[0][1] = *trf++;
    Ap[1][0] = *trf++; Ap[1][1] = *trf++;
    Ap[2][0] = *trf++; Ap[2][1] = *trf++;
  } else {
    if ( ind ) return pushexception( E_TOMOMETA );
    Ap[0][0] = 0; Ap[0][1] = 0;
    Ap[1][0] = 0; Ap[1][1] = 0;
    Ap[2][0] = 0; Ap[2][1] = 0;
  }

  if ( fulltransf != NULL ) {
    *fulltransf = ( transf[TRFHDR] & 1 ) ? True : False;
  }

  return E_NONE;

}
