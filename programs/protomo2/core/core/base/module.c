/*----------------------------------------------------------------------------*
*
*  module.c  -  core: modules
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "module.h"
#include "semaphore.h"
#include "signals.h"
#include "exception.h"
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>



/* variables */

static enum {
  CoreInitBegin,
  CoreInitStatic,
  CoreInitDynamic,
  CoreInitMain,
  CoreInitAfter,
  CoreInitDone,
  CoreInitFinal
} CoreInitStatus = CoreInitBegin;

static Status CoreRegisterStatus = E_NONE;


/* main module descriptor */

static Module CoreModule = {
  CORENAME,
  COREVERS,
  CORECOPY,
  "",
  NULL,
  NULL,
  NULL,
};

static ModuleListNode CoreModuleListNode = {
  NULL,
  NULL,
  &CoreModule,
  NULL
};


/* module lists */

static ModuleListNode *CoreModuleListHead = &CoreModuleListNode;
static ModuleListNode *CoreModuleListTail = &CoreModuleListNode;
static ModuleListNode *CoreModuleStatic = NULL;
static ModuleListNode *CoreModuleDyn = NULL;


/* argument list */

char **CoreArgv = NULL;
int *CoreArgc = NULL;

static const char *CoreRoot = NULL;
static const char *CorePath = NULL;


/* functions */

static void CoreMessage
            (const char *msg)

{

  if ( ( Main == NULL ) || !*Main ) {
    fputs( msg, stderr );
  } else {
    fprintf( stderr, "%s: %s", Main, msg );
  }

}



extern void CorePreinit
            (const char *name,
             const char *vers,
             const char *copy,
             const char *date)

{
  char *cmd = NULL;

  /* command name */
  if ( ( CoreArgv != NULL ) && ( CoreArgv[0] != NULL ) ) {
    cmd = strrchr( CoreArgv[0], '/' );
    if ( cmd == NULL ) {
      cmd = CoreArgv[0];
    } else {
      if ( *++cmd ) CoreArgv[0] = cmd;
    }
    if ( ( name == NULL ) || !*name ) {
      name = cmd;
    }
  }

  /* main module descriptor */
  if ( ( name != NULL ) && *name ) {
    CoreModule.name = name;
  }
  if ( ( vers != NULL ) && *vers ) {
    CoreModule.vers = vers;
  }
  if ( ( copy != NULL ) && *copy ) {
    CoreModule.copy = copy;
  }
  if ( ( date != NULL ) && *date ) {
    CoreModule.date = date;
  }

  if ( CoreArgv == NULL ) {
    static char *argv[2] = { CORENAME, NULL };
    static int argc = 1;
    CoreArgv = argv;
    CoreArgc = &argc;
    return;
  }

  for ( int arg = 1; arg < *CoreArgc; arg++ ) {

    if ( !strcmp( CoreArgv[arg], "-version" ) ) {

      fprintf( stderr, "%s: Version %s", CoreArgv[0], CoreModule.name );
      if ( ( vers != NULL ) && *vers ) fprintf( stderr, "-%s", vers );
      if ( ( date != NULL ) && *date ) fprintf( stderr, " [%s]", date );
      fputc( '\n', stderr );
      if ( ( copy != NULL ) && *copy ) fprintf( stderr, "%s: %s\n", CoreArgv[0], copy );
      fprintf( stderr, "%s: There is NO warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.\n", CoreArgv[0] );
      exit( EXIT_SUCCESS );

    }

  }

  int argc = 1;
  for ( int arg = 1; arg < *CoreArgc; arg++ ) {
    if ( CoreArgv[arg] != NULL ) {
      CoreArgv[argc++] = CoreArgv[arg];
    }
  }
  CoreArgv[argc] = NULL;
  *CoreArgc = argc;

}


static void CoreFinal()

{
  Status status, retstat = E_NONE;

  CoreInitStatus = CoreInitFinal;

  ExceptionReport( NULL );

  while ( CoreModuleDyn != NULL ) {
    const Module *module = CoreModuleDyn->module;
    if ( module != NULL ) {
      if ( module->final != NULL ) {
        status = module->final( CoreModuleDyn->data );
        if ( exception( status ) ) retstat = E_FINAL;
      }
    }
    CoreModuleDyn = CoreModuleDyn->next;
  }

  while ( CoreModuleStatic != NULL ) {
    const Module *module = CoreModuleStatic->module;
    if ( module != NULL ) {
      if ( module->final != NULL ) {
        status = module->final( CoreModuleStatic->data );
        if ( exception( status ) ) retstat = E_FINAL;
      }
    }
    CoreModuleStatic = CoreModuleStatic->next;
  }

  if ( retstat ) {
    pushexception( retstat );
    ExceptionReport( NULL );
  }

}


static Status ModuleInit
              (const Module *module,
               void **data)

{
  Status status;

  if ( module == NULL ) return pushexception( E_BASE );

  if ( module->init != NULL ) {
    status = module->init( module->data );
    if ( exception( status ) ) return status;
    *data = ( module->data == NULL ) ? NULL : *module->data;
  }

  return E_NONE;

}


extern Status CoreInit
              (const char *name,
               ModuleListNode *list,
               ModuleInitFunction init,
               ModuleFinalFunction final,
               void **data)

{
  Status status;

  /* initialize only once */
  if ( CoreInitStatus != CoreInitBegin ) {
    CoreMessage( "already initialized\n" ); return E_INIT;
  }

  /* module name */
  if ( ( name == NULL ) || !*name ) {
    name = CoreModule.name;
  } else {
    CorePreinit( name, NULL, NULL, NULL );
  }
  Main = name;

  /* set module descriptor */
  CoreModule.init = init;
  CoreModule.final = final;
  CoreModule.data = data;

  /* catch signals */
  if ( SignalInit() ) {
    CoreMessage( "could not set signal handlers\n" ); return E_INIT;
  }

  /* set exit function */
  if ( atexit( CoreFinal ) ) {
    CoreMessage( "could not set exit function\n" ); return E_INIT;
  }

  /* fill in reverse links */
  ModuleListNode *node = NULL;
  while ( list != NULL ) {
    list->prev = node;
    node = list;
    list = list->next;
  }

  /* initialize static modules */
  CoreInitStatus = CoreInitStatic;
  while ( node != NULL ) {
    status = ModuleInit( node->module, &node->data );
    if ( exception( status ) ) goto error;
    CoreModuleStatic = node;
    node = node->prev;
  }

  /* initialize dynamic modules */
  CoreInitStatus = CoreInitDynamic;
  node = CoreModuleListHead;
  while ( node != NULL ) {
    if ( node->module == &CoreModule ) CoreInitStatus = CoreInitMain;
    status = ModuleInit( node->module, &node->data );
    if ( exception( status ) ) goto error;
    if ( CoreInitStatus == CoreInitMain ) CoreInitStatus = CoreInitAfter;
    CoreModuleDyn = node;
    node = node->prev;
  }

  /* normal exit */
  CoreInitStatus = CoreInitDone;
  return E_NONE;

  /* error exit */
  error: ExceptionReport( NULL );
  return status;

}


static Status CoreRegisterSub
              (const char *name,
               const char *vers,
               const char *copy,
               ModuleInitFunction init,
               ModuleFinalFunction final,
               void **data,
               ModuleListNode **node)

{
  ModuleListNode *ptr;

  /* must specify name */
  if ( ( name == NULL ) || !*name ) goto error1;

  /* new module descriptor */
  Module *module = malloc( sizeof(Module) );
  if ( module == NULL ) goto error2;
  module->name = strdup( name );
  if ( module->name == NULL ) goto error3;
  module->vers = vers;
  module->copy = copy;
  module->date = "user";
  module->init = init;
  module->final = final;
  module->data = data;

  /* new list node */
  ptr = malloc( sizeof(ModuleListNode) );
  if ( ptr == NULL ) goto error4;
  ptr->module = module;
  ptr->data = NULL;

  /* normal exit */
  *node = ptr;
  return E_NONE;

  /* error exits */
  error4: free( (void *)module->name );
  error3: free( module );
  error2: return E_MALLOC;
  error1: return E_REGISTER;

}


static void CoreLink
            (ModuleListNode *node)

{

  node->prev = &CoreModuleListNode;
  node->next = CoreModuleListNode.next;
  CoreModuleListNode.next = node;
  if ( node->next == NULL ) {
    CoreModuleListHead = node;
  } else {
    node->next->prev = node;
  }

}


static void CoreLinkAfter
            (ModuleListNode *node)

{

  node->prev = CoreModuleListTail->prev;
  node->next = CoreModuleListTail;
  CoreModuleListTail->prev = node;
  CoreModuleListTail = node;

}


extern void CoreRegister
            (const char *name,
             const char *vers,
             const char *copy,
             ModuleInitFunction init,
             ModuleFinalFunction final,
             void **data)

{
  ModuleListNode *node;

  if ( CoreInitStatus != CoreInitBegin ) {

    CoreRegisterStatus = E_REGISTER;

  } else if ( !CoreRegisterStatus ) {

    CoreRegisterStatus = CoreRegisterSub( name, vers, copy, init, final, data, &node );

    if ( !CoreRegisterStatus ) CoreLink( node );

  }

}


extern void CoreRegisterAfter
            (const char *name,
             const char *vers,
             const char *copy,
             ModuleInitFunction init,
             ModuleFinalFunction final,
             void **data)

{
  ModuleListNode *node;

  if ( CoreInitStatus != CoreInitBegin ) {

    CoreRegisterStatus = E_REGISTER;

  } else if ( !CoreRegisterStatus ) {

    CoreRegisterStatus = CoreRegisterSub( name, vers, copy, init, final, data, &node );

    if ( !CoreRegisterStatus ) CoreLinkAfter( node );

  }

}


extern void *CoreRegisterAtExit
             (const char *name,
              const char *vers,
              const char *copy,
              ModuleFinalFunction final,
              void *data)

{
  ModuleListNode *node;
  Status status;

  if ( CoreInitStatus != CoreInitDone ) return NULL;

  status = CoreRegisterSub( name, vers, copy, NULL, final, NULL, &node );
  if ( exception( status ) ) return NULL;

  node->prev = NULL;
  node->next = CoreModuleDyn;
  node->data = data;
  CoreModuleDyn->prev = node;
  CoreModuleDyn = node;

  return node;

}


extern void CoreUnregisterAtExit
            (void *handle)

{
  ModuleListNode *node = handle;

  if ( node != NULL ) {
    node->module = NULL;
    node->data = NULL;
  }

}


extern Status CoreRegisterSetStatus
              (Status status)

{

  if ( status ) {
    if ( !CoreRegisterStatus ) {
      CoreRegisterStatus = status;
    }
  }

  return CoreRegisterStatus;

}


extern char *CoreCopyVersion
             (Size *len,
              char *buf)

{
  const char *ptr = CoreModule.name;

  while ( *len && *ptr ) {
    *buf++ = *ptr++;
    (*len)--;
  }
  if ( *len ) {
    *buf++ = '-';
    (*len)--;
    ptr = CoreModule.vers;
    while ( *len && *ptr ) {
      *buf++ = *ptr++;
      (*len)--;
    }
    if ( *len ) {
      *buf = 0;
    }
  }
  return buf;

}


static Size CoreCopy
            (const char *src,
             char *dst,
             Size len)

{
  Size count = 0;

  if ( *src != DIRSEP ) return 0;

  while ( len && *src ) {

    *dst++ = *src++; len--; count++;
    while ( *src == DIRSEP ) src++;

    while ( len && *src && ( *src != DIRSEP ) ) {
      *dst++ = *src++; len--; count++;
    }

  }

  if ( !len ) return 0;

  *dst-- = 0;
  if ( ( count > 1 ) && ( *dst == DIRSEP ) ) {
    *dst = 0; count--;
  }

  return count;

}


extern Size CoreCopyRoot
            (char *buf,
             Size len)

{
  static const char *rootenv = BUILDPRFX "ROOT";
  const char *root;

  if ( buf == NULL ) return 0;

  if ( CoreRoot == NULL ) {
    root = getenv( rootenv );
    if ( root == NULL ) return 0;
  } else {
    root = CoreRoot;
  }
  Size rootlen = CoreCopy( root, buf, len );

  return rootlen;

}


extern Size CoreCopyPath
            (char *buf,
             Size len)

{
  static const char lib[] = DIRSEPSTR "lib" DIRSEPSTR OS DIRSEPSTR ARCH DIRSEPSTR;
  static const char pathenv[] = BUILDPRFX "PATH";
  const char *path;
  Size pathlen;

  if ( buf == NULL ) return 0;

  if ( CorePath == NULL ) {

    path = getenv( pathenv );

    if ( path == NULL ) {

      pathlen = CoreCopyRoot( buf, len );
      if ( !pathlen ) return 0;

      Size liblen = CoreCopy( lib, buf + pathlen, len - pathlen );
      if ( !liblen ) return 0;

      pathlen += liblen;

    } else {

      pathlen = CoreCopy( path, buf, len );

    }

  } else {

    pathlen = CoreCopy( CorePath, buf, len );

  }

  return pathlen;

}


extern Status CoreSetRoot
              (const char *path)

{

  if ( path == NULL ) {
    free( (char *)CoreRoot ); CoreRoot = NULL;
    return E_NONE;
  }

  Size len = strlen( path ) + 1;
  char *ptr = malloc( len );
  if ( ptr == NULL ) return E_MALLOC;

  len = CoreCopy( path, ptr, len );
  if ( !len ) {
    free( ptr ); return E_ARGVAL;
  }

  free( (char *)CoreRoot );
  CoreRoot = ptr;

  return E_NONE;

}


extern Status CoreSetPath
              (const char *path)

{

  if ( path == NULL ) {
    free( (char *)CorePath ); CorePath = NULL;
    return E_NONE;
  }

  Size len = strlen( path ) + 1;
  char *ptr = malloc( len );
  if ( ptr == NULL ) return E_MALLOC;

  len = CoreCopy( path, ptr, len );
  if ( !len ) {
    free( ptr ); return E_ARGVAL;
  }

  free((char *) CorePath );
  CorePath = ptr;

  return E_NONE;

}


extern Status ModuleRegister
              (const Module *module)

{

  if ( CoreInitStatus != CoreInitStatic ) {
    if ( CoreInitStatus == CoreInitBegin ) {
      return E_REGISTER;
    } else {
      return pushexception( E_REGISTER );
    }
  }

  ModuleListNode *node = malloc( sizeof(ModuleListNode) );
  if ( node == NULL ) return pushexception( E_MALLOC );

  node->module = module;
  node->data = NULL;

  CoreLink( node );

  return E_NONE;

}


extern Status ModuleRegisterAfter
              (const Module *module)

{

  if ( CoreInitStatus == CoreInitBegin ) return E_REGISTER;

  ModuleListNode *node = malloc( sizeof(ModuleListNode) );
  if ( node == NULL ) return pushexception( E_MALLOC );

  node->module = module;
  node->data = NULL;

  CoreLinkAfter( node );

  return E_NONE;

}


extern Status ModuleInitAfter
              (const Module *module)

{
  Status status;

  if ( CoreInitStatus == CoreInitBegin ) return E_REGISTER;

  ModuleListNode *node = malloc( sizeof(ModuleListNode) );
  if ( node == NULL ) return pushexception( E_MALLOC );

  status = ModuleInit( module, &node->data );
  if ( exception( status ) ) {
    free( node ); return status;
  }

  node->module = module;

  CoreLinkAfter( node );

  return E_NONE;

}


#ifdef ENABLE_DYNAMIC

static Status ModuleDyn
              (const char *sopath,
               const char *soname,
               const char *sosym,
               const char *name,
               const char *vers,
               void **data)

{
  Module *mod, *dat = NULL;
  Status status;

  if ( data != NULL ) {
    dat = malloc( sizeof(*dat) );
    if ( dat == NULL ) return pushexception( E_MALLOC );
  }

  const char *msg = "dlopen";
  void *dl = dlopen( sopath, RTLD_LAZY );
  char *err = dlerror();
  if ( dl == NULL ) goto error1;

  msg = "dlsym";
  mod = dlsym( dl, sosym );
  err = dlerror();
  if ( mod == NULL ) goto error1;

  if ( data != NULL ) {
    *dat = *mod;
    mod = dat;
    mod->data = data;
  }

  if ( name != NULL ) {
    if ( strcmp( name, mod->name ) ) { status = pushexceptionmsg( E_MODULE, ", ", soname ); goto error0; }
  }

  if ( vers != NULL ) {
    if ( strcmp( vers, mod->vers ) ) { status = pushexceptionmsg( E_MODULE, ", ", soname ); goto error0; }
  }

  status = ModuleRegister( mod );
  if ( exception( status ) ) goto error0;

  return E_NONE;

  error1:

  status = userexceptionmsg( msg, ": ", ( err == NULL ) ? "<NULL>" : err );

  error0:

  if ( dl != NULL ) {
    if ( dlclose( dl ) ) {
      err = dlerror();
    }
  }

  if ( dat != NULL ) free( dat );

  return status;

}


#define BUFLEN 256

extern Status ModuleDynRegister
              (const char *soname,
               const char *sosym,
               const char *name,
               const char *vers,
               void **data)

{
  char buf[BUFLEN];
  Status status;

  Size buflen = CoreCopyPath( buf, BUFLEN );
  if ( !buflen ) return pushexception( E_PATH );
  Size solen = ( soname == NULL ) ? 0 : strlen( soname );
  if ( !solen ) return pushexception( E_PATH );
  if ( buflen + 1 + solen + 1 > BUFLEN ) return pushexception( E_INTERNAL );
  buf[buflen++] = DIRSEP;
  strcpy( buf + buflen, soname );

  dlerror();
  status = ModuleDyn( buf, soname, sosym, name, vers, data );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern Status ModuleDynRegisterTable
              (const ModuleTable *table,
               const char *vers)

{
  char buf[BUFLEN];
  Status status;

  Size buflen = CoreCopyPath( buf, BUFLEN );
  if ( !buflen ) return pushexception( E_PATH );

  const ModuleTable *tab;
  Size count = 0;
  dlerror();

  for ( tab = table; tab->soname != NULL; tab++ ) {

    Size solen = strlen( tab->soname );
    if ( buflen + 1 + solen + 1 > BUFLEN ) return pushexception( E_INTERNAL );
    buf[buflen] = DIRSEP;
    strcpy( buf + buflen + 1, tab->soname );

    int fd = open( buf, O_RDONLY );
    if ( fd < 0 ) {
      if ( errno == ENOENT ) {
        continue;
      }
    } else {
      close( fd );
    }

    status = ModuleDyn( buf, tab->soname, tab->sosym, tab->ident, vers, NULL );
    if ( exception( status ) ) {
      ExceptionClear();
      fprintf( stderr, "%s: could not load %s, %s disabled\n", Main, tab->soname, tab->sosym );
    } else {
      count++;
    }

  }

  if ( !count && ( tab->ident != NULL ) ) {
    return userexceptionmsg( "no ", tab->ident, " modules found" );
  }

  return E_NONE;

}

#endif
