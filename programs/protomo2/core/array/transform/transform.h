/*----------------------------------------------------------------------------*
*
*  transform.h  -  array: spatial transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef transform_h_
#define transform_h_

#include "statistics.h"
#include "transfer.h"

#define TransformName   "transform"
#define TransformVers   ARRAYVERS"."ARRAYBUILD
#define TransformCopy   ARRAYCOPY


/* exception codes */

enum {
  E_TRANSFORM = TransformModuleCode,
  E_TRANSFORM_CLIP,
  E_TRANSFORM_MAXCODE
};


/* types */

typedef enum {
  TransformCyc  = 0x01,
  TransformClip = 0x02,
  TransformFill = 0x04
} TransformFlags;

typedef struct {
  Size dim;
  Coord *A;
  Coord *b;
} Transform;

typedef struct {
  Stat *stat;
  TransferParam *transf;
  Coord fill;
  TransformFlags flags;
} TransformParam;


/* constants */

#define TransformInitializer  (Transform){ 0, NULL, NULL }

#define TransformParamInitializer  (TransformParam){ NULL, NULL, 0, 0 }


/* prototypes */


#endif
