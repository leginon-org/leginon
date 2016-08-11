/*----------------------------------------------------------------------------*
*
*  callbacks.c  -  guigtk: EM image viewer
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "callbacks.h"
#include "guigtkdisplaycommon.h"
#include "exception.h"
#include "interface.h"
#include "support.h"


/* macros */

#define GuigtkDisplayClr                 GuigtkMessage( False, display->bar, NULL )

#define GuigtkDisplayMsg( msg, ... )     GuigtkMessage( display->status & GuigtkDisplayLog, display->bar, msg, __VA_ARGS__, NULL )

#define GuigtkDisplayErr( msg )          GuigtkMessage( True, display->bar, msg, NULL )

#define GuigtkDisplayCallback( msg )     if ( debug ) GuigtkMessage( display->status & GuigtkDisplayLog, NULL, msg, NULL );


/* functions */

static void GuigtkDisplayErrorReport
            (GuigtkDisplay *display)

{

  if ( !ExceptionGet( False ) ) return;

  GtkWidget *dialog = create_errordialog( display );
  GtkWidget *vbox = lookup_widget( GTK_WIDGET(dialog), "errordialog_text_vbox" );

  GuigtkError( display->status & GuigtkDisplayLog, NULL, dialog, vbox );

}


/* file - open */

void
on_open_activate                       (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  GuigtkDisplayCallback( "open" );

  GtkWidget *dialog = create_filechooser( display );
  if ( dialog == NULL ) {
    GuigtkDisplayErr( "could not open file chooser" );
  } else {
    GuigtkDisplayMsg( "selecting file", NULL );
    gtk_widget_show( dialog );
  }

}


void
on_filechooser_open_button_clicked     (GtkButton       *button,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;
  Status status;

  GuigtkDisplayCallback( "filechooser" );

  GtkWidget *dialog = lookup_widget( GTK_WIDGET(button), "filechooser" );
  if ( dialog == NULL ) {
    GuigtkDisplayErr( "could not find file chooser" );
  } else {
    const char *path = gtk_file_chooser_get_filename( GTK_FILE_CHOOSER(dialog) );
    status = GuigtkDisplayOpen( path, display );
    if ( exception( status ) ) {
      GuigtkDisplayMsg( "could not open file ", path );
      GuigtkDisplayErrorReport( display );
    } else {
      GuigtkDisplayDisplay( display, True );
      GuigtkDisplayMsg( "file ", display->name, " opened" );
      display->func = GuigtkDisplayFuncMax;
      status = GuigtkDisplayLoadImage( display, &display->img.dscr, NULL );
      if ( status ) {
        GuigtkDisplayUnloadImage( display );
        GuigtkDisplayMsg( "could not initialize file ", path );
        GuigtkDisplayErrorReport( display );
      } else {
        if ( ~display->status & GuigtkDisplaySize ) {
          GuigtkDisplaySetSize( display );
          display->status |= GuigtkDisplaySize;
        }
        GuigtkDisplayButtons( display );
      }
      GuigtkDisplayDisplay( display, False );
      GuigtkDisplaySensitivity( display );
    }
    gtk_widget_destroy( dialog );
  }

}


void
on_filechooser_cancel_button_clicked   (GtkButton       *button,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  GuigtkDisplayCallback( "filechooser cancel" );

  GuigtkDisplayClr;

  gtk_widget_destroy( gtk_widget_get_toplevel( GTK_WIDGET(button) ) );

}


/* file - close */

void
on_close_activate                      (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  GuigtkDisplayCallback( "close" );

  display->status &= ~GuigtkDisplayExit;

  GuigtkDisplayFinal( display );

}


/* file - quit */

void
on_quit_activate                       (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  GuigtkDisplayCallback( "quit" );

  display->status |= GuigtkDisplayExit;

  if ( GuigtkDisplayFinal( display ) ) {
    gtk_main_quit();
  }

}


/* save */

void
on_poschooser_save_button_clicked      (GtkButton       *button,
                                        gpointer         user_data)

{
  GuigtkDisplay *display = user_data;
  Bool quit = False;
  Status status;

  GuigtkDisplayCallback( "poschooser" );

  GtkWidget *dialog = lookup_widget( GTK_WIDGET(button), "poschooser" );
  if ( dialog == NULL ) {
    GuigtkDisplayErr( "could not find position file chooser" );
  } else {
    gchar *path = gtk_file_chooser_get_filename( GTK_FILE_CHOOSER(dialog) );
    if ( path != NULL ) {
      status = GuigtkDisplayTransfFile( path, display->img.dscr.dim, display->count, display->pos, display->rot );
      if ( exception( status ) ) {
        GuigtkDisplayMsg( "could not create file ", path );
        GuigtkDisplayErrorReport( display );
      } else {
        GuigtkDisplayMsg( "file ", path, " saved" );
        display->status &= ~GuigtkDisplayPosMod;
        quit = GuigtkDisplayFinal( display );
      }
      g_free( path );
    }
    /* gtk_widget_destroy( dialog ); causes memory corruption */
    if ( quit ) gtk_main_quit();
  }
  display->status &= ~GuigtkDisplayExit;

}


void
on_poschooser_cancel_button_clicked    (GtkButton       *button,
                                        gpointer         user_data)

{
  GuigtkDisplay *display = user_data;

  GuigtkDisplayCallback( "poschooser cancel" );

  display->status &= ~GuigtkDisplayExit;
  GuigtkDisplayClr;
  gtk_widget_destroy( gtk_widget_get_toplevel( GTK_WIDGET(button) ) );

}

void
on_savedialog_save_clicked            (GtkButton       *button,
                                       gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  GuigtkDisplayCallback( "save" );

  GtkWidget *dialog = create_poschooser( display );
  if ( dialog == NULL ) {
    GuigtkDisplayErr( "could not open position file chooser" );
  } else {
    GuigtkDisplayMsg( "selecting position file", NULL );
    gtk_widget_show( dialog );
  }

  gtk_widget_destroy( gtk_widget_get_toplevel( GTK_WIDGET(button) ) );

}


void
on_savedialog_close_clicked           (GtkButton       *button,
                                       gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  GuigtkDisplayCallback( "discard" );

  gtk_widget_destroy( gtk_widget_get_toplevel( GTK_WIDGET(button) ) );

  display->status &= ~GuigtkDisplayPosMod;

  if ( GuigtkDisplayFinal( display ) ) {
    gtk_main_quit();
  }

}


void
on_savedialog_cancel_clicked          (GtkButton       *button,
                                       gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  GuigtkDisplayCallback( "cancel" );

  display->status &= ~GuigtkDisplayExit;

  gtk_widget_destroy( gtk_widget_get_toplevel( GTK_WIDGET(button) ) );

}


/* top window delete */

gboolean
on_top_delete_event                    (GtkWidget       *widget,
                                        GdkEvent        *event,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  GuigtkDisplayCallback( "top delete" );

  display->status |= GuigtkDisplayExit;

  if ( GuigtkDisplayFinal( display ) ) {
    gtk_main_quit();
  }

  return TRUE;

}


/* image - real/imag/modulus */

void
on_real_part_activate                  (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  if ( display->func != GuigtkDisplayRe ) {
    display->func = GuigtkDisplayRe;
    if ( ( display->dsp.addr != NULL ) && ( display->status & GuigtkDisplayInit ) ) {
      if ( GuigtkDisplayLoadImage( display, NULL, NULL ) ) {
        GuigtkDisplayErrorReport( display );
      } else {
        GuigtkDisplayDisplay( display, False );
      }
    }
  }

}


void
on_imaginary_part_activate             (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  if ( display->func != GuigtkDisplayIm ) {
    display->func = GuigtkDisplayIm;
    if ( ( display->dsp.addr != NULL ) && ( display->status & GuigtkDisplayInit ) ) {
      if ( GuigtkDisplayLoadImage( display, NULL, NULL ) ) {
        GuigtkDisplayErrorReport( display );
      } else {
        GuigtkDisplayDisplay( display, False );
      }
    }
  }

}


void
on_modulus_activate                    (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  if ( display->func != GuigtkDisplayAbs ) {
    display->func = GuigtkDisplayAbs;
    if ( ( display->dsp.addr != NULL ) && ( display->status & GuigtkDisplayInit ) ) {
      if ( GuigtkDisplayLoadImage( display, NULL, NULL ) ) {
        GuigtkDisplayErrorReport( display );
      } else {
        GuigtkDisplayDisplay( display, False );
      }
    }
  }

}


void
on_log_modulus_activate                (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  if ( display->func != GuigtkDisplayLogAbs ) {
    display->func = GuigtkDisplayLogAbs;
    if ( ( display->dsp.addr != NULL ) && ( display->status & GuigtkDisplayInit ) ) {
      if ( GuigtkDisplayLoadImage( display, NULL, NULL ) ) {
        GuigtkDisplayErrorReport( display );
      } else {
        GuigtkDisplayDisplay( display, False );
      }
    }
  }

}


/* view - zoom */

void
on_zoom_reset_activate                 (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  display->zoom = 1;
  GuigtkDisplayMessageZoom( display );
  gtk_widget_queue_draw( display->area->widget );

}


void
on_zoom_in_activate                    (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  display->zoom *= 2;
  GuigtkDisplayMessageZoom( display );
  gtk_widget_queue_draw( display->area->widget );

}


void
on_zoom_out_activate                   (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  display->zoom /= 2;
  GuigtkDisplayMessageZoom( display );
  gtk_widget_queue_draw( display->area->widget );

}


/* view - reset */

void
on_view_reset_activate                 (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  display->zoom = 1;
  display->dx = display->dsp.len[0] / 2;
  display->dy = display->dsp.len[1] / 2;
  if ( GuigtkDisplayLoadImage( display, NULL, NULL ) ) {
    GuigtkDisplayErrorReport( display );
  } else {
    GuigtkDisplayDisplay( display, False );
  }
  GuigtkDisplayClr;

}


/* help - about */

void
on_about_activate                      (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  GtkWidget *about = create_about( display );
  gtk_dialog_run( GTK_DIALOG(about) );
  gtk_widget_destroy( about );

}


/* error dialog */

void
on_errordialog_ok_clicked              (GtkButton       *button,
                                        gpointer         user_data)
{

  gtk_widget_destroy( gtk_widget_get_toplevel( GTK_WIDGET(button) ) );

}


/* histogram and threshold */

void
on_histogram_activate                  (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  if ( display->his != NULL ) {
    gtk_widget_destroy( display->his );
    display->his = NULL;
  }
  if ( display->dsp.addr != NULL ) {
    const gchar *label = gtk_menu_item_get_label( menuitem );
    display->status |= GuigtkDisplayHist;
    if ( *label == 'T' ) {
      display->status |= GuigtkDisplayThrs;
    } else {
      display->status &= ~GuigtkDisplayThrs;
    }
    display->his = create_histogram( display );
    if ( display->his != NULL ) {
      GuigtkDisplayHistogramInit( display );
      gtk_widget_show( display->his );
    } else {
      display->status &= ~( GuigtkDisplayHist | GuigtkDisplayThrs );
    }
  }

}


gboolean
on_histogram_delete_event              (GtkWidget       *widget,
                                        GdkEvent        *event,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  if ( display->his != NULL ) {
    gtk_widget_destroy( display->his );
    display->his = NULL;
  }
  display->status &= ~( GuigtkDisplayHist | GuigtkDisplayThrs );
  gtk_widget_queue_draw( display->area->widget );
  return TRUE;

}



/* to do */

void
on_preferences_activate                (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{

}
