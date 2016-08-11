/*----------------------------------------------------------------------------*
*
*  ccp4iodefs.h  -  imageio: CCP4 files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef ccp4iodefs_h_
#define ccp4iodefs_h_

#include "defs.h"


/* types */

typedef enum {
  CCP4_BYTE   = 0,
  CCP4_INT16  = 1,
  CCP4_REAL   = 2,
  CCP4_CMPLXI = 3,
  CCP4_CMPLX  = 4,
  CCP4_MODE5  = 5,
  CCP4_UINT16 = 6,
  CCP4_MAXTYPE
} CCP4Type;

typedef struct {
  uint32_t nx;          /* 1 */
  uint32_t ny;
  uint32_t nz;
  uint32_t mode;        /* 4 */      /* mode 5 and 6 for old MRC format only */
  int32_t  nxstart;     /* 5 */
  int32_t  nystart;
  int32_t  nzstart;
  uint32_t mx;          /* 8 */
  uint32_t my; 
  uint32_t mz;
  Real32 a;             /* 11 */
  Real32 b;
  Real32 c;
  Real32 alpha;
  Real32 beta;
  Real32 gamma;
  uint32_t mapc;        /* 17 */
  uint32_t mapr;
  uint32_t maps;
  Real32 amin;          /* 20 */
  Real32 amax;
  Real32 amean;
  uint32_t ispg;        /* 23 */
  uint32_t nsymbt;      /* 24 */
  uint32_t lskflg;      /* 25 */      /* 25-53 extra for old MRC format */
  Real32 skwmat[3][3];  /* 26-34 */   /* 25-49 extra for MRC2000 format */
  Real32 skwtrn[3];     /* 35-37 */
  uint32_t unused[12];  /* 38-49 */
  Real32 origin[3];     /* 50-52 */   /* transform origin for MRC2000, unused for CCP4 */
  char map[4];          /* 53 */
  uint32_t machst;      /* 54 */      /* 54    xorigin for old MRC format */
  Real32 arms;          /* 55 */      /* 55    yorigin for old MRC format */
  uint32_t nlab;        /* 56 */
  char label[10][80];   /* 57-256 */
} CCP4Header;


/* macros */

#define CCP4HeaderSize 1024


#endif
