/*----------------------------------------------------------------------------*
*
*  guigtkerror.c  -  guigtk: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "guigtk.h"
#include "exception.h"
#include "message.h"
#include "strings.h"
#include <stdlib.h>
#include <string.h>


/* types */

typedef struct {
  char *txt;
  Size prt;
  GtkWidget *bar;
  GtkWidget *box;
} GuigtkDisplayException;


/* functions */

static void GuigtkReport
            (Status code,
             const char *ident,
             const char *msg,
             void *data)

{
  GuigtkDisplayException *except = data;

  if ( except->txt == NULL ) {
    except->txt = strdup( msg );
  } else {
    except->txt = StringConcat( except->txt, "\n  ", msg, NULL );
  }

  if ( except->prt ) {
    Message( msg, "\n" );
  }

  if ( except->bar != NULL ) {
    GtkStatusbar *bar = GTK_STATUSBAR( except->bar );
    gtk_statusbar_pop( bar, 0 );
    gtk_statusbar_push( bar, 0, ( msg == NULL ) ? "" : msg );
    except->bar = NULL;
  }

  if ( except->box != NULL ) {
    GtkWidget *label = gtk_label_new( msg );
    gtk_widget_show( label );
    gtk_box_pack_start( GTK_BOX( except->box ), label, TRUE, TRUE, 0 );
  }

}


extern void GuigtkError
            (Size prt,
             GtkWidget *bar,
             GtkWidget *dialog,
             GtkWidget *vbox)

{
  GuigtkDisplayException except;

  if ( !ExceptionGet( False ) ) return;

  except.txt = NULL;
  except.prt = prt;
  except.bar = bar;
  except.box = ( ( dialog != NULL ) && ( vbox != NULL ) ) ? vbox : NULL;

  ExceptionReportRegister( GuigtkReport );

  ExceptionReport( &except );

  ExceptionReportRegister( NULL );

  if ( except.txt != NULL ) free( except.txt );

  if ( except.box != NULL ) {
    gtk_widget_show( dialog );
  }

}
