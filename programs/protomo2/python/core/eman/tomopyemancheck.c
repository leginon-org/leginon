/*----------------------------------------------------------------------------*
*
*  tomopyemancheck.c  -  eman wrapper library
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomopyeman.h"
#include "tomopy.h"
#include "exception.h"


/* variables */

static PyTypeObject *TomoPyEmdataType = NULL;


/* functions */

static Status TomoPyEmanInit()

{

  if ( TomoPyEmdataType == NULL ) {

    PyObject *modu = PyImport_AddModule( "EMAN2" );
    PyObject *dict = PyModule_GetDict( modu );
    TomoPyEmdataType = (PyTypeObject *)PyDict_GetItemString( dict, "EMData" );
    if ( TomoPyEmdataType == NULL ) return pushexception( E_TOMOPYEMAN_INIT );

  }

  return E_NONE;

}


extern PyObject *TomoPyEmanNew()

{

  if ( TomoPyEmanInit() ) return NULL;

  /* PyObject *obj = PyType_GenericNew( TomoPyEmdataType, NULL, NULL ); */
  /* PyObject *obj = TomoPyEmdataType->tp_new( TomoPyEmdataType, NULL, NULL ); */
  PyObject *glo = PyEval_GetGlobals();
  PyObject *loc = PyEval_GetLocals();
  PyObject *obj = PyRun_String( "EMData()", Py_eval_input, glo, loc );
  if ( obj == NULL ) pushexception( E_TOMOPYEMAN );

  Py_INCREF( obj );

  return obj;

}


extern int TomoPyEmanCheck
           (PyObject *self)

{

  if ( self == NULL ) return pushexception( E_ARGVAL );

  if ( TomoPyEmanInit() ) return pushexception( E_TOMOPYEMAN );

  if ( !PyObject_TypeCheck( self, TomoPyEmdataType ) ) return pushexception( E_TOMOPYEMAN_EMDATA );

  return E_NONE;

}
