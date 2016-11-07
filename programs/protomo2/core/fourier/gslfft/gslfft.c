/*----------------------------------------------------------------------------*
*
*  gslfft.c  -  gslfft: fast Fourier transforms with gsl
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "gslfftcommon.h"
#include "exception.h"
#include "mathdefs.h"
#include <stdlib.h>


/* functions */

static void GSLfftCleanup
            (Size dim,
             GSLfftData *data,
             FourierMode mode)

{

  while ( dim-- ) {

    if ( data->wtab != NULL ) {
      switch ( data->wtype ) {
        case GSLfftReal:  gsl_fft_real_wavetable_float_free( data->wtab ); break;
        case GSLfftHerm:  gsl_fft_halfcomplex_wavetable_float_free( data->wtab ); break;
        case GSLfftCmplx: gsl_fft_complex_wavetable_float_free( data->wtab ); break;
        default: break;
      }
    }

    if ( data->wta2 != NULL ) {
      gsl_fft_halfcomplex_wavetable_float_free( data->wta2 );
    }


    if ( data->wk != NULL ) {
      switch ( data->wktype ) {
        case GSLfftReal:  gsl_fft_real_workspace_float_free( data->wk ); break;
        case GSLfftCmplx: gsl_fft_complex_workspace_float_free( data->wk ); break;
        default: break;
      }
    }

    if ( data->tmp != NULL ) free( data->tmp );


    data++;

  }

}


extern Status GSLfftInit
              (Fourier *fou,
               Status *stat)

{
  Status status = E_NONE;

  if ( sizeof(float) != sizeof(Real) ) {
    return exception( E_GSLFFT );
  }

  Size dim = fou->dim;
  if ( !dim ) {
    return exception( E_ARGVAL );
  }

  GSLfftData *data = malloc( dim * sizeof(GSLfftData) );
  if ( data == NULL ) return exception( E_MALLOC );

  Size ntmp = 0;
  for ( Size d = 0; d < dim; d++ ) {
    Size len = fou->len[d];
    if ( len < 1 ) { status = exception( E_GSLFFT_SIZE ); goto error1; }
    if ( len > SIZE_MAX ) { *stat = exception( E_GSLFFT_SIZE ); goto error1; }
    if ( d ) {
      if ( len > ntmp ) ntmp = len;
    } else if ( fou->mode & FourierSymMask ) {
      if ( len / 2 + 1 > ntmp ) ntmp = len / 2 + 1;
    }
    data[d].n = len;
    data[d].wtab = NULL;
    data[d].wta2 = NULL;
    data[d].wk = NULL;
    data[d].tmp = NULL;
    data[d].scale = 1.0;
  }
  fou->tmpsize = ntmp * sizeof(Cmplx);
  if ( ntmp && ( fou->mode & FourierBackward ) ) {
    data[0].tmp = malloc( fou->tmpsize );
    if ( data[0].tmp == NULL ) goto error2;
  }

  for ( Size d = 0; d < dim; d++ ) {
    size_t n = data[d].n;
    if ( n > 1 ) {
      switch ( fou->mode & FourierSeqMask ) {
        case FourierRealSeq:
        case FourierImagSeq: {
          if ( d == 0 ) {
            if ( fou->mode & FourierBackward ) {
              data[d].wtype = GSLfftHerm;
              data[d].wtab = gsl_fft_halfcomplex_wavetable_float_alloc( n );
            } else {
              data[d].wtype = GSLfftReal;
              data[d].wtab = gsl_fft_real_wavetable_float_alloc( n );
            }
            if ( data[d].wtab == NULL ) goto error3;
            data[d].wktype = GSLfftReal;
            data[d].wk = gsl_fft_real_workspace_float_alloc( n );
            if ( data[d].wk == NULL ) goto error3;
          } else {
            data[d].wtype = GSLfftCmplx;
            data[d].wtab = gsl_fft_complex_wavetable_float_alloc( n );
            if ( data[d].wtab == NULL ) goto error3;
            if ( fou->mode & FourierBackward ) {
              data[d].wta2 = gsl_fft_halfcomplex_wavetable_float_alloc( n );
              if ( data[d].wta2 == NULL ) goto error3;
            }
            data[d].wktype = GSLfftCmplx;
            data[d].wk = gsl_fft_complex_workspace_float_alloc( n );
            if ( data[d].wk == NULL ) goto error3;
          }
          break;
        }
        case FourierCmplxSeq: {
          data[d].wtype = GSLfftCmplx;
          data[d].wtab = gsl_fft_complex_wavetable_float_alloc( n );
          if ( data[d].wtab == NULL ) goto error3;
          data[d].wktype = GSLfftCmplx;
          data[d].wk = gsl_fft_complex_workspace_float_alloc( n );
          if ( data[d].wk == NULL ) goto error3;
          break;
        }
        default: status = exception( E_GSLFFT ); goto error2;
      }
    }
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

  error3:
  status = exception( E_MALLOC );

  error2:
  GSLfftCleanup( dim, data, fou->mode );

  error1:
  free( data );

  return status;

}


extern Status GSLfftFinal
              (Fourier *fou)

{

  if ( ( fou != NULL ) && ( fou->data != NULL ) ) {

    GSLfftCleanup( fou->dim, fou->data, fou->mode );
    free( fou->data ); fou->data = NULL;

  }

  return E_NONE;

}


extern Status GSLfftWk
              (Size dim,
               GSLfftData *data,
               void *wk[],
               Size wksize)

{
  Status status = E_NONE;

  if ( wksize < dim * sizeof(void *) ) {
    return exception( E_FOURIER_DIM );
  }


  for ( Size d = 0; d < dim; d++ ) {
    wk[d] = data[d].wk;
  }

  return status;

}


