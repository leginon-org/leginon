/*----------------------------------------------------------------------------*
*
*  neldermead.c  -  approx: Nelder Mead minimization
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "nmmin.h"
#include "message.h"
#include "mathdefs.h"
#include "exception.h"


/* constants */

/* Maximum allowed number of parameters in the present code. */
#define MAXPARM 16
/* Maximum number of function values returned */
#define MAXFNVAL 4
/* Maximum number of columns in polytope */
#define Pcol (MAXPARM+2)
/* Maximum number of rows in polytope (including function value + additional values) */
#define Prow (MAXPARM+MAXFNVAL)


/* functions */

extern Status NMmin
              (Size n,          /* number of parameters in function */
               const Coord *X0, /* input parameters */
               NMfunc fn,       /* minimization function */
               void *fndata,    /* data for minimization function */
               NMdata *data,    /* minimization data/options */
               Coord *X,        /* output parameters */
               Size m,          /* number of returned values */
               Coord *Fmin)     /* "minimal" function value */

{
  Size C;                 /* pointer column in workspace P which stores the centroid of the polytope. C is set to n+2 here */
  Bool calcvert;          /* true if vertices to be calculated, as at start or after a shrink operation */
  Bool shrinkfail;        /* true if shrink has not reduced polytope size */
  Coord convtol = 1e-5;   /* a convergence tolerance based on function value differences */
  Size H;                 /* pointer to highest vertex in polytope */
  Size L;                 /* pointer to lowest vertex in polytope */
  Coord size;             /* a size measure for the polytope */
  Coord oldsize;          /* former size measure of polytope */
  Coord P[Pcol][Prow];    /* polytope workspace; rows and cols interchanged, consecutive addresses of index Prow */
  Coord *f = &P[0][n];    /* pointer to function value; this is an array now, [0] function value, [1],[2] x,y coo */
  Size N = n + m;         /* number of parameters in function plus number of function values returned */
  Coord VH, VL /* VN */;  /* function values of "highest", "lowest", and "next" vertices */ /* VN seems to be unused */
  Coord VR;               /* function value at Reflection */
  Coord f0;               /* initial function value */
  Coord alpha = 1.0;      /* reflection factor */
  Coord beta  = 0.5;      /* contraction and reduction factor */
  Coord gamma = 2.0;      /* extension factor */
  static const char *fmt1 = "%s  it %2"SizeU"  %-5s  #f %3"SizeU" ";
  static const char *fmt2 = " %9.6"CoordF;
  static const char *fmt3 = "   %9.6"CoordF"\n";
  static const char *fmt4 = "   %9.6"CoordF";  %-9.3"CoordG"\n";
  const char *action;
  Status status, fail;

  /* initialize */
  data->fncount = 0;
  data->iter = 0;
  if ( ( n > MAXPARM ) || ( m > MAXFNVAL ) ) {
    return exception( E_ARGVAL );
  }
  if ( data->tol   > 0 ) convtol = data->tol;
  if ( data->alpha > 0 ) alpha = data->alpha;
  if ( data->beta  > 0 ) beta  = data->beta;
  if ( data->gamma > 0 ) gamma = data->gamma;
  for ( Size i = 0; i < n; i++ ) {
    P[0][i] = X[i] = X0[i]; /* keep X0 unchanged */
  }
  action = "init";
  status = fn( n, P[0], m, f, fndata, &data->fncount ); /* initial fn calculation ( STEP 1) */
  if ( status ) return exception( status );
  if ( data->log != NULL ) {
    MessageFormatBegin( fmt1, data->log, data->iter, action, data->fncount );
    for ( Size i = 0; i < n; i++ ) {
      MessageFormatPrint( fmt2, P[0][i] );
    }
    for ( Size i = 1; i < m; i++ ) {
      MessageFormatPrint( fmt2, f[i] );
    }
    MessageFormatEnd( fmt3, -f[0] );
  }
  if ( f[0] == CoordMax ) {
    for ( Size i = n; i < N; i++ ) {
      Fmin[i-n] = f[i-n];
    }
    return exception( E_NMMIN_FAIL );
  }
  f0 = f[0]; /* initial value */
  convtol *= fabs( f0 ) + convtol; /* ensures small value relative to function value */
  C = n + 1; /* STEP 2 */
  L = 0; /* we indicate that it is the "lowest" vertex at the moment, so that its function value is not recomputed later in STEP 10 */
  size = 0; /* STEP 3 */
  /* STEP 4: build the initial polytope using a fixed step size */
  /* modified step size calculation */
  action = "bld";
  for ( Size j = 1; j <= n; j++ ) { /* main loop to build polytope, STEP 5 */
    /* STEP 6 */
    Coord trystep = data->step[j-1]; /* trial step -- STEP 7 */
    for ( Size i = 0; i < N; i++ ) {
      P[j][i] = P[0][i]; /* set the parameters */
    }
    if ( trystep > 0 ) {
      while ( P[j][j-1] == P[0][j-1] ) {
        P[j][j-1] = P[0][j-1] + trystep;
        trystep *= 10;
      } /* end while */
      size += trystep; /* to compute a size measure for polytope -- STEP 8 */
    }
  } /* end loop on j for parameters */
  fail = E_NONE;
  oldsize = size; /* to save the size measure -- STEP 9 */
  calcvert = True; /* must calculate vertices when polytope is new */
  shrinkfail = False; /* initialize shrink failure flag so we don't have false convergence */
  do { /* main loop for Nelder-Mead operations -- STEP 10 */
    data->iter++;
    if ( calcvert ) {
      for ( Size j = 0; j <= n; j++ ) { /* compute the function at each vertex */
        if ( j != L ) { /* we already have function value for L(owest) vertex */
          status = fn( n, P[j], m, &P[j][n], fndata, &data->fncount ); /* function calculation */
          if ( exception( status ) ) break;
        } /* end if j != L */
      } /* end loop on j to compute polytope vertices */
      if ( status ) break;
      calcvert = False; /* remember to reset flag so we don't calculate vertices every cycle of algorithm */
    } /* end calculation of vertices */
    /* STEP 11: find the highest and lowest vertices in current polytope */
    VL = P[L][n]; /* supposedly lowest value */
    VH = VL; /* highest value must hopefully be higher */
    H = L; /* pointer to highest vertex initialized to L */
    /* now perform the search */
    for ( Size j = 0; j <= n; j++ ) {
      if ( j != L ) {
        Coord f = P[j][n]; /* function value at vertex j */
        if ( f < VL ) {
          L = j; VL = f; /* save new "low" */
        }
        if ( f > VH ) {
          H = j; VH = f; /* save new "high" */
        }
      } /* end if j != L */
    } /* search for highest and lowest */
    /* STEP 12: test and display current polytope information */
    if ( data->log != NULL ) {
      MessageFormatBegin( fmt1, data->log, data->iter, action, data->fncount );
      for ( Size i = 0; i < n; i++ ) {
        MessageFormatPrint( fmt2, P[L][i] );
      }
      if ( P[L][n] == CoordMax ) {
        MessageFormatPrint( " not comp" );
      } else {
        for ( Size i = n + 1; i < n + m; i++ ) {
           MessageFormatPrint( fmt2, P[L][i] );
        }
        MessageFormatEnd( fmt4, -P[L][n], size );
      }
    }
    if ( shrinkfail || !( VH > VL + convtol ) ) {
      if ( P[L][n] >= f0 ) {
        fail = exception( E_NMMIN_FAIL );
      }
      break;
    } else {
      Coord Bvec[Prow];
      /* major cycle of the method */
      /* VN = beta * VL + ( 1.0 - beta ) * VH; */ /* interpolate to get "next to highest" function value -- there are many options here, we have chosen a fairly conservative one */
      for ( Size i = 0; i < n; i++ ) { /* compute centroid of all but point H -- STEP 13 */
        Coord temp = -P[H][i]; /* leave out point H by subtraction */
        for ( Size j = 0; j <= n; j++ ) {
          temp += P[j][i];
        }
        P[C][i] = temp / n; /* centroid parameter i */
      } /* end loop on i for centroid */
      for ( Size i = 0; i < n; i++ ) { /* compute reflection in Bvec -- STEP 14 */
        Bvec[i] = ( 1.0 + alpha ) * P[C][i] - alpha * P[H][i];
      }
      status = fn( n, Bvec, m, &Bvec[n], fndata, &data->fncount ); /* function value at refln point (when function is not computable, a very large value is assigned) */
      if ( exception( status ) ) break;
      action = "rfl"; /* action = reflection */
      VR = Bvec[n]; /* STEP 15: test if extension should be tried */
      if ( VR < VL ) {
        /* STEP 16: try extension */
        for ( Size i = n; i < N; i++ ) {
          P[C][i] = Bvec[i]; /* save the function value at reflection point */
        }
        for ( Size i = 0; i < n; i++ ) {
          Coord f = gamma * Bvec[i] + ( 1 - gamma ) * P[C][i];
          P[C][i] = Bvec[i]; /* save the reflection point in case we need it */
          Bvec[i] = f;
        } /* end loop on i for extension point */
        status = fn( n, Bvec, m, &Bvec[n], fndata, &data->fncount ); /* function calculation */
        if ( exception( status ) ) break;
        if ( Bvec[n] < VR ) { /* STEP 17: test extension */
          /* STEP 18: save extension point, replacing H */
          for ( Size i = 0; i < N; i++ ) {
            P[H][i] = Bvec[i];
          }
          action = "ext"; /* action = extension */
          /* end replace H */
        } else {
          /* STEP 19: save reflection point and function value */
          for ( Size i = 0; i < N; i++ ) {
            P[H][i] = P[C][i];
          }
        } /* end save reflection point in H; note action is still reflection */
        /* end try extension */
      } else { /* reflection point not lower than current lowest point */
        /* reduction and shrink -- STEP 20 */
        action = "hi-rd"; /* default to hi-side reduction */
        if ( VR < VH ) { /* save reflection -- then try reduction on lo-side if function value not also < VN */
          /* STEP 21: replace H with reflection point */
          for ( Size i = 0; i < N; i++) {
            P[H][i] = Bvec[i];
          }
          action = "lo-rd"; /* re-label action taken */
        } /* R replaces H so reduction on lo side */
        /* STEP 22: carry out the reduction step */
        for ( Size i = 0; i < n; i++ ) {
          Bvec[i] = ( 1 - beta ) * P[H][i] + beta * P[C][i];
        }
        status = fn( n, Bvec, m, &Bvec[n], fndata, &data->fncount ); /* function calculation */
        if ( exception( status ) ) break;
        /* STEP 23: test reduction point */
        if ( Bvec[n] < P[H][n] ) { /* replace H -- may be old R in this case, so we do not use VH in this comparison */
          /* STEP 24: save new point and its function value, which may now not be the highest in polytope */
          for ( Size i = 0; i < N; i++ ) {
            P[H][i] = Bvec[i];
          }
          /* end replace H */
        } else { /* not a new point during reduction */
          /* STEP 25: test for failure of all tactics so far to reduce the function value. Note that this cannot be an "else" statement from the "if VR < VH" since we have used that statement in STEP 21 to save the reflection point as a prelude to lo-reduction, which has failed to reduce the function value. */
          if ( VR >= VH ) { /* hi-reduction has failed to find a point lower than H, and reflection point was also higher */
            /* STEP 26: shrink polytope toward point L */
            calcvert = True; /* must recalculate the vertices after this */
            size = 0;
            for ( Size j = 0; j <= n; j++ ) {
              if ( j != L ) { /* ignore the low vertex */
                for ( Size i = 0; i < n; i++ ) {
                  P[j][i] = beta * ( P[j][i] - P[L][i] ) + P[L][i]; /* note the form of expression used to avoid rounding errors */
                  size+=fabs( P[j][i] - P[L][i] );
                } /* end loop on i */
              } /* end if j != L */
            } /* end loop on j */
            if ( ( oldsize > 0 ) && ( size / oldsize < 0.99999 ) ) { /* STEP 27 -- test if shrink reduced size */
            /* if (size < oldsize) { ... may cause infinite loop */
              action = "shr";
              shrinkfail = False; /* restart after shrink */
              oldsize = size;
            } else { /* shrink failed -- polytope has not shrunk */
              /* STEP 28 -- exit on failure */
              action = "shr-f";
              shrinkfail = True;
              /* end shink failed */
            } /* end if size */
          } /* end if VR >= VH -- shrink */
        } /* end if f < P[H][n] */
      } /* VR < VL */
    } /* end if VH > VL+convtol */
    /* STEP 29 -- end of major cycle of method */
  } while ( True );
  /* STEP 30: if progress made, or polytope shrunk successfully, try another major cycle from STEP 10 */
  /* end minimization */
  /* STEP 31: save best parameters and function value found */
  for ( Size i = n; i < N; i++ ) {
    Fmin[i-n] = P[L][i]; /* save best value found */
  }
  for ( Size i = 0; i < n; i++ ) {
    X[i] = P[L][i];
  }
  /* STEP 32: exit */
  if ( !status ) {
    /* mod: compute function at minimum */
    action = "end";
    status = fn( n, X, m, f, fndata, &data->fncount );
    if ( exception( status ) ) {
      status = fail;
      if ( data->log != NULL ) {
        MessageFormatBegin( fmt1, data->log, data->iter, action, data->fncount );
        for ( Size i = 0; i < n; i++ ) {
          MessageFormatPrint( fmt2, X[i] );
        }
        for ( Size i = 1; i < m; i++ ) {
          MessageFormatPrint( fmt2, Fmin[i] );
        }
        MessageFormatEnd( fmt3, -Fmin[0] );
      }
    }
  }
  return status;

}
