/*----------------------------------------------------------------------------*
*
*  fftpackcommon.h  -  fftpack: fast Fourier transforms with fftpack
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef fftpackcommon_h_
#define fftpackcommon_h_

#include "fftpack.h"
#include "fouriercommon.h"


/* types */

typedef struct {
  int n;
  int ifac[15];
  int ifa2[15];
  float *wa;
  float *w2;
  float *wk;
  Cmplx *tmp;
  Size ntmp;
  double scale;
} FFTpackData;


/* external functions */

extern void cffti1_( int *, float *, int[] );
extern void cfftf1_( int *, float *, float *, float *, int[] );
extern void cfftb1_( int *, float *, float *, float *, int[] );
extern void rffti1_( int *, float *, int[] );
extern void rfftf1_( int *, float *, float *, float *, int[] );
extern void rfftb1_( int *, float *, float *, float *, int[] );


/* prototypes */

extern Status FFTpackInit
              (Fourier *fou,
               Status *stat);

extern Status FFTpackFinal
              (Fourier *fou);


#endif
