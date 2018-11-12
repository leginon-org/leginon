/*----------------------------------------------------------------------------*
*
*  tomoparamcommon.h  -  tomography: parameter files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomoparamcommon_h_
#define tomoparamcommon_h_

#include "tomoparam.h"
#include "parse.h"
#include "stringtable.h"
#include <stdio.h>


/* types */

typedef union {
  Size uint;
  Index sint;
  Coord real;
  Bool bool;
  Size index;
} TomoparamVal;

typedef struct {
  Size dim;
  Size count;
  TomoparamVal len;
  TomoparamVal val;
  TomoparamType type;
  ParseLoc loc;
  Size name;
  Bool tmplen;
  Bool tmpval;
  Bool param;
} TomoparamVar;

typedef struct {
  TomoparamType type;
  TomoparamVal val;
  ParseLoc loc;
} TomoparamScalar;

typedef struct {
  Size dim;
  TomoparamType type;
  Size tmplen;
  Size elelen;
} TomoparamStk;

struct _Tomoparam {
  const char *prfx;
  char *sect;
  char *ident;
  char *strlit;
  char *sname;
  TomoparamVar *vartab;
  Size varlen;
  TomoparamVal *valtab;
  Size vallen;
  TomoparamVal *tmptab;
  Size tmplen;
  TomoparamVar *eletab;
  Size elelen;
  TomoparamStk *stk;
  Size stklen;
  ParseBuf *sav;
  Size savlen;
  Parse *parse;
  Bool logparam;
};


/* constants */

#define TomoparamVarInitializer  (TomoparamVar){ SizeMax, SizeMax, { 0 }, { 0 }, TomoparamUndef, ParseLocInitializer, SizeMax, False, False, False }

#define TomoparamInitializer  (Tomoparam){ NULL, NULL, NULL, NULL, NULL, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, 0, NULL, False }


/* macros */

#define TomoparamGetLen( v )  ( ( (v).dim > 1 ) ? ( (v).tmplen ? tomoparam->tmptab : tomoparam->valtab ) + (v).len.uint : &(v).len )

#define TomoparamGetVal( v )  ( (v).dim ? ( ( (v).tmpval ? tomoparam->tmptab : tomoparam->valtab ) + (v).val.uint ) : &(v).val )


/* prototypes */

extern Status TomoparamExtend
              (Tomoparam *tomoparam,
               const char *ident,
               Size len);

extern char *TomoparamAppend
             (const char *section,
              const char *ident,
              Size len);

extern void TomoparamRemove
            (char *ident);

extern Status TomoparamLookup
              (const Tomoparam *tomoparam,
               const char *ident,
               TomoparamVar **var);

extern Status TomoparamInsertIdent
              (Tomoparam *tomoparam,
               const char *ident,
               Size len,
               Size *index);

extern Status TomoparamLookupIdent
              (const Tomoparam *tomoparam,
               const char *ident,
               Size len,
               Bool param,
               Size *index);

extern Status TomoparamInsertString
              (Tomoparam *tomoparam,
               const char *ident,
               const char *val);

extern TomoparamVar *TomoparamLookupVar
                     (const Tomoparam *tomoparam,
                      Size index);

extern Status TomoparamPrintVar
              (const Tomoparam *tomoparam,
               const TomoparamVar *var,
               const char *section,
               FILE *stream);

extern Status TomoparamParseType
              (Tomoparam *tomoparam,
               const char *str,
               const TomoparamType type,
               void **val,
               int *len);

extern Status TomoparamParseNumeric
              (const char *str,
               TomoparamType *type,
               void **val,
               int *len);

extern void TomoparamLexInit
            (Tomoparam *tomoparam);

extern int tomoparam_yyparse
           (Tomoparam *tomoparam);


#endif
