/*----------------------------------------------------------------------------*
*
*  fftw2.c  -  fftw2: fast Fourier transforms with fftw version 2
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "fftw2common.h"
#include "exception.h"
#include "mathdefs.h"
#include <stdlib.h>


/* variables */

#ifdef FFTW2_THREADS
pthread_mutex_t FFTW2_mutex = PTHREAD_MUTEX_INITIALIZER;
#endif


/* functions */

extern Status FFTW2Init
              (Fourier *fou,
               Status *stat)

{
  FFTW2data *data;

  if ( fou->len[0] < 1 ) {
    *stat = exception( E_FFTW2_SIZE );
    return E_NONE;
  }

  data = malloc( sizeof(FFTW2data) );
  if ( data == NULL ) return exception( E_MALLOC );
  fou->data = data;

  data->type = FFTW2_PLAN_unknown;
  data->plan = NULL;
  data->flags = ( fou->mode & FourierMulti ) ? FFTW_ESTIMATE : 0;
#ifdef FFTW2_THREADS
  data->flags |= FFTW_THREADSAFE;
#endif
  data->tmp = NULL;

  if ( fou->opt & FourierUnscaled ) {
    if ( fou->mode & FourierBackward ) {
      data->scale = 1.0 / fou->seqlen;
    } else {
      data->scale = 1.0;
    }
  } else {
    if ( fou->mode & FourierBackward ) {
      data->scale = 1.0;
    } else {
      data->scale = 1.0 / fou->seqlen;
    }
  }

  *stat = E_NONE;

  return E_NONE;

}


extern Status FFTW2Final
              (Fourier *fou)

{
  FFTW2data *data = fou->data;
  Status status = E_NONE;

  if ( data != NULL ) {

    if ( data->plan != NULL ) {

      status = FFTW2_BEGIN_CRITICAL;
      if ( !status ) {
        switch ( data->type ) {
          case FFTW2_PLAN_fftw:    fftw_destroy_plan( data->plan ); break;
          case FFTW2_PLAN_fftwnd:  fftwnd_destroy_plan( data->plan ); break;
          case FFTW2_PLAN_rfftw:   rfftw_destroy_plan( data->plan ); break;
          case FFTW2_PLAN_rfftwnd: rfftwnd_destroy_plan( data->plan ); break;
          default: status = exception( E_FFTW2 );
        }
        if ( FFTW2_END_CRITICAL ) {
          logexception( E_ERRNO ); if ( !status ) status = E_ERRNO;
        }
      }

    }

    if ( data->tmp != NULL ) free( data->tmp );

    free( fou->data ); fou->data = NULL;

  }

  return status;

}
