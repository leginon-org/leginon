/*----------------------------------------------------------------------------*
*
*  module.h  -  core: modules
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef module_h_
#define module_h_

#include "defs.h"
#include <stdlib.h>
#ifdef ENABLE_DYNAMIC
  #include <dlfcn.h>
#endif



/* module initialization/finalization */

typedef Status (*ModuleInitFunction)( void **data );
typedef Status (*ModuleFinalFunction)( void *data );


/* data structures */

typedef struct {
  const char *name;
  const char *vers;
  const char *copy;
  const char *date;
  ModuleInitFunction init;
  ModuleFinalFunction final;
  void **data;
} Module;

typedef struct _ModuleListNode ModuleListNode;

struct _ModuleListNode {
  ModuleListNode *prev;
  ModuleListNode *next;
  const Module *module;
  void *data;
};

typedef struct {
  const char *soname;
  const char *sosym;
  const char *ident;
} ModuleTable;


/* variables */

extern int *CoreArgc;
extern char **CoreArgv;


/* prototypes */

extern Status CoreInit
              (const char *name,
               ModuleListNode *list,
               ModuleInitFunction init,
               ModuleFinalFunction final,
               void **data);

extern void *CoreRegisterAtExit
             (const char *name,
              const char *vers,
              const char *copy,
              ModuleFinalFunction final,
              void *data);

extern void CoreUnregisterAtExit
            (void *handle); 

extern Status CoreRegisterSetStatus
              (Status status);

extern char *CoreCopyVersion
             (Size *len,
              char *buf);

extern Size CoreCopyRoot
            (char *buf,
             Size len);

extern Size CoreCopyPath
            (char *buf,
             Size len);

extern Status CoreSetRoot
              (const char *path);

extern Status CoreSetPath
              (const char *path);

extern Status ModuleRegister
              (const Module *module);

extern Status ModuleRegisterAfter
              (const Module *module);

extern Status ModuleInitAfter
              (const Module *module);

#ifdef ENABLE_DYNAMIC

extern Status ModuleDynRegister
              (const char *soname,
               const char *sosym,
               const char *name,
               const char *vers,
               void **data);

extern Status ModuleDynRegisterTable
              (const ModuleTable *table,
               const char *vers);

#endif

#endif
