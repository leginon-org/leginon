/*----------------------------------------------------------------------------*
*
*  tomopyeman.h  -  eman wrapper library
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomopyeman_h_
#define tomopyeman_h_

#ifdef __cplusplus
extern "C" {
#endif

#include "tomopy.h"
#include <Python.h>

#define TomoPyEmanName   TomoPyName"eman"
#define TomoPyEmanVers   TOMOPYVERS"."TOMOPYBUILD
#define TomoPyEmanCopy   TOMOPYCOPY


/* exception codes */

enum {
  E_TOMOPYEMAN = TomoPyEmanModuleCode,
  E_TOMOPYEMAN_INIT,
  E_TOMOPYEMAN_EMDATA,
  E_TOMOPYEMAN_MAXCODE
};


/* types */

typedef struct {
  PyObject *(*create)();
  int (*set)(PyObject *,PyObject *);
  PyObject *(*get)(PyObject *);
} TomoPyEmanFn;


/* prototypes */

extern PyObject *TomoPyEmanNew();

extern int TomoPyEmanSet
           (PyObject *emobj,
            PyObject *imgobj);

extern PyObject *TomoPyEmanGet
                 (PyObject *self);

extern int TomoPyEmanCheck
           (PyObject *self);


#ifdef __cplusplus
}
#endif

#endif
