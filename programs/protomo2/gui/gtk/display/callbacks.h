/*----------------------------------------------------------------------------*
*
*  callbacks.h  -  EM image viewer - callbacks
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "guigtkdisplay.h"
#include <gtk/gtk.h>


gboolean
on_top_delete_event                    (GtkWidget       *widget,
                                        GdkEvent        *event,
                                        gpointer         user_data);

void
on_open_activate                       (GtkMenuItem     *menuitem,
                                        gpointer         user_data);

void
on_close_activate                      (GtkMenuItem     *menuitem,
                                        gpointer         user_data);

void
on_preferences_activate                (GtkMenuItem     *menuitem,
                                        gpointer         user_data);

void
on_quit_activate                       (GtkMenuItem     *menuitem,
                                        gpointer         user_data);

void
on_histogram_activate                  (GtkMenuItem     *menuitem,
                                        gpointer         user_data);

void
on_real_part_activate                  (GtkMenuItem     *menuitem,
                                        gpointer         user_data);

void
on_imaginary_part_activate             (GtkMenuItem     *menuitem,
                                        gpointer         user_data);

void
on_modulus_activate                    (GtkMenuItem     *menuitem,
                                        gpointer         user_data);

void
on_log_modulus_activate                (GtkMenuItem     *menuitem,
                                        gpointer         user_data);

void
on_zoom_reset_activate                 (GtkMenuItem     *menuitem,
                                        gpointer         user_data);

void
on_zoom_in_activate                    (GtkMenuItem     *menuitem,
                                        gpointer         user_data);

void
on_zoom_out_activate                   (GtkMenuItem     *menuitem,
                                        gpointer         user_data);

void
on_view_reset_activate                 (GtkMenuItem     *menuitem,
                                        gpointer         user_data);

void
on_about_activate                      (GtkMenuItem     *menuitem,
                                        gpointer         user_data);

void
on_filechooser_open_button_clicked     (GtkButton       *button,
                                        gpointer         user_data);

void
on_filechooser_cancel_button_clicked   (GtkButton       *button,
                                        gpointer         user_data);

void
on_poschooser_save_button_clicked      (GtkButton       *button,
                                        gpointer         user_data);

void
on_poschooser_cancel_button_clicked    (GtkButton       *button,
                                        gpointer         user_data);

void
on_savedialog_save_clicked             (GtkButton       *button,
                                        gpointer         user_data);

void
on_savedialog_close_clicked            (GtkButton       *button,
                                        gpointer         user_data);

void
on_savedialog_cancel_clicked           (GtkButton       *button,
                                        gpointer         user_data);

void
on_errordialog_ok_clicked              (GtkButton       *button,
                                        gpointer         user_data);

gboolean
on_histogram_delete_event              (GtkWidget       *widget,
                                        GdkEvent        *event,
                                        gpointer         user_data);

void
on_histogram_viewport_realize          (GtkWidget       *widget,
                                        gpointer         user_data);

gboolean
on_histogram_drawingarea_expose_event  (GtkWidget       *widget,
                                        GdkEventExpose  *event,
                                        gpointer         user_data);

gboolean
on_histogram_drawingarea_button_press_event
                                        (GtkWidget       *widget,
                                        GdkEventButton  *event,
                                        gpointer         user_data);

gboolean
on_histogram_drawingarea_button_release_event
                                        (GtkWidget       *widget,
                                        GdkEventButton  *event,
                                        gpointer         user_data);

gboolean
on_histogram_drawingarea_motion_notify_event
                                        (GtkWidget       *widget,
                                        GdkEventMotion  *event,
                                        gpointer         user_data);

gboolean
on_histogram_drawingarea_configure_event
                                        (GtkWidget       *widget,
                                        GdkEventConfigure *event,
                                        gpointer         user_data);

gboolean
on_histogram_drawingarea_bottom_expose_event
                                        (GtkWidget       *widget,
                                        GdkEventExpose  *event,
                                        gpointer         user_data);

gboolean
on_histogram_drawingarea_left_button_press_event
                                        (GtkWidget       *widget,
                                        GdkEventButton  *event,
                                        gpointer         user_data);

gboolean
on_histogram_drawingarea_bottom_configure_event
                                        (GtkWidget       *widget,
                                        GdkEventConfigure *event,
                                        gpointer         user_data);

gboolean
on_histogram_drawingarea_right_button_press_event
                                        (GtkWidget       *widget,
                                        GdkEventButton  *event,
                                        gpointer         user_data);
