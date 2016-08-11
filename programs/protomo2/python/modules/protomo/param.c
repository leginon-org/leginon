/*----------------------------------------------------------------------------*
*
*  param.c  -  python tomography extension
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "protomo.h"
#include "exception.h"
#include "signals.h"
#include <stdio.h>


/* variables */

PyTypeObject *ProtomoParamTypeObject = NULL;


/* methods */

static void ProtomoParamReset
            (ProtomoParam *self)

{

  if ( self->param != NULL ) {
    TomoparamDestroy( self->param );
    self->param = NULL;
  }

}


static void ProtomoParamDealloc
            (ProtomoParam *self)

{

  ProtomoParamReset( self );

  self->ob_type->tp_free( self );

}


static PyObject *ProtomoParamNew
                 (PyTypeObject *type,
                  PyObject *args,
                  PyObject *kwds)

{
  char *path;
  const char *sect;
  Status status;

  if ( !PyArg_ParseTuple( args, "s", &path ) ) return NULL;

  ProtomoParam *obj = (ProtomoParam *)type->tp_alloc( type, 0 );
  if ( obj == NULL ) return NULL;

  TomoPyBegin( protomo );

  obj->param = TomoparamParse( path );
  if ( testcondition( obj->param == NULL ) ) goto error;

  status = TomoparamSet( obj->param, ProtomoSection, &sect );
  if ( pushexception( status ) ) goto error;
  if ( sect == NULL ) {
    pushexceptionmsg( E_TOMOPARAM_UNSEC, ", ", ProtomoSection ); goto error;
  }

  TomoPyEnd( protomo );

  return (PyObject *)obj;

  error: TomoPyEnd( protomo ); Py_DECREF( obj );

  return NULL;

}


static PyObject *ProtomoParamRead
                 (ProtomoParam *self,
                  PyObject *args)

{
  char *path;

  if ( !PyArg_ParseTuple( args, "s", &path ) ) return NULL;

  TomoPyBegin( protomo );

  Tomoparam *param = TomoparamParse( path );
  if ( testcondition( param == NULL ) ) goto error;

  ProtomoParamReset( self );

  self->param = param;

  TomoPyEnd( protomo );

  Py_INCREF( Py_None );
  return Py_None;

  error: TomoPyEnd( protomo );

  return NULL;

}


static PyObject *ProtomoParamList
                 (ProtomoParam *self,
                  PyObject *args)

{
  char *ident = NULL;

  if ( !PyArg_ParseTuple( args, "|s", &ident ) ) return NULL;

  TomoPyBegin( protomo );

  if ( TomoparamList( self->param, ident, ProtomoSection, stdout ) ) goto error;

  TomoPyEnd( protomo );

  Py_INCREF( Py_None );
  return Py_None;

  error: TomoPyEnd( protomo );

  return NULL;

}


static PyObject *ProtomoParamSet
                 (ProtomoParam *self,
                  PyObject *args)

{
  char *ident, *val;
  Status status;

  if ( !PyArg_ParseTuple( args, "ss", &ident, &val ) ) return NULL;

  TomoPyBegin( protomo );

  status = TomoparamWriteParam( self->param, ident, val );
  if ( pushexception( status ) ) goto error;

  TomoPyEnd( protomo );

  Py_INCREF( Py_None );
  return Py_None;

  error: TomoPyEnd( protomo );

  return NULL;

}


/* tables */

static struct PyMethodDef ProtomoParamMethods[] = {
  { "read", (PyCFunction)ProtomoParamRead, METH_VARARGS, "read parameters" },
  { "list", (PyCFunction)ProtomoParamList, METH_VARARGS, "list parameters" },
  { "set",  (PyCFunction)ProtomoParamSet,  METH_VARARGS, "set parameters"  },
  { NULL,   NULL,                          0,            NULL }
};

static PyTypeObject ProtomoParamType = {
  PyObject_HEAD_INIT( NULL )
  0,                              /* ob_size */
  NULL,                           /* tp_name */
  sizeof(ProtomoParam),           /* tp_basicsize */
  0,                              /* tp_itemsize */
  (destructor)ProtomoParamDealloc, /* tp_dealloc */
  0,                              /* tp_print */
  0,                              /* tp_getattr */
  0,                              /* tp_setattr */
  0,                              /* tp_compare */
  0,                              /* tp_repr */
  0,                              /* tp_as_number */
  0,                              /* tp_as_sequence */
  0,                              /* tp_as_mapping */
  0,                              /* tp_hash */
  0,                              /* tp_call */
  0,                              /* tp_str */
  0,                              /* tp_getattro */
  0,                              /* tp_setattro */
  0,                              /* tp_as_buffer */
  Py_TPFLAGS_DEFAULT,             /* tp_flags */
  NULL,                           /* tp_doc */
  0,		                  /* tp_traverse */
  0,		                  /* tp_clear */
  0,		                  /* tp_richcompare */
  0,		                  /* tp_weaklistoffset */
  0,		                  /* tp_iter */
  0,		                  /* tp_iternext */
  ProtomoParamMethods,            /* tp_methods */
  0,                              /* tp_members */
  0,                              /* tp_getset */
  0,                              /* tp_base */
  0,                              /* tp_dict */
  0,                              /* tp_descr_get */
  0,                              /* tp_descr_set */
  0,                              /* tp_dictoffset */
  0,                              /* tp_init */
  0,                              /* tp_alloc */
  ProtomoParamNew,                /* tp_new */
  0,                              /* tp_free */
  0,                              /* tp_is_gc */
  0,                              /* tp_bases */
  0,                              /* tp_mro */
  0,                              /* tp_cache */
  0,                              /* tp_subclasses */
  0,                              /* tp_weaklis */
  0,                              /* tp_del */
  0,                              /* tp_tp_version_tag */
#ifdef COUNT_ALLOCS
  0,                              /* tp_allocs */
  0,                              /* tp_frees */
  0,                              /* tp_maxalloc */
  0,                              /* tp_prev */
  0,                              /* tp_next */
#endif
};


/* initialization */

extern void ProtomoParamInit
            (TomoPy *mod)

{

  ProtomoParamTypeObject = TomoPyClassInit( mod, "param", &ProtomoParamType );

}
