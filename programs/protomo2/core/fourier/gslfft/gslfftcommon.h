/*----------------------------------------------------------------------------*
*
*  gslfftcommon.h  -  gslfft: fast Fourier transforms with gsl
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef gslfftcommon_h_
#define gslfftcommon_h_

#include "gslfft.h"
#include "fouriercommon.h"
#include <gsl/gsl_errno.h>
#include <gsl/gsl_fft_complex_float.h>
#include <gsl/gsl_fft_halfcomplex_float.h>
#include <gsl/gsl_fft_real_float.h>


/* types */

typedef enum {
  GSLfftReal,
  GSLfftHerm,
  GSLfftCmplx
} GSLfftType;

typedef struct {
  size_t n;
  GSLfftType wtype;
  void *wtab;
  void *wta2;
  GSLfftType wktype;
  void *wk;
  void *tmp;
  double scale;
} GSLfftData;


/* prototypes */

extern Status GSLfftInit
              (Fourier *fou,
               Status *stat);

extern Status GSLfftFinal
              (Fourier *fou);

extern Status GSLfftWk
              (Size dim,
               GSLfftData *data,
               void *wk[],
               Size wksize);


#endif
