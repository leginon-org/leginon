/*----------------------------------------------------------------------------*
*
*  tomopy.h  -  tomopy: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomopy_h_
#define tomopy_h_

#ifdef __cplusplus
extern "C" {
#endif

#include "tomopydefs.h"
#include <Python.h>

#define TomoPyName   TOMOPYNAME
#define TomoPyVers   TOMOPYVERS"."TOMOPYBUILD
#define TomoPyCopy   TOMOPYCOPY


/* exception codes */

enum {
  E_TOMOPY = TomoPyModuleCode,
  E_TOMOPY_MAXCODE
};


/* types */

typedef struct {
  const char *name;
  PyObject *module;
  PyObject *exception;
} TomoPy;


/* prototypes */

extern TomoPy *TomoPyInit
               (const char *name);

extern PyTypeObject *TomoPyClassInit
                     (const TomoPy *mod,
                      const char *cls,
                      PyTypeObject *obj);

extern void TomoPyBegin
            (const TomoPy *mod);

extern void TomoPyEnd
            (const TomoPy *mod);

extern void TomoPyException
            (const TomoPy *mod,
             const char *msg);


#ifdef __cplusplus
}
#endif

#endif
