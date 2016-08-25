/*----------------------------------------------------------------------------*
*
*  window.h  -  window: image window
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef window_h_
#define window_h_

#include "mask.h"

#define WindowName   "window"
#define WindowVers   ARRAYVERS"."ARRAYBUILD
#define WindowCopy   ARRAYCOPY


/* exception codes */

enum {
  E_WINDOW = WindowModuleCode,
  E_WINDOW_AREA,
  E_WINDOW_MAXCODE
};


/* data structures */

typedef struct {
  Size dim;
  const Size *len;
  Size size;
  Coord area;
} Window;

typedef struct {
  const MaskParam *msk;
  Coord area;
} WindowParam;


/* constants */

#define WindowInitializer  (Window){ 0, NULL, 0, 0 }

#define WindowParamInitializer  (WindowParam){ NULL, -1 }


/* macros */

#define WindowAlloc( w )  ( (Real *)malloc( (w)->size * sizeof(Real) ) )


/* prototypes */

extern Status WindowInit
              (Size dim,
               const Size *len,
               Window *win,
               const WindowParam *param);

extern Status WindowCut
              (const Size *len,
               Type type,
               const void *addr,
               const Size *ori,
               const Window *win,
               Real *winaddr,
               Size *count,
               const MaskParam *winmsk);

extern Status WindowCutNorm
              (const Size *len,
               Type type,
               const void *addr,
               const Size *ori,
               const Window *win,
               Real *winaddr,
               Size *count,
               const MaskParam *winmsk);

extern Status WindowExtract
              (const Size *len,
               Type type,
               const void *addr,
               const Size *b,
               const Window *win,
               Real *winaddr,
               Size *count,
               const MaskParam *winmsk);

extern Status WindowExtractNorm
              (const Size *len,
               Type type,
               const void *addr,
               const Size *b,
               const Window *win,
               Real *winaddr,
               Size *count,
               const MaskParam *winmsk);

extern Status WindowSample
              (const Size *len,
               Type type,
               const void *addr,
               const Size *smp,
               const Size *b,
               const Window *win,
               Real *winaddr,
               Stat *winstat,
               const MaskParam *winmsk);

extern Status WindowResample
              (const Size *len,
               Type type,
               const void *addr,
               const Coord *A,
               const Coord *b,
               const Window *win,
               Real *winaddr,
               Stat *winstat,
               const MaskParam *winmsk);


#endif
