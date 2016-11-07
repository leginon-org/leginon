/*----------------------------------------------------------------------------*
*
*  tomotransfer.h  -  tomography: transfer functions
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomotransfer_h_
#define tomotransfer_h_

#include "tomoparamread.h"

#define TomotransferName   "tomotransfer"
#define TomotransferVers   TOMOVERS"."TOMOBUILD
#define TomotransferCopy   TOMOCOPY


/* exception codes */

enum {
  E_TOMOTRANSFER = TomotransferModuleCode,
  E_TOMOTRANSFER_MAXCODE
};


/* data structures */

typedef struct {
  Coord A[3][3];
  Coord A1[3][3];
} Tomotransfer;

typedef struct {
  Coord body;
  Coord bfsh;
  Coord bwid;
  Coord bthr;
} TomotransferParam;


/* constants */

#define TomotransferInitializer  (Tomotransfer){ TomoMat3Undef, TomoMat3Undef };

#define TomotransferParamInitializer  (TomotransferParam){ 0, 0, 0, 0 }


/* prototypes */

extern Tomotransfer *TomotransferCreate
                     (Size n);

extern Status TomotransferDestroy
              (Size n,
               Tomotransfer *trans);

extern Coord TomotransferFsh
             (Coord A[3][3]);

extern void TomotransferScale
            (Coord A[3][3],
             Coord sampling,
             const Size len[3],
             Coord B[3][3]);

extern void TomotransferAdd
            (const Size len[2],
             const Index low[2],
             Coord Ai[3][3],
             Coord A1j[3][3],
             Real *Hi,
             const TomotransferParam *param);

extern void TomotransferCalc
            (const Size len[2],
             const Index low[2],
             Tomotransfer *trans,
             Size count,
             Coord Ai[3][3],
             Real *Hi,
             const TomotransferParam *param);

extern Status TomotransferGetParam
              (Tomoparam *tomoparam,
               const char *ident,
               TomotransferParam *transferparam);


#endif
