#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>

#include <gdk/gdkkeysyms.h>
#include <gtk/gtk.h>

#include "callbacks.h"
#include "interface.h"
#include "support.h"

#define GLADE_HOOKUP_OBJECT(component,widget,name) \
  g_object_set_data_full (G_OBJECT (component), name, \
    gtk_widget_ref (widget), (GDestroyNotify) gtk_widget_unref)

#define GLADE_HOOKUP_OBJECT_NO_REF(component,widget,name) \
  g_object_set_data (G_OBJECT (component), name, widget)

extern GtkWidget *create_top
                  (GuigtkDisplay *display)

{
  GtkWidget *top;
  GtkWidget *top_vbox;
  GtkWidget *menubar;
  GtkWidget *file;
  GtkWidget *image18;
  GtkWidget *file_menu;
  GtkWidget *open;
  GtkWidget *close;
  GtkWidget *separator_file_close;
  GtkWidget *preferences;
  GtkWidget *separator_file_preferences;
  GtkWidget *quit;
  GtkWidget *image;
  GtkWidget *image19;
  GtkWidget *image_menu;
  GtkWidget *histogram;
  GtkWidget *threshold;
  GtkWidget *separator_image_histogram;
  GSList *real_part_group = NULL;
  GtkWidget *real_part;
  GtkWidget *imaginary_part;
  GtkWidget *modulus;
  GtkWidget *log_modulus;
  GtkWidget *view;
  GtkWidget *image20;
  GtkWidget *view_menu;
  GtkWidget *zoom_reset;
  GtkWidget *zoom_in;
  GtkWidget *zoom_out;
  GtkWidget *separator_view_zoom_out;
  GtkWidget *view_reset;
  GtkWidget *image21;
  GtkWidget *about;
  GtkWidget *dummy;
  GtkWidget *viewport;
  GtkWidget *appbar;
  GtkAccelGroup *accel_group;

  accel_group = gtk_accel_group_new ();

  top = gtk_window_new (GTK_WINDOW_TOPLEVEL);
  gtk_window_set_title (GTK_WINDOW (top), _("EM image viewer"));
  gtk_window_set_default_size (GTK_WINDOW (top), 400, 300);
  gtk_window_set_position (GTK_WINDOW (top), GTK_WIN_POS_NONE);

  top_vbox = gtk_vbox_new (FALSE, 0);
  gtk_widget_show (top_vbox);
  gtk_container_add (GTK_CONTAINER (top), top_vbox);

  menubar = gtk_menu_bar_new ();
  gtk_widget_show (menubar);
  gtk_box_pack_start (GTK_BOX (top_vbox), menubar, FALSE, FALSE, 0);

  file = gtk_image_menu_item_new_with_mnemonic (_("_File"));
  gtk_widget_show (file);
  gtk_container_add (GTK_CONTAINER (menubar), file);

  image18 = gtk_image_new_from_stock ("gtk-open", GTK_ICON_SIZE_MENU);
  gtk_widget_show (image18);
  gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (file), image18);

  file_menu = gtk_menu_new ();
  gtk_menu_item_set_submenu (GTK_MENU_ITEM (file), file_menu);

  open = gtk_image_menu_item_new_from_stock ("gtk-open", accel_group);
  gtk_widget_show (open);
  gtk_container_add (GTK_CONTAINER (file_menu), open);

  close = gtk_image_menu_item_new_from_stock ("gtk-close", accel_group);
  gtk_widget_show (close);
  gtk_container_add (GTK_CONTAINER (file_menu), close);

  separator_file_close = gtk_separator_menu_item_new ();
  gtk_widget_show (separator_file_close);
  gtk_container_add (GTK_CONTAINER (file_menu), separator_file_close);
  gtk_widget_set_sensitive (separator_file_close, FALSE);

  preferences = gtk_image_menu_item_new_from_stock ("gtk-preferences", accel_group);
  gtk_widget_show (preferences);
  gtk_container_add (GTK_CONTAINER (file_menu), preferences);

  separator_file_preferences = gtk_separator_menu_item_new ();
  gtk_widget_show (separator_file_preferences);
  gtk_container_add (GTK_CONTAINER (file_menu), separator_file_preferences);
  gtk_widget_set_sensitive (separator_file_preferences, FALSE);

  quit = gtk_image_menu_item_new_from_stock ("gtk-quit", accel_group);
  gtk_widget_show (quit);
  gtk_container_add (GTK_CONTAINER (file_menu), quit);

  image = gtk_image_menu_item_new_with_mnemonic (_("_Image"));
  gtk_widget_show (image);
  gtk_container_add (GTK_CONTAINER (menubar), image);

  image19 = gtk_image_new_from_stock ("gtk-no", GTK_ICON_SIZE_MENU);
  gtk_widget_show (image19);
  gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (image), image19);

  image_menu = gtk_menu_new ();
  gtk_menu_item_set_submenu (GTK_MENU_ITEM (image), image_menu);

  histogram = gtk_menu_item_new_with_mnemonic (_("Histogram"));
  gtk_widget_show (histogram);
  gtk_container_add (GTK_CONTAINER (image_menu), histogram);

  threshold = gtk_menu_item_new_with_mnemonic (_("Threshold"));
  gtk_widget_show (threshold);
  gtk_container_add (GTK_CONTAINER (image_menu), threshold);

  separator_image_histogram = gtk_separator_menu_item_new ();
  gtk_widget_show (separator_image_histogram);
  gtk_container_add (GTK_CONTAINER (image_menu), separator_image_histogram);
  gtk_widget_set_sensitive (separator_image_histogram, FALSE);

  real_part = gtk_radio_menu_item_new_with_mnemonic (real_part_group, _("Real part"));
  real_part_group = gtk_radio_menu_item_get_group (GTK_RADIO_MENU_ITEM (real_part));
  gtk_widget_show (real_part);
  gtk_container_add (GTK_CONTAINER (image_menu), real_part);

  imaginary_part = gtk_radio_menu_item_new_with_mnemonic (real_part_group, _("Imaginary part"));
  real_part_group = gtk_radio_menu_item_get_group (GTK_RADIO_MENU_ITEM (imaginary_part));
  gtk_widget_show (imaginary_part);
  gtk_container_add (GTK_CONTAINER (image_menu), imaginary_part);

  modulus = gtk_radio_menu_item_new_with_mnemonic (real_part_group, _("Modulus"));
  real_part_group = gtk_radio_menu_item_get_group (GTK_RADIO_MENU_ITEM (modulus));
  gtk_widget_show (modulus);
  gtk_container_add (GTK_CONTAINER (image_menu), modulus);

  log_modulus = gtk_radio_menu_item_new_with_mnemonic (real_part_group, _("Log(modulus)"));
  real_part_group = gtk_radio_menu_item_get_group (GTK_RADIO_MENU_ITEM (log_modulus));
  gtk_widget_show (log_modulus);
  gtk_container_add (GTK_CONTAINER (image_menu), log_modulus);
  gtk_check_menu_item_set_active (GTK_CHECK_MENU_ITEM (log_modulus), TRUE);

  view = gtk_image_menu_item_new_with_mnemonic (_("_View"));
  gtk_widget_show (view);
  gtk_container_add (GTK_CONTAINER (menubar), view);

  image20 = gtk_image_new_from_stock ("gtk-yes", GTK_ICON_SIZE_MENU);
  gtk_widget_show (image20);
  gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (view), image20);

  view_menu = gtk_menu_new ();
  gtk_menu_item_set_submenu (GTK_MENU_ITEM (view), view_menu);

  zoom_reset = gtk_image_menu_item_new_from_stock ("gtk-zoom-100", accel_group);
  gtk_widget_show (zoom_reset);
  gtk_container_add (GTK_CONTAINER (view_menu), zoom_reset);

  zoom_in = gtk_image_menu_item_new_from_stock ("gtk-zoom-in", accel_group);
  gtk_widget_show (zoom_in);
  gtk_container_add (GTK_CONTAINER (view_menu), zoom_in);

  zoom_out = gtk_image_menu_item_new_from_stock ("gtk-zoom-out", accel_group);
  gtk_widget_show (zoom_out);
  gtk_container_add (GTK_CONTAINER (view_menu), zoom_out);

  separator_view_zoom_out = gtk_separator_menu_item_new ();
  gtk_widget_show (separator_view_zoom_out);
  gtk_container_add (GTK_CONTAINER (view_menu), separator_view_zoom_out);
  gtk_widget_set_sensitive (separator_view_zoom_out, FALSE);

  view_reset = gtk_image_menu_item_new_with_mnemonic (_("Reset"));
  gtk_widget_show (view_reset);
  gtk_container_add (GTK_CONTAINER (view_menu), view_reset);

  image21 = gtk_image_new_from_stock ("gtk-revert-to-saved", GTK_ICON_SIZE_MENU);
  gtk_widget_show (image21);
  gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (view_reset), image21);

  about = gtk_image_menu_item_new_from_stock ("gtk-about", accel_group);
  gtk_widget_show (about);
  gtk_container_add (GTK_CONTAINER (menubar), about);

  dummy = gtk_label_new ("");
  gtk_widget_show (dummy);
  gtk_box_pack_start (GTK_BOX (top_vbox), dummy, FALSE, FALSE, 0);

  viewport = gtk_viewport_new (NULL, NULL);
  gtk_widget_show (viewport);
  gtk_box_pack_start (GTK_BOX (top_vbox), viewport, TRUE, TRUE, 0);
  gtk_viewport_set_shadow_type (GTK_VIEWPORT (viewport), GTK_SHADOW_NONE);

  appbar = gtk_statusbar_new ();
  gtk_widget_show (appbar);
  gtk_box_pack_start (GTK_BOX (top_vbox), appbar, FALSE, FALSE, 0);

  g_signal_connect ((gpointer) top, "delete_event",
                    G_CALLBACK (on_top_delete_event),
                    display);
  g_signal_connect ((gpointer) open, "activate",
                    G_CALLBACK (on_open_activate),
                    display);
  g_signal_connect ((gpointer) close, "activate",
                    G_CALLBACK (on_close_activate),
                    display);
  g_signal_connect ((gpointer) preferences, "activate",
                    G_CALLBACK (on_preferences_activate),
                    display);
  g_signal_connect ((gpointer) quit, "activate",
                    G_CALLBACK (on_quit_activate),
                    display);
  g_signal_connect ((gpointer) histogram, "activate",
                    G_CALLBACK (on_histogram_activate),
                    display);
  g_signal_connect ((gpointer) threshold, "activate",
                    G_CALLBACK (on_histogram_activate),
                    display);
  g_signal_connect ((gpointer) real_part, "activate",
                    G_CALLBACK (on_real_part_activate),
                    display);
  g_signal_connect ((gpointer) imaginary_part, "activate",
                    G_CALLBACK (on_imaginary_part_activate),
                    display);
  g_signal_connect ((gpointer) modulus, "activate",
                    G_CALLBACK (on_modulus_activate),
                    display);
  g_signal_connect ((gpointer) log_modulus, "activate",
                    G_CALLBACK (on_log_modulus_activate),
                    display);
  g_signal_connect ((gpointer) zoom_reset, "activate",
                    G_CALLBACK (on_zoom_reset_activate),
                    display);
  g_signal_connect ((gpointer) zoom_in, "activate",
                    G_CALLBACK (on_zoom_in_activate),
                    display);
  g_signal_connect ((gpointer) zoom_out, "activate",
                    G_CALLBACK (on_zoom_out_activate),
                    display);
  g_signal_connect ((gpointer) view_reset, "activate",
                    G_CALLBACK (on_view_reset_activate),
                    display);
  g_signal_connect ((gpointer) about, "button_press_event",
                    G_CALLBACK (on_about_activate),
                    display);

  /* Store pointers to all widgets, for use by lookup_widget(). */
  GLADE_HOOKUP_OBJECT_NO_REF (top, top, "top");
  GLADE_HOOKUP_OBJECT (top, top_vbox, "top_vbox");
  GLADE_HOOKUP_OBJECT (top, menubar, "menubar");
  GLADE_HOOKUP_OBJECT (top, file, "file");
  GLADE_HOOKUP_OBJECT (top, image18, "image18");
  GLADE_HOOKUP_OBJECT (top, file_menu, "file_menu");
  GLADE_HOOKUP_OBJECT (top, open, "open");
  GLADE_HOOKUP_OBJECT (top, close, "close");
  GLADE_HOOKUP_OBJECT (top, separator_file_close, "separator_file_close");
  GLADE_HOOKUP_OBJECT (top, preferences, "preferences");
  GLADE_HOOKUP_OBJECT (top, separator_file_preferences, "separator_file_preferences");
  GLADE_HOOKUP_OBJECT (top, quit, "quit");
  GLADE_HOOKUP_OBJECT (top, image, "image");
  GLADE_HOOKUP_OBJECT (top, image19, "image19");
  GLADE_HOOKUP_OBJECT (top, image_menu, "image_menu");
  GLADE_HOOKUP_OBJECT (top, histogram, "histogram");
  GLADE_HOOKUP_OBJECT (top, threshold, "threshold");
  GLADE_HOOKUP_OBJECT (top, separator_image_histogram, "separator_image_histogram");
  GLADE_HOOKUP_OBJECT (top, real_part, "real_part");
  GLADE_HOOKUP_OBJECT (top, imaginary_part, "imaginary_part");
  GLADE_HOOKUP_OBJECT (top, modulus, "modulus");
  GLADE_HOOKUP_OBJECT (top, log_modulus, "log_modulus");
  GLADE_HOOKUP_OBJECT (top, view, "view");
  GLADE_HOOKUP_OBJECT (top, image20, "image20");
  GLADE_HOOKUP_OBJECT (top, view_menu, "view_menu");
  GLADE_HOOKUP_OBJECT (top, zoom_reset, "zoom_reset");
  GLADE_HOOKUP_OBJECT (top, zoom_in, "zoom_in");
  GLADE_HOOKUP_OBJECT (top, zoom_out, "zoom_out");
  GLADE_HOOKUP_OBJECT (top, separator_view_zoom_out, "separator_view_zoom_out");
  GLADE_HOOKUP_OBJECT (top, view_reset, "view_reset");
  GLADE_HOOKUP_OBJECT (top, image21, "image21");
  GLADE_HOOKUP_OBJECT (top, about, "about");
  GLADE_HOOKUP_OBJECT (top, dummy, "dummy");
  GLADE_HOOKUP_OBJECT (top, viewport, "viewport");
  GLADE_HOOKUP_OBJECT (top, appbar, "appbar");

  gtk_window_add_accel_group (GTK_WINDOW (top), accel_group);

  return top;
}


extern GtkWidget *create_filechooser
                  (GuigtkDisplay *display)

{
  GtkWidget *filechooser;
  GtkWidget *filechooser_vbox;
  GtkWidget *filechooser_action_area;
  GtkWidget *filechooser_cancel_button;
  GtkWidget *filechooser_open_button;

  filechooser = gtk_file_chooser_dialog_new ("", NULL, GTK_FILE_CHOOSER_ACTION_OPEN, NULL, NULL );
  gtk_container_set_border_width (GTK_CONTAINER (filechooser), 10);
  gtk_window_set_type_hint (GTK_WINDOW (filechooser), GDK_WINDOW_TYPE_HINT_DIALOG);

  filechooser_vbox = GTK_DIALOG (filechooser)->vbox;
  gtk_widget_show (filechooser_vbox);

  filechooser_action_area = GTK_DIALOG (filechooser)->action_area;
  gtk_widget_show (filechooser_action_area);
  gtk_button_box_set_layout (GTK_BUTTON_BOX (filechooser_action_area), GTK_BUTTONBOX_END);

  filechooser_cancel_button = gtk_button_new_from_stock ("gtk-cancel");
  gtk_widget_show (filechooser_cancel_button);
  gtk_dialog_add_action_widget (GTK_DIALOG (filechooser), filechooser_cancel_button, GTK_RESPONSE_CANCEL);
  GTK_WIDGET_SET_FLAGS (filechooser_cancel_button, GTK_CAN_DEFAULT);

  filechooser_open_button = gtk_button_new_from_stock ("gtk-open");
  gtk_widget_show (filechooser_open_button);
  gtk_dialog_add_action_widget (GTK_DIALOG (filechooser), filechooser_open_button, GTK_RESPONSE_OK);
  GTK_WIDGET_SET_FLAGS (filechooser_open_button, GTK_CAN_DEFAULT);

  g_signal_connect ((gpointer) filechooser_cancel_button, "clicked",
                    G_CALLBACK (on_filechooser_cancel_button_clicked),
                    display);
  g_signal_connect ((gpointer) filechooser_open_button, "clicked",
                    G_CALLBACK (on_filechooser_open_button_clicked),
                    display);

  /* Store pointers to all widgets, for use by lookup_widget(). */
  GLADE_HOOKUP_OBJECT_NO_REF (filechooser, filechooser, "filechooser");
  GLADE_HOOKUP_OBJECT_NO_REF (filechooser, filechooser_vbox, "filechooser_vbox");
  GLADE_HOOKUP_OBJECT_NO_REF (filechooser, filechooser_action_area, "filechooser_action_area");
  GLADE_HOOKUP_OBJECT (filechooser, filechooser_cancel_button, "filechooser_cancel_button");
  GLADE_HOOKUP_OBJECT (filechooser, filechooser_open_button, "filechooser_open_button");

  gtk_widget_grab_default (filechooser_open_button);
  return filechooser;
}


extern GtkWidget *create_poschooser
                  (GuigtkDisplay *display)

{
  GtkWidget *poschooser;
  GtkWidget *poschooser_vbox;
  GtkWidget *poschooser_action_area;
  GtkWidget *poschooser_cancel_button;
  GtkWidget *poschooser_save_button;

  poschooser = gtk_file_chooser_dialog_new ("", NULL, GTK_FILE_CHOOSER_ACTION_SAVE, NULL, NULL );
  gtk_container_set_border_width (GTK_CONTAINER (poschooser), 10);
  gtk_window_set_type_hint (GTK_WINDOW (poschooser), GDK_WINDOW_TYPE_HINT_DIALOG);

  poschooser_vbox = GTK_DIALOG (poschooser)->vbox;
  gtk_widget_show (poschooser_vbox);

  poschooser_action_area = GTK_DIALOG (poschooser)->action_area;
  gtk_widget_show (poschooser_action_area);
  gtk_button_box_set_layout (GTK_BUTTON_BOX (poschooser_action_area), GTK_BUTTONBOX_END);

  poschooser_cancel_button = gtk_button_new_from_stock ("gtk-cancel");
  gtk_widget_show (poschooser_cancel_button);
  gtk_dialog_add_action_widget (GTK_DIALOG (poschooser), poschooser_cancel_button, GTK_RESPONSE_CANCEL);
  GTK_WIDGET_SET_FLAGS (poschooser_cancel_button, GTK_CAN_DEFAULT);

  poschooser_save_button = gtk_button_new_from_stock ("gtk-save");
  gtk_widget_show (poschooser_save_button);
  gtk_dialog_add_action_widget (GTK_DIALOG (poschooser), poschooser_save_button, GTK_RESPONSE_OK);
  GTK_WIDGET_SET_FLAGS (poschooser_save_button, GTK_CAN_DEFAULT);

  g_signal_connect ((gpointer) poschooser_cancel_button, "clicked",
                    G_CALLBACK (on_poschooser_cancel_button_clicked),
                    display);
  g_signal_connect ((gpointer) poschooser_save_button, "clicked",
                    G_CALLBACK (on_poschooser_save_button_clicked),
                    display);

  /* Store pointers to all widgets, for use by lookup_widget(). */
  GLADE_HOOKUP_OBJECT_NO_REF (poschooser, poschooser, "poschooser");
  GLADE_HOOKUP_OBJECT_NO_REF (poschooser, poschooser_vbox, "poschooser_vbox");
  GLADE_HOOKUP_OBJECT_NO_REF (poschooser, poschooser_action_area, "poschooser_action_area");
  GLADE_HOOKUP_OBJECT (poschooser, poschooser_cancel_button, "poschooser_cancel_button");
  GLADE_HOOKUP_OBJECT (poschooser, poschooser_save_button, "poschooser_save_button");

  gtk_widget_grab_default (poschooser_save_button);
  return poschooser;
}


extern GtkWidget *create_savedialog
                  (GuigtkDisplay *display)

{
  GtkWidget *savedialog;
  GtkWidget *savedialog_vbox;
  GtkWidget *savedialog_hbox;
  GtkWidget *savedialog_icon;
  GtkWidget *savedialog_label;
  GtkWidget *savedialog_action_area;
  GtkWidget *savedialog_save;
  GtkWidget *savedialog_close;
  GtkWidget *savedialog_cancel;

  savedialog = gtk_dialog_new ();
  gtk_window_set_title (GTK_WINDOW (savedialog), _("Save"));
  gtk_window_set_modal (GTK_WINDOW (savedialog), TRUE);
  gtk_window_set_resizable (GTK_WINDOW (savedialog), FALSE);
  gtk_window_set_type_hint (GTK_WINDOW (savedialog), GDK_WINDOW_TYPE_HINT_DIALOG);

  savedialog_vbox = GTK_DIALOG (savedialog)->vbox;
  gtk_widget_show (savedialog_vbox);

  savedialog_hbox = gtk_hbox_new (FALSE, 0);
  gtk_widget_show (savedialog_hbox);
  gtk_box_pack_start (GTK_BOX (savedialog_vbox), savedialog_hbox, TRUE, TRUE, 0);

  savedialog_icon = gtk_image_new_from_stock ("gtk-dialog-warning", GTK_ICON_SIZE_DIALOG);
  gtk_widget_show (savedialog_icon);
  gtk_box_pack_start (GTK_BOX (savedialog_hbox), savedialog_icon, TRUE, TRUE, 5);

  savedialog_label = gtk_label_new (_("The position list has been modified.\nSave it or close it without saving."));
  gtk_widget_show (savedialog_label);
  gtk_box_pack_start (GTK_BOX (savedialog_hbox), savedialog_label, FALSE, FALSE, 5);

  savedialog_action_area = GTK_DIALOG (savedialog)->action_area;
  gtk_widget_show (savedialog_action_area);
  gtk_button_box_set_layout (GTK_BUTTON_BOX (savedialog_action_area), GTK_BUTTONBOX_END);

  savedialog_save = gtk_button_new_from_stock ("gtk-save");
  gtk_widget_show (savedialog_save);
  gtk_dialog_add_action_widget (GTK_DIALOG (savedialog), savedialog_save, GTK_RESPONSE_APPLY);
  GTK_WIDGET_SET_FLAGS (savedialog_save, GTK_CAN_DEFAULT);

  savedialog_close = gtk_button_new_from_stock ("gtk-close");
  gtk_widget_show (savedialog_close);
  gtk_dialog_add_action_widget (GTK_DIALOG (savedialog), savedialog_close, GTK_RESPONSE_CLOSE);
  GTK_WIDGET_SET_FLAGS (savedialog_close, GTK_CAN_DEFAULT);

  savedialog_cancel = gtk_button_new_from_stock ("gtk-cancel");
  gtk_widget_show (savedialog_cancel);
  gtk_dialog_add_action_widget (GTK_DIALOG (savedialog), savedialog_cancel, GTK_RESPONSE_CANCEL);
  GTK_WIDGET_SET_FLAGS (savedialog_cancel, GTK_CAN_DEFAULT);

  g_signal_connect ((gpointer) savedialog_save, "clicked",
                    G_CALLBACK (on_savedialog_save_clicked),
                    display);
  g_signal_connect ((gpointer) savedialog_close, "clicked",
                    G_CALLBACK (on_savedialog_close_clicked),
                    display);
  g_signal_connect ((gpointer) savedialog_cancel, "clicked",
                    G_CALLBACK (on_savedialog_cancel_clicked),
                    display);

  /* Store pointers to all widgets, for use by lookup_widget(). */
  GLADE_HOOKUP_OBJECT_NO_REF (savedialog, savedialog, "savedialog");
  GLADE_HOOKUP_OBJECT_NO_REF (savedialog, savedialog_vbox, "savedialog_vbox");
  GLADE_HOOKUP_OBJECT (savedialog, savedialog_hbox, "savedialog_hbox");
  GLADE_HOOKUP_OBJECT (savedialog, savedialog_icon, "savedialog_icon");
  GLADE_HOOKUP_OBJECT (savedialog, savedialog_label, "savedialog_label");
  GLADE_HOOKUP_OBJECT_NO_REF (savedialog, savedialog_action_area, "savedialog_action_area");
  GLADE_HOOKUP_OBJECT (savedialog, savedialog_save, "savedialog_save");
  GLADE_HOOKUP_OBJECT (savedialog, savedialog_save, "savedialog_close");
  GLADE_HOOKUP_OBJECT (savedialog, savedialog_cancel, "savedialog_cancel");

  return savedialog;
}


extern GtkWidget *create_errordialog
                  (GuigtkDisplay *display)

{
  GtkWidget *errordialog;
  GtkWidget *errordialog_vbox;
  GtkWidget *errordialog_hbox;
  GtkWidget *errordialog_icon;
  GtkWidget *errordialog_text_vbox;
  GtkWidget *label2;
  GtkWidget *errordialog_action_area;
  GtkWidget *errordialog_ok;

  errordialog = gtk_dialog_new ();
  gtk_window_set_title (GTK_WINDOW (errordialog), _("Error"));
  gtk_window_set_modal (GTK_WINDOW (errordialog), TRUE);
  gtk_window_set_resizable (GTK_WINDOW (errordialog), FALSE);
  gtk_window_set_type_hint (GTK_WINDOW (errordialog), GDK_WINDOW_TYPE_HINT_DIALOG);

  errordialog_vbox = GTK_DIALOG (errordialog)->vbox;
  gtk_widget_show (errordialog_vbox);

  errordialog_hbox = gtk_hbox_new (FALSE, 0);
  gtk_widget_show (errordialog_hbox);
  gtk_box_pack_start (GTK_BOX (errordialog_vbox), errordialog_hbox, TRUE, TRUE, 0);

  errordialog_icon = gtk_image_new_from_stock ("gtk-dialog-error", GTK_ICON_SIZE_DIALOG);
  gtk_widget_show (errordialog_icon);
  gtk_box_pack_start (GTK_BOX (errordialog_hbox), errordialog_icon, TRUE, TRUE, 5);

  errordialog_text_vbox = gtk_vbox_new (FALSE, 0);
  gtk_widget_show (errordialog_text_vbox);
  gtk_box_pack_start (GTK_BOX (errordialog_hbox), errordialog_text_vbox, TRUE, TRUE, 0);

  label2 = gtk_label_new (_("Error"));
  gtk_widget_show (label2);
  gtk_box_pack_start (GTK_BOX (errordialog_text_vbox), label2, FALSE, FALSE, 5);

  errordialog_action_area = GTK_DIALOG (errordialog)->action_area;
  gtk_widget_show (errordialog_action_area);
  gtk_button_box_set_layout (GTK_BUTTON_BOX (errordialog_action_area), GTK_BUTTONBOX_END);

  errordialog_ok = gtk_button_new_from_stock ("gtk-ok");
  gtk_widget_show (errordialog_ok);
  gtk_dialog_add_action_widget (GTK_DIALOG (errordialog), errordialog_ok, GTK_RESPONSE_OK);
  GTK_WIDGET_SET_FLAGS (errordialog_ok, GTK_CAN_DEFAULT);

  g_signal_connect ((gpointer) errordialog_ok, "clicked",
                    G_CALLBACK (on_errordialog_ok_clicked),
                    display);

  /* Store pointers to all widgets, for use by lookup_widget(). */
  GLADE_HOOKUP_OBJECT_NO_REF (errordialog, errordialog, "errordialog");
  GLADE_HOOKUP_OBJECT_NO_REF (errordialog, errordialog_vbox, "errordialog_vbox");
  GLADE_HOOKUP_OBJECT (errordialog, errordialog_hbox, "errordialog_hbox");
  GLADE_HOOKUP_OBJECT (errordialog, errordialog_icon, "errordialog_icon");
  GLADE_HOOKUP_OBJECT (errordialog, errordialog_text_vbox, "errordialog_text_vbox");
  GLADE_HOOKUP_OBJECT (errordialog, label2, "label2");
  GLADE_HOOKUP_OBJECT_NO_REF (errordialog, errordialog_action_area, "errordialog_action_area");
  GLADE_HOOKUP_OBJECT (errordialog, errordialog_ok, "errordialog_ok");

  return errordialog;
}


extern GtkWidget *create_histogram
                  (GuigtkDisplay *display)
{
  GtkWidget *histogram;
  GtkWidget *histogram_vbox;
  GtkWidget *histogram_frame;
  GtkWidget *histogram_vbox_file;
  GtkWidget *histogram_hbox_file;
  GtkWidget *histogram_hbox_left;
  GtkWidget *histogram_vbox_left;
  GtkWidget *histogram_label_min;
  GtkWidget *histogram_label_max;
  GtkWidget *histogram_vbox_left_val;
  GtkWidget *histogram_label_min_val;
  GtkWidget *histogram_label_max_val;
  GtkWidget *histogram_hbox_right;
  GtkWidget *histogram_vbox_right;
  GtkWidget *histogram_label_mean;
  GtkWidget *histogram_label_sd;
  GtkWidget *histogram_vbox_right_val;
  GtkWidget *histogram_label_mean_val;
  GtkWidget *histogram_label_sd_val;
  GtkWidget *histogram_vbox_pad;
  GtkWidget *histogram_label_pad;
  GtkWidget *histogram_frame_title;
  GtkWidget *histogram_viewport;
  GtkWidget *histogram_vbox_draw;
  GtkWidget *histogram_drawingarea;
  GtkWidget *histogram_hbox_draw;
  GtkWidget *histogram_drawingarea_left;
  GtkWidget *histogram_label_left;
  GtkWidget *histogram_label_right;
  GtkWidget *histogram_drawingarea_right;
  GtkWidget *histogram_hbox2_draw;
  GtkWidget *histogram_label2_left;
  GtkWidget *histogram_label2_center;
  GtkWidget *histogram_label2_right;

  histogram = gtk_window_new (GTK_WINDOW_TOPLEVEL);
  gtk_window_set_title( GTK_WINDOW(histogram), ( display->status & GuigtkDisplayThrs ) ? _("Threshold") : _("Histogram") );
  gtk_window_set_resizable (GTK_WINDOW (histogram), FALSE);
  /* gtk_window_set_keep_above (GTK_WINDOW (histogram), TRUE); */
  gtk_window_set_position (GTK_WINDOW (histogram), GTK_WIN_POS_NONE);

  histogram_vbox = gtk_vbox_new (FALSE, 0);
  gtk_widget_show (histogram_vbox);
  gtk_container_add (GTK_CONTAINER (histogram), histogram_vbox);

  histogram_frame = gtk_frame_new (NULL);
  gtk_widget_show (histogram_frame);
  gtk_box_pack_start (GTK_BOX (histogram_vbox), histogram_frame, FALSE, FALSE, 0);
  gtk_container_set_border_width (GTK_CONTAINER (histogram_frame), 4);
  gtk_frame_set_label_align (GTK_FRAME (histogram_frame), 0.5, 0.7);
  gtk_frame_set_shadow_type (GTK_FRAME (histogram_frame), GTK_SHADOW_ETCHED_OUT);

  histogram_vbox_file = gtk_vbox_new (FALSE, 6);
  gtk_widget_show (histogram_vbox_file);
  gtk_container_add (GTK_CONTAINER (histogram_frame), histogram_vbox_file);

  histogram_hbox_file = gtk_hbox_new (TRUE, 0);
  gtk_widget_show (histogram_hbox_file);
  gtk_box_pack_start (GTK_BOX (histogram_vbox_file), histogram_hbox_file, TRUE, TRUE, 0);

  histogram_hbox_left = gtk_hbox_new (FALSE, 8);
  gtk_widget_show (histogram_hbox_left);
  gtk_box_pack_start (GTK_BOX (histogram_hbox_file), histogram_hbox_left, TRUE, TRUE, 4);

  histogram_vbox_left = gtk_vbox_new (TRUE, 0);
  gtk_widget_show (histogram_vbox_left);
  gtk_box_pack_start (GTK_BOX (histogram_hbox_left), histogram_vbox_left, FALSE, TRUE, 0);

  histogram_label_min = gtk_label_new (_("min"));
  gtk_widget_show (histogram_label_min);
  gtk_box_pack_start (GTK_BOX (histogram_vbox_left), histogram_label_min, FALSE, FALSE, 0);
  gtk_misc_set_alignment (GTK_MISC (histogram_label_min), 0, 0.5);

  histogram_label_max = gtk_label_new (_("max"));
  gtk_widget_show (histogram_label_max);
  gtk_box_pack_start (GTK_BOX (histogram_vbox_left), histogram_label_max, FALSE, FALSE, 0);
  gtk_misc_set_alignment (GTK_MISC (histogram_label_max), 0, 0.5);

  histogram_vbox_left_val = gtk_vbox_new (TRUE, 0);
  gtk_widget_show (histogram_vbox_left_val);
  gtk_box_pack_start (GTK_BOX (histogram_hbox_left), histogram_vbox_left_val, TRUE, TRUE, 0);

  histogram_label_min_val = gtk_label_new (_("9999"));
  gtk_widget_show (histogram_label_min_val);
  gtk_box_pack_start (GTK_BOX (histogram_vbox_left_val), histogram_label_min_val, FALSE, FALSE, 0);
  gtk_misc_set_alignment (GTK_MISC (histogram_label_min_val), 0, 0.5);

  histogram_label_max_val = gtk_label_new (_("9999"));
  gtk_widget_show (histogram_label_max_val);
  gtk_box_pack_start (GTK_BOX (histogram_vbox_left_val), histogram_label_max_val, FALSE, FALSE, 0);
  gtk_misc_set_alignment (GTK_MISC (histogram_label_max_val), 0, 0.5);

  histogram_hbox_right = gtk_hbox_new (FALSE, 8);
  gtk_widget_show (histogram_hbox_right);
  gtk_box_pack_start (GTK_BOX (histogram_hbox_file), histogram_hbox_right, TRUE, TRUE, 0);

  histogram_vbox_right = gtk_vbox_new (TRUE, 0);
  gtk_widget_show (histogram_vbox_right);
  gtk_box_pack_start (GTK_BOX (histogram_hbox_right), histogram_vbox_right, FALSE, TRUE, 0);

  histogram_label_mean = gtk_label_new (_("mean"));
  gtk_widget_show (histogram_label_mean);
  gtk_box_pack_start (GTK_BOX (histogram_vbox_right), histogram_label_mean, FALSE, FALSE, 0);
  gtk_misc_set_alignment (GTK_MISC (histogram_label_mean), 0, 0.5);

  histogram_label_sd = gtk_label_new (_("st.dev"));
  gtk_widget_show (histogram_label_sd);
  gtk_box_pack_start (GTK_BOX (histogram_vbox_right), histogram_label_sd, FALSE, FALSE, 0);
  gtk_misc_set_alignment (GTK_MISC (histogram_label_sd), 0, 0.5);

  histogram_vbox_right_val = gtk_vbox_new (TRUE, 0);
  gtk_widget_show (histogram_vbox_right_val);
  gtk_box_pack_start (GTK_BOX (histogram_hbox_right), histogram_vbox_right_val, TRUE, TRUE, 0);

  histogram_label_mean_val = gtk_label_new (_("9999"));
  gtk_widget_show (histogram_label_mean_val);
  gtk_box_pack_start (GTK_BOX (histogram_vbox_right_val), histogram_label_mean_val, FALSE, FALSE, 0);
  gtk_misc_set_alignment (GTK_MISC (histogram_label_mean_val), 0, 0.5);

  histogram_label_sd_val = gtk_label_new (_("9999"));
  gtk_widget_show (histogram_label_sd_val);
  gtk_box_pack_start (GTK_BOX (histogram_vbox_right_val), histogram_label_sd_val, FALSE, FALSE, 0);
  gtk_misc_set_alignment (GTK_MISC (histogram_label_sd_val), 0, 0.5);

  histogram_vbox_pad = gtk_vbox_new (FALSE, 0);
  gtk_widget_show (histogram_vbox_pad);
  gtk_box_pack_start (GTK_BOX (histogram_vbox_file), histogram_vbox_pad, FALSE, FALSE, 0);
  gtk_widget_set_size_request (histogram_vbox_pad, 1, 1);

  histogram_label_pad = gtk_label_new ("");
  gtk_widget_show (histogram_label_pad);
  gtk_box_pack_start (GTK_BOX (histogram_vbox_pad), histogram_label_pad, FALSE, FALSE, 0);
  gtk_widget_set_size_request (histogram_label_pad, 1, 1);

  histogram_frame_title = gtk_label_new (_("file"));
  gtk_widget_show (histogram_frame_title);
  gtk_frame_set_label_widget (GTK_FRAME (histogram_frame), histogram_frame_title);
  gtk_label_set_justify (GTK_LABEL (histogram_frame_title), GTK_JUSTIFY_CENTER);

  histogram_viewport = gtk_viewport_new (NULL, NULL);
  gtk_widget_show (histogram_viewport);
  gtk_box_pack_start (GTK_BOX (histogram_vbox), histogram_viewport, TRUE, TRUE, 0);
  /* gtk_container_set_border_width (GTK_CONTAINER (histogram_viewport), 4); */
  gtk_viewport_set_shadow_type (GTK_VIEWPORT (histogram_viewport), GTK_SHADOW_NONE);

  histogram_vbox_draw = gtk_vbox_new (FALSE, 0);
  gtk_widget_show (histogram_vbox_draw);
  gtk_container_set_border_width (GTK_CONTAINER (histogram_vbox_draw), 10 );
  gtk_container_add (GTK_CONTAINER (histogram_viewport), histogram_vbox_draw);

  histogram_hbox2_draw = gtk_hbox_new (FALSE, 0);
  gtk_widget_show (histogram_hbox2_draw);
  gtk_box_pack_start (GTK_BOX (histogram_vbox_draw), histogram_hbox2_draw, TRUE, TRUE, 0);

  histogram_label2_left = gtk_label_new (_(""));
  gtk_widget_show (histogram_label2_left);
  gtk_box_pack_start (GTK_BOX (histogram_hbox2_draw), histogram_label2_left, TRUE, TRUE, 0);
  gtk_misc_set_alignment (GTK_MISC (histogram_label2_left), 0, 0);

  histogram_label2_center = gtk_label_new (_(""));
  gtk_widget_show (histogram_label2_center);
  gtk_box_pack_start (GTK_BOX (histogram_hbox2_draw), histogram_label2_center, TRUE, TRUE, 0);
  gtk_misc_set_alignment (GTK_MISC (histogram_label2_center), 0.5, 0);

  histogram_label2_right = gtk_label_new (_(""));
  gtk_widget_show (histogram_label2_right);
  gtk_box_pack_start (GTK_BOX (histogram_hbox2_draw), histogram_label2_right, TRUE, TRUE, 0);
  gtk_label_set_justify (GTK_LABEL (histogram_label2_right), GTK_JUSTIFY_RIGHT);
  gtk_misc_set_alignment (GTK_MISC (histogram_label2_right), 1, 0);

  histogram_drawingarea = gtk_drawing_area_new ();
  gtk_widget_show (histogram_drawingarea);
  gtk_box_pack_start (GTK_BOX (histogram_vbox_draw), histogram_drawingarea, TRUE, TRUE, 0);
  gtk_widget_set_size_request (histogram_drawingarea, 280, 330);
  gtk_widget_set_events (histogram_drawingarea, GDK_EXPOSURE_MASK | GDK_BUTTON1_MOTION_MASK | GDK_BUTTON_PRESS_MASK | GDK_BUTTON_RELEASE_MASK);

  histogram_hbox_draw = gtk_hbox_new (FALSE, 0);
  gtk_widget_show (histogram_hbox_draw);
  gtk_box_pack_start (GTK_BOX (histogram_vbox_draw), histogram_hbox_draw, TRUE, TRUE, 0);

  histogram_drawingarea_left = gtk_drawing_area_new ();
  gtk_widget_show (histogram_drawingarea_left);
  gtk_box_pack_start (GTK_BOX (histogram_hbox_draw), histogram_drawingarea_left, FALSE, TRUE, 0);
  gtk_widget_set_size_request (histogram_drawingarea_left, 40, 12);
  gtk_widget_set_events (histogram_drawingarea_left, GDK_EXPOSURE_MASK | GDK_BUTTON_PRESS_MASK);

  histogram_label_left = gtk_label_new (_("9999"));
  gtk_widget_show (histogram_label_left);
  gtk_box_pack_start (GTK_BOX (histogram_hbox_draw), histogram_label_left, TRUE, TRUE, 0);
  gtk_misc_set_alignment (GTK_MISC (histogram_label_left), 0, 0.5);

  histogram_label_right = gtk_label_new (_("9999"));
  gtk_widget_show (histogram_label_right);
  gtk_box_pack_start (GTK_BOX (histogram_hbox_draw), histogram_label_right, TRUE, TRUE, 0);
  gtk_label_set_justify (GTK_LABEL (histogram_label_right), GTK_JUSTIFY_RIGHT);
  gtk_misc_set_alignment (GTK_MISC (histogram_label_right), 1, 0.5);

  histogram_drawingarea_right = gtk_drawing_area_new ();
  gtk_widget_show (histogram_drawingarea_right);
  gtk_box_pack_start (GTK_BOX (histogram_hbox_draw), histogram_drawingarea_right, FALSE, TRUE, 0);
  gtk_widget_set_size_request (histogram_drawingarea_right, 40, 12);
  gtk_widget_set_events (histogram_drawingarea_right, GDK_EXPOSURE_MASK | GDK_BUTTON_PRESS_MASK);

  g_signal_connect ((gpointer) histogram, "delete_event",
                    G_CALLBACK (on_histogram_delete_event),
                    display);
  g_signal_connect ((gpointer) histogram_viewport, "realize",
                    G_CALLBACK (on_histogram_viewport_realize),
                    display);
  g_signal_connect ((gpointer) histogram_drawingarea, "expose_event",
                    G_CALLBACK (on_histogram_drawingarea_expose_event),
                    display);
  g_signal_connect ((gpointer) histogram_drawingarea, "button_press_event",
                    G_CALLBACK (on_histogram_drawingarea_button_press_event),
                    display);
  g_signal_connect ((gpointer) histogram_drawingarea, "button_release_event",
                    G_CALLBACK (on_histogram_drawingarea_button_release_event),
                    display);
  g_signal_connect ((gpointer) histogram_drawingarea, "motion_notify_event",
                    G_CALLBACK (on_histogram_drawingarea_motion_notify_event),
                    display);
  g_signal_connect ((gpointer) histogram_drawingarea, "configure_event",
                    G_CALLBACK (on_histogram_drawingarea_configure_event),
                    display);
  g_signal_connect ((gpointer) histogram_drawingarea_left, "expose_event",
                    G_CALLBACK (on_histogram_drawingarea_bottom_expose_event),
                    display);
  g_signal_connect ((gpointer) histogram_drawingarea_left, "button_press_event",
                    G_CALLBACK (on_histogram_drawingarea_left_button_press_event),
                    display);
  g_signal_connect ((gpointer) histogram_drawingarea_left, "configure_event",
                    G_CALLBACK (on_histogram_drawingarea_bottom_configure_event),
                    display);
  g_signal_connect ((gpointer) histogram_drawingarea_right, "expose_event",
                    G_CALLBACK (on_histogram_drawingarea_bottom_expose_event),
                    display);
  g_signal_connect ((gpointer) histogram_drawingarea_right, "button_press_event",
                    G_CALLBACK (on_histogram_drawingarea_right_button_press_event),
                    display);
  g_signal_connect ((gpointer) histogram_drawingarea_right, "configure_event",
                    G_CALLBACK (on_histogram_drawingarea_bottom_configure_event),
                    display);

  /* Store pointers to all widgets, for use by lookup_widget(). */
  GLADE_HOOKUP_OBJECT_NO_REF (histogram, histogram, "histogram");
  GLADE_HOOKUP_OBJECT (histogram, histogram_vbox, "histogram_vbox");
  GLADE_HOOKUP_OBJECT (histogram, histogram_frame, "histogram_frame");
  GLADE_HOOKUP_OBJECT (histogram, histogram_vbox_file, "histogram_vbox_file");
  GLADE_HOOKUP_OBJECT (histogram, histogram_hbox_file, "histogram_hbox_file");
  GLADE_HOOKUP_OBJECT (histogram, histogram_hbox_left, "histogram_hbox_left");
  GLADE_HOOKUP_OBJECT (histogram, histogram_vbox_left, "histogram_vbox_left");
  GLADE_HOOKUP_OBJECT (histogram, histogram_label_min, "histogram_label_min");
  GLADE_HOOKUP_OBJECT (histogram, histogram_label_max, "histogram_label_max");
  GLADE_HOOKUP_OBJECT (histogram, histogram_vbox_left_val, "histogram_vbox_left_val");
  GLADE_HOOKUP_OBJECT (histogram, histogram_label_min_val, "histogram_label_min_val");
  GLADE_HOOKUP_OBJECT (histogram, histogram_label_max_val, "histogram_label_max_val");
  GLADE_HOOKUP_OBJECT (histogram, histogram_hbox_right, "histogram_hbox_right");
  GLADE_HOOKUP_OBJECT (histogram, histogram_vbox_right, "histogram_vbox_right");
  GLADE_HOOKUP_OBJECT (histogram, histogram_label_mean, "histogram_label_mean");
  GLADE_HOOKUP_OBJECT (histogram, histogram_label_sd, "histogram_label_sd");
  GLADE_HOOKUP_OBJECT (histogram, histogram_vbox_right_val, "histogram_vbox_right_val");
  GLADE_HOOKUP_OBJECT (histogram, histogram_label_mean_val, "histogram_label_mean_val");
  GLADE_HOOKUP_OBJECT (histogram, histogram_label_sd_val, "histogram_label_sd_val");
  GLADE_HOOKUP_OBJECT (histogram, histogram_vbox_pad, "histogram_vbox_pad");
  GLADE_HOOKUP_OBJECT (histogram, histogram_label_pad, "histogram_label_pad");
  GLADE_HOOKUP_OBJECT (histogram, histogram_frame_title, "histogram_frame_title");
  GLADE_HOOKUP_OBJECT (histogram, histogram_viewport, "histogram_viewport");
  GLADE_HOOKUP_OBJECT (histogram, histogram_vbox_draw, "histogram_vbox_draw");
  GLADE_HOOKUP_OBJECT (histogram, histogram_drawingarea, "histogram_drawingarea");
  GLADE_HOOKUP_OBJECT (histogram, histogram_hbox_draw, "histogram_hbox_draw");
  GLADE_HOOKUP_OBJECT (histogram, histogram_drawingarea_left, "histogram_drawingarea_left");
  GLADE_HOOKUP_OBJECT (histogram, histogram_label_left, "histogram_label_left");
  GLADE_HOOKUP_OBJECT (histogram, histogram_label_right, "histogram_label_right");
  GLADE_HOOKUP_OBJECT (histogram, histogram_drawingarea_right, "histogram_drawingarea_right");
  GLADE_HOOKUP_OBJECT (histogram, histogram_hbox2_draw, "histogram_hbox2_draw");
  GLADE_HOOKUP_OBJECT (histogram, histogram_label2_left, "histogram_label2_left");
  GLADE_HOOKUP_OBJECT (histogram, histogram_label2_center, "histogram_label2_center");
  GLADE_HOOKUP_OBJECT (histogram, histogram_label2_right, "histogram_label2_right");

  return histogram;
}


extern GtkWidget *create_about
                  (GuigtkDisplay *display)

{
  GtkWidget *about;
  /* TRANSLATORS: Replace this string with your names, one name per line. */
  gchar *translators = _("translator-credits");

  about = gtk_about_dialog_new ();
  gtk_container_set_border_width (GTK_CONTAINER (about), 5);
  gtk_about_dialog_set_version (GTK_ABOUT_DIALOG (about), GuigtkDisplayVersion );
  gtk_about_dialog_set_name (GTK_ABOUT_DIALOG (about), _("EM image viewer"));
  /* gtk_about_dialog_set_copyright (GTK_ABOUT_DIALOG (about), _(GuigtkDisplayCopyright) ); */
  gchar *txt = g_convert( GuigtkDisplayCopyright, -1, "ISO-8859-1", "UTF-8", NULL, NULL, NULL );
  gtk_about_dialog_set_copyright( GTK_ABOUT_DIALOG(about), txt );
  g_free( txt );
  gtk_about_dialog_set_comments (GTK_ABOUT_DIALOG (about), _("Display images in TIFF, CCP4, MRC, EM, FFF, IMAGIC, SPIDER, and SUPRIM formats."));
  gtk_about_dialog_set_translator_credits (GTK_ABOUT_DIALOG (about), translators);

  /* Store pointers to all widgets, for use by lookup_widget(). */
  GLADE_HOOKUP_OBJECT_NO_REF (about, about, "about");

  return about;
}

