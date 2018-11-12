/*----------------------------------------------------------------------------*
*
*  series.c  -  python tomography extension
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
#include "tomopyimage.h"
#include "tomoalign.h"
#include "tomoparamread.h"
#include "tomoseriesmap.h"
#include "tomotiltfit.h"
#include "tomowindow.h"
#include "tomopatch.h"
#include "exception.h"
#include "message.h"
#include "signals.h"
#include "strings.h"
#include <stdio.h>
#include <unistd.h>


/* variables */

PyTypeObject *ProtomoSeriesTypeObject = NULL;


/* methods */

static void ProtomoSeriesAlignReset
            (ProtomoSeries *self)

{
  Status status;

  if ( self->alignd != NULL ) {
    status = TomotiltDestroy( self->alignd );
    logexception( status );
    self->alignd = NULL;
  }

  if ( self->fitted != NULL ) {
    status = TomotiltDestroy( self->fitted );
    logexception( status );
    self->fitted = NULL;
  }

  if ( self->geom != NULL ) {
    free( self->geom );
    self->geom = NULL;
  }

  self->unaligned = True;

}


static void ProtomoSeriesReset
            (ProtomoSeries *self)

{
  Status status = E_NONE;

  ProtomoSeriesAlignReset( self );

  if ( self->series != NULL ) {
    status = TomoseriesClose( self->series );
    logexception( status );
    self->series = NULL;
  }

  if ( self->param != NULL ) {
    TomoparamDestroy( self->param );
    self->param = NULL;
  }

}


static void ProtomoSeriesDealloc
            (ProtomoSeries *self)

{

  TomoPyBegin( protomo );

  ProtomoSeriesReset( self );

  TomoPyEnd( protomo );

  self->ob_type->tp_free( self );

}


static PyObject *ProtomoSeriesNew
                 (PyTypeObject *type,
                  PyObject *args,
                  PyObject *kwds)

{
  ProtomoParam *param;
  PyObject *arg2 = NULL;
  char *arg3 = NULL;
  char *prfx = NULL;
  ProtomoGeom *geom = NULL;
  Status status;

  if ( !PyArg_ParseTuple( args, "O!|Os", ProtomoParamTypeObject, &param, &arg2, &arg3 ) ) return NULL;

  if ( arg2 != NULL ) {
    if ( PyString_CheckExact( arg2 ) ) {
      prfx = PyString_AsString( arg2 );
      if ( prfx == NULL ) return NULL;
    } else if ( PyObject_TypeCheck( arg2, ProtomoGeomTypeObject ) ) {
      geom = (ProtomoGeom *)arg2;
      prfx = arg3; arg3 = NULL;
    } else {
      PyErr_SetString( PyExc_TypeError, "argument 2 has invalid type" ); return NULL;
    }
  }
  if ( arg3 != NULL ) {
    PyErr_SetString( PyExc_TypeError, "too many arguments" ); return NULL;
  }

  ProtomoSeries *obj = (ProtomoSeries *)type->tp_alloc( type, 0 );
  if ( obj == NULL ) return NULL;

  obj->series = NULL;
  obj->alignd = NULL;
  obj->fitted = NULL;
  obj->param = NULL;
  obj->unaligned = True;

  TomoPyBegin( protomo );

  Tomoparam *tomoparam = TomoparamDup( param->param );
  if ( testcondition( tomoparam == NULL ) ) goto error1;

  TomoseriesParam seriesparam;
  status = TomoseriesGetParam( tomoparam, NULL, &seriesparam );
  if ( exception( status ) ) goto error2;

  if ( prfx != NULL ) {
    prfx = strdup( prfx );
    if ( prfx == NULL ) {
      pushexception( E_MALLOC ); goto error2;
    }
    if ( seriesparam.prfx != NULL ) free( (char *)seriesparam.prfx );
    seriesparam.prfx = prfx;
  }

  seriesparam.flags |= TomoCycle;
  if ( geom == NULL ) {
    obj->series = TomoseriesOpen( NULL, &seriesparam );
    if ( testcondition( obj->series == NULL ) ) goto error3;
  } else {
    obj->series = TomoseriesCreate( geom->tilt, NULL, &seriesparam );
    if ( testcondition( obj->series == NULL ) ) goto error3;
  }

  TomoseriesParamFinal( &seriesparam );

  TomoPyEnd( protomo );

  obj->param = tomoparam;

  return (PyObject *)obj;

  error3: TomoseriesParamFinal( &seriesparam );
  error2: TomoparamDestroy( tomoparam );
  error1: TomoPyEnd( protomo ); Py_DECREF( obj );

  return NULL;

}


static PyObject *ProtomoSeriesParam
                 (ProtomoSeries *self,
                  PyObject *args)

{
  ProtomoParam *param;

  if ( !PyArg_ParseTuple( args, "O!", ProtomoParamTypeObject, &param ) ) return NULL;

  TomoPyBegin( protomo );

  Tomoparam *tomoparam = TomoparamDup( param->param );
  if ( testcondition( tomoparam == NULL ) ) goto error;

  if ( self->param != NULL ) {
    TomoparamDestroy( self->param );
  }
  self->param = tomoparam;

  TomoPyEnd( protomo );

  Py_INCREF( Py_None );
  return Py_None;

  error: TomoPyEnd( protomo );

  return NULL;

}


static PyObject *ProtomoSeriesSetpar
                 (ProtomoSeries *self,
                  PyObject *args)

{
  char *ident, *val = NULL;
  Status status;

  if ( !PyArg_ParseTuple( args, "s|s", &ident, &val ) ) return NULL;

  TomoPyBegin( protomo );

  if ( val == NULL ) {

    if ( TomoparamList( self->param, ident, ProtomoSection, stdout ) ) goto error;

  } else {

    status = TomoparamWriteParam( self->param, ident, val );
    if ( pushexception( status ) ) goto error;

  }

  TomoPyEnd( protomo );

  Py_INCREF( Py_None );
  return Py_None;

  error: TomoPyEnd( protomo );

  return NULL;

}


static PyObject *ProtomoSeriesSetori
                 (ProtomoSeries *self,
                  PyObject *args)

{
  double x = CoordMax, y = CoordMax, z = 0;
  Status status;

  if ( !PyArg_ParseTuple( args, "|ddd", &x, &y, &z ) ) return NULL;

  TomoPyBegin( protomo );

  if ( x == CoordMax ) {

    Coord *ori = self->series->tilt->param.origin;
    MessageFormat( "ORIGIN [ %.3"CoordF" %.3"CoordF" %.3"CoordF" ]\n", ori[0], ori[1], ori[2] );

  } else if ( y == CoordMax ) {

    userexception( "missing y coordinate" ); goto error;

  } else {

    if ( !self->unaligned || ( self->alignd != NULL ) || ( self->fitted != NULL ) || ( self->geom != NULL ) ) {
      userexception( "cannot set origin for already aligned tilt series" ); goto error;
    }

    Coord ori[3] = { x, y, z };
    status = TomoseriesSetOrigin( self->series, ori );
    if ( exception( status ) ) goto error;

  }

  TomoPyEnd( protomo );

  Py_INCREF( Py_None );
  return Py_None;

  error: TomoPyEnd( protomo );

  return NULL;

}


static PyObject *ProtomoSeriesSeteul
                 (ProtomoSeries *self,
                  PyObject *args)

{
  double e0 = CoordMax, e1 = CoordMax, e2 = CoordMax;
  Status status;

  if ( !PyArg_ParseTuple( args, "|ddd", &e0, &e1, &e2 ) ) return NULL;

  TomoPyBegin( protomo );

  if ( e0 == CoordMax ) {

    Coord *euler = self->series->tilt->param.euler;
    MessageFormat( "PSI  %.3"CoordF"  THETA %.3"CoordF"  PHI %.3"CoordF"\n", euler[0], euler[1], euler[2] );

  } else if ( ( e1 == CoordMax ) || ( e2 == CoordMax ) ) {

    userexception( "missing Euler angle(s)" ); goto error;

  } else {

    if ( !self->unaligned || ( self->alignd != NULL ) || ( self->fitted != NULL ) || ( self->geom != NULL ) ) {
      userexception( "cannot set Euler angles for already aligned tilt series" ); goto error;
    }

    Coord euler[3] = { e0, e1, e2 };
    status = TomoseriesSetEuler( self->series, euler );
    if ( exception( status ) ) goto error;

  }

  TomoPyEnd( protomo );

  Py_INCREF( Py_None );
  return Py_None;

  error: TomoPyEnd( protomo );

  return NULL;

}


static PyObject *ProtomoSeriesSetcyc
                 (ProtomoSeries *self,
                  PyObject *args)

{
  unsigned int cyc = UINT_MAX;
  int cycle;
  Status status;

  if ( !PyArg_ParseTuple( args, "|I", &cyc ) ) return NULL;

  TomoPyBegin( protomo );

  if ( cyc <= INT_MAX ) {

    cycle = TomometaGetCycle( self->series->meta );
    if ( cycle > (int)cyc ) {
      status = TomometaSetCycle(self->series->meta, (int)cyc );
      if ( exception( status ) ) goto error;
      cycle = TomometaGetCycle( self->series->meta );
      if ( cycle != (int)cyc ) {
        pushexception( E_PROTOMO ); goto error;
      }
      ProtomoSeriesAlignReset( self );
    }

  }

  cycle = TomometaGetCycle( self->series->meta );
  MessageFormat( "cycle %02d\n", cycle );

  TomoPyEnd( protomo );

  Py_INCREF( Py_None );
  return Py_None;

  error: TomoPyEnd( protomo );

  return NULL;

}


static PyObject *ProtomoSeriesPreproc
                 (ProtomoSeries *self,
                  PyObject *args)

{
  unsigned int number;
  Status status;

  if ( !PyArg_ParseTuple( args, "I", &number ) ) return NULL;

  uint32_t index = TomotiltGetIndex( self->series->tilt, number );
  if ( index >= self->series->tilt->images ) {
    PyErr_SetString( PyExc_TypeError, "invalid image number" ); return NULL;
  }

  PyObject *obj = TomoPyImageCreate();
  if ( obj == NULL ) return NULL;

  TomoPyBegin( protomo );

  TomoseriesParam seriesparam;
  status = TomoseriesGetParam( self->param, NULL, &seriesparam );
  if ( exception( status ) ) goto error1;

  status = TomoseriesSampling( self->series, &seriesparam );
  if ( exception( status ) ) goto error2;

  Image dscr; void *addr;
  status = TomoseriesPreproc( self->series, index, &dscr, &addr );
  if ( exception( status ) ) goto error2;

  TomoPyImageSet( &dscr, &addr, obj );

  free( dscr.len ); free( dscr.low );

  TomoseriesParamFinal( &seriesparam );

  TomoPyEnd( protomo );

  return obj;

  error2: TomoseriesParamFinal( &seriesparam );
  error1: TomoPyEnd( protomo ); Py_DECREF( obj );

  return NULL;

}


static PyObject *ProtomoSeriesImageTransf
                 (ProtomoSeries *self,
                  PyObject *args,
                  Bool transform,
                  Bool filter)

{
  unsigned int number;
  Image dst;
  void *addr, *addrfourier;
  Status status;

  if ( !PyArg_ParseTuple( args, "I", &number ) ) return NULL;

  uint32_t index = TomotiltGetIndex( self->series->tilt, number );
  if ( index >= self->series->tilt->images ) {
    PyErr_SetString( PyExc_TypeError, "invalid image number" ); return NULL;
  }

  PyObject *obj = TomoPyImageCreate();
  if ( obj == NULL ) return NULL;

  TomoPyBegin( protomo );

  TomoseriesParam seriesparam;
  status = TomoseriesGetParam( self->param, NULL, &seriesparam );
  if ( exception( status ) ) goto error1;

  TomoalignParam alignparam;
  status = TomoalignGetParam( self->param, "align", &alignparam );
  if ( exception( status ) ) goto error2;

  TomowindowParam windowparam;
  status = TomowindowGetParam( self->param, "window", &windowparam );
  if ( exception( status ) ) goto error3;

  status = TomoseriesSampling( self->series, &seriesparam );
  if ( exception( status ) ) goto error4;

  WindowParam param = WindowParamInitializer;
  param.area = windowparam.area;

  Window window;
  status = WindowInit( 2, windowparam.len, &window, &param );
  if ( pushexception( status ) ) goto error4;

  status = TomoseriesWindowImage( self->series, &window, index, &dst, &addr, False );
  if ( exception( status ) ) goto error4;

  WindowFourier windowfourier;

  if ( !transform ) {

    TomoPyImageSet( &dst, addr, obj );

  } else {

    WindowFourierParam fourierparam = WindowFourierParamInitializer;
    fourierparam.opt = FourierZeromean;

    status = WindowFourierInit( 2, window.len, windowparam.msk, windowparam.flt, NULL, &windowfourier, &fourierparam );
    if ( pushexception( status ) ) goto error5;

    addrfourier = WindowFourierAlloc( &windowfourier );
    if ( addrfourier == NULL ) { pushexception( E_MALLOC ); goto error6; }

    status = WindowTransform( &windowfourier, addr, addrfourier, NULL, windowfourier.flt );
    if ( pushexception( status ) ) goto error7;

    if ( filter ) {

      status = FourierInvRealTransf( windowfourier.back, addrfourier, addr, 1 );
      if ( pushexception( status ) ) goto error7;

      TomoPyImageSet( &dst, addr, obj );

      free( addrfourier );

    } else {

      TomoPyImageSet( &windowfourier.fou, addrfourier, obj );

      free( addr );

    }

    windowfourier.fou = dst;
    status = WindowFourierFinal( &windowfourier );
    logexception( status );

  }

  TomowindowParamFinal( &windowparam );
  TomoalignParamFinal( &alignparam );
  TomoseriesParamFinal( &seriesparam );

  TomoPyEnd( protomo );

  return obj;

  error7: free( addrfourier );
  error6: WindowFourierFinal( &windowfourier );
  error5: free( dst.len ); free( dst.low ); free( addr );
  error4: TomowindowParamFinal( &windowparam );
  error3: TomoalignParamFinal( &alignparam );
  error2: TomoseriesParamFinal( &seriesparam );
  error1: TomoPyEnd( protomo ); Py_DECREF( obj );

  return NULL;

}


static PyObject *ProtomoSeriesImage
                 (ProtomoSeries *self,
                  PyObject *args)

{

  return ProtomoSeriesImageTransf( self, args, False, False );

}


static PyObject *ProtomoSeriesTransf
                 (ProtomoSeries *self,
                  PyObject *args)

{

  return ProtomoSeriesImageTransf( self, args, True, False );

}


static PyObject *ProtomoSeriesFilter
                 (ProtomoSeries *self,
                  PyObject *args)

{

  return ProtomoSeriesImageTransf( self, args, True, True );

}


static PyObject *ProtomoSeriesWindow
                 (ProtomoSeries *self,
                  PyObject *args)

{
  Status status;

  if ( !PyArg_ParseTuple( args, "" ) ) return NULL;

  PyObject *obj = TomoPyImageCreate();
  if ( obj == NULL ) return NULL;

  TomoPyBegin( protomo );

  TomoseriesParam seriesparam;
  status = TomoseriesGetParam( self->param, NULL, &seriesparam );
  if ( exception( status ) ) goto error1;

  WindowParam windowparam; Size dim = 2; Size len[2];
  status = TomoparamWindow( self->param, "window", &dim, len, &windowparam );
  if ( exception( status ) ) goto error2;

  Window window;
  status = WindowInit( dim, len, &window, &windowparam );
  if ( pushexception( status ) ) goto error2;

  status = TomoseriesSampling( self->series, &seriesparam );
  if ( exception( status ) ) goto error2;

  Image dscr; Real *addr;
  status = TomoseriesWindow( self->series, &window, &dscr, &addr, False );
  if ( exception( status ) ) goto error2;

  TomoPyImageSet( &dscr, addr, obj );

  TomoseriesParamFinal( &seriesparam );

  TomoPyEnd( protomo );

  return obj;

  error2: TomoseriesParamFinal( &seriesparam );
  error1: TomoPyEnd( protomo ); Py_DECREF( obj );

  return NULL;

}


static PyObject *ProtomoSeriesArea
                 (ProtomoSeries *self,
                  PyObject *args)

{
  Status status;

  if ( !PyArg_ParseTuple( args, "" ) ) return NULL;

  PyObject *obj = TomoPyImageCreate();
  if ( obj == NULL ) return NULL;

  TomoPyBegin( protomo );

  TomoseriesParam seriesparam;
  status = TomoseriesGetParam( self->param, NULL, &seriesparam );
  if ( exception( status ) ) goto error1;

  status = TomoseriesSampling( self->series, &seriesparam );
  if ( exception( status ) ) goto error2;

  Image dscr; uint16_t *addr;
  Size len[2]; Index low[2];
  status = TomoseriesVolume( self->series, 0, &dscr, &addr, len, low );
  if ( exception( status ) ) goto error2;

  Index hx = low[0] + len[0] - 1;
  Index hy = low[1] + len[1] - 1;
  Index ox = len[0] / 2; ox += low[0];
  Index oy = len[1] / 2; oy += low[1];
  Coord sampling = self->series->sampling;
  Coord *origin = self->series->tilt->param.origin;
  Coord orix = origin[0] + ox * sampling;
  Coord oriy = origin[1] + oy * sampling;
  Coord oriz = origin[2];

  if ( self->series->flags & TomoLog ) {
    MessageFormat( "size %"SizeU" x %"SizeU"  [%"IndexD"..%"IndexD"][%"IndexD"..%"IndexD"]  ORIGIN [ %.3"CoordF" %.3"CoordF" %.3"CoordF" ]\n", len[0], len[1], low[0], hx, low[1], hy, orix, oriy, oriz );
  }

  TomoPyImageSet( &dscr, addr, obj );

  TomoseriesParamFinal( &seriesparam );

  TomoPyEnd( protomo );

  return obj;

  error2: TomoseriesParamFinal( &seriesparam );
  error1: TomoPyEnd( protomo ); Py_DECREF( obj );

  return NULL;

}


static PyObject *ProtomoSeriesAlign
                 (ProtomoSeries *self,
                  PyObject *args)

{
  Status status;

  if ( !PyArg_ParseTuple( args, "" ) ) return NULL;

  TomoPyBegin( protomo );

  TomoseriesParam seriesparam;
  status = TomoseriesGetParam( self->param, NULL, &seriesparam );
  if ( exception( status ) ) goto error1;

  TomorefParam refparam;
  status = TomorefGetParam( self->param, "reference", &refparam );
  if ( exception( status ) ) goto error2;

  TomoalignParam alignparam;
  status = TomoalignGetParam( self->param, "align", &alignparam );
  if ( exception( status ) ) goto error3;

  TomowindowParam windowparam;
  status = TomowindowGetParam( self->param, "window", &windowparam );
  if ( exception( status ) ) goto error4;

  if ( self->alignd != NULL ) {
    status = TomotiltDestroy( self->alignd );
    logexception( status );
    self->alignd = NULL;
  }

  if ( self->geom != NULL ) {
    free( self->geom ); self->geom = NULL;
  }

  status = TomoseriesSampling( self->series, &seriesparam );
  if ( exception( status ) ) goto error5;

  self->unaligned = False;

  Tomoalign *align = TomoalignSeries( self->series, &alignparam, &windowparam, &refparam );
  if ( testcondition( align == NULL ) ) goto error5;

  self->alignd = TomoalignTilt( align );
  if ( self->alignd == NULL ) goto error5;

  self->geom = TomoseriesGetGeom( self->series );
  if ( self->geom == NULL ) goto error5;

  TomoalignDestroy( align );
  TomowindowParamFinal( &windowparam );
  TomoalignParamFinal( &alignparam );
  TomorefParamFinal( &refparam );
  TomoseriesParamFinal( &seriesparam );

  TomoPyEnd( protomo );

  Py_INCREF( Py_None );
  return Py_None;

  error5: TomowindowParamFinal( &windowparam );
  error4: TomoalignParamFinal( &alignparam );
  error3: TomorefParamFinal( &refparam );
  error2: TomoseriesParamFinal( &seriesparam );
  error1: TomoPyEnd( protomo );

  return NULL;

}


static PyObject *ProtomoSeriesUnalign
                 (ProtomoSeries *self,
                  PyObject *args)

{
  Status status;

  if ( !PyArg_ParseTuple( args, "" ) ) return NULL;

  TomoPyBegin( protomo );

  ProtomoSeriesAlignReset( self );

  status = TomometaResetTransf( self->series->meta );
  logexception( status );

  self->unaligned = True;

  TomoPyEnd( protomo );

  Py_INCREF( Py_None );
  return Py_None;

}


static PyObject *ProtomoSeriesPlot
                 (ProtomoSeries *self,
                  PyObject *args)

{
  int pfd[2], qfd[2];

  if ( !PyArg_ParseTuple( args, "" ) ) return NULL;

  if ( self->alignd == NULL ) {
    pushexception( E_PROTOMO_ALI ); goto error;
  }

  Size images = self->alignd->images;
  const TomotiltGeom *geom = self->alignd->tiltgeom;

  Size count = 0;
  for ( Size index = 0; index < images; index++ ) {
    if ( geom[index].corr[0] > 0 ) count++;
  }
  if ( !count ) {
    pushexception( E_PROTOMO_IMG ); goto error;
  }

  TomoPyBegin( protomo );

  if ( pipe( pfd ) == -1 ) {
    pushexception( E_ERRNO ); goto error;
  }
  pid_t p0 = fork();
  if ( p0 == -1 ) {
    pushexception( E_ERRNO ); goto error;
  } else if ( !p0 ) {
    /* child */
    if ( close( pfd[1] ) ) goto childerror;
    if ( dup2( pfd[0], STDIN_FILENO ) == -1 ) goto childerror;
    if ( pipe( qfd ) == -1 ) goto childerror;
    pid_t p1 = fork();
    if ( p1 == -1 ) goto childerror;
    if ( !p1 ) {
      /* grandchild */
      if ( close( qfd[1] ) ) goto childerror;
      if ( dup2( qfd[0], STDIN_FILENO ) == -1 ) goto childerror;
      execlp( "/usr/bin/gv", "gv", "-", NULL );
      execlp( "/usr/bin/display", "display", "-", NULL );
      goto childerror;
    }
    if ( close( qfd[0] ) ) goto childerror;
    if ( dup2( qfd[1], STDOUT_FILENO ) == -1 ) goto childerror;
    int cycle = TomometaGetCycle( self->series->meta );
    char buf[64]; sprintf( buf, "%02d", cycle );
    const char *title = StringConcat( ( self->series->prfx == NULL ) ? "correction" : self->series->prfx, ( cycle < 0 ) ? NULL : buf, NULL );
    execlp( "/usr/bin/graph", "graph", "-T", "ps", "-L", title, "-C", "--title-font-size", "0.03", "--symbol-font-name", "Helvetica-Bold", "--font-size", "0.025",  "-w", "0.8", "-h", "0.9", "-r", "0.1", "-u", "0.0", "-m", "-1", "-S", "6", "0.01", NULL );
    goto childerror;
  }

  if ( close( pfd[0] ) ) {
    pushexception( E_ERRNO ); goto error;
  }
  FILE *handle = fdopen( pfd[1], "w" );
  if ( handle == NULL ) {
    pushexception( E_ERRNO ); goto error;
  } else {
    for ( Size index = 0; index < images; index++ ) {
      if ( geom[index].corr[0] > 0 ) {
        fprintf( handle, " %"SizeU" %.12"CoordG"\n", index, geom[index].corr[0] );
      }
    }
    fputc( '\n', handle );
    for ( Size index = 0; index < images; index++ ) {
      if ( geom[index].corr[0] > 0 ) {
        fprintf( handle, " %"SizeU" %.12"CoordG"\n", index, geom[index].corr[1] );
      }
    }
    if ( fclose( handle ) ) {
      pushexception( E_ERRNO ); goto error;
    }
  }

  TomoPyEnd( protomo );

  Py_INCREF( Py_None );
  return Py_None;

  error: TomoPyEnd( protomo );

  return NULL;

  childerror: perror( ProtomoName );

  _exit( EXIT_FAILURE );

}


static PyObject *ProtomoSeriesCorr
                 (ProtomoSeries *self,
                  PyObject *args)

{
  char *path, *str = NULL;

  if ( !PyArg_ParseTuple( args, "|s", &str ) ) return NULL;

  TomoPyBegin( protomo );

  if ( self->alignd == NULL ) {
    pushexception( E_PROTOMO_ALI ); goto error1;
  }

  Size count = 0;
  for ( Size index = 0; index < self->alignd->images; index++ ) {
    if ( self->alignd->tiltgeom[index].corr[0] > 0 ) count++;
  }
  if ( !count ) {
    pushexception( E_PROTOMO_IMG ); goto error1;
  }

  if ( str == NULL ) {
    path = TomoseriesOutName( self->series, ".corr" );
    if ( testcondition( path == NULL ) ) goto error1;
  } else {
    path = str;
  }

  FILE *handle = fopen( path, "w" );
  if ( handle == NULL ) {
    pushexceptionmsg( E_ERRNO, ", file ", path ); goto error2;
  } else {
    TomotiltGeom *geom = self->alignd->tiltgeom;
    for ( Size index = 0; index < self->alignd->images; index++, geom++ ) {
      if ( geom->corr[0] > 0 ) {
        fprintf( handle, " %"SizeU" %.12g %.12g %.12g %.12g %.12g\n", index, geom->alpha, geom->corr[0], geom->corr[1], geom->beta, ( geom->scale > 0 ) ? geom->scale : 1 );
      }
    }
    if ( fclose( handle ) ) {
      pushexceptionmsg( E_ERRNO, ", file ", path ); goto error2;
    }
  }

  if ( str == NULL ) free( path );

  TomoPyEnd( protomo );

  Py_INCREF( Py_None );
  return Py_None;

  error2: if ( str == NULL ) free( path );
  error1: TomoPyEnd( protomo );

  return NULL;

}


static PyObject *ProtomoSeriesGeom
                 (ProtomoSeries *self,
                  PyObject *args)

{
  unsigned int mode = 0;
  Tomotilt *tilt;

  if ( !PyArg_ParseTuple( args, "|I", &mode ) ) return NULL;

  ProtomoGeom *obj = (ProtomoGeom *)ProtomoGeomTypeObject->tp_alloc( ProtomoGeomTypeObject, 0 );
  if ( obj == NULL ) return NULL;

  TomoPyBegin( protomo );

  switch ( mode ) {

    case 1: {
      tilt = self->alignd;
      if ( tilt == NULL ) {
        pushexception( E_PROTOMO_ALI ); goto error;
      }
      break;
    }

    case 2: {
      tilt = self->fitted;
      if ( tilt == NULL ) {
        pushexception( E_PROTOMO_FIT ); goto error;
      }
      break;
    }

    default: {
      tilt = self->series->tilt;
      if ( tilt == NULL ) {
        pushexception( E_PROTOMO ); goto error;
      }
    }

  }

  obj->tilt = TomotiltDup( tilt );

  TomoPyEnd( protomo );

  return (PyObject *)obj;

  error: TomoPyEnd( protomo ); Py_DECREF( obj );

  return NULL;

}


static PyObject *ProtomoSeriesFit
                 (ProtomoSeries *self,
                  PyObject *args)

{
  Status status;

  if ( !PyArg_ParseTuple( args, "" ) ) return NULL;

  TomoPyBegin( protomo );

  if ( ( self->alignd == NULL ) || ( self->geom == NULL ) ) {
    pushexception( E_PROTOMO_ALI ); goto error1;
  }

  TomotiltFitParam fitparam;
  status = TomotiltFitGetParam( self->param, "fit", &fitparam );
  if ( exception( status ) ) goto error1;

  const Tomoseries *series = self->series;

  Tomotilt *tilt = TomotiltFit( series->tilt, self->geom, &fitparam );
  if ( testcondition( tilt == NULL ) ) goto error2;

  if ( self->fitted != NULL ) {
    status = TomotiltDestroy( self->fitted );
    logexception( status );
  }

  TomotiltFitParamFinal( &fitparam );

  self->fitted = tilt;

  TomoPyEnd( protomo );

  Py_INCREF( Py_None );
  return Py_None;

  error2: TomotiltFitParamFinal( &fitparam );
  error1: TomoPyEnd( protomo );

  return NULL;

}


static PyObject *ProtomoSeriesUpdate
                 (ProtomoSeries *self,
                  PyObject *args)

{
  Status status;

  if ( !PyArg_ParseTuple( args, "" ) ) return NULL;

  TomoPyBegin( protomo );

  if ( self->fitted != NULL ) {

    status = TomoseriesUpdate( self->series, self->fitted );
    if ( exception( status ) ) goto error;

    self->fitted = NULL;

    ProtomoSeriesAlignReset( self );

  }

  self->unaligned = True;

  TomoPyEnd( protomo );

  Py_INCREF( Py_None );
  return Py_None;

  error: TomoPyEnd( protomo );

  return NULL;

}


static PyObject *ProtomoSeriesSave
                 (ProtomoSeries *self,
                  PyObject *args)

{
  char *path, *str = NULL;
  Status status;

  if ( !PyArg_ParseTuple( args, "|s", &str ) ) return NULL;

  TomoPyBegin( protomo );

  if ( str == NULL ) {
    path = TomoseriesOutName( self->series, "_sav.i3t" );
    if ( testcondition( path == NULL ) ) goto error1;
  } else {
    path = str;
  }

  status = TomometaSave( self->series->meta, path );
  if ( exception( status ) ) goto error2;

  if ( str == NULL ) free( path );

  TomoPyEnd( protomo );

  Py_INCREF( Py_None );
  return Py_None;

  error2: if ( str == NULL ) free( path );
  error1: TomoPyEnd( protomo );

  return NULL;

}


static PyObject *ProtomoSeriesMap
                 (ProtomoSeries *self,
                  PyObject *args)

{
  Status status;

  if ( !PyArg_ParseTuple( args, "" ) ) return NULL;

  PyObject *obj = TomoPyImageCreate();
  if ( obj == NULL ) return NULL;

  TomoPyBegin( protomo );

  TomoseriesParam seriesparam;
  status = TomoseriesGetParam( self->param, NULL, &seriesparam );
  if ( exception( status ) ) goto error1;

  TomoseriesmapParam mapparam;
  status = TomoseriesmapGetParam( self->param, "map", &seriesparam, &mapparam );
  if ( exception( status ) ) goto error2;

  status = TomoseriesSampling( self->series, &seriesparam );
  if ( exception( status ) ) goto error3;

  Real *addr = TomoseriesmapMem( self->series, &mapparam );
  if ( testcondition( addr == NULL ) ) goto error3;

  Image dscr;
  dscr.dim = 3;
  dscr.len = mapparam.len;
  dscr.low = NULL;
  dscr.type = TypeReal;
  dscr.attr = ImageRealspc;

  TomoPyImageSet( &dscr, addr, obj );

  TomoseriesmapParamFinal( &mapparam );
  TomoseriesParamFinal( &seriesparam );

  TomoPyEnd( protomo );

  return obj;

  error3: TomoseriesmapParamFinal( &mapparam );
  error2: TomoseriesParamFinal( &seriesparam );
  error1: TomoPyEnd( protomo ); Py_DECREF( obj );

  return NULL;

}


static PyObject *ProtomoSeriesMapfile
                 (ProtomoSeries *self,
                  PyObject *args)

{
  char *path = NULL;
  char *fmt = NULL;
  Status status;

  if ( !PyArg_ParseTuple( args, "|ss", &path, &fmt ) ) return NULL;
  if ( fmt == NULL ) fmt = "MRC";

  TomoPyBegin( protomo );

  TomoseriesParam seriesparam;
  status = TomoseriesGetParam( self->param, NULL, &seriesparam );
  if ( exception( status ) ) goto error1;

  TomoseriesmapParam mapparam;
  status = TomoseriesmapGetParam( self->param, "map", &seriesparam, &mapparam );
  if ( exception( status ) ) goto error2;

  status = TomoseriesSampling( self->series, &seriesparam );
  if ( exception( status ) ) goto error3;

  status = TomoseriesmapFile( path, fmt, self->series, &mapparam );
  if ( exception( status ) ) goto error3;

  TomoseriesmapParamFinal( &mapparam );
  TomoseriesParamFinal( &seriesparam );

  TomoPyEnd( protomo );

  Py_INCREF( Py_None );
  return Py_None;

  error3: TomoseriesmapParamFinal( &mapparam );
  error2: TomoseriesParamFinal( &seriesparam );
  error1: TomoPyEnd( protomo );

  return NULL;

}


static PyObject *ProtomoSeriesCompare
                 (ProtomoSeries *self,
                  PyObject *args)

{
  Status status;

  if ( !PyArg_ParseTuple( args, "" ) ) return NULL;

  if ( self->alignd != NULL ) {
    pushexception( E_PROTOMO_UPD ); return NULL;
  }

  TomoPyBegin( protomo );

  TomoseriesParam seriesparam;
  status = TomoseriesGetParam( self->param, NULL, &seriesparam );
  if ( exception( status ) ) goto error1;

  TomorefParam refparam;
  status = TomorefGetParam( self->param, "reference", &refparam );
  if ( exception( status ) ) goto error2;

  TomoalignParam alignparam;
  status = TomoalignGetParam( self->param, "align", &alignparam );
  if ( exception( status ) ) goto error3;

  TomowindowParam windowparam;
  status = TomowindowGetParam( self->param, "window", &windowparam );
  if ( exception( status ) ) goto error4;

  status = TomoseriesSampling( self->series, &seriesparam );
  if ( exception( status ) ) goto error5;

  status = TomoalignSeriesCorr( self->series, NULL, &alignparam, &windowparam, &refparam );
  if ( exception( status ) ) goto error5;

  TomowindowParamFinal( &windowparam );
  TomoalignParamFinal( &alignparam );
  TomorefParamFinal( &refparam );
  TomoseriesParamFinal( &seriesparam );

  TomoPyEnd( protomo );

  Py_INCREF( Py_None );
  return Py_None;

  error5: TomowindowParamFinal( &windowparam );
  error4: TomoalignParamFinal( &alignparam );
  error3: TomorefParamFinal( &refparam );
  error2: TomoseriesParamFinal( &seriesparam );
  error1: TomoPyEnd( protomo );

  return NULL;

}


static PyObject *ProtomoSeriesPatchfiles
                 (ProtomoSeries *self,
                  PyObject *args)

{
  Status status;

  if ( !PyArg_ParseTuple( args, "" ) ) return NULL;

  TomoPyBegin( protomo );

  TomoseriesParam seriesparam;
  status = TomoseriesGetParam( self->param, NULL, &seriesparam );
  if ( exception( status ) ) goto error1;

  TomopatchParam patchparam;
  status = TomopatchGetParam( self->param, "patch", &patchparam );
  if ( exception( status ) ) goto error2;

  status = TomopatchWrite( self->series, NULL, &patchparam );
  if ( exception( status ) ) goto error3;

  TomopatchParamFinal( &patchparam );
  TomoseriesParamFinal( &seriesparam );

  TomoPyEnd( protomo );

  Py_INCREF( Py_None );
  return Py_None;

  error3: TomopatchParamFinal( &patchparam );
  error2: TomoseriesParamFinal( &seriesparam );
  error1: TomoPyEnd( protomo );

  return NULL;

}


/* tables */

static struct PyMethodDef ProtomoSeriesMethods[] = {
  { "param",      (PyCFunction)ProtomoSeriesParam,      METH_VARARGS, "replace all parameters" },
  { "setparam",   (PyCFunction)ProtomoSeriesSetpar,     METH_VARARGS, "set specific parameter" },
  { "setorigin",  (PyCFunction)ProtomoSeriesSetori,     METH_VARARGS, "set common origin" },
  { "seteuler",   (PyCFunction)ProtomoSeriesSeteul,     METH_VARARGS, "set global map rotation" },
  { "setcycle",   (PyCFunction)ProtomoSeriesSetcyc,     METH_VARARGS, "set cycle and discard alignments" },
  { "preprocess", (PyCFunction)ProtomoSeriesPreproc,    METH_VARARGS, "preprocess image" },
  { "image",      (PyCFunction)ProtomoSeriesImage,      METH_VARARGS, "resample image" },
  { "transform",  (PyCFunction)ProtomoSeriesTransf,     METH_VARARGS, "image transform" },
  { "filter",     (PyCFunction)ProtomoSeriesFilter,     METH_VARARGS, "resampled and filtered image" },
  { "window",     (PyCFunction)ProtomoSeriesWindow,     METH_VARARGS, "extract image windows" },
  { "area",       (PyCFunction)ProtomoSeriesArea,       METH_VARARGS, "common usable area" },
  { "align",      (PyCFunction)ProtomoSeriesAlign,      METH_VARARGS, "align tilt series" },
  { "unalign",    (PyCFunction)ProtomoSeriesUnalign,    METH_VARARGS, "discard current alignment" },
  { "plot",       (PyCFunction)ProtomoSeriesPlot,       METH_VARARGS, "plot correction factors" },
  { "corr",       (PyCFunction)ProtomoSeriesCorr,       METH_VARARGS, "write corrections to a file" },
  { "geom",       (PyCFunction)ProtomoSeriesGeom,       METH_VARARGS, "return tilt geometry" },
  { "fit",        (PyCFunction)ProtomoSeriesFit,        METH_VARARGS, "fit tilt geometry" },
  { "update",     (PyCFunction)ProtomoSeriesUpdate,     METH_VARARGS, "update tilt geometry" },
  { "save",       (PyCFunction)ProtomoSeriesSave,       METH_VARARGS, "save current alignment and metadata" },
  { "map",        (PyCFunction)ProtomoSeriesMap,        METH_VARARGS, "compute 3D map" },
  { "mapfile",    (PyCFunction)ProtomoSeriesMapfile,    METH_VARARGS, "write 3D map to a file" },
  { "compare",    (PyCFunction)ProtomoSeriesCompare,    METH_VARARGS, "compare reprojected images" },
  { "patchfiles", (PyCFunction)ProtomoSeriesPatchfiles, METH_VARARGS, "write patch files for CTF determination" },
  { NULL,         NULL,                                 0,            NULL }
};

static PyTypeObject ProtomoSeriesType = {
  PyObject_HEAD_INIT( NULL )
  0,                              /* ob_size */
  NULL,                           /* tp_name */
  sizeof(ProtomoSeries),          /* tp_basicsize */
  0,                              /* tp_itemsize */
  (destructor)ProtomoSeriesDealloc, /* tp_dealloc */
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
  ProtomoSeriesMethods,           /* tp_methods */
  0,                              /* tp_members */
  0,                              /* tp_getset */
  0,                              /* tp_base */
  0,                              /* tp_dict */
  0,                              /* tp_descr_get */
  0,                              /* tp_descr_set */
  0,                              /* tp_dictoffset */
  0,                              /* tp_init */
  0,                              /* tp_alloc */
  ProtomoSeriesNew,               /* tp_new */
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

extern void ProtomoSeriesInit
            (TomoPy *mod)

{

  ProtomoSeriesTypeObject = TomoPyClassInit( mod, "series", &ProtomoSeriesType );

}
