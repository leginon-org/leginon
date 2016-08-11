/*----------------------------------------------------------------------------*
*
*  nmmin.h  -  approx: Nelder Mead minimization
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef nmmin_h_
#define nmmin_h_

#include "approxdefs.h"

#define NMminName   "NMmin"
#define NMminVers   APPROXVERS"."APPROXBUILD
#define NMminCopy   APPROXCOPY


/* exception codes */

enum {
  E_NMMIN = NMminModuleCode,
  E_NMMIN_FAIL,
  E_NMMIN_MAXCODE
};


/* types */

typedef Status (*NMfunc)( Size, const Coord *, Size, Coord *, void *, Size *);

typedef struct {
  const Coord *step;
  Size fncount;
  Size iter;
  const char *log;
  Coord tol;
  Coord alpha;
  Coord beta;
  Coord gamma;
} NMdata;


/* constants */

#define NMdataInitializer  (NMdata){ NULL, 0, 0, NULL, 0, 0, 0, 0 }


/* prototypes */

extern Status NMmin
              (Size n,          /* number of parameters in function */
               const Coord *X0, /* input parameters */
               NMfunc fn,       /* minimization function */
               void *fndata,    /* data for minimization function */
               NMdata *data,    /* minimization data/options */
               Coord *X,        /* output parameters */
               Size m,          /* number of returned values */
               Coord *Fmin);    /* "minimal" function value */

#endif
