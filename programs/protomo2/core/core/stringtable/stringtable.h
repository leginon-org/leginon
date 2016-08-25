/*----------------------------------------------------------------------------*
*
*  stringtable.h  -  core: character string table
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef stringtable_h_
#define stringtable_h_

#include "defs.h"

#define StringTableName   "stringtable"
#define StringTableVers   COREVERS"."COREBUILD
#define StringTableCopy   CORECOPY


/* exception codes */

enum {
  E_STRINGTABLE = StringTableModuleCode,
  E_STRINGTABLE_NOTFOUND,
  E_STRINGTABLE_EXISTS,
  E_STRINGTABLE_MAXCODE
};


/* prototypes */

extern Status StringTableInsert
              (char **table,
               const char *string,
               Size *index);

extern Status StringTableInsertLen
              (char **table,
               const char *string,
               Size length,
               Size *index);

extern Status StringTableInsertTail
              (char **table,
               const char *string,
               Size *index);

extern Status StringTableInsertTailLen
              (char **table,
               const char *string,
               Size length,
               Size *index);

extern Status StringTableLookup
              (const char *table,
               const char *string,
               Size *index);

extern Status StringTableLookupLen
              (const char *table,
               const char *string,
               Size length,
               Size *index);

extern Status StringTableDup
              (const char *src,
               char **dst);

extern Status StringTableFree
              (char **table);

extern Size StringTableSize
            (const char *table);



#endif
