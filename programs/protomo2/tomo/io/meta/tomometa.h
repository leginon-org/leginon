/*----------------------------------------------------------------------------*
*
*  tomometa.h  -  series: tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomometa_h_
#define tomometa_h_

#include "tomotilt.h"
#include "tomofile.h"
#include "i3io.h"

#define TomometaName   "tomometa"
#define TomometaVers   TOMOIOVERS"."TOMOIOBUILD
#define TomometaCopy   TOMOIOCOPY


/* exception codes */

enum {
  E_TOMOMETA = TomometaModuleCode,
  E_TOMOMETA_FMT,
  E_TOMOMETA_MAXCODE
};


/* types */

struct _Tomometa;

typedef struct _Tomometa Tomometa;


/* prototypes */

extern Tomometa *TomometaCreate
                 (const char *path,
                  const char *prfx,
                  const Tomotilt *tilt,
                  Tomoflags flags);

extern Tomometa *TomometaOpen
                 (const char *path,
                  const char *prfx,
                  Tomotilt **tiltptr,
                  Tomofile **fileptr,
                  Tomoflags flags);

extern Tomometa *TomometaCreateSegm
                 (I3io *i3io,
                  int segm,
                  const Tomotilt *tilt,
                  Tomoflags flags);

extern Tomometa *TomometaOpenSegm
                 (I3io *i3io,
                  int segm,
                  Tomotilt **tiltptr,
                  Tomofile **fileptr,
                  Tomoflags flags);

extern Status TomometaClose
              (Tomometa *meta,
               Status fail);

extern Status TomometaWrite
              (Tomometa *meta,
               const Tomotilt *tilt,
               const Tomofile *file);

extern Status TomometaUpdate
              (Tomometa *meta,
               const Tomotilt *tilt);

extern Status TomometaSave
              (const Tomometa *meta,
               const char *path);

extern Status TomometaSaveSegm
              (const Tomometa *meta,
               I3io *i3io,
               int segm);

extern IOMode TomometaGetMode
              (const Tomometa *meta);

extern int TomometaGetCycle
           (const Tomometa *meta);

extern Size TomometaGetImages
            (const Tomometa *meta);

extern Tomotilt *TomometaGetTilt
                 (Tomometa *meta);

extern Status TomometaSetCycle
              (Tomometa *meta,
               int cycle);

extern Status TomometaSetEuler
              (Tomometa *meta,
               Tomotilt *tilt,
               const Coord euler[3]);

extern Status TomometaSetOrigin
              (Tomometa *meta,
               Tomotilt *tilt,
               const Coord origin[3]);

extern Status TomometaResetTransf
              (Tomometa *meta);

extern Status TomometaSetTransf
              (Tomometa *meta,
               Size index,
               Coord Ap[3][2],
               Bool fulltransf);

extern Status TomometaGetTransf
              (Tomometa *meta,
               Size index,
               Coord Ap[3][2],
               Bool *fulltransf);


#endif
