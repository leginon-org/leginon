/*----------------------------------------------------------------------------*
*
*  guigtkdisplaycommon.h  -  guigtk: EM image viewer
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef guigtkdisplaycommon_h_
#define guigtkdisplaycommon_h_

#include "guigtkdisplay.h"
#include "guigtk.h"
#include "graph.h"
#include "imageio.h"
#include "statistics.h"


/* constants */

#define NHISTO 256


/* data structures */

typedef enum {
  GuigtkDisplayInit = 0x001,
  GuigtkDisplaySize = 0x002,
  GuigtkDisplayDisp = 0x004,
  GuigtkDisplayHist = 0x010,
  GuigtkDisplayThrs = 0x020,
  GuigtkDisplayRnge = 0x040,
  GuigtkDisplayRead = 0x080,
  GuigtkDisplayDupl = 0x100,
  GuigtkDisplayExit = 0x200,
  GuigtkDisplayPosDisp = 0x010000,
  GuigtkDisplayPosCurr = 0x020000,
  GuigtkDisplayPosRot  = 0x040000,
  GuigtkDisplayPosOri  = 0x080000,
  GuigtkDisplayPosSqr  = 0x100000,
  GuigtkDisplayPosMem  = 0x200000,
  GuigtkDisplayPosMod  = 0x400000,
  GuigtkDisplayLog    = 0x1000000,
} GuigtkDisplayStatus;

typedef struct {
  Image dscr;
  Size len[3];
  Index low[3];
  Size size;
  void *addr;
  Bool alloc;
} GuigtkDisplayImage;

typedef struct {
  const char *name;
  Imageio *handle;
  ImageioParam iopar;
  GuigtkDisplayImage img;
  GuigtkDisplayImage dsp;
  Coord range[2];
  Coord thresh;
  Coord zoom;
  GuigtkDisplayFunc func;
  Size count;
  Coord *pos;
  Coord *rot;
  GuigtkArea *area;
  GtkWidget *top;
  GtkWidget *bar;
  char *title;
  GLenum fmt,glt;
  Coord dx, dy;
  Size z;
  gdouble mouse_x;
  gdouble mouse_y;
  GtkWidget *his;
  GdkGC *gcfore;
  GdkGC *gcback;
  GdkPixmap *hmap;
  GdkPixmap *hbot;
  GdkColor hback;
  Size histo[NHISTO];
  Size histomaxcount;
  Coord histomin, histostep;
  Size markerselect;
  Stat stat;
  GLint maxviewport[2];
  GuigtkDisplayStatus status;
} GuigtkDisplay;


/* prototypes */

extern Status GuigtkDisplayLoadImage
              (GuigtkDisplay *display,
               const Image *img,
               const void *addr);

extern Status GuigtkDisplayUnloadImage
              (GuigtkDisplay *display);

extern Status GuigtkDisplayOpen
              (const char *path,
               GuigtkDisplay *display);

extern Status GuigtkDisplayClose
              (GuigtkDisplay *display);

extern Status GuigtkDisplayTransfFile
              (const char *path,
               const Size dim,
               const Size count,
               const Coord *pos,
               const Coord *rot);

extern Status GuigtkDisplayStat
              (GuigtkDisplay *display);

extern Status GuigtkDisplayHistogram
              (GuigtkDisplay *display);

extern void GuigtkDisplaySetSize
            (GuigtkDisplay *display);

extern void GuigtkDisplayButtons
            (GuigtkDisplay *display);

extern void GuigtkDisplaySensitivity
            (GuigtkDisplay *display);

extern void GuigtkDisplayTitle
            (GuigtkDisplay *display);

extern void GuigtkDisplayDisplay
            (GuigtkDisplay *display,
             Bool clear);

extern void GuigtkDisplayMessagePos
            (GuigtkDisplay *display,
             Coord x,
             Coord y);

extern void GuigtkDisplayMessagePosz
            (GuigtkDisplay *display);

extern void GuigtkDisplayMessageZoom
            (GuigtkDisplay *display);

extern void GuigtkDisplayMessageKey
            (GuigtkDisplay *display,
             const char *msg,
             GuigtkDisplayStatus mask);

extern Bool GuigtkDisplayFinal
            (GuigtkDisplay *display);

extern void GuigtkDisplayHistogramInit
            (GuigtkDisplay *display);

extern void GuigtkDisplayHistogramDraw
            (GuigtkDisplay *display);


#endif
