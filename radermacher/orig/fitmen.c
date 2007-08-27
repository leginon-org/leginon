
/*$Header: /ami/sw/cvsroot/radermacher/orig/fitmen.c,v 1.1.1.1 2007-08-27 17:35:52 vossman Exp $*/

/*
C++************************************************************************
C
C fitmen
C              In: fit_butfit  moved Unmanage      Dec 04 ArDean Leith
C
C **********************************************************************
C *  AUTHOR:  ArDean Leith                                                 *
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
C    FITMEN
C
C    PURPOSE:         display fitmen menu
C
C    CALLED BY:       fitorigin, others.
C
C***********************************************************************
*/

#include "common.h"
#include "routines.h"
#include <Xm/Text.h>

 /* internal function prototypes */
 void          fit_buttilt  (Widget, XtPointer, XtPointer);
 void          fit_butfit   (Widget, XtPointer, XtPointer);
 void          fit_butdraw2 (Widget, XtPointer, XtPointer);
 void          fit_butsavang(Widget, XtPointer, XtPointer);

 /* external global variables */
 extern int     maxpart;
 extern  float  xu0t,  yu0t,  xs0t,  ys0t;
 extern float  * xim, * xu0, * yu0, * xs,  * ys, * xs2, * ys2; 
 extern int    fitted;
	       
 /* global variables used here & elsewhere */
 float         xorg,  yorg;
 float         phif, thetaf, gammaff;
 Widget        iw_fitmen = (Widget) 0;    /* used in pickp */

 /* file scope variables used here */
 static Widget  iw_area, iw_xorg, iw_yorg;
 static Widget  iw_phif, iw_gammaf, iw_thetaf;
 static float   arealim = 5000;

 /****************************   fitmen   ****************************/

 void fitmen(void)

 { 
 static Widget iw_rowcolv, iw_rowcolh1, iw_rowcolh2;
 Widget        iw_pushs, iw_dums; 

 char   cval[40];
 
 if (iw_fitmen == (Widget)0)
    {   /* create fit menu widget first */

    iw_fitmen  = wid_dialog(iw_win, 0, "Angle fitting menu", -1, -1);
    iw_rowcolv = wid_rowcol(iw_fitmen, 'v', -1, -1);

    /* create horizontal rowcol for origins ------------------------  */
    iw_rowcolh1  = wid_rowcol(iw_rowcolv, 'h', -1, -1);

    /* create text box for x origin -----------------------  x origin */
    sprintf(cval,"%f",xu0t);
    iw_xorg = wid_textboxb(iw_rowcolh1,0,"X origin:",cval,10);

    /* create text box for y origin -----------------------  y origin */
    sprintf(cval,"%f",yu0t);
    iw_yorg = wid_textboxb(iw_rowcolh1,0,"Y origin:",cval,10);

    /* create horizontal rowcol for angles -------------------------  */
    iw_rowcolh2  = wid_rowcol(iw_rowcolv, 'h', -1, -1);

    /* create text box for phif -------------------------------- phif */
    sprintf(cval,"%f",phif);
    iw_phif = wid_textboxb(iw_rowcolh2,0,"Phi:",cval,10);

    /* create text box for gammaf ---------------------------  gammaf */
    sprintf(cval,"%f",gammaff);
    iw_gammaf = wid_textboxb(iw_rowcolh2,0,"Gamma:",cval,10);

    /* create text box for thetaf ---------------------------  thetaf */
    sprintf(cval,"%f",thetaf);
    iw_thetaf = wid_textboxb(iw_rowcolh2,0,"Theta:",cval,10);

    /* create text box for arealim -------------------------  arealim */
    sprintf(cval,"%f",arealim);
    iw_area = wid_textboxb(iw_rowcolv,iw_area,
                           "Tiltangle area:",cval,10);

    /* create push button for tilt angle det. ------------------ tilt */
    wid_pushg(iw_rowcolv, 0, "Determine theta",
                     fit_buttilt, NULL, -1,-1);

    /* create push button for fitting angles ------------------- fit */
    wid_pushg(iw_rowcolv, 0, "Fit angles",
                     fit_butfit, NULL, -1,-1);

    /* create push button for draw points ---------------------- draw */
    wid_pushg(iw_rowcolv, 0, "Draw fitted locations",
                     fit_butdraw2, NULL, -1,-1);

    /* create push button for saving angles --------------- save ang. */
    wid_pushg(iw_rowcolv, 0, "Save angles",
                     fit_butsavang, NULL, -1,-1);

    /* create box for cancel --------------------------------- cancel */
    iw_dums = wid_stdbut(iw_rowcolv, iw_fitmen, 
                        &iw_pushs, &iw_dums, &iw_dums,  "C",
                        fin_cb,fin_cb ,fin_cb, NULL);
    }

 else
    {
    /* create text box for x origin -----------------------  x origin */
    sprintf(cval,"%f",xu0t);
    iw_xorg = wid_textboxb(iw_rowcolh1,iw_xorg,"X origin:",cval,10);

    /* create text box for y origin -----------------------  y origin */
    sprintf(cval,"%f",yu0t);
    iw_yorg = wid_textboxb(iw_rowcolh1,iw_yorg,"Y origin:",cval,10);

    /* create text box for phi --------------------------------- phif */
    sprintf(cval,"%f",phif);
    iw_phif = wid_textboxb(iw_rowcolh2,iw_phif,"Phi:",cval,10);

    /* create text box for gammaf ---------------------------  gammaf */
    sprintf(cval,"%f",gammaff);
    iw_gammaf = wid_textboxb(iw_rowcolh2,iw_gammaf,"Gamma:",cval,10);

    /* create text box for thetaf ---------------------------  thetaf */
    sprintf(cval,"%f",thetaf);
    iw_thetaf = wid_textboxb(iw_rowcolh2,iw_thetaf,"Theta:",cval,10);

    /* create text box for arealim -------------------------  arealim */
    sprintf(cval,"%f",arealim);
    iw_area = wid_textboxb(iw_rowcolv,iw_area,"Tiltangle area:",cval,10);
    }

 XtManageChild(iw_fitmen);
 }  

/****************  fitting  callback ***********************/

 void fit_butfit(Widget iw_temp, XtPointer data, XtPointer calldata)
 {
 char * string;
 char   outmes[80];
 int    iflag;

 /* remove the fitting menu so the values of angles will change */
 XtUnmanageChild(iw_fitmen);

 /* find xorg */
 string = XmTextGetString(iw_xorg);
 sscanf(string,"%f",&xu0t);
 if (string) free(string);

 /* find yorg */
 string = XmTextGetString(iw_yorg);
 sscanf(string,"%f",&yu0t);
 if (string) free(string);
    
 /* find phi */
 string = XmTextGetString(iw_phif);
 sscanf(string,"%f",&phif);
 if (string) free(string);

 /* find gammaf */
 string = XmTextGetString(iw_gammaf);
 sscanf(string,"%f",&gammaff);
 if (string) free(string);

 /* find theta */
 string = XmTextGetString(iw_thetaf);
 sscanf(string,"%f",&thetaf);
 if (string) free(string);

 /* fit the tilt angles to the selected points */
 spoutfile(TRUE);

 /* willsq returns phif, gammaff, & error flag */
 iflag = willsq(xu0, yu0, xs, ys, maxpart, thetaf, &gammaff, &phif);

 if (iflag == 0)
   {   /* willsq succeeded, fitting is OK */
   fitted = TRUE;
   sprintf(outmes,
   "Fitted Gamma: %5.2f  Phi:%5.2f Theta:%5.2f  Origin: (%7.2f,%7.2f)",
   gammaff,phif,thetaf, xs0t,ys0t);
   spout(outmes);
   }
 else
   {
   XBell(idispl,50);
   }
 spoutfile(FALSE);

 /* restart the fitting menu */
 fitmen();
 }


/***********  determine tilt callback *******************************/

 void fit_buttilt(Widget iw_temp,  XtPointer data, XtPointer calldata )
 {
 char *  string;
 int     flag;
 int     iarea;

 /* find arealim */
 string = XmTextGetString(iw_area);
 sscanf(string,"%f",&arealim);
 if (string) free(string);

 spoutfile(TRUE);

 /* determine theta tilt angle */
 flag = tiltang(xu0,yu0, xs,ys, maxpart, &thetaf, &iarea, arealim);
 if (flag > 0)
    {  
    spout("*** Warning, can not calculate tilted angle.  Try again");
    XBell(idispl,50); XBell(idispl,50);
    }
 if (flag < 0)
    { /* some bad locations accepted */ 
    XBell(idispl,50);
    }

 spoutfile(FALSE);
 XtUnmanageChild(iw_fitmen);

 fitmen();
 }

/***********  fit_butdraw2 button callback *************************/

 void fit_butdraw2(Widget iw_temp,  XtPointer data, XtPointer calldata )
 {
 if (thetaf == 0.0)
    {
    spout("*** Do not have tilt angle yet.");
    XBell(idispl,50); return;
    }

 if (! fitted)
    {
    spout("*** Do not have fit angles yet.");
    XBell(idispl,50); return;
    }

 /* first calculate fitted positions using  gamma, theta & phi */
 spoutfile(TRUE);
 witran(xu0, yu0, xs2, ys2, maxpart, gammaff, thetaf, phif);
 spoutfile(FALSE);

 /* draw fitted positions now */
 pickdraw(FALSE, FALSE, TRUE, FALSE, TRUE, maxpart);
 }

/***********  save angles callback *********************************/

 void fit_butsavang(Widget iw_temp,  XtPointer data, XtPointer calldata )
 {
 spoutfile(TRUE);
 fitsav(maxpart);
 spoutfile(FALSE);
 }


