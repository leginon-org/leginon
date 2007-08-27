
/*$Header: /ami/sw/cvsroot/radermacher/orig/fitsav.c,v 1.1.1.1 2007-08-27 17:35:52 vossman Exp $*/

/*
C++*************************************************************************
C
C    fitsav
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
C    fitsav
C
C    PURPOSE:    saves fit angles in dfil3
C                      tilted predicted loactions in dfil6
C
C    CALLED BY:   
C
C **********************************************************************
*/

#include "std.h"
#include "common.h"
#include "x.h"
#include "routines.h"

 /* function prototypes */

 /* external variables used here */
 extern char   dfil3[12], dfil6[12];     /* doc file names     */
 extern int    iredu;                    /* current reduction */
 extern int    fitted;
 extern float  phif, thetaf, gammaff;    /* tilt angles       */
 extern float  xu0t, yu0t, xs0t, ys0t;   /* tilt origins      */
 extern float  * xu0, * yu0, * xs2, * ys2; 
 extern int    lbnum, maxpart;
 extern char   datexc[4];                /* file extension   */    
     
 /*****************************   fitsav   ****************************/

 void fitsav(int limfitt)

 { 
 float          dlist[8];
 FILE           * fpdoc;
 int            i, openit, append_flag;

 /* save fit info in doc file */ 
 dlist[0] = 121;
 dlist[1] = 0.0;
 dlist[2] = 0.0;
 dlist[3] = 0.0;
 dlist[4] = 0.0;
 dlist[5] = limfitt; 
 dlist[6] = lbnum; 
    
 /* dfil3 will be opened and closed here. */

 openit   = TRUE;  /* openit first time to get fpdoc pointer */
 fpdoc    = savdn1(dfil3, datexc, &fpdoc, dlist, 7, &openit, FALSE, TRUE);
 if (!fpdoc) 
    { /* unable to open the doc file!! */
    XBell(idispl,50); XBell(idispl,50);
    return;
    }

 /* set fitted flag */
 dlist[0] = 122;
 dlist[1] = fitted;
 dlist[2] = 0.0;
 dlist[3] = 0.0;
 dlist[4] = 0.0;
 dlist[5] = 0.0;
 dlist[6] = 0.0;
      
 fprintf(fpdoc," ; FITTED flag\n");
 fpdoc    = savdn1(dfil3, datexc, &fpdoc,dlist, 7, &openit, TRUE, TRUE);

 /* set origin */
 dlist[0] = 123;
 dlist[1] = xu0t;
 dlist[2] = yu0t;
 dlist[3] = xs0t;
 dlist[4] = ys0t;
 dlist[5] = iredu; 
 dlist[6] = 0.0;
 
 fprintf(fpdoc," ; X0,Y0 ORIG. IN 0 DEG IM., XS0,YS0 ORIG. IN TILTED IM. REDUCTION FACTOR\n");
 fpdoc    = savdn1(dfil3, datexc, &fpdoc,dlist, 7, &openit, TRUE, TRUE);

 /* set tilt angles */
 dlist[0] = 124;
 dlist[1] = thetaf;
 dlist[2] = gammaff;
 dlist[3] = phif;
 dlist[4] = 0.0;
 dlist[5] = 0.0; 
 dlist[6] = 0.0;
      
 fprintf(fpdoc," ; TILTANGLE, AXIS DIR. IN:  0 DEG IM.  THETA GAMMA PHI\n");
 fpdoc    = savdn1(dfil3, datexc, &fpdoc, dlist, 7, &openit, TRUE, TRUE);

 fclose(fpdoc); fpdoc = NULL;

 if (fitted)
    {
    openit      = TRUE; append_flag = TRUE;

    /* use angles to get predicted location in tilted image  */
    witran(xu0, yu0, xs2, ys2, maxpart, gammaff, thetaf, phif);

    dlist[6] = 1.0; 

    for ( i = 0; i < maxpart; i++)
       {
       /* save predicted right locations in doc file: dfil6 */ 
       dlist[0] = i+1;
       dlist[1] = i+1;
       dlist[2] = xs2[i] * iredu;
       dlist[3] = ys2[i] * iredu;
       dlist[4] = xs2[i];
       dlist[5] = ys2[i];       
       dlist[6] = 0.0;       
   
       fpdoc   = savdn1(dfil6, datexc, &fpdoc,
                         dlist, 7, &openit, append_flag, TRUE);
       if (i == 0) 
          { /* first time thru, will have opened file now */ 
          if (!fpdoc) 
              { /* unable to open the doc file!! */
              XBell(idispl,50); XBell(idispl,50);
              return;
              }
          append_flag = TRUE;
          }
       }
    fclose(fpdoc);
    }
 }

