/*----------------------------------------------------------------------------*
*
*  guigtkdisplayhisto.c  -  guigtk: EM image viewer
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "guigtkdisplaycommon.h"
#include "exception.h"
#include "mathdefs.h"
#include "support.h"


/* macros */

/* convert coordinates to right-handed system */
#define X(x) ( (x) + hx0 )
#define Y(y) ( wy - 1 - ( (y) + hy0 ) )
/* convert pixel values to/from index value */
#define val_to_marker(x) ( ( (x) - display->histomin ) / display->histostep )
#define marker_to_val(i) ( (i) * display->histostep + display->histomin )


/* constants */

#define markersize   10
#define markerheight 9
#define markerpos    (-3)


/* histogram origin */

static const gint hy0 = 30;


/* for drawing */

static GdkColor hdisp = { 0, 60000, 10000, 0 };
static GdkColor hclip = { 0, 60000, 50000, 0 };
static GdkColor hmark = { 0, 0, 0, 0 };


/* drawing */

static void GuigtkDisplayDraw
            (GuigtkDisplay *display,
             GtkWidget *widget)

{
  GdkGC *gcfore = display->gcfore;
  GdkGC *gcback = display->gcback;
  GdkPixmap *hmap = display->hmap;

  gint wx = widget->allocation.width;
  gint wy = widget->allocation.height;

  gint vmin, vmax;
  if ( display->status & GuigtkDisplayThrs ) {
    vmin = val_to_marker( display->thresh );
    vmax = NHISTO;
  } else {
    vmin = val_to_marker( display->range[0] );
    vmax = val_to_marker( display->range[1] );
  }

  gint hx0 = ( wx - NHISTO ) / 2;
  Coord f = ( wy - 1.5 * hy0 ) / display->histomaxcount;
  GdkPoint min[3], max[3];

  gdk_draw_rectangle( hmap, gcback, TRUE, 0, 0, wx, wy );

  gdk_gc_set_rgb_fg_color( gcfore, &hmark );
  gdk_draw_line( hmap, gcfore, X( 0 ), Y( -1 ), X( NHISTO - 1 ), Y( -1 ) );

  min[0].x = X( vmin );
  min[0].y = Y( markerpos );
  min[1].x = min[0].x - markersize / 2;
  min[1].y = min[0].y + markerheight;
  min[2].x = min[0].x + markersize / 2;
  min[2].y = min[0].y + markerheight;

  gdk_draw_polygon( hmap, gcfore, TRUE, min, 3 );

  if ( ~display->status & GuigtkDisplayThrs ) {

    max[0].x = X( vmax );
    max[0].y = Y( markerpos );
    max[1].x = max[0].x - markersize / 2;
    max[1].y = max[0].y + markerheight;
    max[2].x = max[0].x + markersize / 2;
    max[2].y = max[0].y + markerheight;

    gdk_draw_polygon( hmap, gcfore, TRUE, max, 3 );

  }

  if ( ( display->dsp.addr != NULL ) && ( display->status & GuigtkDisplayHist ) ) {
    gint i = 0;
    gdk_gc_set_rgb_fg_color( gcfore, &hclip );
    while ( i < vmin ) {
      gint sy = Ceil( f * display->histo[i] );
      gdk_draw_rectangle( hmap, gcfore, TRUE, X( i ), Y( sy - 1 ), 1, sy );
      i++;
    }
    gdk_gc_set_rgb_fg_color( gcfore, &hdisp );
    while ( ( i < vmax ) && ( i < NHISTO ) ) {
      gint sy = Ceil( f * display->histo[i] );
      gdk_draw_rectangle( hmap, gcfore, TRUE, X( i ), Y( sy - 1 ), 1, sy );
      i++;
    }
    gdk_gc_set_rgb_fg_color( gcfore, &hclip );
    while ( i < NHISTO ) {
      gint sy = Ceil( f * display->histo[i] );
      gdk_draw_rectangle( hmap, gcfore, TRUE, X( i ), Y( sy - 1 ), 1, sy );
      i++;
    }
  }

}


extern void GuigtkDisplayHistogramDraw
            (GuigtkDisplay *display)

{
  GtkWidget *widget = lookup_widget( display->his, "histogram_drawingarea" );

  GuigtkDisplayDraw( display, widget );

}


extern void GuigtkDisplayHistogramInit
            (GuigtkDisplay *display)

{
  GuigtkDisplayStatus stat;
  GtkWidget *label;
  char buf[64];

  stat = display->status & GuigtkDisplayHist;
  if ( display->dsp.addr == NULL ) stat = 0;

  buf[0] = 0;

  label = lookup_widget( GTK_WIDGET(display->his), "histogram_frame_title" );
  gtk_label_set_text( GTK_LABEL(label), ( display->name == NULL ) ? "" : display->name );

  if ( stat ) sprintf( buf, "%- "CoordG, display->stat.min );
  label = lookup_widget( GTK_WIDGET(display->his), "histogram_label_min_val" );
  gtk_label_set_text( GTK_LABEL(label), buf );

  if ( stat ) sprintf( buf, "%- "CoordG, display->stat.max );
  label = lookup_widget( GTK_WIDGET(display->his), "histogram_label_max_val" );
  gtk_label_set_text( GTK_LABEL(label), buf );

  if ( stat ) sprintf( buf, "%- "CoordG, display->stat.mean );
  label = lookup_widget( GTK_WIDGET(display->his), "histogram_label_mean_val" );
  gtk_label_set_text( GTK_LABEL(label), buf );

  if ( stat ) sprintf( buf, "%- "CoordG, display->stat.sd );
  label = lookup_widget( GTK_WIDGET(display->his), "histogram_label_sd_val" );
  gtk_label_set_text( GTK_LABEL(label), buf );

  if ( stat ) sprintf( buf, "%- "CoordG, display->histomin );
  label = lookup_widget( GTK_WIDGET(display->his), "histogram_label_left" );
  gtk_label_set_text( GTK_LABEL(label), buf );

  if ( stat ) sprintf( buf, "%- "CoordG, display->histomin + NHISTO * display->histostep );
  label = lookup_widget( GTK_WIDGET(display->his), "histogram_label_right" );
  gtk_label_set_text( GTK_LABEL(label), buf );

  if ( display->status & GuigtkDisplayThrs ) {

    if ( stat ) sprintf( buf, "%- "CoordG, display->thresh );
    label = lookup_widget( GTK_WIDGET(display->his), "histogram_label2_center" );
    gtk_label_set_text( GTK_LABEL(label), buf );

    buf[0] = 0;

    label = lookup_widget( GTK_WIDGET(display->his), "histogram_label2_left" );
    gtk_label_set_text( GTK_LABEL(label), buf );

    label = lookup_widget( GTK_WIDGET(display->his), "histogram_label2_right" );
    gtk_label_set_text( GTK_LABEL(label), buf );

  } else {

    if ( stat ) sprintf( buf, "%- "CoordG, display->range[0] );
    label = lookup_widget( GTK_WIDGET(display->his), "histogram_label2_left" );
    gtk_label_set_text( GTK_LABEL(label), buf );

    if ( stat ) sprintf( buf, "%- "CoordG, display->range[1] );
    label = lookup_widget( GTK_WIDGET(display->his), "histogram_label2_right" );
    gtk_label_set_text( GTK_LABEL(label), buf );

    buf[0] = 0;

    label = lookup_widget( GTK_WIDGET(display->his), "histogram_label2_center" );
    gtk_label_set_text( GTK_LABEL(label), buf );

  }

}


/* callbacks */

void
on_histogram_viewport_realize          (GtkWidget       *widget,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;
  GdkGCValues gcv;

  display->gcfore = gdk_gc_new( widget->window );
  display->gcback = gdk_gc_new( widget->window );
  gdk_gc_copy( display->gcfore, widget->style->fg_gc[GTK_STATE_NORMAL] );
  gdk_gc_copy( display->gcback, widget->style->mid_gc[GTK_STATE_NORMAL] );
  gdk_gc_set_fill( display->gcfore,GDK_SOLID );
  gdk_gc_set_line_attributes( display->gcfore, 1, GDK_LINE_SOLID, GDK_CAP_BUTT, GDK_JOIN_BEVEL );
  GdkColormap *cmap = gdk_gc_get_colormap( display->gcback );
  gdk_gc_get_values( display->gcback, &gcv );
  gdk_colormap_query_color( cmap, gcv.foreground.pixel, &display->hback );
  gtk_widget_modify_bg( widget, GTK_STATE_NORMAL, &display->hback );

}


extern gboolean on_histogram_drawingarea_configure_event
                                        (GtkWidget       *widget,
                                        GdkEventConfigure *event,
                                        gpointer         user_data)

{
  GuigtkDisplay *display = user_data;

  gint wx = widget->allocation.width;
  gint wy = widget->allocation.height;

  if ( display->hmap != NULL ) {
    gdk_pixmap_unref( display->hmap );
  }
  display->hmap = gdk_pixmap_new( widget->window, wx, wy, -1 );

  GuigtkDisplayDraw( display, widget );

  return TRUE;

}


extern gboolean on_histogram_drawingarea_expose_event
                                       (GtkWidget       *widget,
                                        GdkEventExpose  *event,
                                        gpointer         user_data)

{
  GuigtkDisplay *display = user_data;

  gdk_draw_pixmap( widget->window, widget->style->fg_gc[GTK_WIDGET_STATE(widget)],
                   display->hmap, event->area.x, event->area.y,
                   event->area.x, event->area.y,
                   event->area.width, event->area.height );
  return FALSE;

}


extern gboolean on_histogram_drawingarea_button_press_event
                                       (GtkWidget       *widget,
                                        GdkEventButton  *event,
                                        gpointer         user_data)

{
  GuigtkDisplay *display = user_data;

  if ( ( display->dsp.addr != NULL ) && ( display->status & GuigtkDisplayHist ) ) {
    if ( event->button == 1 ) {
      gint wx = widget->allocation.width;
      gint wy = widget->allocation.height;
      gint hx0 = ( wx - NHISTO ) / 2;
      /* distance from marker center */
      if ( display->status & GuigtkDisplayThrs ) {
        Coord m1x = X( val_to_marker( display->thresh ) ), m1y = Y( markerpos - markerheight / 2 );
        m1x -= event->x; m1y -= event->y;
        if ( ( m1x*m1x + m1y*m1y ) < ( markersize * markersize / 4.0 ) ) {
          display->markerselect = 1;
        } else {
          display->markerselect = 0;
        }
      } else {
        Coord m1x = X( val_to_marker( display->range[0] ) ), m1y = Y( markerpos - markerheight / 2 );
        Coord m2x = X( val_to_marker( display->range[1] ) ), m2y = Y( markerpos - markerheight / 2 );
        m1x -= event->x; m1y -= event->y;
        m2x -= event->x; m2y -= event->y;
        if ( ( m1x*m1x + m1y*m1y ) < ( markersize * markersize / 4.0 ) ) {
          display->markerselect = 1;
        } else if ( ( m2x*m2x + m2y*m2y ) < ( markersize * markersize / 4.0 ) ) {
          display->markerselect = 2;
        } else {
          display->markerselect = 0;
        }
      }
    } /* end if button */
  }
  return FALSE;

}


extern gboolean on_histogram_drawingarea_button_release_event
                                       (GtkWidget       *widget,
                                        GdkEventButton  *event,
                                        gpointer         user_data)

{
  GuigtkDisplay *display = user_data;

  if ( display->markerselect ) {
    gtk_widget_queue_draw( widget );
    gtk_widget_queue_draw( display->area->widget );
    display->markerselect = 0;
  }
  return FALSE;

}


extern gboolean on_histogram_drawingarea_motion_notify_event
                                       (GtkWidget       *widget,
                                        GdkEventMotion  *event,
                                        gpointer         user_data)

{
  GuigtkDisplay *display = user_data;
  GtkWidget *label;
  char buf[64];

  if ( ( display->dsp.addr != NULL ) && ( display->status & GuigtkDisplayHist ) ) {

    if ( event->state & GDK_BUTTON1_MASK ) {

      if ( display->markerselect ) {

        Bool redraw = False;
        Bool set0 = False, set1 = False;
        gint wx = widget->allocation.width;
        gint hx0 = ( wx - NHISTO ) / 2;
        gint i = event->x - hx0;
        if ( i < 0 ) i = 0;
        if ( i >= NHISTO ) i = NHISTO - 1;

        if ( display->status & GuigtkDisplayThrs ) {

          if ( display->markerselect == 1 ) {
            if ( i != val_to_marker( display->thresh ) ) {
              display->thresh = marker_to_val( i );
              sprintf( buf,"%- "CoordG, display->thresh );
              label = lookup_widget( display->his, "histogram_label2_center" );
              gtk_label_set_text( GTK_LABEL(label), buf );
              redraw = True;
            }
          }

        } else {

          if ( display->markerselect == 1 ) {
            if ( i != val_to_marker( display->range[0] ) ) {
              display->range[0] = marker_to_val( i );
              set0 = True;
              if ( display->range[0] > display->range[1] ) {
                display->range[1] = display->range[0];
                set1 = True;
              }
              redraw = True;
            }
          } else {
            if ( i != val_to_marker( display->range[1] ) ) {
              display->range[1] = marker_to_val( i );
              set1 = True;
              if ( display->range[1] < display->range[0] ) {
                display->range[0] = display->range[1];
                set0 = True;
              }
              redraw = True;
            }
          }

          if ( set0 ) {
            sprintf( buf,"%- "CoordG, display->range[0] );
            label = lookup_widget( display->his, "histogram_label2_left" );
            gtk_label_set_text( GTK_LABEL(label), buf );
          }
          if ( set1 ) {
            sprintf( buf,"%- "CoordG, display->range[1] );
            label = lookup_widget( display->his, "histogram_label2_right" );
            gtk_label_set_text( GTK_LABEL(label), buf );
          }

        }

        if ( redraw ) {
          GuigtkDisplayDraw( display, widget );
          gtk_widget_queue_draw( widget );
          gtk_widget_queue_draw( display->area->widget );
        }

      }

    }

  }

  return TRUE;

}


#define markersep 3

gboolean
on_histogram_drawingarea_bottom_configure_event
                                        (GtkWidget       *widget,
                                        GdkEventConfigure *event,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  gint wx = widget->allocation.width;
  gint wy = widget->allocation.height;
  GdkPoint mark[3]; gint x0, y0;

  if ( display->hbot != NULL ) {
    gdk_pixmap_unref( display->hbot );
  }
  display->hbot = gdk_pixmap_new( widget->window, wx, wy, -1 );

  gdk_draw_rectangle( display->hbot, display->gcback, TRUE, 0, 0, wx, wy );
  gdk_gc_set_rgb_fg_color( display->gcfore, &hmark );

  x0 = wx / 2 - markersep;
  y0 = wy / 2;
  mark[0].x = x0 - markerheight; mark[0].y = y0;
  mark[1].x = x0;                mark[1].y = y0 - markersize / 2;
  mark[2].x = x0;                mark[2].y = y0 + markersize / 2;
  gdk_draw_polygon( display->hbot, display->gcfore, TRUE, mark, 3 );

  x0 = wx / 2 + markersep;
  y0 = wy / 2;
  mark[0].x = x0 + markerheight; mark[0].y = y0;
  mark[1].x = x0;                mark[1].y = y0 - markersize / 2;
  mark[2].x = x0;                mark[2].y = y0 + markersize / 2;
  gdk_draw_polygon( display->hbot, display->gcfore, TRUE, mark, 3 );

  return TRUE;

}


extern gboolean on_histogram_drawingarea_bottom_expose_event
                                       (GtkWidget       *widget,
                                        GdkEventExpose  *event,
                                        gpointer         user_data)

{
  GuigtkDisplay *display = user_data;

  gdk_draw_pixmap( widget->window, widget->style->fg_gc[GTK_WIDGET_STATE(widget)],
                   display->hbot, event->area.x, event->area.y,
                   event->area.x, event->area.y,
                   event->area.width, event->area.height);
  return FALSE;

}


static void histogram_limits
            (GuigtkDisplay *display,
             Coord hmin,
             Coord hmax)

{
  GtkWidget *label;
  char buf[64];

  if ( hmin > display->range[0] ) hmin = display->range[0];
  if ( hmax < display->range[1] ) hmax = display->range[1];
  if ( hmax > hmin ) {
    display->histomin = hmin;
    switch ( display->dsp.dscr.type ) {
      case TypeReal32:
      case TypeImag32:
      case TypeReal64:
      case TypeImag64:
        display->histostep = ( hmax - hmin ) / ( NHISTO - 1 ); break;
      default:
        display->histostep = ( hmax - hmin + 1 ) / NHISTO; break;
    }
    sprintf( buf,"%- "CoordG, hmin );
    label = lookup_widget( display->his, "histogram_label_left" );
    gtk_label_set_text( GTK_LABEL(label), buf );
    sprintf( buf, "%- "CoordG, hmax );
    label = lookup_widget( display->his, "histogram_label_right" );
    gtk_label_set_text( GTK_LABEL(label), buf );
    GuigtkDisplayHistogram( display );
    GuigtkDisplayHistogramDraw( display );
    gtk_widget_queue_draw( display->his );
  }

}


gboolean
on_histogram_drawingarea_left_button_press_event
                                        (GtkWidget       *widget,
                                        GdkEventButton  *event,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  if ( ( display->dsp.addr != NULL ) && ( display->status & GuigtkDisplayHist ) ) {
    if ( event->button == 1 ) {
      gint wx = widget->allocation.width;
      gint wy = widget->allocation.height;
      /* distance from marker center */
      Coord m1x = wx / 2 - markersep - markerheight / 2.0, m1y = wy / 2;
      Coord m2x = wx / 2 + markersep + markerheight / 2.0, m2y = wy / 2;
      m1x -= event->x; m1y -= event->y;
      m2x -= event->x; m2y -= event->y;
      if ( ( m1x*m1x + m1y*m1y ) < ( markersize * markersize / 4.0 ) ) {
        /* decrease histomin */
        Coord hmin = display->histomin - ( NHISTO / 2 ) * display->histostep;
        Coord hmax = display->histomin + NHISTO * display->histostep;
        histogram_limits( display, hmin, hmax );
      } else if ( ( m2x*m2x + m2y*m2y ) < ( markersize * markersize / 4.0 ) ) {
        /* move histomin up to image min */
        Coord hmax = display->histomin + NHISTO * display->histostep;
        histogram_limits( display, display->range[0], hmax );
      }
    } /* end if button */
  }
  return FALSE;

}


gboolean
on_histogram_drawingarea_right_button_press_event
                                        (GtkWidget       *widget,
                                        GdkEventButton  *event,
                                        gpointer         user_data)
{
  GuigtkDisplay *display = user_data;

  if ( ( display->dsp.addr != NULL ) && ( display->status & GuigtkDisplayHist ) ) {
    if ( event->button == 1 ) {
      gint wx = widget->allocation.width;
      gint wy = widget->allocation.height;
      /* distance from marker center */
      Coord m1x = wx / 2 - markersep - markerheight / 2.0, m1y = wy / 2;
      Coord m2x = wx / 2 + markersep + markerheight / 2.0, m2y = wy / 2;
      m1x -= event->x; m1y -= event->y;
      m2x -= event->x; m2y -= event->y;
      if ( ( m1x*m1x + m1y*m1y ) < ( markersize * markersize / 4.0 ) ) {
        /* move histomax down to image max */
        histogram_limits( display, display->histomin, display->range[1] );
      } else if ( ( m2x*m2x + m2y*m2y ) < ( markersize * markersize / 4.0 ) ) {
        /* increase histomax */
        Coord hmax = display->histomin + ( NHISTO + NHISTO / 2 ) * display->histostep;
        histogram_limits( display, display->histomin, hmax );
      }
    } /* end if button */
  }
  return FALSE;

}
