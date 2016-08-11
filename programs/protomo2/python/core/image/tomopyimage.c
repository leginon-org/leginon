/*----------------------------------------------------------------------------*
*
*  tomopyimage.c  -  tomopy: image handling
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomopyimagecommon.h"
#include "tomopygtk.h"
#include "tomopyeman.h"
#include "array.h"
#include "imagefourier.h"
#include "imageio.h"
#include "imagestat.h"
#include "exception.h"


/* types */

#define TomoPyImageMaxDim 4

typedef struct {
  PyObject_HEAD
  Image dscr;
  Size len[TomoPyImageMaxDim];
  Index low[TomoPyImageMaxDim];
  void *addr;
} TomoPyImage;


/* variables */

static TomoPy *TomoPyImageMod = NULL;

PyTypeObject *TomoPyImageTypeObject = NULL;


/* functions */

extern PyObject *TomoPyImageCreate()

{

  PyObject *obj = TomoPyImageTypeObject->tp_alloc( TomoPyImageTypeObject, 0 );
  if ( obj == NULL ) return NULL;

  TomoPyImage *img = (TomoPyImage *)obj;
  img->dscr = ImageInitializer;
  img->dscr.len = img->len;
  img->dscr.low = img->low;
  img->addr = NULL;

  return obj;

}


static Status TomoPyImageObjectAlloc
              (PyObject *image,
               const void *buf)

{
  TomoPyImage *img = (TomoPyImage *)image;
  Size size;
  Status status;

  status = ArraySize( img->dscr.dim, img->dscr.len, TypeGetSize( img->dscr.type ), &size );
  if ( pushexception( status ) ) return status;
  size *= TypeGetSize( img->dscr.type );

  void *addr = malloc( size );
  if ( addr == NULL ) return pushexception( E_MALLOC );

  if ( img->addr != NULL ) free( img->addr );
  img->addr = addr;

  if ( buf != NULL ) {
    memcpy( addr, buf, size );
  }

  return E_NONE;

}


extern void TomoPyImageSet
            (const void *src,
             void *buf,
             PyObject *image)

{
  const Image *dscr = src;
  TomoPyImage *img = (TomoPyImage *)image;

  img->dscr.dim = dscr->dim;
  img->dscr.type = dscr->type;
  img->dscr.attr = dscr->attr;

  for ( Size d = 0; d < dscr->dim; d++ ) {
    img->len[d] = dscr->len[d];
    img->low[d] = ( dscr->low == NULL ) ? -(Index)( dscr->len[d] / 2 ) : dscr->low[d];
  }

  if ( img->addr != NULL ) free( img->addr );
  img->addr = buf;

}


extern int TomoPyToImage
           (const int dim,
            const int *len,
            const int *low,
            const int type,
            const int attr,
            const void *buf,
            PyObject *image)

{
  TomoPyImage *img = (TomoPyImage *)image;
  Size dstsize, dstlen[TomoPyImageMaxDim];
  Status status;

  if ( dim > TomoPyImageMaxDim ) {
    pushexception( E_IMAGE_DIM ); return TomoPyError;
  }

  for ( int d = 0; d < dim; d++ ) {
    if ( len[d] < 1 ) { pushexception( E_IMAGE_SIZE ); return TomoPyError; }
    if ( len[d] - IndexMax > 0 ) { pushexception( E_INTOVFL ); return TomoPyError; }
    if ( low[d] < 0 ) {
      if ( IndexMin - low[d] > 0 ) { pushexception( E_INTOVFL ); return TomoPyError; }
    } else {
      if ( low[d] - IndexMax > 0 ) { pushexception( E_INTOVFL ); return TomoPyError; }
    }
    dstlen[d] = len[d];
  }

  Type dsttype;
  switch ( type ) {
    case TomoPyUint8:   dsttype = TypeUint8;   break;
    case TomoPyUint16:  dsttype = TypeUint16;  break;
    case TomoPyUint32:  dsttype = TypeUint32;  break;
    case TomoPyInt8:    dsttype = TypeInt8;    break;
    case TomoPyInt16:   dsttype = TypeInt16;   break;
    case TomoPyInt32:   dsttype = TypeInt32;   break;
    case TomoPyReal32:  dsttype = TypeReal32;  break;
    case TomoPyCmplx32: dsttype = TypeCmplx32; break;
    default: pushexception( E_IMAGE_TYPE ); return TomoPyError;
  }

  ImageAttr dstattr;
  switch ( attr ) {
    case TomoPyRealspace: dstattr = ImageRealspc; break;
    case TomoPyFourier:   dstattr = ImageFourspc | ImageSymHerm; break;
    default: pushexception( E_IMAGE_ATTR ); return TomoPyError;
  }

  status = ImageAttrCopy( dsttype, dstattr, &dsttype, &dstattr, 0 );
  if ( pushexception( status ) ) return TomoPyError;

  Size dstelsize = TypeGetSize( dsttype );
  status = ArraySize( dim, dstlen, dstelsize, &dstsize );
  if ( pushexception( status ) ) return TomoPyError;

  void *addr = malloc( dstsize * dstelsize );
  if ( addr == NULL ){
    pushexception( E_MALLOC ); return TomoPyError;
  }
  memcpy( addr, buf, dstsize * dstelsize );

  if ( img->addr != NULL ) free( img->addr );
  img->addr = addr;

  img->dscr.dim = dim;
  img->dscr.type = dsttype;
  img->dscr.attr = dstattr;

  for ( int d = 0; d < dim; d++ ) {
    img->len[d] = dstlen[d];
    img->low[d] = low[d];
  }

  return TomoPySuccess;

}


extern int TomoPyFromImage
           (int *dim,
            int *len,
            int *low,
            int *type,
            int *attr,
            void **buf,
            const PyObject *image)

{
  const TomoPyImage *img = (TomoPyImage *)image;

  if ( img->dscr.dim > TomoPyImageMaxDim ) {
    pushexception( E_IMAGE_DIM ); return TomoPyError;
  }

  for ( Size d = 0; d < img->dscr.dim; d++ ) {
    if ( ( img->dscr.len[d] > INT_MAX ) || ( img->dscr.low[d] > INT_MAX ) || ( img->dscr.low[d] < INT_MIN ) ) {
      pushexception( E_INTOVFL ); return TomoPyError;
    }
  }

  int dsttype;
  switch ( img->dscr.type ) {
    case TypeReal32:  dsttype = TomoPyReal32;  break;
    case TypeCmplx32: dsttype = TomoPyCmplx32; break;
    default:          dsttype = TomoPyUndef;
  }

  int dstattr;
  if ( dsttype == TomoPyCmplx32 ) {
    if ( ( img->dscr.attr & ( ImageFourspc | ImageSymMask ) ) != ( ImageFourspc | ImageSymMask ) ) {
      pushexception( E_IMAGE_TYPE ); return TomoPyError;
    }
    dstattr = TomoPyFourier;
  } else if ( dsttype != TomoPyUndef ){
    if ( img->dscr.attr != ImageRealspc ) {
      pushexception( E_IMAGE_TYPE ); return TomoPyError;
    }
    dstattr = TomoPyRealspace;
  } else {
    userexception( "unsupported image data type" ); return TomoPyError;
  }

  *dim = img->dscr.dim;
  *type = dsttype;
  *attr = dstattr;
  *buf = img->addr;

  for ( Size d = 0; d < img->dscr.dim; d++ ) {
    len[d] = img->len[d];
    low[d] = img->low[d];
  }

  return TomoPySuccess;

}


static void TomoPyImageDealloc
            (PyObject *self)

{
  TomoPyImage *img = (TomoPyImage *)self;

  if ( img->addr != NULL ) free( img->addr );

  self->ob_type->tp_free( self );

}


static PyObject *TomoPyImageNew
                 (PyTypeObject *type,
                  PyObject *args,
                  PyObject *kwds)

{
  PyObject *arg = NULL;
  PyObject *obj;

  if ( !PyArg_ParseTuple( args, "O", &arg ) ) return NULL;

  if ( PyString_CheckExact( arg ) ) {

    obj = TomoPyImageCreate();
    if ( obj == NULL ) return NULL;

    TomoPyBegin( TomoPyImageMod );

    Image dst;
    const char *path = PyString_AsString( arg );
    void *addr = ImageioIn( path, &dst, NULL );
    if ( testcondition( addr == NULL ) ) goto error2;
    if ( dst.dim > TomoPyImageMaxDim ) {
      free( addr ); pushexception( E_IMAGE_DIM ); goto error2;
    }

    TomoPyImage *img = (TomoPyImage *)obj;

    img->dscr.dim = dst.dim;
    img->dscr.type = dst.type;
    img->dscr.attr = dst.attr;

    for ( Size d = 0; d < dst.dim; d++ ) {
      img->len[d] = dst.len[d];
      img->low[d] = dst.low[d];
    }

    if ( img->addr != NULL ) free( img->addr );
    img->addr = addr;

  } else {

    TomoPyBegin( TomoPyImageMod );

    TomoPyEmanFn *fn = TomoPyImageEmanFn;
    if ( ( fn == NULL ) || ( fn->get == NULL ) ) { pushexception( E_TOMOPYIMAGE_EMAN ); goto error1; }
    obj = fn->get( arg );
    if ( obj == NULL ) goto error1;

  }

  TomoPyEnd( TomoPyImageMod );

  return obj;

  error2: Py_DECREF( obj );
  error1: TomoPyEnd( TomoPyImageMod );

  return NULL;

}


static PyObject *TomoPyImageWrite
                 (PyObject *self,
                  PyObject *args)

{
  TomoPyImage *img = (TomoPyImage *)self;
  char *path, *fmt = NULL;
  Status status;

  if ( !PyArg_ParseTuple( args, "s|s", &path, &fmt ) ) return NULL;

  TomoPyBegin( TomoPyImageMod );

  if ( img->addr == NULL ) {
    pushexception( E_IMAGE_ZERO ); goto error;
  }

  ImageioParam iopar = ImageioParamInitializer;
  iopar.format = fmt;
  iopar.cap = ImageioCapRdWr;
  status = ImageioOut( path, &img->dscr, img->addr, &iopar );
  if ( exception( status ) ) goto error;

  TomoPyEnd( TomoPyImageMod );

  Py_INCREF( Py_None );
  return Py_None;

  error: TomoPyEnd( TomoPyImageMod );

  return NULL;

}


static PyObject *TomoPyImageStat
                 (PyObject *self,
                  PyObject *args)

{
  TomoPyImage *img = (TomoPyImage *)self;
  Status status;

  if ( !PyArg_ParseTuple( args, "" ) ) return NULL;

  TomoPyBegin( TomoPyImageMod );

  status = ImageStatPrint( NULL, &img->dscr, img->addr, NULL );
  if ( pushexception( status ) ) goto error;

  TomoPyEnd( TomoPyImageMod );

  Py_INCREF( Py_None );
  return Py_None;

  error: TomoPyEnd( TomoPyImageMod );

  return NULL;

}


static PyObject *TomoPyImageFourier
                 (PyObject *self,
                  PyObject *args)

{
  TomoPyImage *img = (TomoPyImage *)self;
  Status status;

  if ( !PyArg_ParseTuple( args, "" ) ) return NULL;

  TomoPyImage *obj = (TomoPyImage *)TomoPyImageCreate();
  if ( obj == NULL ) return NULL;

  TomoPyBegin( TomoPyImageMod );

  if ( img->dscr.dim > TomoPyImageMaxDim ) {
    pushexception( E_IMAGE_DIM ); goto error;
  }

  status = ImageMetaCopy( &img->dscr, &obj->dscr, ImageModeFou );
  if ( pushexception( status ) ) goto error;

  if ( TomoPyImageObjectAlloc( (PyObject *)obj, NULL ) ) goto error;

  status = ImageFourierTransform( &img->dscr, img->addr, NULL, obj->addr, 1, NULL );
  if ( exception( status ) ) goto error;

  TomoPyEnd( TomoPyImageMod );

  return (PyObject *)obj;

  error: TomoPyEnd( TomoPyImageMod ); Py_DECREF( obj );

  return NULL;

}


static PyObject *TomoPyImageDisplay
                 (PyObject *self,
                  PyObject *args)

{
  TomoPyImage *img = (TomoPyImage *)self;

  if ( !PyArg_ParseTuple( args, "" ) ) return NULL;

  TomoPyBegin( TomoPyImageMod );

  TomoPyGtkFn *fn = TomoPyImageGtkFn;
  if ( ( fn == NULL ) || ( fn->display == NULL ) ) {
    pushexception( E_TOMOPYIMAGE_GTK ); goto error;
  }

  if ( fn->display( &img->dscr, img->addr ) ) goto error;

  TomoPyEnd( TomoPyImageMod );

  Py_INCREF( Py_None );
  return Py_None;

  error: TomoPyEnd( TomoPyImageMod );

  return NULL;

}


static PyObject *TomoPyImageEmdata
                 (PyObject *self,
                  PyObject *args)

{

  if ( !PyArg_ParseTuple( args, "" ) ) return NULL;

  TomoPyBegin( TomoPyImageMod );

  TomoPyEmanFn *fn = TomoPyImageEmanFn;
  if ( ( fn == NULL ) || ( fn->create == NULL ) || ( fn->set == NULL ) ) {
    pushexception( E_TOMOPYIMAGE_EMAN ); goto error1;
  }

  PyObject *obj = fn->create();
  if ( obj == NULL ) goto error1;

  if ( fn->set( obj, self ) ) goto error2;

  TomoPyEnd( TomoPyImageMod );

  return obj;

  error2: Py_DECREF( obj );
  error1: TomoPyEnd( TomoPyImageMod );

  return NULL;

}


/* tables */

static struct PyMethodDef TomoPyImageMethods[] = {
  { "write",   (PyCFunction)TomoPyImageWrite,   METH_VARARGS, "write i3 image"      },
  { "stat",    (PyCFunction)TomoPyImageStat,    METH_VARARGS, "i3 image statistics" },
  { "fft",     (PyCFunction)TomoPyImageFourier, METH_VARARGS, "transform i3 image"  },
  { "display", (PyCFunction)TomoPyImageDisplay, METH_VARARGS, "display i3 image"    },
  { "emdata",  (PyCFunction)TomoPyImageEmdata,  METH_VARARGS, "create EMdata image" },
  { NULL,      NULL,                            0,            NULL }
};

static PyTypeObject TomoPyImageType = {
  PyObject_HEAD_INIT( NULL )
  0,                              /* ob_size */
  NULL,                           /* tp_name */
  sizeof(TomoPyImage),            /* tp_basicsize */
  0,                              /* tp_itemsize */
  (destructor)TomoPyImageDealloc, /* tp_dealloc */
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
  TomoPyImageMethods,             /* tp_methods */
  0,                              /* tp_members */
  0,                              /* tp_getset */
  0,                              /* tp_base */
  0,                              /* tp_dict */
  0,                              /* tp_descr_get */
  0,                              /* tp_descr_set */
  0,                              /* tp_dictoffset */
  0,                              /* tp_init */
  0,                              /* tp_alloc */
  TomoPyImageNew,                 /* tp_new */
  0,                              /* tp_free */
  0,                              /* tp_is_gc */
  0,                              /* tp_bases */
  0,                              /* tp_mro */
  0,                              /* tp_cache */
  0,                              /* tp_subclasses */
  0,                              /* tp_weaklist */
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


extern void TomoPyImageInit
            (TomoPy *mod)

{

  TomoPyImageTypeObject = TomoPyClassInit( mod, "image", &TomoPyImageType );

  TomoPyImageMod = mod;

}
