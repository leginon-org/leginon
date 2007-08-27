
/*$Header: /ami/sw/cvsroot/radermacher/orig/pickmen.c,v 1.1.1.1 2007-08-27 17:35:52 vossman Exp $*/

/*
C++********************************************************************
C
C  pickmen.c          May 93 al
C
C *********************************************************************
C    AUTHOR:  ArDean Leith                                            *
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
C *********************************************************************
C
C    PICKMEN()
C
C    PURPOSE:    displays particle picking selecting menu
C
C    PARAMETERS: none   
C
C    CALLed BY:  pickpop 
C
C    CALL TREE:
  
 imagemen --> imagemen_cb --> imagemen1 --> showimag --> redvol
                                                            v   
 showimage <-- imagemen1 <-- imagemen_cb <-- imagemen <--  wipic 
    |
  redvol
    |                 | _buta  -->
  wipic               |
    |                 | _butsh --> shift --> pickp
 fitdocmen            |
 fitdocmen_buta       | _butel --> backmen
    |                 |
 fitdoc ->unsdal      | _buter --> backmen
    |                 |
 pickp                | _butcl --> pickdisp
    |                 |
 pickpop -> pickmen --| _butl  --> fitdoc --> unsdal 
                      |              v          
                      |            pickdraw                  
                      |              ^                       pickbackmen 
                      | _butn  --> fitdoc ---> unsdal        rcaver 
                      |                                      |
                      |                                      _pop
                      |                                      |
                      | _butb  --> pickbackmen --> _buts --> pickbacksave
                      |              |
                      |              `-----------> _buta --> pickback
                      |
                      |
                      | fitorigin
                           |
                        fitorigin_buta
                           |
                        fitdoc     |_butfit   --> willsq -> fitmen
                           |       |
                           |       |_buttilt  --> tiltang -> fitmen
                        fitmen --->|
                                   |_butdraw2 --> fitdoc
                                   |              witran
                                   |              pickdraw -> fitmen 
                                   |
                                   |_fitbutsavang --> fitsav
                                                      
                                   


C--*********************************************************************
*/

#include "common.h"
#include "routines.h"

#include <Xm/ToggleBG.h>
#include <Xm/Text.h>

 /* internal function prototypes */
 void          pickmen_buts (Widget, XtPointer, XtPointer);
 void          pickmen_buta (Widget, XtPointer, XtPointer);
 void          pickmen_butm (Widget, XtPointer, XtPointer);
 void          pickmen_butsh(Widget, XtPointer, XtPointer);
 void          pickmen_butl (Widget, XtPointer, XtPointer);
 void          pickmen_butn (Widget, XtPointer, XtPointer);
 void          pickmen_butcl(Widget, XtPointer, XtPointer);
 void          pickmen_butel(Widget, XtPointer, XtPointer);
 void          pickmen_buter(Widget, XtPointer, XtPointer);
 void          pickmen_butb (Widget, XtPointer, XtPointer);
  
 /* externally defined global variables */
 extern int       irad, numm, maxpart;
 extern float     * xim, * xu0, * yu0, * xs,  * ys, * xs2, * ys2;
 extern FILEDATA  * filedatal;
 extern FILEDATA  * filedatar;

 /* internally defined global variables */
 Widget iw_pickmen = (Widget)0;       /* used in pickp_pop */
 
 /* internal file scope variables */
 static Widget iw_parkey, iw_ximoff;
 int           ximoff = 0;

 /***********************   pickmen   ********************************/

 void pickmen(void)

 {
 static  Widget  iw_rowcolh;
 Widget  iw_pushs, iw_pushc, iw_pusha; 
 Widget  iw_rowcolv;

 char    cval[10];


 if (iw_pickmen == (Widget)0)
    {   /* create  picking menu first */

    iw_pickmen = wid_dialog(iw_win, 0, "Particle picking menu", -1, -1);
    iw_rowcolv = wid_rowcol(iw_pickmen, 'v', -1, -1);

    iw_rowcolh = wid_rowcol(iw_rowcolv, 'h', -1, -1);

    /* create text box for particle key  */
    if ( numm == 0 ) numm = 1;  /* initialize to 1  */
    sprintf(cval,"%4d",numm);
    iw_parkey   = wid_textboxb(iw_rowcolh,0,"Key number:",cval,4);

    /* create text box for ximoff  */
    sprintf(cval,"%4d",ximoff);
    iw_ximoff   = wid_textboxb(iw_rowcolh,0,"Offset:",cval,4);

    /* create pushbutton for fitting angles */
    wid_pushg(iw_rowcolv, 0, "Fit angles",
                  fitorigin, NULL, -1,-1);

    /* create pushbutton for shifting image */
    wid_pushg(iw_rowcolv, 0, "Shift image",
                  pickmen_butsh, NULL, -1,-1);

    /* create pushbutton for enhancing left image */
    wid_pushg(iw_rowcolv, 0, "Enhance left",
                  pickmen_butel, NULL, -1,-1);

    /* create pushbutton for enhancing right image */
    wid_pushg(iw_rowcolv, 0, "Enhance right",
                  pickmen_buter, NULL, -1,-1);

    /* create pushbutton for backgrounding images */
                  wid_pushg(iw_rowcolv, 0, "Backgrounding",
                  pickmen_butb, NULL, -1,-1);

    /* create pushbutton for erasing locations and numbers */
    wid_pushg(iw_rowcolv, 0, "Erase notations",
                  pickmen_butcl, NULL, -1,-1);

     wid_pushg(iw_rowcolv, 0, "Show particle locations",
                  pickmen_butl, NULL, -1,-1);

     wid_pushg(iw_rowcolv, 0, "Show particle numbers",
                  pickmen_butn, NULL, -1,-1);

    /* create box for apply  */
    wid_stdbut(iw_rowcolv, iw_pickmen, 
               &iw_pushs, &iw_pushc, &iw_pusha, "SCA",
               pickmen_buts, fin_cb ,pickmen_buta, NULL);
 
    }

 else
    {
    /* create text box for particle key  */
    sprintf(cval,"%4d",numm);
    iw_parkey = wid_textboxb(iw_rowcolh,iw_parkey,"Key number:",cval,4);
    }

 XtManageChild(iw_pickmen);
 }



/*********** accept button callback **********************************/

 void pickmen_buta(Widget iw_temp, XtPointer data, XtPointer calldata)
 {

 char * string = NULL;

 /* find particle key */
 string = XmTextGetString(iw_parkey);
 sscanf(string,"%d",&numm);
 if(string) free(string);

 /* find ximoff  */
 string = XmTextGetString(iw_ximoff);
 sscanf(string,"%d",&ximoff);
 if(string) free(string);

 if (numm < 1) 
    { spout("*** Key number must be > 0"); return; }

 if (ximoff < 0) 
    { spout("*** Offset must be >= 0"); return; }


 /*  remove  pickmen menu */
 XtUnmanageChild(iw_pickmen);
}

/************ erase button callback **********************************/

 void pickmen_butcl(Widget iw_temp, XtPointer data, XtPointer calldata)
 {

 /*  remove  pickmen menu */
 XtUnmanageChild(iw_pickmen);

 /* redisplay original images at current shifted location */
 pickdisp(TRUE,TRUE);

 /*  replace  pickmen menu */
 XtManageChild(iw_pickmen);
 }

/************ shift button callback **********************************/

 void pickmen_butsh(Widget iw_temp, XtPointer data, XtPointer calldata)
 {

 /*  remove message */
 showbutx("","","",TRUE);

 /*  remove the menu widget */
 XtUnmanageChild(iw_pickmen);

 /*  cancel buttons */
 XtUninstallTranslations(iw_win);

 /* shift the image using mouse for input */
 shift(TRUE);

 }

/************ background picking callback ****************************/

 void pickmen_butb(Widget iw_temp, XtPointer data, XtPointer calldata)
 {
 /*  remove message */
 showbutx("","","",TRUE);

 /*  remove the menu widget */
 XtUnmanageChild(iw_pickmen);

 /*  cancel buttons */
 XtUninstallTranslations(iw_win);

 /* pick background windows using mouse for input, first display menu */
 pickbackmen();
 }

/*************  draw particle callback *********************************/

 void pickmen_butn(Widget iw_temp, XtPointer data, XtPointer calldata)
 {
 /* retrieve tilted and untilted points, & fit angles */
 fitdoc(FALSE);

 /* draw */
 pickdraw(TRUE, TRUE, FALSE, TRUE, FALSE, maxpart);
 }


/***********  draw locations callback *********************************/

 void pickmen_butl(Widget iw_temp, XtPointer data, XtPointer alldata)
 {
 /* retrieve tilted and untilted points, & fit angles */
 fitdoc(FALSE);

 /* draw */
 pickdraw(TRUE, TRUE, TRUE, FALSE, FALSE, maxpart);
 }

/*************  enhance left callback *********************************/

 void pickmen_butel(Widget iw_temp, XtPointer data, XtPointer calldata)
 {
 backmen(TRUE);
 }

/*************  enhance right callback *********************************/

 void pickmen_buter(Widget iw_temp, XtPointer data, XtPointer calldata)
 {
 backmen(FALSE);
 }

/************* stop button callback **********************************/

 void pickmen_buts(Widget iw_temp, XtPointer data, XtPointer calldata )
 {

 /*  remove message */
 showbutx("","","",TRUE);

 /*  remove the menu widget */
 XtUnmanageChild(iw_pickmen);

 /*  cancel buttons,  stop this routine */
 XtUninstallTranslations(iw_win);

 /*  restore default cursor */
 setacursor(0,-1,-1);

 /* deallocate array storage */ 
 if (xim  != (float *)NULL) {free(xim);  xim = (float *) NULL;}
 if (xu0  != (float *)NULL) {free(xu0);  xu0 = (float *) NULL;}
 if (yu0  != (float *)NULL) {free(yu0);  yu0 = (float *) NULL;}
 if (xs   != (float *)NULL) {free(xs);    xs = (float *) NULL;}
 if (ys   != (float *)NULL) {free(ys);    ys = (float *) NULL;}
 if (xs2  != (float *)NULL) {free(xs2);  xs2 = (float *) NULL;}
 if (ys2  != (float *)NULL) {free(ys2);  ys2 = (float *) NULL;}

 /* stop recording output in results file */
 spoutfile(FALSE);

 closefile(filedatal); filedatal = NULL;
 closefile(filedatar); filedatar = NULL;
 }
