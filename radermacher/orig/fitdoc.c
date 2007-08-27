
/*$Header: /ami/sw/cvsroot/radermacher/orig/fitdoc.c,v 1.1.1.1 2007-08-27 17:35:52 vossman Exp $*/

/*
C++*************************************************************************
C
C    fitdoc
C
C **********************************************************************
 C=* FROM: WEB - VISUALIZER FOR SPIDER MODULAR IMAGE PROCESSING SYSTEM *
 C=* Copyright (C) 1992-2005  Health Research Inc.                     *
 C=*                                                                   *
 C=* HEALTH RESEARCH INCORPORATED (HRI),                               *   
 C=* ONE UNIVERSITY PLACE, RENSSELAER, NY 12144-3455.                  *
 C=*                                                                   *
 C=* Email:  spider@wadsworth.org                                      *
 C=*                                                                   *
 C=* This program is free software; you can redistribute it and/or     *
 C=* modify it under the terms of the GNU General Public License as    *
 C=* published by the Free Software Foundation; either version 2 of    *
 C=* the License, or (at your option) any later version.               *
 C=*                                                                   *
 C=* This program is distributed in the hope that it will be useful,   *
 C=* but WITHOUT ANY WARRANTY; without even the implied warranty of    *
 C=* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU *
 C=* General Public License for more details.                          *
 C=*                                                                   *
 C=* You should have received a copy of the GNU General Public License *
 C=* along with this program; if not, write to the                     *
 C=* Free Software Foundation, Inc.,                                   *
 C=* 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.     *
 C=*                                                                   *
C **********************************************************************
C
C    fitdoc
C
C    PURPOSE:    input untilted point locations from doc file dfil1
C                input   tilted point locations from doc file dfil2
C                input tilt parameters from doc file dfil3 (if present)
C
C    VARIABLES:  xim       image  number             dfil1 + 2
C                xu0,yu0   untilted picked points    dfil1
C                xs,ys     tilted picked points      dfil2
C                xs2,ys2   tilted predicted points   dfil6
C 
C                dfil1  = untilted
C                dfil2  = tilted points
C                dfil3  = tilt parameters
C                dfil4  = background               (pickback)
C                dfil4  = background               (pickback)
C                dfil6  = tilted predicted points 
C
C    RETURNS:    0 if all OK
C               -1 if no untilted doc file
C               -2 if no   tilted doc file
C                1 if unrecoverable error reading or allocating
C                  or some other disaster
C
C    CALLED BY:  
C
C **********************************************************************
*/

#include "std.h"
#include "x.h"
#include "routines.h"

 /* external global variables */
 extern char   dfil1[12], dfil2[12], dfil3[12];
 extern int    numm, numb, iredu;
 extern int    fitted;
 extern float  phif, thetaf, gammaff;
 extern float  xu0t, yu0t, xs0t, ys0t;
 extern char   datexc[4];         /* file extension  */

 /* variables used elsewhere also */
 int           limfit, lbnum, ifit, maxtilts, maxpart;
 float        * xu0  = 0, * yu0  = 0, * xs   = 0, * ys   = 0;
 float        * xs2  = 0, * ys2  = 0, * xim  = 0;
      
 /********************   fitdoc   ****************************/

 int fitdoc(int unused)

 { 
 int      k, maxreg, maxkeys, maxpartt;
 static   nptsnow = 0;
 float  * dbuf = NULL, * ptr;
 
 /* set size for array pointed to by dbuf */
 maxreg    = 6+1; maxkeys   = 9999;

 /* retrieve data from dfil1 for untilted points */
 
 if (getdoc((FILE *) NULL, dfil1, datexc,maxkeys, maxreg, 
           &dbuf, &maxpart) > 0) 
    {   /* problem retrieving doc file, assume it does not exist */
    if (dbuf) free(dbuf); dbuf = NULL;
    spouts("*** Unable to read untilted doc. file: "); spout(dfil1); 
    maxpart = 0;
    return -1;
    }

 if ((xim == NULL) || (maxpart > nptsnow))
    {
    /* allocate space for  arrays */
   if (((xim = (float *) realloc((void *) xim, maxpart * sizeof(float))) == 
               (float *) NULL) ||
       ((xu0 = (float *) realloc((void *) xu0, maxpart * sizeof(float))) == 
               (float *) NULL) ||
       ((yu0 = (float *) realloc((void *) yu0, maxpart * sizeof(float))) ==  
               (float *) NULL) ||
       ((xs =  (float *) realloc((void *) xs,  maxpart * sizeof(float))) == 
               (float *) NULL) ||
       ((ys =  (float *) realloc((void *) ys,  maxpart * sizeof(float))) == 
               (float *) NULL) ||
       ((xs2 = (float *) realloc((void *) xs2, maxpart * sizeof(float))) == 
               (float *) NULL) ||
       ((ys2 = (float *) realloc((void *) ys2, maxpart * sizeof(float))) == 
               (float *) NULL))
      { spout("*** Unable to reallocate memory in fitdoc."); return 1; }
    }
 nptsnow = maxpart;

 ptr = dbuf;
 for (k=0; k<maxpart ; k++)
    {
    xim[k]  = *(ptr+1);  xu0[k]  = *(ptr+4);
    yu0[k]  = *(ptr+5);  ptr  += maxreg; 
    }

 /* retrieve data from dfil2 for tilted points */
  if (getdoc((FILE *) NULL, dfil2, datexc,maxkeys, maxreg, 
           &dbuf, &maxpartt) > 0) 
    {   /* problem retrieving doc file, assume it does not exist */
    if (dbuf) free(dbuf); dbuf = NULL;
    spouts("*** Unable to read tilted doc. file: ");spout(dfil2); 
    maxpart = 0;
    return -2;
    }

 if (maxpartt < maxpart)
    {
    /* Tilted file has more points than first! */  
    if (dbuf) free(dbuf); dbuf = NULL;
    spout("*** Tilted file has fewer particles than untilted.");
    maxpart = 0;
    return 1;
    }

 if (maxpartt > maxpart)
    {
    /* Tilted file has more points than first! */  
    if (dbuf) free(dbuf); dbuf = NULL;
    spout("*** Tilted file has more particles than untilted.");
    maxpart = 0;
    return 1;
    }
 
 ptr = dbuf;
 for (k=0; k < maxpart ; k++)
    { xs[k]  = *(ptr+4); ys[k]  = *(ptr+5);  ptr  += maxreg; }

 /* free dbuf here*/
 if (dbuf) free(dbuf); dbuf = NULL;


 /* retrieve data from dfil3 for tilt parameters (if any) */
 /* (x,y) coordinates of origin and tilt angles delta, phi ,gamma */
 
 maxreg  = 6+1;  maxkeys = 125;
     
  /* read the maxpart from dcb*** file */
  if (getdoc((FILE *) NULL, dfil3, datexc, maxkeys, maxreg, 
           &dbuf, &maxtilts) > 1) 
    {   /* problem retrieving doc file, assume it does not exist */
    if (dbuf) free(dbuf); dbuf = NULL;
    spouts("*** Tilt angle doc. file not available yet: "); spout(dfil3);
    return 0;
    }

  if (maxtilts < 124)
     {
     spout(" Tilt angle doc. file lacks necessary info.");
     if (dbuf) free(dbuf); dbuf = NULL;
     return 1;
     }

  /*get last particle number */
  ptr    = dbuf + ((121-1) * maxreg);
  limfit = *(ptr+5);   /* number of markers used in fitting */
  lbnum  = *(ptr+6);   /* used for pickback */
  numb = lbnum;        /* used for pickback */

  /* get fitted flag  */
  ptr    = dbuf + ((122-1) * maxreg);
  fitted = *(ptr+1);

  /* get origin */
  ptr    = dbuf + ((123-1) * maxreg);
  xu0t   = *(ptr+1);
  yu0t   = *(ptr+2);
  xs0t   = *(ptr+3);
  ys0t   = *(ptr+4);
  iredu  = *(ptr+5);

  /* get tilt angles */
  ptr      = dbuf + ((124-1) * maxreg);
  thetaf   = *(ptr+1);
  gammaff  = *(ptr+2);
  phif     = *(ptr+3);
	      
  /* free dbuf here */
  if (dbuf) free(dbuf);  dbuf = NULL;

 return 0;
 }


