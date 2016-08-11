/*----------------------------------------------------------------------------*
*
*  guigtk.h  -  guigtk: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef guigtk_h_
#define guigtk_h_

#include "guigtkdefs.h"
#include <gtk/gtk.h>
#include <gtk/gtkgl.h>
#include <gdk/gdkgl.h>

#define GuigtkName   "guigtk"
#define GuigtkVers   GUIVERS"."GUIBUILD
#define GuigtkCopy   GUICOPY


/* exception codes */

enum {
  E_GUIGTK = GuigtkModuleCode,
  E_GUIGTK_INIT,
  E_GUIGTK_GLINIT,
  E_GUIGTK_VISUAL,
  E_GUIGTK_GLCAP,
  E_GUIGTK_GLDRAW,
  E_GUIGTK_MAXCODE
};


/* data structures */

typedef struct {
  GdkGLConfig *config;
  GdkGLContext *context;
  GdkGLDrawable *drawable;
  GtkWidget *widget;
  Size viewport[2];
} GuigtkArea;


/* variables */

extern Bool GuigtkLog;


/* prototypes */

extern Status GuigtkInit();

extern GuigtkArea *GuigtkAreaCreate
                   (const Size viewport[2]);

extern GuigtkArea *GuigtkAreaDestroy
                   (GuigtkArea *area);

extern Status GuigtkAreaBegin
              (GuigtkArea *area);

extern void GuigtkAreaDraw
            (GuigtkArea *area);

extern void GuigtkAreaEnd
            (GuigtkArea *area);

extern void GuigtkMessage
            (Size prt,
             GtkWidget *bar,
             const char *str,
             ...);

extern void GuigtkError
            (Size prt,
             GtkWidget *bar,
             GtkWidget *dialog,
             GtkWidget *vbox);

#endif
