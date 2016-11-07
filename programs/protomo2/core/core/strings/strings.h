/*----------------------------------------------------------------------------*
*
*  strings.h  -  core: character string operations
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef strings_h_
#define strings_h_

#include "defs.h"

#define StringsName   "strings"
#define StringsVers   COREVERS"."COREBUILD
#define StringsCopy   CORECOPY


/* exception codes */

enum {
  E_STRINGS=StringsModuleCode,
  E_STRINGS_MAXCODE
};


/* prototypes */

extern Size StringListCount
            (char **list);

extern void StringListFree
            (char **list);

extern char **StringSeparate
              (const char *str,
               char sep);

extern char *StringConcat
             (const char *str, ...);

extern void StringReverse
            (char *str);


#endif
