/*----------------------------------------------------------------------------*
*
*  tomometacommon.h  -  series: tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomometacommon_h_
#define tomometacommon_h_

#include "tomometa.h"


/* macros */

#define CYC   0
#define HDR   1
#define STR   2
#define PAR   3
#define FIL   4
#define IMG   5
#define TRF   6
#define OFFS  7

#define GLOBL 0
#define AXIS  1
#define ORIEN 2
#define GEOM  3
#define BLOCK 4


/* data structures */

#define HDRVRS 0
#define HDRSTR 1
#define HDRAXS 2
#define HDRORN 3
#define HDRIMG 4
#define HDRFIL 5
#define TomometaHeaderSize 6

typedef uint32_t TomometaHeader[TomometaHeaderSize];

#define PARVRS 0
#define PARPIX 1
#define PARLMB 2
#define PARCS  3
#define PARFS  4
#define PARBET 5
#define PARRESERVED  6
#define PARRESERVED2 7
#define TomometaParamSize 8

typedef uint64_t TomometaParam[TomometaParamSize];

#define FILIND   0
#define FILDIM   1
#define FILLEN0  2
#define FILLEN1  3
#define FILLEN2  4
#define FILLOW0  5
#define FILLOW1  6
#define FILLOW2  7
#define FILTYPE  8
#define FILATTR  9
#define FILCHKS 10
#define FILCHKSLEN 16
#define TomometaTiltfileSize ( FILCHKS + FILCHKSLEN )

typedef uint32_t TomometaTiltfile[TomometaTiltfileSize];

#define IMGNUM  0
#define IMGIND  1
#define IMGOFF  2
#define IMGPIX  3
#define IMGLOCX 4
#define IMGLOCY 5
#define IMGFOC  6
#define IMGCAST 7
#define IMGPAST 8
#define IMGAMPC 9
#define IMGRESERVED  10
#define IMGRESERVED2 11
#define TomometaImageSize 12

typedef uint64_t TomometaImage[TomometaImageSize];

#define TRFHDR 0
#define TRFTRF 1
#define TomometaTransfSize ( TRFTRF + 3 * 2 )

typedef uint64_t TomometaTransf[TomometaTransfSize];

#define GLBREF  0
#define GLBEUL0 1
#define GLBEUL1 2
#define GLBEUL2 3
#define GLBORIX 4
#define GLBORIY 5
#define GLBORIZ 6
#define GLBRESERVED 7
#define TomometaGlobalSize 8

typedef uint64_t TomometaGlobal[TomometaGlobalSize];

#define AXSREF 0
#define AXSPHI 1
#define AXSTHE 2
#define AXSOFF 3
#define TomometaAxisSize 4

typedef uint64_t TomometaAxis[TomometaAxisSize];

#define ORNAXS  0
#define ORNEUL0 1
#define ORNEUL1 2
#define ORNEUL2 3
#define TomometaOrientSize 4

typedef uint64_t TomometaOrient[TomometaOrientSize];

#define GEOAXS  0
#define GEOORN  1
#define GEOORIX 2
#define GEOORIY 3
#define GEOTHET 4
#define GEOALPH 5
#define GEOBETA 6
#define GEOCORX 7
#define GEOCORY 8
#define GEOSCAL 9
#define TomometaGeomSize 10

typedef uint64_t TomometaGeom[TomometaGeomSize];

struct _Tomometa {
  const char *ident;
  I3io *handle;
  IOMode mode;
  int32_t cycle;
  Bool hdrwr;
  TomometaHeader header;
  TomometaParam param;
  TomometaGlobal global;
};


/* prototypes */

extern char *TomometaPath
             (const char *path,
              const char *prfx);

extern Status TomometaInit
              (Tomometa *meta,
               const Tomotilt *tilt);

extern Status TomometaSetup
              (Tomometa *meta,
               Tomotilt **tiltptr,
               Tomofile **fileptr,
               Tomoflags flags);

extern Status TomometaCycleInit
              (Tomometa *meta,
               const Size cycle);

extern Status TomometaInitTransf
              (Tomometa *meta);

#endif
