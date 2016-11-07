/*----------------------------------------------------------------------------*
*
*  imagiciodefs.h  -  imageio: imagic files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef imagiciodefs_h_
#define imagiciodefs_h_

#include "defs.h"


/* types */

typedef struct {
  int32_t imn;          /*  1   */
  int32_t ifol;         /*  2 M */
  int32_t ierror;
  int32_t nblocks;      /*  4 M */     /* nhfr */
  int32_t nmonth;       /*  5 M */
  int32_t nday;         /*  6 M */
  int32_t nyear;        /*  7 M */
  int32_t nhour;        /*  8 M */
  int32_t nminut;       /*  9 M */
  int32_t nsec;         /* 10 M */
  int32_t rsize;        /* 11   */    /* npix2 */
  int32_t izold;        /* 12   */    /* npixel */
  int32_t ixlp;         /* 13 M */    /* number of lines per image */
  int32_t iylp;         /* 14 M */    /* number of pixels per line */
  char type[4];         /* 15 M */
  int32_t ixold;
  int32_t iyold;
  Real32 avdens;        /* 18 */
  Real32 sigma;
  Real32 user1;         /* 20 */    /* varian */
  Real32 user2;         /* 21 */    /* oldavd */
  Real32 densmax;
  Real32 densmin;
  int32_t cmplx;
  Real32 defocus1;      /* 25 */    /* cxlength */
  Real32 defocus2;      /* 26 */    /* cylength */
  Real32 defangle;      /* 27 */    /* czlength */
  Real32 sinostrt;      /* 28 */    /* calpha */
  Real32 sinoend;       /* 29 */    /* cbeta */
  char name[80];        /* 30 */
  Real32 ccc3d;         /* 50 */    /* cgamma */
  int32_t ref3d;        /* 51 */    /* mapc */
  int32_t mident;       /* 52 */    /* mapr */
  int32_t ezshift;      /* 53 */    /* maps */
  Real32 ealpha;        /* 54 */    /* ispg */
  Real32 ebeta;         /* 55 */    /* nxstart */
  Real32 egamma;        /* 56 */    /* nystart */
  int32_t ref3dold;     /* 57 */    /* nzstart */
  int32_t active;       /* 58 */    /* nxintv */
  int32_t nalisum;      /* 59 */    /* nyintv */
  int32_t pgroup;       /* 60 */    /* nzintv */
  int32_t izlp;         /* 61 M */
  int32_t i4lp;         /* 62 M */
  int32_t i5lp;
  int32_t i6lp;
  Real32 alpha;         /* 65 */
  Real32 beta;
  Real32 gamma;
  int32_t imavers;      /* 68 M */
  int32_t realtype;     /* 69 M */
  int32_t bufvar[30];
  Real32 angle;         /* 100 */
  Real32 voltage;       /* 101 */   /* rcp */
  Real32 spaberr;       /* 102 */   /* ixpeak */
  Real32 focdist;       /* 103 */   /* iypeak */
  Real32 ccc;
  Real32 errar;
  Real32 err3d;
  int32_t ref;
  Real32 classno;
  Real32 locold;
  Real32 repqual;       /* 110 */    /* oldavdens */
  Real32 zshift;        /* 111 */    /* oldsigma */
  Real32 xshift;        /* 112 */
  Real32 yshift;
  Real32 numcls;
  Real32 ovqual;
  Real32 eangle;
  Real32 exshift;
  Real32 eyshift;
  Real32 cmtotvar;
  Real32 informat;
  int32_t numeigen;
  int32_t niactive;
  Real32 resol;         /* 123 */
  Real32 reserved124;
  Real32 reserved125;
  Real32 alpha2;
  Real32 beta2;
  Real32 gamma2;
  Real32 nmetric;       /* 129 */
  Real32 actmsa;        /* 130 */
  Real32 coosmsa[69];   /* 131 */
  char history[228];    /* 200 */
} ImagicHeader;


/* macros */

#define ImagicHeaderSize 1024


#endif
