/*----------------------------------------------------------------------------*
*
*  tomopyeman.cpp  -  eman wrapper library
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
#include "tomopyimage.h"

#include "emobject.h"
#include "emdata.h"

#include <boost/python.hpp>
#include <boost/python/to_python_converter.hpp>
#include <vector>

using namespace EMAN;


/* functions */

extern PyObject *TomoPyEmanGet
                 (PyObject *self)

{
  int len[3], low[3];

  if ( TomoPyEmanCheck( self ) ) return NULL;

  EMData *img = boost::python::extract<EMData*>(self);
  len[0] = img->get_xsize();
  len[1] = img->get_ysize();
  len[2] = img->get_zsize();

  int dim = ( len[2] > 1 ) ? 3 : 2;

  vector<int> offsets = img->get_array_offsets();
  low[0] = offsets[0];
  low[1] = offsets[1];
  low[2] = offsets[2];

  int type = img->is_complex() ? TomoPyCmplx32 : TomoPyReal32;

  int attr = img->is_complex() ? TomoPyFourier : TomoPyRealspace;

  const float *buf = img->get_data();

  PyObject *obj = TomoPyImageCreate();
  if ( obj == NULL ) return NULL;

  if ( TomoPyToImage( dim, len, low, type, attr, buf, obj ) ) goto error;

  return obj;

  error: Py_DECREF( obj );

  return NULL;

}


extern int TomoPyEmanSet
           (PyObject *emobj,
            PyObject *imgobj)

{
  int dim, type, attr;
  int len[3] = { 1, 1, 1 };
  int low[3] = { 0, 0, 0 };
  void *addr;

  int status = TomoPyFromImage( &dim, len, low, &type, &attr, &addr, imgobj );
  if ( status ) return status;

  EMData *img = boost::python::extract<EMData*>(emobj);

  img->set_complex( type == TomoPyCmplx32 );
  img->set_data( (float *)addr, len[0], len[1], len[2] );
  img->set_array_offsets( low[0], low[1], low[2] );
  img->update();

  return 0;

}
