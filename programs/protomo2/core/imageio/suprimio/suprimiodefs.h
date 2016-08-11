/*----------------------------------------------------------------------------*
*
*  suprimiodefs.h  -  imageio: suprim files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef suprimiodefs_h_
#define suprimiodefs_h_

#include "defs.h"


/* register indices  */

#define F_AVG        0 
#define BACKGROUND   0
#define ANG_SAMP     1
#define RAD_SAMP     2
#define O_ROW_SZ     3
#define O_COL_SZ     4
#define ROW_ORG      5
#define COL_ORG      6
#define MASK_RAD     7
#define F_NOTE_R     8
#define F_NOTE_I     9
#define SAMP_DIST   10
#define NSLICES     11
#define ENL_BP      12
#define X_FMAX      12
#define THE_BP      13
#define PHI_BP      14
#define FOUR_TR_CEN 15
#define GSBAR       15 
#define X_NIMA      16
#define SYMP2       17
#define X_NPIX      17
#define X_NCLU      18
#define X_NCTR      19
#define X_NAME      20
#define X_LNAM      21
#define X_NTRM      21
#define X_NFAC      22
#define X_NTYP      23
#define FRTHDIM     24
#define X_NIMI      26
#define X_UFAC      27
#define X_WALL      28
#define NUM_POLYS   31
#define X_FBEG      32
#define PSI_BP      40
#define X_TRP       70
#define R_ANGX      81
#define R_ANGY      82
#define R_ANGZ      83
#define R_NPROJ     84
#define XGLOB	    90
#define YGLOB	    91
#define ROTGLOB     92
#define XX_CELL     93
#define XY_CELL     94
#define YX_CELL     95
#define YY_CELL     96
#define IR_WINID    97
#define O_SLICE_SZ  98
#define CALIB       99
#define NAV        100

#define SuprimRegisterMax 128


/* types */

typedef enum {
  SuprimUndef,
  SuprimUint8,
  SuprimReal32,
  SuprimCmplx32,
  SuprimReal32RLC,
  SuprimInt16,
  SuprimRGB,
  SuprimInt32,
  SuprimReal64,
  SuprimTypeMax,
} SuprimType;

typedef union {
  int32_t l;
  Real32 f;
} SuprimRegister;

typedef struct {
  uint8_t version;
  int32_t nrow;
  int32_t ncol;
  int32_t format;
  int32_t intern;
  int32_t filetype;
  Real32 min;
  Real32 max;
  Real32 mean;
  Real32 sd;
  SuprimRegister reg[SuprimRegisterMax];
  char trace[1024];
} SuprimHeader;


/* macros */

#define SuprimHeaderSize 1573
#define SuprimTraceOffs   549


#endif
