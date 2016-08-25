/*----------------------------------------------------------------------------*
*
*  tomotiltfit.c  -  tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomotiltfit.h"
#include "stringparse.h"
#include "baselib.h"
#include "mathdefs.h"
#include "message.h"
#include "exception.h"
#include "mat2.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


/* types */

typedef struct {
  Coord A[2][2];
  Coord det;
} TomotiltAlign;

typedef struct {
  int iter;
  int call;
  double rms;
  int flags;
  Coord (*A0)[2][2];
  TomotiltGeom *refgeom;
  Tomotilt *tomotiltfit;
  const Tomotilt *tomotilt;
  TomotiltAlign *align;
  TomotiltAlign *resid;
  Bool *fit;
  Bool *ofit;
  Bool *afit;
  Status status;
} TomotiltFitFunctionData;


/* constants */

#define raddeg ( 180.0 / Pi )


/* variables */

static TomotiltFitFunctionData TomotiltFitDataBuf;


/* prototypes */

void lmdif_( void (*f)(int *,int *,double *,double *,int *), int *, int *, double *, double *, double *, double *, double *, int *, double *, double *, int *, double *, int *, int *, int *,  double *, int *, int *, double *, double *, double *, double *, double * );


/* functions */

static double diffang
              (double a,
               double b)

{

  while ( a < b ) a += 360;
  a -= b;
  while ( a >= 360 ) a -= 360;
  if ( a > 180 ) a = 360 - a;
  return a;

}


static double normang
              (double a)

{

  while ( a < 0 ) a += 360;
  while ( a >= 360 ) a -= 360;
  if ( a > 180 ) a -= 360;
  return a;

}


static void TomotiltFitLogger
            (const Tomotilt *tomotilt,
             const Tomotilt *tomotiltfit,
             const Bool *fit,
             int flags)

{

  MessageStringBegin( "\n", NULL );
  if ( flags & TomotiltFitOrient ) {
    MessageStringHeadr( "indx      ", NULL );
    MessageFormatPrint( "   %-20s", "psi" );
    MessageFormatPrint( "   %-20s", "theta" );
    MessageFormatPrint( "   %-20s", "phi" );
    MessageStringPrint( "\n", NULL );
    for ( Size index = 0; index < tomotilt->orients; index++ ) {
      Coord *eul = tomotilt->tiltorient[index].euler;
      Coord *eulfit = tomotiltfit->tiltorient[index].euler;
      MessageFormatHeadr( "%4"SizeU" ", index );
      MessageFormatPrint( "    %9.3"CoordF" %9.3"CoordF, eulfit[0], eulfit[0] - eul[0] );
      MessageFormatPrint( "    %9.3"CoordF" %9.3"CoordF, eulfit[1], eulfit[1] - eul[1] );
      MessageFormatPrint( "    %9.3"CoordF" %9.3"CoordF, eulfit[2], eulfit[2] - eul[2] );
      MessageStringPrint( "\n", NULL );
    }
    MessageStringHeadr( "\n", NULL );
  }

  if ( flags & ( TomotiltFitAzim | TomotiltFitElev | TomotiltFitOffs ) ) {
    MessageStringHeadr( "indx      ", NULL );
    if ( flags & TomotiltFitAzim ) MessageFormatPrint( "   %-20s", "tilt azimuth" );
    if ( flags & TomotiltFitElev ) MessageFormatPrint( "   %-20s", "tilt elevation" );
    if ( flags & TomotiltFitOffs ) MessageFormatPrint( "   %-20s", "tilt offset" );
    MessageStringPrint( "\n", NULL );
    for ( Size index = 0; index < tomotilt->axes; index++ ) {
      TomotiltAxis *axis = tomotilt->tiltaxis + index;
      TomotiltAxis *axisfit = tomotiltfit->tiltaxis + index;
      MessageFormatHeadr( "%4"SizeU" ", index );
      if ( flags & TomotiltFitAzim ) MessageFormatPrint( "    %9.3"CoordF" %9.3"CoordF, axisfit->phi, axisfit->phi - axis->phi );
      if ( flags & TomotiltFitElev ) MessageFormatPrint( "    %9.3"CoordF" %9.3"CoordF, axisfit->theta, axisfit->theta - axis->theta );
      if ( flags & TomotiltFitOffs ) MessageFormatPrint( "    %9.3"CoordF" %9.3"CoordF, axisfit->offset, axisfit->offset - axis->offset );
      MessageStringPrint( "\n", NULL );
    }
    MessageStringHeadr( "\n", NULL );
  }

  if ( flags & ( TomotiltFitTheta | TomotiltFitAlpha | TomotiltFitScale ) ) {
    MessageStringHeadr( "indx img#  ", NULL );
    if ( flags & TomotiltFitAlpha ) MessageFormatPrint( "    %-20s", " rotation" );
    if ( !( flags & TomotiltFitOffs ) && ( flags & TomotiltFitTheta ) ) MessageFormatPrint( "    %-20s", "tilt angle" );
    if ( flags & TomotiltFitScale ) MessageFormatPrint( "    %-20s", "  scale" );
    MessageStringPrint( "\n", NULL );
    for ( Size index = 0; index < tomotilt->images; index++ ) {
      if ( fit[index] ) {
        Size number = tomotilt->tiltimage[index].number;
        TomotiltGeom *geom = tomotilt->tiltgeom + index;
        TomotiltGeom *geomfit = tomotiltfit->tiltgeom + index;
        MessageFormatHeadr( "%4"SizeU" %4"SizeU" ", index, number );
        if ( flags & TomotiltFitAlpha ) {
          MessageFormatPrint( "     %9.3"CoordF" %9.3"CoordF, geomfit->alpha, geomfit->alpha - geom->alpha );
        }
        if ( !( flags & TomotiltFitOffs ) && ( flags & TomotiltFitTheta ) ) {
          MessageFormatPrint( "     %9.3"CoordF" %9.3"CoordF, geomfit->theta, geomfit->theta - geom->theta );
        }
        if ( flags & TomotiltFitScale ) {
          Coord scale = ( geom->scale > 0 ) ? geom->scale : 1;
          Coord scalefit = ( geomfit->scale > 0 ) ? geomfit->scale : 1;
          MessageFormatPrint( "     %9.5"CoordF" %9.5"CoordF, scalefit, scalefit - scale );
        }
        MessageStringPrint( "\n", NULL );
      }
    }
    MessageStringHeadr( "\n", NULL );
  }

  MessageStringEnd( NULL, NULL );

}


static void TomotiltFitFunction
            (int *m,
             int *n,
             double *x,
             double *f,
             int *istat)

{
  TomotiltFitFunctionData *data = &TomotiltFitDataBuf;
  int flags = data->flags;
  double *xptr = x;
  double *fptr = f;
  int errstat = -99;
  Status matstat;

  data->call++;

  Tomotilt *tomotiltfit = data->tomotiltfit;
  TomotiltGeom *geom = tomotiltfit->tiltgeom;
  TomotiltAxis *axis = tomotiltfit->tiltaxis;
  TomotiltOrient *orient = tomotiltfit->tiltorient;
  Coord *euler = tomotiltfit->param.euler;

  const Tomotilt *tomotilt = data->tomotilt;
  const Size images = tomotilt->images;
  const Size axes = tomotilt->axes;
  const Size orients = tomotilt->orients;

  const Size cooref = tomotilt->param.cooref;
  const Size oriref = geom[cooref].orientindex;

  TomotiltAlign *align = data->align;
  TomotiltAlign *resid = data->resid;
  Bool *fit = data->fit;
  Bool *ofit = data->ofit;
  Bool *afit = data->afit;

  /* set up parameters */

  if ( flags & TomotiltFitOrient ) {
    for ( Size index = 0; index < orients; index++ ) {
      if ( ofit[index] ) {
        if ( ( index != oriref ) || ( flags & TomotiltFitEuler ) ) {
          Coord *euler = tomotilt->tiltorient[index].euler;
          orient[index].euler[1] = normang( *xptr++ );
          orient[index].euler[2] = normang( *xptr++ );
          orient[index].euler[0] = normang( euler[0] + euler[2] - orient[index].euler[2] );
        }
      }
    }
  }

  if ( flags & TomotiltFitAzim ) {
    for ( Size index = 0; index < axes; index++ ) {
      if ( afit[index] ) {
        axis[index].phi = *xptr++;
      }
    }
  }
  if ( flags & TomotiltFitElev ) {
    for ( Size index = 0; index < axes; index++ ) {
      if ( afit[index] ) {
        axis[index].theta = *xptr++;
      }
    }
  }

  if ( flags & TomotiltFitOffs ) {
    for ( Size index = 0; index < axes; index++ ) {
      if ( afit[index] ) {
        axis[index].offset = *xptr++;
      }
    }
  } else if ( flags & TomotiltFitTheta ) {
    for ( Size index = 0; index < images; index++ ) {
      if ( fit[index] ) {
        geom[index].theta = *xptr++;
      }
    }
  }

  if ( flags & TomotiltFitAlpha ) {
    for ( Size index = 0; index < images; index++ ) {
      if ( fit[index] ) {
        geom[index].alpha = *xptr++;
      }
    }
  }

  if ( flags & TomotiltFitScale ) {
    for ( Size index = 0; index < images; index++ ) {
      if ( fit[index] ) {
        geom[index].scale = *xptr++;
      }
    }
  }

  if ( ( xptr - x ) != *n ) {
    data->status = E_TOMOTILTFIT;
    *istat = errstat;
    return;
  }

  /* debug */
  if ( !*istat && ( flags & TomotiltFitDbg ) ) {
    MessageStringBegin( "\n", NULL );
    MessageStringHeadr( "\n", NULL );
    MessageFormatHeadr( "DEBUG: iter %2d    call #%d\n", data->iter, data->call );
    MessageStringEnd( NULL, NULL );
    TomotiltFitLogger( tomotilt, tomotiltfit, fit, flags );
  }

  /* compute rotation matrices and correction */
  {
    Coord A0[orients][2][2], Ai[3][3];
    for ( Size index = 0; index < orients; index++ ) {
      matstat = TomotiltMat( euler, axis + orient[index].axisindex, orient + index, data->refgeom, NULL, Ai, NULL, NULL, True );
      if ( matstat ) {
        data->status = matstat; *istat = errstat; return;
      }
      A0[index][0][0] = Ai[0][0]; A0[index][0][1] = Ai[0][1];
      A0[index][1][0] = Ai[1][0]; A0[index][1][1] = Ai[1][1];
      matstat = Mat2Inv( A0[index], A0[index], NULL );
      if ( matstat ) {
        data->status = matstat; *istat = errstat; return;
      }
      Mat2Mul( data->A0[index], A0[index], A0[index] );
    }
    for ( Size index = 0; index < images; index++ ) {
      if ( fit[index] ) {
        Coord Ap[2][2], detAp;
        matstat = TomotiltMat( euler, axis + geom[index].axisindex, orient + geom[index].orientindex, geom + index, NULL, Ai, NULL, NULL, True );
        if ( matstat ) {
          data->status = matstat; *istat = errstat; return;
        }
        Ap[0][0] = Ai[0][0]; Ap[0][1] = Ai[0][1];
        Ap[1][0] = Ai[1][0]; Ap[1][1] = Ai[1][1];
        Mat2Mul( A0[geom[cooref].orientindex], Ap, Ap );
        matstat = Mat2Inv( Ap, Ap, &detAp );
        if ( matstat ) {
          data->status = matstat; *istat = errstat; return;
        }
        Mat2Mul( Ap, align[index].A, resid[index].A );
        *fptr++ = resid[index].A[0][0] - 1;
        *fptr++ = resid[index].A[0][1];
        *fptr++ = resid[index].A[1][0];
        *fptr++ = resid[index].A[1][1] - 1;
        if ( flags & TomotiltFitDet ) *fptr++ = detAp - align[index].det;
        if ( !*istat && ( flags & TomotiltFitDbg ) ) {
          if ( flags & TomotiltFitDet ) {
            MessageFormat( "%4"SizeU"   %8.5f %8.5f %8.5f %8.5f   %8.5f   %8.5f\n", index, fptr[-5], fptr[-4], fptr[-3], fptr[-2], fptr[-1], align[index].det );
          } else {
            MessageFormat( "%4"SizeU"   %8.5f %8.5f %8.5f %8.5f   %8.5f\n", index, fptr[-4], fptr[-3], fptr[-2], fptr[-1], align[index].det );
          }
        }
      }
    }
    data->rms = 0;
    for ( int index = 0; index < *m; index++ ) {
      data->rms += sqrt( f[index] * f[index] );
    }
    data->rms /= *m;
  }

  /* log fitting statistics */

  if ( !*istat && ( flags & TomotiltFitLog ) ) {

    MessageFormatBegin( "iter %2d", data->iter++ );
    if ( flags & TomotiltFitOrient ) {
      Coord dpsi = 0, dthe = 0, dphi = 0;
      for ( Size index = 0; index < orients; index++ ) {
        Coord psi = tomotilt->tiltorient[index].euler[0];
        Coord the = tomotilt->tiltorient[index].euler[1];
        Coord phi = tomotilt->tiltorient[index].euler[2];
        if ( ( index != oriref ) || ( flags & TomotiltFitEuler ) ) {
          dpsi += diffang( psi, ( psi + phi ) - orient[index].euler[2] );
          dthe += diffang( the, orient[index].euler[1] );
          dphi += diffang( phi, orient[index].euler[2] );
        }
      }
      MessageFormatPrint( "   S(do) %7.3"CoordF" %7.3"CoordF" %7.3"CoordF"", dpsi, dthe, dphi );
    }
    if ( flags & ( TomotiltFitAzim | TomotiltFitElev ) ) {
      Coord dphi = 0, dtheta = 0;
      if ( flags & TomotiltFitAzim ) {
        for ( Size index = 0; index < axes; index++ ) {
          dphi += diffang( tomotilt->tiltaxis[index].phi, axis[index].phi );
        }
      }
      if ( flags & TomotiltFitElev ) {
        for ( Size index = 0; index < axes; index++ ) {
          dtheta += diffang( tomotilt->tiltaxis[index].theta, axis[index].theta );
        }
      }
      MessageFormatPrint( "   S(da) %7.3"CoordF" %7.3"CoordF"", dphi, dtheta );
    }
    if ( flags & TomotiltFitOffs ) {
      Coord dtheta = 0;
      for ( Size index = 0; index < axes; index++ ) {
        dtheta += diffang( tomotilt->tiltaxis[index].offset, axis[index].offset );
      }
      MessageFormatPrint( "   S(do) %7.3"CoordF"", dtheta );
    } else if ( flags & TomotiltFitTheta ) {
      Coord dtheta = 0;
      for ( Size index = 0; index < images; index++ ) {
        if ( fit[index] ) {
          dtheta += diffang( tomotilt->tiltgeom[index].theta, geom[index].theta );
        }
      }
      MessageFormatPrint( "   S(dt) %7.3"CoordF"", dtheta );
    }
    if ( flags & TomotiltFitAlpha ) {
      Coord dalpha = 0;
      for ( Size index = 0; index < images; index++ ) {
        if ( fit[index] ) {
          dalpha += diffang( tomotilt->tiltgeom[index].alpha, geom[index].alpha );
        }
      }
      MessageFormatPrint( "   S(dr) %7.3"CoordF"", dalpha );
    }
    if ( flags & TomotiltFitScale ) {
      Coord dscale = 0;
      for ( Size index = 0; index < images; index++ ) {
        if ( fit[index] ) {
          Coord tiltscale = tomotilt->tiltgeom[index].scale; if ( tiltscale <= 0 ) tiltscale = 1;
          Coord scale = geom[index].scale; if ( scale <= 0 ) scale = 1;
          dscale += fabs( tiltscale - scale );
        }
      }
      MessageFormatPrint( "   S(ds) %7.5lf", dscale );
    }
    MessageFormatEnd( "   rms %.5lg\n", data->rms );

  } /* end if !*istat */

}


extern Tomotilt *TomotiltFit
                 (const Tomotilt *tomotilt,
                  const Tomogeom *tomogeom,
                  const TomotiltFitParam *param)

{
  TomotiltFitFunctionData *data = &TomotiltFitDataBuf;
  Status status = E_NONE;

  if ( tomotilt == NULL ) { pushexception( E_ARGVAL ); return NULL; }
  if ( tomogeom == NULL ) { pushexception( E_ARGVAL ); return NULL; }

  const Size images = tomotilt->images;
  const Size axes = tomotilt->axes;
  const Size orients = tomotilt->orients;
  if ( ( images < 3 ) || !axes || !orients ) { pushexception( E_ARGVAL ); return NULL; }

  int flags = ( param == NULL ) ? 0 : param->flags;
  if ( !( flags & TomotiltFitMask ) ) {
    pushexception( E_TOMOTILTFIT_NONE ); return NULL;
  }

  Tomotilt *tomotiltfit = TomotiltDup( tomotilt );
  if ( testcondition( tomotiltfit == NULL ) ) return NULL;

  TomotiltGeom *geom = tomotiltfit->tiltgeom;
  TomotiltAxis *axis = tomotiltfit->tiltaxis;
  TomotiltOrient *orient = tomotiltfit->tiltorient;
  Coord *euler = tomotiltfit->param.euler;

  TomotiltAlign *align = malloc( images * sizeof(TomotiltAlign) );
  TomotiltAlign *resid = malloc( images * sizeof(TomotiltAlign) );
  Coord (*A0)[2][2] = malloc( orients * sizeof(*A0) );
  Bool *fit = malloc( ( images + orients + axes ) * sizeof(Bool) );
  if ( ( align == NULL ) || ( resid == NULL ) || ( A0 == NULL ) || ( fit == NULL ) ) {
    status = pushexception( E_MALLOC ); goto exit;
  }
  Bool *ofit = fit + images;
  Bool *afit = ofit + orients;
  memset( ofit, 0, ( orients + axes ) * sizeof(Bool) );

  for ( Size index = 0; index < images; index++ ) {
    fit[index] = SelectExclude( param->selection, param->exclusion, tomotilt->tiltimage[index].number );
  }

  Size cooref = tomotiltfit->param.cooref;
  Size oriref = geom[cooref].orientindex;
  if ( oriref >= orients ) { pushexception( E_TOMOTILTFIT ); goto exit; }

  if ( ( ( tomogeom[cooref].Aa[0][0] == 0 ) && ( tomogeom[cooref].Aa[0][1] == 0 ) )
    || ( ( tomogeom[cooref].Aa[1][0] == 0 ) && ( tomogeom[cooref].Aa[1][1] == 0 ) ) ) {
    for ( Size index = 0; index < images; index++, tomogeom++ ) {
      if ( ( ( tomogeom->Aa[0][0] == 0 ) && ( tomogeom->Aa[0][1] == 0 ) )
        || ( ( tomogeom->Aa[1][0] == 0 ) && ( tomogeom->Aa[1][1] == 0 ) ) ) {
        align[index].A[0][0] = tomogeom->Ap[0][0]; align[index].A[0][1] = tomogeom->Ap[0][1];
        align[index].A[1][0] = tomogeom->Ap[1][0]; align[index].A[1][1] = tomogeom->Ap[1][1];
        fit[index] = False;
      } else {
        align[index].A[0][0] = tomogeom->Aa[0][0]; align[index].A[0][1] = tomogeom->Aa[0][1];
        align[index].A[1][0] = tomogeom->Aa[1][0]; align[index].A[1][1] = tomogeom->Aa[1][1];
        status = TomogeomSave( (void *)tomogeom->A, (void *)tomogeom->Am, (void *)tomogeom->Aa, (Coord *)tomogeom->origin, True, index, tomotiltfit );
        if ( exception( status ) ) goto exit;
      }
    }
  } else {
    status = pushexception( E_TOMOTILTFIT_REF ); goto exit;
  }

  fit[cooref] = False;
  for ( Size index = 0; index < images; index++ ) {
    if ( fit[index] ) {
      ofit[geom[index].orientindex] = True;
      afit[geom[index].axisindex] = True;
      status = Mat2Inv( align[index].A, NULL, &align[index].det );
      if ( pushexception( status ) ) goto exit;
    } else {
      align[index].det = 0;
    }
    geom[index].corr[0] = geom[index].corr[1] = 0;
  }

  TomotiltGeom refgeom;
  refgeom.theta = 0;
  refgeom.alpha = 0;
  refgeom.corr[0] = 0;
  refgeom.corr[1] = 0;
  refgeom.scale = geom[cooref].scale;
  for ( Size index = 0; index < orients; index++ ) {
    Coord Ai[3][3];
    status = TomotiltMat( euler, axis + orient[index].axisindex, orient + index, &refgeom, NULL, Ai, NULL, NULL, True );
    if ( pushexception( status ) ) goto exit;
    A0[index][0][0] = Ai[0][0]; A0[index][0][1] = Ai[0][1];
    A0[index][1][0] = Ai[1][0]; A0[index][1][1] = Ai[1][1];
  }

  for ( Size index = 0; index < axes; index++ ) {
    if ( axis[index].phi == CoordMax ) axis[index].phi = 0;
    if ( axis[index].theta == CoordMax ) axis[index].theta = 0;
    if ( axis[index].offset == CoordMax ) axis[index].offset = 0;
  }

  for ( Size index = 0; index < orients; index++ ) {
    if ( orient[index].euler[0] == CoordMax ) orient[index].euler[0] = 0;
    if ( orient[index].euler[1] == CoordMax ) orient[index].euler[1] = 0;
    if ( orient[index].euler[2] == CoordMax ) orient[index].euler[2] = 0;
  }

  if ( euler[0] == CoordMax ) euler[0] = 0;
  if ( euler[1] == CoordMax ) euler[1] = 0;
  if ( euler[2] == CoordMax ) euler[2] = 0;

  if ( flags & TomotiltFitLog ) {
    Size number = tomotilt->tiltimage[cooref].number;
    MessageFormatBegin( "tilt series %s\n", tomotilt->tiltstrings );
    MessageFormatHeadr( "number of images: %"SizeU" [ref %"SizeU"]\n", images, number );
    MessageFormatHeadr( "number of tilt axes:   %"SizeU"\n", axes );
    MessageFormatHeadr( "number of tilt groups: %"SizeU"\n", orients );
    MessageFormatEnd( NULL );
  }

  /* count fitted parameters */

  int npar = 0;

  if ( flags & TomotiltFitOrient ) {
    for ( Size index = 0; index < orients; index++ ) {
      if ( ofit[index] ) {
        if ( ( index == oriref ) || ( flags & TomotiltFitEuler ) ) {
          npar += 2; /* theta, phi */
        }
      }
    }
  }

  if ( flags & TomotiltFitAzim ) {
    for ( Size index = 0; index < axes; index++ ) {
      if ( afit[index] ) {
        npar++; /* tilt azimuth */
      }
    }
  }
  if ( flags & TomotiltFitElev ) {
    for ( Size index = 0; index < axes; index++ ) {
      if ( afit[index] ) {
        npar++; /* tilt elevation */
      }
    }
  }

  if ( flags & TomotiltFitOffs ) {
    for ( Size index = 0; index < axes; index++ ) {
      if ( afit[index] ) {
        npar++; /* tilt offset */
      }
    }
  } else if ( flags & TomotiltFitTheta ) {
    for ( Size index = 0; index < images; index++ ) {
      if ( fit[index] ) {
        npar++; /* tilt angles */
      }
    }
  }

  if ( flags & TomotiltFitAlpha ) {
    for ( Size index = 0; index < images; index++ ) {
      if ( fit[index] ) {
        npar++; /* rotation */
      }
    }
  }

  if ( flags & TomotiltFitScale ) {
    for ( Size index = 0; index < images; index++ ) {
      if ( fit[index] ) {
        npar++; /* scale factors */
      }
    }
  }

  /* count images to fit */

  int nimg = 0;

  for ( Size index = 0; index < images; index++ ) {
    if ( fit[index] ) {
      nimg++;
    }
  }

  if ( flags & TomotiltFitLog ) {
    MessageFormat( "%d images to fit\n", nimg );
  }
  if ( nimg < 3 ) {
    status = pushexception( E_TOMOTILTFIT_IMG ); goto exit;
  }

  /* fitting routine arguments */
  int n = npar;
  int m = ( flags & TomotiltFitDet ) ? 5 : 4;
  m *= nimg; /* functions for all images except reference image */
  if ( flags & TomotiltFitDbg ) {
    MessageFormat( "m = %d; n = %d\n", m, n );
  }
  if ( n > m ) {
    status = pushexception( E_TOMOTILTFIT_PARAM ); goto exit;
  }

  /* set up fitting routine call */
  {
    double *x = malloc( n * sizeof(double) );
    double *f = malloc( m * sizeof(double) );
    double ftol = 1E-5;
    double xtol = 1E-5;
    double gtol = 1E-5;
    int maxfev = 200 * ( n + 1 );
    double epsfcn = 1E-12;
    double *diag = malloc( n * sizeof(double) );
    int mode = 2;
    double factor = 1;
    int nprint = 1;
    int info;
    int nfev;
    double *fjac = malloc( m * n * sizeof(double) );
    int ldfjac = m;
    int *ipvt = malloc( n * sizeof(int) );
    double *qtf = malloc( n * sizeof(double) );
    double *wa1 = malloc( n * sizeof(double) );
    double *wa2 = malloc( n * sizeof(double) );
    double *wa3 = malloc( n * sizeof(double) );
    double *wa4 = malloc( m * sizeof(double) );
    double *xptr = x;

    if ( ( x == NULL ) || ( f == NULL ) || ( diag == NULL ) || ( fjac == NULL ) || ( ipvt == NULL )
      || ( qtf == NULL ) || ( wa1 == NULL ) || ( wa2 == NULL ) || ( wa3 == NULL ) || ( wa4 == NULL ) )  {
      status = E_MALLOC;
      goto cleanup;
    }

    /* initial estimate */

    if ( flags & TomotiltFitOrient ) {
      for ( Size index = 0; index < orients; index++ ) {
        if ( ofit[index] ) {
          if ( ( index == oriref ) || ( flags & TomotiltFitEuler ) ) {
            *xptr++ = orient[index].euler[1];
            *xptr++ = orient[index].euler[2];
          }
        }
      }
    }

    if ( flags & TomotiltFitAzim ) {
      for ( Size index = 0; index < axes; index++ ) {
        if ( afit[index] ) {
         *xptr++ = axis[index].phi;
        }
      }
    }
    if ( flags & TomotiltFitElev ) {
      for ( Size index = 0; index < axes; index++ ) {
        if ( afit[index] ) {
          *xptr++ = axis[index].theta;
        }
      }
    }

    if ( flags & TomotiltFitOffs ) {
      for ( Size index = 0; index < axes; index++ ) {
        if ( afit[index] ) {
          *xptr++ = axis[index].offset;
        }
      }
    } else if ( flags & TomotiltFitTheta ) {
      for ( Size index = 0; index < images; index++ ) {
        if ( fit[index] ) {
          *xptr++ = geom[index].theta;
        }
      }
    }

    if ( flags & TomotiltFitAlpha ) {
      for ( Size index = 0; index < images; index++ ) {
        if ( fit[index] ) {
          *xptr++ = geom[index].alpha;
        }
      }
    }

    if ( flags & TomotiltFitScale ) {
      for ( Size index = 0; index < images; index++ ) {
        if ( fit[index] ) {
          *xptr++ = ( geom[index].scale > 0 ) ? geom[index].scale : 1;
        }
      }
    }

    if ( ( xptr - x ) != n ) {
      status = pushexception( E_TOMOTILTFIT ); goto cleanup;
    }

    /* initialize fit */
    {
      data->iter = 0;
      data->call = 0;
      data->rms = 0;
      data->flags = flags;
      data->A0 = A0;
      data->refgeom = &refgeom;
      data->tomotiltfit = tomotiltfit;
      data->tomotilt = tomotilt;
      data->align = align;
      data->resid = resid;
      data->fit = fit;
      data->ofit = ofit;
      data->afit = afit;
      data->status=E_NONE;
    }

    /* compute initial values and check for errors */
    {
      int zero = 0;
      TomotiltFitFunction( &m, &n, x, f, &zero );
    }
    if ( data->status ) {
      status = pushexception( E_TOMOTILTFIT_DATA ); goto cleanup;
    }

    /* initialize */
    for ( int i = 0; i < n; i++ ) {
      diag[i] = 1;
    }
    for ( int i = 0; i < m; i++ ) {
      f[i] = 0;
    }

    /* call MINPACK routine */
    if ( flags & TomotiltFitDbg ) {
      MessageString( "entering lmdif_\n", NULL );
    }
    lmdif_( TomotiltFitFunction, &m, &n, x, f, &ftol, &xtol, &gtol, &maxfev, &epsfcn,
         diag, &mode, &factor, &nprint, &info, &nfev, fjac, &ldfjac,
         ipvt, qtf, wa1, wa2, wa3, wa4 );
    if ( flags & TomotiltFitDbg ) {
      MessageString( "leaving lmdif_\n", NULL );
    }
    {
      char *msg, msgbuf[64];
      switch ( info ) {
        case 1: msg = "sum of squares <= ftol"; break;
        case 2: msg = "relative error between two consecutive iterates <= xtol"; break;
        case 3: msg = "sum of squares <= ftol and relative error <= xtol"; break;
        case 4: msg = "|cos()| <= gtol"; break;
        case 5: msg = "maximum number of calls exceeded"; break;
        case 6: msg = "ftol too small, no further reduction possible"; break;
        case 7: msg = "xtol too small, no further improvement possible"; break;
        case 8: msg = "gtol too small, f is orthogonal to columns of the jacobian"; break;
        default: {
          sprintf( msgbuf, "error in routine LMDIF, code = %d", info );
          status = pushexceptionmsg( E_TOMOTILTFIT_FIT, ", ", msgbuf );
          msg = msgbuf;
        }
      }
      if ( flags & TomotiltFitLog ) {
        MessageFormatBegin( "returned from LMDIF after %d iterations\n", data->iter );
        MessageFormatHeadr( "%d function calls (%d)\n", nfev, data->call );
        MessageFormatHeadr( "%s\n", msg );
        MessageFormatEnd( NULL );
      }
      if ( status ) goto cleanup;
    }

    /* compute and log result */
    {
      int one = 1;
      TomotiltFitFunction( &m, &n, x, f, &one );
    }
    if ( data->status ) {
      char *msg = "error in function evaluation";
      status = pushexceptionmsg( E_TOMOTILTFIT_FIT, ", ", msg );
      if ( flags & TomotiltFitLog ) {
        MessageFormat( "%s\n", msg );
      }
      goto cleanup;
    }
    TomotiltFitResid *tiltresid = param->resid;
    for ( Size index = 0; index < images; index++, geom++, tiltresid++ ) {
      if ( param->resid != NULL ) {
        tiltresid->corr[0] = 0;
        tiltresid->corr[1] = 0;
        tiltresid->beta = 0;
      }
      if ( fit[index] ) {
        Coord U[2][2], S[2], V[2][2];
        status = Mat2Svd( resid[index].A, U, S, V );
        if ( status ) { pushexception( E_TOMOTILTFIT_CORR ); goto exit; }
        geom->beta = raddeg * Atan2( V[1][0], V[0][0] );
        geom->alpha += raddeg * Atan2( U[0][1], U[0][0] ) + geom->beta;
        geom->corr[0] = S[0];
        geom->corr[1] = S[1];
        if ( param->resid != NULL ) {
          tiltresid->corr[0] = geom->corr[0];
          tiltresid->corr[1] = geom->corr[1];
          tiltresid->beta = geom->beta;
        }
        if ( flags & TomotiltFitDbg ) {
          MessageFormat( "%4"SizeU"   %8.5f %8.5f %8.5f %8.5f   %8.3f  %8.5f %8.5f  %8.3f\n",
            index, resid[index].A[0][0], resid[index].A[0][1], resid[index].A[1][0], resid[index].A[1][1],
            raddeg * Atan2( U[0][1], U[0][0] ), S[0], S[1], raddeg * Atan2( V[1][0], V[0][0] ) );
        }
      }
      geom->corr[0] = geom->corr[1] = 0;
    }
    if ( flags & TomotiltFitDat ) {
      TomotiltFitLogger( tomotilt, tomotiltfit, fit, flags );
    }

    cleanup:
    if ( x != NULL ) free( x );
    if ( f != NULL ) free( f );
    if ( diag != NULL ) free( diag );
    if ( fjac != NULL ) free( fjac );
    if ( ipvt != NULL ) free( ipvt );
    if ( qtf != NULL ) free( qtf );
    if ( wa1 != NULL ) free( wa1 );
    if ( wa2 != NULL ) free( wa2 );
    if ( wa3 != NULL ) free( wa3 );
    if ( wa4 != NULL ) free( wa4 );

  }

  exit:

  if ( align != NULL ) free( align );
  if ( resid != NULL ) free( resid );
  if ( fit != NULL ) free( fit );
  if ( A0 != NULL ) free( A0 );

  if ( status ) {
    TomotiltDestroy( tomotiltfit );
    tomotiltfit = NULL;
  }

  return tomotiltfit;

}
