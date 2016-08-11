/*----------------------------------------------------------------------------*
*
*  tomoparam.h  -  tomography: parameter files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoparam_h_
#define tomoparam_h_

#include "tomodefs.h"
#include <stdio.h>

#define TomoparamName   "tomoparam"
#define TomoparamVers   TOMOVERS"."TOMOBUILD
#define TomoparamCopy   TOMOCOPY


/* exception codes */

enum {
  E_TOMOPARAM = TomoparamModuleCode,
  E_TOMOPARAM_OPSEC,
  E_TOMOPARAM_UNSEC,
  E_TOMOPARAM_UNDEF,
  E_TOMOPARAM_UINT,
  E_TOMOPARAM_REAL,
  E_TOMOPARAM_IDENT,
  E_TOMOPARAM_EXISTS,
  E_TOMOPARAM_OPERAT,
  E_TOMOPARAM_OPER,
  E_TOMOPARAM_TYPE,
  E_TOMOPARAM_DAT,
  E_TOMOPARAM_DIM,
  E_TOMOPARAM_LEN,
  E_TOMOPARAM_MAT,
  E_TOMOPARAM_SEL,
  E_TOMOPARAM_MAXCODE
};


/* data structures */

typedef enum {
  TomoparamUndef,
  TomoparamUint,
  TomoparamSint,
  TomoparamReal,
  TomoparamBool,
  TomoparamStr,
  TomoparamTypeMax
} TomoparamType;

struct _Tomoparam;

typedef struct _Tomoparam Tomoparam;


/* prototypes */

extern Tomoparam *TomoparamParse
                 (const char *path);

extern void TomoparamDestroy
            (Tomoparam *tomoparam);

extern Tomoparam *TomoparamDup
                  (Tomoparam *tomoparam);

extern char *TomoparamGetPrfx
             (const Tomoparam *tomoparam);

extern const char *TomoparamSname
                   (const Tomoparam *tomoparam);

extern Status TomoparamSet
              (Tomoparam *tomoparam,
               const char *section,
               const char **sname);

extern Status TomoparamPush
              (Tomoparam *tomoparam,
               const char *ident,
               const char **sname);

extern Status TomoparamPop
              (Tomoparam *tomoparam,
               const char **sname);

extern void TomoparamSetLog
            (Tomoparam *tomoparam);

extern void TomoparamClearLog
            (Tomoparam *tomoparam);

extern char *TomoparamGetValue
             (const Tomoparam *tomoparam,
              const char *ident);

extern Status TomoparamList
              (const Tomoparam *tomoparam,
               const char *ident,
               const char *section,
               FILE *stream);

extern Status TomoparamReadMeta
              (const Tomoparam *tomoparam,
               const char *ident,
               Size *dim,
               Size **lenaddr,
               TomoparamType *type);

extern Status TomoparamReadSize
              (const Tomoparam *tomoparam,
               const char *ident,
               Size *dim,
               Size **len,
               Size **val,
               Size *count);

extern Status TomoparamReadIndex
              (const Tomoparam *tomoparam,
               const char *ident,
               Size *dim,
               Size **len,
               Index **val,
               Size *count);

extern Status TomoparamReadCoord
              (const Tomoparam *tomoparam,
               const char *ident,
               Size *dim,
               Size **len,
               Coord **val,
               Size *count);

extern Status TomoparamReadScalarSize
              (const Tomoparam *tomoparam,
               const char *ident,
               Size *scalar);

extern Status TomoparamReadScalarIndex
              (const Tomoparam *tomoparam,
               const char *ident,
               Index *scalar);

extern Status TomoparamReadScalarCoord
              (const Tomoparam *tomoparam,
               const char *ident,
               Coord *scalar);

extern Status TomoparamReadScalarBool
              (const Tomoparam *tomoparam,
               const char *ident,
               Bool *scalar);

extern Status TomoparamReadScalarString
              (const Tomoparam *tomoparam,
               const char *ident,
               char **scalar);

extern Status TomoparamReadArraySize
              (const Tomoparam *tomoparam,
               const char *ident,
               Size *array,
               Size len,
               Size *outlen);

extern Status TomoparamReadArrayIndex
              (const Tomoparam *tomoparam,
               const char *ident,
               Index *array,
               Size len,
               Size *outlen);

extern Status TomoparamReadArrayCoord
              (const Tomoparam *tomoparam,
               const char *ident,
               Coord *array,
               Size len,
               Size *outlen);

extern Status TomoparamReadMat
              (const Tomoparam *tomoparam,
               const char *ident,
               Coord *array,
               const Size *len,
               Size *outlen);

extern Status TomoparamReadMatn
              (const Tomoparam *tomoparam,
               const char *ident,
               Coord *array,
               Size len,
               Size *outlen);

extern Status TomoparamReadSelection
              (const Tomoparam *tomoparam,
               const char *ident,
               Size **selection);

extern Status TomoparamWrite
              (Tomoparam *tomoparam,
               const char *ident,
               TomoparamType type,
               Size dim,
               const Size *len,
               const void *val);

extern Status TomoparamWriteParam
              (Tomoparam *tomoparam,
               const char *ident,
               const char *val);


#endif
