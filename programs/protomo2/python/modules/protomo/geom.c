/*----------------------------------------------------------------------------*
*
*  geom.c  -  python tomography extension
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


/* variables */

PyTypeObject *ProtomoGeomTypeObject;


/* methods */

static void ProtomoGeomReset
            (ProtomoGeom *self)

{
  Status status;

  if ( self->tilt != NULL ) {
    status = TomotiltDestroy( self->tilt );
    logexception( status );
    self->tilt = NULL;
  }

}


static void ProtomoGeomDealloc
            (ProtomoGeom *self)

{

  ProtomoGeomReset( self );

  self->ob_type->tp_free( self );

}


static PyObject *ProtomoGeomNew
                 (PyTypeObject *type,
                  PyObject *args,
                  PyObject *kwds)

{
  char *path;

  if ( !PyArg_ParseTuple( args, "s", &path ) ) return NULL;

  ProtomoGeom *obj = (ProtomoGeom *)type->tp_alloc( type, 0 );
  if ( obj == NULL ) return NULL;

  TomoPyBegin( protomo );

  obj->tilt = TomotiltRead( path );
  if ( testcondition( obj->tilt == NULL ) ) goto error;

  TomoPyEnd( protomo );

  return (PyObject *)obj;

  error: TomoPyEnd( protomo ); Py_DECREF( obj );

  return NULL;

}


static PyObject *ProtomoGeomWrite
                 (ProtomoGeom *self,
                  PyObject *args)

{
  char *path;

  if ( !PyArg_ParseTuple( args, "s", &path ) ) return NULL;

  TomoPyBegin( protomo );

  FILE *handle = fopen( path, "w" );
  if ( handle == NULL ) {
    pushexceptionmsg( E_ERRNO, ", file ", path ); goto error;
  } else {
    TomotiltWrite( self->tilt, handle );
    if ( fclose( handle ) ) {
      pushexceptionmsg( E_ERRNO, ", file ", path ); goto error;
    }
  }

  TomoPyEnd( protomo );

  Py_INCREF( Py_None );
  return Py_None;

  error: TomoPyEnd( protomo );

  return NULL;

}


/* tables */

static struct PyMethodDef ProtomoGeomMethods[] = {
  { "write", (PyCFunction)ProtomoGeomWrite, METH_VARARGS, "write tilt geometry" },
  { NULL,    NULL,                          0,            NULL }
};

static PyTypeObject ProtomoGeomType = {
  PyObject_HEAD_INIT( NULL )
  0,                              /* ob_size */
  NULL,                           /* tp_name */
  sizeof(ProtomoGeom),            /* tp_basicsize */
  0,                              /* tp_itemsize */
  (destructor)ProtomoGeomDealloc, /* tp_dealloc */
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
  ProtomoGeomMethods,             /* tp_methods */
  0,                              /* tp_members */
  0,                              /* tp_getset */
  0,                              /* tp_base */
  0,                              /* tp_dict */
  0,                              /* tp_descr_get */
  0,                              /* tp_descr_set */
  0,                              /* tp_dictoffset */
  0,                              /* tp_init */
  0,                              /* tp_alloc */
  ProtomoGeomNew,                 /* tp_new */
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

extern void ProtomoGeomInit
            (TomoPy *mod)

{

  ProtomoGeomTypeObject = TomoPyClassInit( mod, "geom", &ProtomoGeomType );

}
