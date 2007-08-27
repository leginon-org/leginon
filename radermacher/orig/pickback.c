
/*$Header: /ami/sw/cvsroot/radermacher/orig/pickback.c,v 1.1.1.1 2007-08-27 17:35:52 vossman Exp $*/

/*
 ***********************************************************************
 *
 * pickback.c
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
 * PURPOSE:     Interactive tilt-pair background selecting      
 * 
 * PARAMETERS:	 
 *
 * VARIABLES:   
 *
 ***********************************************************************
*/

#include "common.h"
#include "routines.h"

 /* internal functions */
 void           pickback_pop (Widget, XEvent *, String *, Cardinal *);
          
 /* externally defined file global variables */
 extern int         nsam1l,nrow1l,nsam2l,nrow2l;
 extern int         nsam1r,nrow1r,nsam2r,nrow2r;
 extern int         ixull,iyull,ixulr,iyulr;
 extern char        dfil4[12], dfil5[12];
 extern int         ixulli,iyulli,ixulri,iyulri;
 extern int         ixulw,iyulw,nsamw,nroww;
 extern int         iredu;          /* image reduction factor  */
 extern int         fitted, lbnum;
 extern float       phif, thetaf, gammaff;
 extern FILEDATA*   filedatal;
 extern FILEDATA*   filedatar;
 extern int         firstback;
 extern GC          icontxor;
 extern             int maxpart;

 /* internal file scope  variables */
 static int         gotright = FALSE;
 static int         nsamsl, nrowsl, nsamsr, nrowsr;
 static int         maxbox = 0;     /* max. box  in doc file   */
 static int         left  = TRUE;   /* start with left image   */
 static int         openitl, openitr;

 /* global variables */
 int                numb;           /* current window number   */
 FILE    *          fpdoc4, *fpdoc5;

 /***********************  pick  ***********************************/

 void pickback(int firstrun)

 {
 openitl = firstrun;
 openitr = firstrun;
 firstback = FALSE;

 /* find displayed size of both images */
 nsamsl = nsam2l - nsam1l + 1;
 nsamsr = nsam2r - nsam1r + 1;
 nrowsl = nrow2l - nrow1l + 1;
 nrowsr = nrow2r - nrow1r + 1;

 gotright = FALSE;
 left     = TRUE;

 /* open a message window with the following strings  */
 showbutx("Select left background window.", 
          "Menu.", 
          " ", FALSE);


 /* set the actions for right, left, and center buttons */
 actions(iw_win, "pickback_pop", pickback_pop,"M123");
 }

 /************************* pickback_pop **************************/

 void pickback_pop(Widget iw_t, XEvent *event, String *params,
               Cardinal *num_params)
 {
 int           ixr,iyr, ixs, iys, ixt, iyt;
 static int    ixp, iyp;
 char          outstr[60];
 float         dlist[8];
 float         xt,yt,  fx,fy, aver;

 if (!(strcmp(*params, "M")))
   {  /****************************************** mouse movement only */
   getloc(event,'m',&ixs,&iys);
   if (left && 
       (ixs < ixull || ixs >= ixull + nsamsl || 
        iys < iyull || iys >= iyull + nrowsl ))
       {    /* cursor outside of displayed left image */
       spouto("*** Not in left image.");
       }

    else if (!left &&
       (ixs < ixulr || ixs >= ixulr + nsamsr || 
        iys < iyulr || iys >= iyulr + nrowsr ))
       {    /* cursor outside displayed right image */
       spouto("*** Not in right image.");
       }
    else
       spouto("                        ");

    /* draw xor box */
    xorbox(iwin,    icontxor, FALSE, ixs, iys, nsamw, nroww);
    xorbox(imagsav, icontxor, FALSE, ixs, iys, nsamw, nroww); 
    } 

 /********************************************************left button */ 

 else if (left && !(strcmp(*params, "1")))
   {   /*  in left image -- button 1 pushed */
    getloc(event,'B',&ixs,&iys);

    /* find location inside whole left image */
    ixulw    = ixs - ixulli + 1;
    iyulw    = iys - iyulli + 1;

   if (ixs < ixull || ixs >= ixull + nsamsl || 
       iys < iyull || iys >= iyull + nrowsl )
       {       /* cursor is outside displayed left image, want inside */
       spouto("*** Not in left image.");
       }

    else 
       {   /* want to record left background window location */
       numb++;
       spoutfile(TRUE);
       sprintf(outstr,"Left window: %d (%d,%d)",numb,ixulw,iyulw);
       spout(outstr);
       spoutfile(FALSE);

       /* leave permanent box at this location  */
       xorbox(iwin,    icontxor, TRUE, ixs, iys, nsamw, nroww); 
       xorbox(imagsav, icontxor, TRUE, ixs, iys, nsamw, nroww);  

       /* find average within window */
       rcaver(filedatal, nsaml, nrowl, nsamw, nroww, 
              ixulw, iyulw,  &aver);

       /* save info in doc file */        
       dlist[0] = numb;
       dlist[1] = aver;
       dlist[2] = ixulw * iredu;
       dlist[3] = iyulw * iredu;
       dlist[4] = nsamw;
       dlist[5] = nroww;       
       dlist[6] = 1.0;       
       fpdoc4   = savdn1(dfil4, datexc, &fpdoc4,
                         dlist, 7, &openitl, TRUE, TRUE);

       /* find predicted location in right image */
       if (fitted)
          {
          /* transform the values */
          fx = (float)ixulw;
          fy = (float)iyulw;

          /* use angles to get predicted location in tilted image */
          witran(&fx, &fy,  &xt, &yt, 1, gammaff, thetaf, phif);

          ixt = xt;
          iyt = yt;

          if ((ixt < 1 || ixt > ixulr + nsamsr ||
               iyt < 1 || iyt > iyulr + nrowsr))
             {    /* predicted  loc. is outside of right image, */
             sprintf(outstr,"*** Tilted not in right image: (%d,%d)",
                             ixt,iyt);
             spout(outstr);
             }
          else
             {   /* warp cursor to predicted location on tilted side */
             ixr = ixt + ixulri;
             iyr = iyt + iyulri;

             movecur(ixr-ixs,iyr-iys);

             /* draw box at this location */
             xorbox(iwin,    icontxor, FALSE, ixr, iyr, nsamw, nroww);
             xorbox(imagsav, icontxor, FALSE, ixr, iyr, nsamw, nroww); 
             }
          }
       else
          { /* no tilt angle available yet */
          /* warp cursor to center of tilted side */
          ixt = ixulr + nsamsr / 2;
          iyt = iyulr + nrowsr / 2;

          movecur(ixt-ixs,iyt-iys);

          /* draw box at this location  */
          xorbox(iwin,    icontxor, TRUE, ixt, iyt, nsamw, nroww);
          xorbox(imagsav, icontxor, TRUE, ixt, iyt, nsamw, nroww);
          } 

       left     = FALSE;
       gotright = FALSE;
       if (numb > maxbox) maxbox = numb;

       /*  remove message */
       showbutx("","","",TRUE);

       /* open a message window with the following strings  */
       showbutx("Select right background window.", 
                "Menu.", 
                "Reselect left window.", FALSE);

       /* record undo location */
       ixp  = ixs;
       iyp  = iys;
       }
    }

 else if (!(strcmp(*params, "1")))
    {                          /*  in right image -- button 1 pushed */
    getloc(event,'B',&ixs,&iys);

    /* find location inside whole right image */
    ixulw    = ixs - ixulri + 1;
    iyulw    = iys - iyulri + 1; 

    if (ixs < ixulr || ixs >= ixulr + nsamsr || 
        iys < iyulr || iys >= iyulr + nrowsr )
       {    /* cursor outside of displayed right image, want inside */
       spouto("*** Not in right image.");
       }

    else 
       {   /* want to record this location */
       spoutfile(TRUE);
       sprintf(outstr,"Right window:%d  (%d,%d)",numb,ixulw,iyulw);
       spout(outstr);
       spoutfile(FALSE);

       /* leave permanent box at this location 
       xorbox(iwin,    icontxor, TRUE, ixs, iys, nsamw, nroww);
       xorbox(imagsav, icontxor, TRUE, ixs, iys, nsamw, nroww);  */

       /* find average within window */
       rcaver(filedatar, nsamr, nrowr, nsamw, nroww,
              ixulw, iyulw,  &aver);


       /* save info in doc file */ 
       dlist[0] = numb;
       dlist[1] = aver;
       dlist[2] = ixulw * iredu;
       dlist[3] = iyulw * iredu;
       dlist[4] = nsamw;
       dlist[5] = nroww;       
       dlist[6] = 1.0;       
       fpdoc5   = savdn1(dfil5, datexc, &fpdoc5,
                         dlist, 7, &openitr, TRUE, TRUE);

       /*  remove message */
       showbutx("","","",TRUE);

       /* open a message window with the following strings  */
       showbutx("Select left background window.", 
                "Menu.", 
                "Reselect right window.", FALSE);

       left     = TRUE;
       gotright = TRUE;
       if (numb > maxbox) maxbox = numb;

       /* warp cursor to last position of untilted side */
        movecur(ixp-ixs,iyp-iys);

       /* record undo location */
       ixp  = ixs;
       iyp  = iys;

       /* draw box at previous location on left side */  
       xorbox(iwin,    icontxor, TRUE, ixp, iyp, nsamw, nroww);
       xorbox(imagsav, icontxor, TRUE, ixp, iyp, nsamw, nroww); 
       }
    }

 /***************************************************** middle button */ 

 else if (!(strcmp(*params, "2")))
    {                          /* show menu --       button 2 pushed */
    lbnum = numb;
    fitsav(maxpart);

    pickbackmen();
    }

 /****************************************************** right button */ 

 else if (!left && !(strcmp(*params, "3")))

    {                          /*  in right image -- button 3 pushed */
    getloc(event,'B',&ixs,&iys);

    /* warp cursor back to left image location */
    spout("Moving cursor back to left");
    movecur(ixp-ixs, iyp-iys);
 
    /* draw box at previous location on  other side  */ 
    xorbox(iwin,    icontxor, FALSE, ixp, iyp, nsamw, nroww);
    xorbox(imagsav, icontxor, FALSE, ixp, iyp, nsamw, nroww); 

    numb--;
   left = TRUE;
    ixp = ixs; iyp = iys;
    }

 else if (!(strcmp(*params, "3")))
    {                          /*  in left image -- button 3 pushed */
    /* warp cursor back to previous right position */
    spout("Moving cursor back to right");

    if (gotright) 
       {
       getloc(event,'B',&ixs,&iys);
       left = FALSE;

       movecur(ixp-ixs, iyp-iys);
       /* draw box at previous location on  other side */ 
       xorbox(iwin,    icontxor, FALSE, ixp, iyp, nsamw, nroww);
       xorbox(imagsav, icontxor, FALSE, ixp, iyp, nsamw, nroww); 
       ixp  = ixs; iyp = iys;
       }
    }             
 }
