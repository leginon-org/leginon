/*----------------------------------------------------------------------------*
*
*  emiodefs.h  -  imageio: em files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef emiodefs_h_
#define emiodefs_h_

#include "defs.h"


/* types */

typedef enum {
  EMOS9=0,
  EMVAX=1,
  EMCONVEX=2,
  EMSGI=3,
  EMSUN=4,
  EMMAC=5,
  EMPC=6,
  EMmachinemax
} EMmachine;

typedef enum {
  EMundef=0,
  EMbyte=1,
  EMint16=2,
  EMint32=4,
  EMfloat=5,
  EMcmplx=8,
  EMdouble=9,
  EMdatatypemax
} EMType;

typedef enum {
  EMexternal=0,
  EM420=1,
  CM12=2,
  CM200=3,
  CM120bio=4,
  CM300=5,
  POLARA=6,
  EMcodemax
} EMcode;

typedef struct {
  uint8_t machine;
  uint8_t general;
  uint8_t unused;
  uint8_t datatype;
  int32_t nx;
  int32_t ny;
  int32_t nz;
  char label[80];
  int32_t voltage;      /* [mV] */
  int32_t Cs;           /* [um] */
  int32_t aperture;     /* [urad] */
  int32_t mag;
  int32_t postmag;      /* times 1000 */
  int32_t exposure;     /* [ms] */
  int32_t objpixel;     /* [pm] */
  int32_t emcode;
  int32_t ccdpixel;     /* [nm] */
  int32_t ccdlength;    /* [nm] */
  int32_t defocus;      /* [A] */
  int32_t astig;        /* [A] */
  int32_t astigdir;	/* [degrees/1000]*/
  int32_t defocusinc;   /* [A] */
  int32_t counts;       /* [/1000] */
  int32_t c2;           /* [/1000] */
  int32_t slit;         /* [eV] */
  int32_t offs;         /* [eV] */
  int32_t tiltangle;    /* [degrees/1000] */
  int32_t tiltdir;	/* [degrees/1000] */
  int32_t internal21;
  int32_t internal22;
  int32_t internal23;
  int32_t subframex0;
  int32_t subframey0;
  int32_t resolution;   /* [uA] */
  int32_t density;
  int32_t contrast;
  int32_t unknown;
  int32_t cmx;          /* [/1000] */
  int32_t cmy;          /* [/1000] */
  int32_t cmz;          /* [/1000] */
  int32_t cmh;          /* [/1000] */
  int32_t reserved34;
  int32_t d1;           /* [/1000] */
  int32_t d2;           /* [/1000] */
  int32_t lambda;
  int32_t dtheta;
  int32_t reserved39;
  int32_t reserved40;
  char username[20];
  char date[8];
  char extra[228];
} EMHeader;


/* macros */

#define EMHeaderSize 512


#endif
