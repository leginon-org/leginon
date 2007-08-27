
/*$Header: /ami/sw/cvsroot/radermacher/orig/pickp.c,v 1.1.1.1 2007-08-27 17:35:52 vossman Exp $*/

/*
 ***********************************************************************
 *
 * pickp.c
 *
 ***********************************************************************
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
 ***********************************************************************
 *
 * 
 * 
 * PURPOSE:     Interactive tilt-pair particle selecting      
 * 
 * PARAMETERS:	 
 *
 * VARIABLES:   xim       imaged number             dfil1 + 2
 *              xu0,yu0   untilted picked points    dfil1
 *              xs,ys     tilted picked points      dfil2
 *              xs2,ys2   tilted predicted points   
 *
 ***********************************************************************
*/

#include "std.h"
#include "x.h"
#include "common.h"
#include "routines.h"

 /* internal functions */
 void           pick_pop (Widget, XEvent *, String *, Cardinal *);

 /* external variables */
 extern XImage  * imagep;
 extern int       firstback;
 
 /* internal file scope  variables */
 int              openitl, openitr;
 int              fitted;
 static int       gotright = FALSE;
           
 /* externally defined file global variables */
 extern XImage *    imagel;
 extern XImage *    imager;
 extern int         nsaml, nrowl, nsamr, nrowr;
 extern int         nsam1l,nrow1l,nsam2l,nrow2l;
 extern int         nsam1r,nrow1r,nsam2r,nrow2r;
 extern int         ixull,iyull,ixulr,iyulr, ximoff;
 extern int         ixulli,iyulli,ixulri,iyulri;
 extern int         ixullmin,ixlrlmax,iyullmin,iylrlmax;
 extern int         ixulrmin,ixlrrmax,iyulrmin,iylrrmax;
 extern float       phif, thetaf, gammaff;
 extern Widget      iw_pickmen, iw_fitmen;


 int                nsamsl, nrowsl, nsamsr, nrowsr;
 static FILE    *   fpdoc1 = NULL, *fpdoc2 = NULL;
 int                iradi = 4;      /* marker radius           */
 int                numm  = 1;      /* current marker number   */
 extern int         maxpart;        /* max. marker in doc file */
 extern int         iredu ;         /* image reduction factor  */
 int                left  = TRUE;   /* start with left image   */
 extern char        dfil1[12], dfil2[12];

 /***********************  pick  ***********************************/

 void pickp(int firstrun)

 {
 if (firstrun)
    {
    /* set next marker to number already in doc file */
    numm = maxpart + 1;
    /* initialize the first back picking flag */
    firstback = TRUE;
    left      = TRUE;
    }

 openitl = TRUE;
 openitr = TRUE;

 /* find displayed size of both images */
 nsamsl = nsam2l - nsam1l + 1;
 nsamsr = nsam2r - nsam1r + 1;
 nrowsl = nrow2l - nrow1l + 1;
 nrowsr = nrow2r - nrow1r + 1;

 /* open a message window with the following strings  */
 if (left)
    showbutx("Select left particle.", 
             "Menu.", 
             " ", FALSE);
 else
    showbutx("Select right particle.", 
             "Menu.", 
             " ", FALSE);


 /* set the actions for right, left, and center buttons */
 actions(iw_win, "pick_pop", pick_pop,"M123");

 }


 /************************* pick_pop **************************/

 void pick_pop(Widget iw_t, XEvent *event, String *params,
               Cardinal *num_params)
 {
 int           ixr, iyr, ixi, iyi, ixs, iys;
 int           ixt, iyt;
 static int    ixp, iyp;
 char          outstr[60];
 float         dlist[8];
 float         xt,yt,  fx,fy;
 char        * string;


 if (!(strcmp(*params, "M")))
   {  /****************************************** mouse movement only */
   getloc(event,'m',&ixs,&iys);
   if (left && 
       (ixs < ixull || ixs >= ixull + nsamsl || 
        iys < iyull || iys >= iyull + nrowsl ))
       {    /* cursor is outside of displayed left image */
       spout("*** Not in left image.$");
       }

    else if (left)
       {    /* cursor inside displayed left image */
       ixi = ixs - ixulli + 1;
       iyi = iys - iyulli + 1;
       sprintf(outstr,"In left image: (%d,%d)$", ixi,iyi);
       spout(outstr);
       }

    else if (!left &&
       (ixs < ixulr || ixs >= ixulr + nsamsr || 
        iys < iyulr || iys >= iyulr + nrowsr ))
       {    /* cursor outside displayed right image */
       spout("*** Not in right image.$");
       }

    else if (!left)
       {    /* cursor inside displayed right image */
       ixi = ixs - ixulri + 1;
       iyi = iys - iyulri + 1;
       sprintf(outstr,"In right image: (%d,%d)$", ixi,iyi);
       spout(outstr);
       }
    }
    /* should add position indicator in right side window !!!!! */ 

 /********************************************************left button */ 

 else if (left && !(strcmp(*params, "1")))
   {   /*  in left image -- button 1 pushed */
    getloc(event,'B',&ixs,&iys);

    /* find location inside whole left image */
    ixi    = ixs - ixulli + 1;
    iyi    = iys - iyulli + 1;

   if (ixs < ixull || ixs >= ixull + nsamsl || 
       iys < iyull || iys >= iyull + nrowsl )
       {    /* cursor is outside displayed left image, want inside */
       spout("*** Not in left image.$"); XBell(idispl,50);
       }

    else 
       {   /* want to record this left particle location */
       spoutfile(TRUE);
       sprintf(outstr,"Left: %d  (%d,%d)",numm,ixi,iyi);
       spout(outstr);
       spoutfile(FALSE);

       /* Make sure pickmen menu is gone */
       if (iw_pickmen && XtIsManaged(iw_pickmen)) 
              XtUnmanageChild(iw_pickmen);

       if (iw_fitmen && XtIsManaged(iw_fitmen))
              XtUnmanageChild(iw_fitmen);

        /* save info in doc file */ 
       dlist[0] = numm;
       dlist[1] = numm + ximoff;
       dlist[2] = ixi * iredu;
       dlist[3] = iyi * iredu;
       dlist[4] = ixi;
       dlist[5] = iyi;       
       dlist[6] = 1.0;        
       fpdoc1   = savdn1(dfil1, datexc, &fpdoc1,
                         dlist, 7, &openitl, TRUE, TRUE);

       /* leave permanent circle at this location */
       xorc(iwin,    icontx, TRUE, ixs, iys, iradi);
       xorc(imagsav, icontx, TRUE, ixs, iys, iradi);

       /*   write marker number at this location */
       string = itoa(numm);
       witext(icontx, string, ixs, iys, 1, 0, 9, 2, FALSE);
       if(string) free(string);

       /* find predicted location in right image */
       if (fitted)
          {
          /* transform the x values */
          fx = (float)ixi;
          fy = (float)iyi;
	  
          /* use angles to get predicted location in tilted image */
          witran(&fx, &fy,  &xt, &yt, 1, gammaff, thetaf, phif);

          ixt = xt;
          iyt = yt;

          if ((ixt < 1 || ixt > nsamr ||
               iyt < 1 || iyt > nrowr))
             {    /* predicted cursor loc. is outside of right image, */
             sprintf(outstr,"*** Tilted not in right image: (%d,%d)",
                             ixt,iyt);
             spout(outstr); XBell(idispl,50);
             }
          else
             {   /* warp cursor to predicted location on tilted side */
             ixr = ixt + ixulri;
             iyr = iyt + iyulri;
             movecur(ixr-ixs,iyr-iys);
             }
          
          }
       else
          { /* no tilt angle available yet */
          /* warp cursor to center of tilted side */
          ixt = ixulr + nsamsr / 2;
          iyt = iyulr + nrowsr / 2;
          movecur(ixt-ixs,iyt-iys);
          }

       left     = FALSE;
       gotright = FALSE;
       if (numm > maxpart) maxpart = numm;

       /*  remove message */
       showbutx("","","",TRUE);

       /* open a message window with the following strings  */
       showbutx("Select right particle.", 
                "Menu.", 
                "Reselect left particle.", FALSE);

       /* record undo location */
       ixp  = ixs;
       iyp  = iys;
       }
    }

 else if (!(strcmp(*params, "1")))
    {                          /*  in right image -- button 1 pushed */
    getloc(event,'B',&ixs,&iys);

    /* find location inside whole right image */
    ixi    = ixs - ixulri + 1;
    iyi    = iys - iyulri + 1; 

    if (ixs < ixulr || ixs >= ixulr + nsamsr || 
        iys < iyulr || iys >= iyulr + nrowsr )
       {    /* cursor outside of displayed right image, want inside */
       spout("*** Not in right image.$"); XBell(idispl,50);
       }

    else 
       {   /* want to record this location */
        spoutfile(TRUE);
        sprintf(outstr,"Right:%d  (%d,%d)",numm,ixi,iyi);
        spout(outstr);
        spoutfile(FALSE);

       /* Make sure pickmen menu is gone */
       if (iw_pickmen && XtIsManaged(iw_pickmen)) 
              XtUnmanageChild(iw_pickmen);

       if (iw_fitmen && XtIsManaged(iw_fitmen))
              XtUnmanageChild(iw_fitmen);

        /* save info in doc file */ 
        dlist[0] = numm;
        dlist[1] = numm + ximoff;
        dlist[2] = ixi * iredu;
        dlist[3] = iyi * iredu;
        dlist[4] = ixi;
        dlist[5] = iyi;       
        dlist[6] = 1.0;   
	    
        fpdoc2   = savdn1(dfil2, datexc, &fpdoc2, 
                         dlist, 7, &openitr, TRUE, TRUE);

        /* leave permanent circle at this location */
        xorc(iwin,    icontx, TRUE, ixs, iys, iradi);
        xorc(imagsav, icontx, TRUE, ixs, iys, iradi);

        /*   write marker number at this location */
        string = itoa(numm);
        witext(icontx, string, ixs, iys, 1, 0, 9, 2, FALSE);
        if(string) free(string);

        /*  remove message */
        showbutx("","","",TRUE);

        /* open a message window with the following strings  */
        showbutx("Select left particle.", 
                "Menu.", 
                "Reselect right particle.", FALSE);

        left     = TRUE;
        gotright = TRUE;
        if (numm > maxpart) maxpart = numm;
        numm++;

        /* warp cursor to last position of untilted side */
        movecur(ixp-ixs,iyp-iys);

        /* record undo location */
        ixp  = ixs;
        iyp  = iys;
       }
    }

 /***************************************************** middle button */ 

 else if (!(strcmp(*params, "2")))
    {                          /* show menu --       button 2 pushed */
      if(fpdoc1) {
        fclose(fpdoc1); fpdoc1 = NULL; openitl = TRUE;  }
      if(fpdoc2) {
        fclose(fpdoc2); fpdoc2 = NULL; openitr = TRUE;  }

    /* display picking menu */
    pickmen();
    }

 /****************************************************** right button */ 

 else if (!left && !(strcmp(*params, "3")))

    {                          /*  in right image -- button 3 pushed */
    getloc(event,'B',&ixs,&iys);

    /* warp cursor back to left image location 
    spout("Moving cursor back to left");       */

    /*  remove message */
    showbutx("","","",TRUE);

    /* open a message window with the following strings  */
    showbutx("Select left particle.", 
             "Menu.", 
             " ", FALSE);
    
    movecur(ixp-ixs, iyp-iys);
    left = TRUE;
    ixp = ixs; iyp = iys;
    }

 else if (!(strcmp(*params, "3")))
    {                          /*  in left image -- button 3 pushed */
    /* warp cursor back to previous right position 
    spout("Moving cursor back to right");          */

    if (gotright) 
       {
       getloc(event,'B',&ixs,&iys);

       /*  remove message */
       showbutx("","","",TRUE);

       /* open a message window with the following strings  */
       showbutx("Select right particle.", 
              "Menu.", 
             " ", FALSE);

       numm--;
       left = FALSE;
       movecur(ixp-ixs, iyp-iys);
       ixp  = ixs; iyp = iys;
       }
    }             
 }
