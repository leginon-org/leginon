/*----------------------------------------------------------------------------*
*
*  fftw2common.h  -  fftw2: fast Fourier transforms with fftw version 2
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef fftw2common_h_
#define fftw2common_h_

#include "fftw2.h"
#include "fouriercommon.h"
#ifdef ENABLE_FFTW2_THREADS
  #define FFTW2_THREADS
  #include "thread.h"
  #include <pthread.h>
  #include <sfftw_threads.h>
  #include <srfftw_threads.h>
#else
  #include <sfftw.h>
  #include <srfftw.h>
#endif


/* types */

typedef enum {
  FFTW2_PLAN_unknown,
  FFTW2_PLAN_fftw,
  FFTW2_PLAN_fftwnd,
  FFTW2_PLAN_rfftw,
  FFTW2_PLAN_rfftwnd
} FFTW2PlanType;

typedef struct {
  FFTW2PlanType type;
  void *plan;
  int flags;
  void *tmp;
  double scale;
} FFTW2data;


/* variables */

#ifdef FFTW2_THREADS
extern pthread_mutex_t FFTW2_mutex;
#endif


/* macros */

#ifdef FFTW2_THREADS
  #define FFTW2_BEGIN_CRITICAL ( errno = pthread_mutex_lock( &FFTW2_mutex ) )
  #define FFTW2_END_CRITICAL   ( errno = pthread_mutex_unlock( &FFTW2_mutex ) )
#else
  #define FFTW2_BEGIN_CRITICAL False
  #define FFTW2_END_CRITICAL   False
#endif


/* prototypes */

extern Status FFTW2Init
              (Fourier *fou,
               Status *stat);

extern Status FFTW2Final
              (Fourier *fou);

#define FFTW2_c_1( plan, src, dst )      fftw_one( plan, (fftw_complex *)(src), (fftw_complex *)(dst) )
#define FFTW2_rr_1( plan, src, dst )     rfftw_one( plan, (fftw_real *)(src), (fftw_real *)(dst) )
#define FFTW2_c_n( plan, src, dst )      fftwnd_one( plan, (fftw_complex *)(src), (fftw_complex *)(dst) )
#define FFTW2_cr_n( plan, src, dst )     rfftwnd_one_complex_to_real( plan, (fftw_complex *)(src), (fftw_real *)(dst) )
#define FFTW2_rc_n( plan, src, dst )     rfftwnd_one_real_to_complex( plan, (fftw_real *)(src), (fftw_complex *)(dst) )

#ifdef ENABLE_FFTW2_THREADS

  #define FFTW2_t_c_n( plan, src, dst )    ( ( data->threads > 1 ) ? fftwnd_threads_one( data->threads, plan, (fftw_complex *)(src), (fftw_complex *)(dst) ) : FFTW2_c_n( plan, src, dst ) )
  #define FFTW2_t_cr_n( plan, src, dst )   ( ( data->threads > 1 ) ? rfftwnd_threads_one_complex_to_real( data->threads, plan, (fftw_complex *)(src), (fftw_real *)(dst) ) : FFTW2_cr_n( plan, src, dst ) )
  #define FFTW2_t_rc_n( plan, src, dst )   ( ( data->threads > 1 ) ? rfftwnd_threads_one_real_to_complex( data->threads, plan, (fftw_real *)(src), (fftw_complex *)(dst) ) : FFTW2_rc_n( plan, src, dst ) )

#else

  #define FFTW2_t_c_n( plan, src, dst )    FFTW2_c_n( plan, src, dst )
  #define FFTW2_t_cr_n( plan, src, dst )   FFTW2_cr_n( plan, src, dst )
  #define FFTW2_t_rc_n( plan, src, dst )   FFTW2_rc_n( plan, src, dst )

#endif

#endif
