/*----------------------------------------------------------------------------*
*
*  tomopy.c  -  tomopy: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomopymodule.h"
#include "tomopyimagemodule.h"

#include "exception.h"
#include "signals.h"
#include "strings.h"
#include <stdlib.h>
#include <string.h>


/* variables */

static const char *TomoPyMain = NULL;


/* functions */

extern TomoPy *TomoPyInit
               (const char *name)

{
  static Bool init = False;
  Status status;

  if ( !init ) {
    SignalCatch = 1;
    status = CoreInit( name, ModuleListPtr, NULL, NULL, NULL );
    if ( status ) exit( EXIT_FAILURE );
    init = True;
  }

  TomoPy *mod = malloc( sizeof(TomoPy) );
  if ( mod == NULL ) goto error;

  char *modname = StringConcat( name, " module", NULL );
  if ( modname == NULL ) goto error;
  mod->name = modname;

  mod->module = Py_InitModule3( name, NULL, mod->name );
  if ( mod->module == NULL ) goto error;

  size_t len = strlen( name );
  strcpy( modname + len, ".error" );
  mod->exception = PyErr_NewException( modname, NULL, NULL );
  Py_INCREF( mod->exception );
  PyModule_AddObject( mod->module, "error", mod->exception );

  modname[len] = 0;

  return mod;

  error: pushexception( E_TOMOPY ); exit( EXIT_FAILURE );

  return NULL;

}


extern PyTypeObject *TomoPyClassInit
                     (const TomoPy *mod,
                      const char *cls,
                      PyTypeObject *obj)

{

  obj->tp_name = StringConcat( mod->name, ".", cls, NULL );
  obj->tp_doc  = StringConcat( obj->tp_name, " object", NULL );

  if ( PyType_Ready( obj ) < 0 ) {
    pushexception( E_TOMOPY ); exit( EXIT_FAILURE );
  }

  Py_INCREF( obj );

  PyModule_AddObject( mod->module, cls, (PyObject *)obj );

  return obj;

}


extern void TomoPyBegin
            (const TomoPy *mod)

{

  TomoPyMain = Main;
  Main = mod->name;
  SignalSet();

}


extern void TomoPyEnd
            (const TomoPy *mod)

{

  TomoPyException( mod, NULL ); 
  SignalRestore();
  Main = TomoPyMain;

}


static void TomoPyExceptionReport
            (Status code,
             const char *ident,
             const char *msg,
             void *data)

{
  char **txt = data;

  if ( *txt == NULL ) {
    *txt = strdup( msg );
  } else {
    *txt = StringConcat( *txt, "\n  ", msg, NULL );
  }

}


extern void TomoPyException
            (const TomoPy *mod,
             const char *msg)

{

  if ( msg == NULL ) {

    char *txt = NULL;

    ExceptionReportRegister( TomoPyExceptionReport );

    if ( ExceptionReport( &txt ) ) {

      if ( txt == NULL ) {
        PyErr_SetString( mod->exception, "unidentified error" );
      } else {
        PyErr_SetString( mod->exception, txt );
        free( txt );
      }

    }

    ExceptionReportRegister( NULL );

  } else {

    PyErr_SetString( mod->exception, msg );

  }

}
