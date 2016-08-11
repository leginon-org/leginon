/*----------------------------------------------------------------------------*
*
*  spideriodefs.h  -  imageio: spider files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef spideriodefs_h_
#define spideriodefs_h_

#include "defs.h"


/* types */

typedef enum {
  SPIDER_FMT_2D = 1,
  SPIDER_FMT_3D = 3,
  SPIDER_FMT_2D_FOU_ODD  = -11,
  SPIDER_FMT_2D_FOU_EVEN = -12,
  SPIDER_FMT_3D_FOU_ODD  = -21,
  SPIDER_FMT_3D_FOU_EVEN = -22,
} SpiderType;

typedef struct {
  Real32 nslice;         /* 1 */
  Real32 nrow;           /* 2 */
  Real32 irec;
  Real32 nhistrec;
  Real32 iform;          /* 5 */
  Real32 imami;          /* 6 */
  Real32 fmax;           /* 7 */
  Real32 fmin;
  Real32 av; 
  Real32 sig;
  Real32 ihist;
  Real32 nsam;           /* 12 */
  Real32 labrec;
  Real32 iangle;         /* 14 */
  Real32 phi;
  Real32 theta;
  Real32 gamma;
  Real32 xoff;           /* 18 */
  Real32 yoff;
  Real32 zoff;
  Real32 scale;
  Real32 labbyt;         /* 22 */
  Real32 lenbyt;
  Real32 istack;         /* 24 */
  Real32 unused25;
  Real32 maxim;
  Real32 imgnum;
  Real32 lastindx;
  Real32 unused29;
  Real32 unused30;
  Real32 kangle;
  Real32 phi1;           /* 32 */
  Real32 theta1;
  Real32 psi1;
  Real32 phi2;           /* 35 */
  Real32 theta2;
  Real32 psi2;
  Real32 unused38[2];
  Real32 unused40[10];
  Real32 jose[27];       /* 50 */
  Real32 unused77[3];
  Real32 unused80[20];
  Real32 unused100[100];
  Real32 unused200[12];
  char cdat[12];          /* 212 */
  char ctim[8];           /* 215 */
  char ctit[160];         /* 217 */
} SpiderHeader;


/* macros */

#define SpiderHeaderSize 1024


#endif
