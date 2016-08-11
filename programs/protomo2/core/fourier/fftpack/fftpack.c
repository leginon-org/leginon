/*----------------------------------------------------------------------------*
*
*  fftpack.c  -  fftpack: fast Fourier transforms with fftpack
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "fftpackcommon.h"
#include "exception.h"
#include "mathdefs.h"
#include <stdlib.h>


/* functions */

static void FFTpackCleanup
            (Size dim,
             FFTpackData *data)

{

  while ( dim-- ) {

    if ( data->wa  != NULL ) free( data->wa );
    if ( data->w2  != NULL ) free( data->w2 );
    if ( data->tmp != NULL ) free( data->tmp );
    data++;

  }

}


extern Status FFTpackInit
              (Fourier *fou,
               Status *stat)

{
  Status status = E_NONE;

  if ( sizeof(float) != sizeof(Real) ) {
    return exception( E_FFTPACK );
  }

  Size dim = fou->dim;
  if ( !dim ) {
    return exception( E_ARGVAL );
  }

  FFTpackData *data = malloc( dim * sizeof(FFTpackData) );
  if ( data == NULL ) return exception( E_MALLOC );

  Size tsize, tsize2 = 0;
  void (*fninit_)( int *, float *, int * );
  if ( fou->mode & FourierSeqMask ) {
    fninit_ = rffti1_;
    tsize = sizeof(Real);
    if ( fou->mode & FourierBackward ) {
      tsize2 = sizeof(Real);
    }
  } else {
    fninit_ = cffti1_;
    tsize = 2 * sizeof(Real);
  }

  Size nwk = 0, ntmp = 0;
  for ( Size d = 0; d < dim; d++ ) {
    Size len = fou->len[d];
    if ( len < 1 ) { status = exception( E_FFTPACK_SIZE ); goto error1; }
    if ( len > INT_MAX ) { *stat = exception( E_FFTPACK_SIZE ); goto error1; }
    if ( len * tsize > nwk ) nwk = len * tsize;
    if ( d ) {
      if ( len > ntmp ) ntmp = len;
    } else if ( fou->mode & FourierSymMask ) {
      if ( len / 2 + 1 > ntmp ) ntmp = len / 2 + 1;
    }
    data[d].n = len;
    data[d].wa = ( len > 1 ) ? malloc( len * tsize ) : NULL;
    data[d].w2 = ( ( len > 1 ) && tsize2 ) ? malloc( len * tsize2 ) : NULL;
    data[d].wk = NULL;
    data[d].tmp = NULL;
    data[d].scale = 1.0;
    tsize = 2 * sizeof(Real);
  }
  data[0].ntmp = ntmp;
  fou->tmpsize = ntmp * sizeof(Cmplx) + nwk;
  data[0].tmp = malloc( fou->tmpsize );
  if ( data[0].tmp == NULL ) goto error2;
  data[0].wk = (float *)( data[0].tmp + data[0].ntmp );

  for ( Size d = 0; d < dim; d++ ) {
    if ( data[d].n > 1 ) {
      if ( data[d].wa == NULL ) goto error2;
      fninit_( &data[d].n, data[d].wa, data[d].ifac );
      if ( tsize2 ) {
        if ( data[d].w2 == NULL ) goto error2;
        rffti1_( &data[d].n, data[d].w2, data[d].ifa2 );
      }
    }
    fninit_ = cffti1_;
  }

  if ( fou->opt & FourierUnscaled ) {
    if ( fou->mode & FourierBackward ) {
      data[0].scale = 1.0 / fou->seqlen;
    }
  } else {
    if ( ~fou->mode & FourierBackward ) {
      data[0].scale = 1.0 / fou->seqlen;
    }
  }

  fou->data =data;
  *stat = E_NONE;
  return E_NONE;

  error2:
  status = exception( E_MALLOC ); 
  FFTpackCleanup( dim, data );

  error1:
  free( data );
  return status;

}


extern Status FFTpackFinal
              (Fourier *fou)

{

  if ( ( fou != NULL ) && ( fou->data != NULL ) ) {

    FFTpackCleanup( fou->dim, fou->data );
    free( fou->data ); fou->data = NULL;

  }

  return E_NONE;

}
