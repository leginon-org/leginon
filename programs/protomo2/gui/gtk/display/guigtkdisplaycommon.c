/*----------------------------------------------------------------------------*
*
*  guigtkdisplaycommon.c  -  guigtk: EM image viewer
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
#include "statistics.h"
#include "exception.h"
#include "message.h"
#include "mathdefs.h"
#include "strings.h"
#include "interface.h"
#include "support.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


/* variables */

const char *GuigtkDisplayVersion = GuigtkDisplayName"-"GuigtkDisplayVers;

const char *GuigtkDisplayCopyright = GuigtkDisplayCopy;


/* functions */

extern Status GuigtkDisplayTransfFile
              (const char *path,
               const Size dim,
               const Size count,
               const Coord *pos,
               const Coord *rot)

{

  FILE *handle = fopen( path, "w" );
  if ( handle == NULL ) {
    return pushexceptionmsg( E_ERRNO, ", ", path, NULL );
  }

  for ( Size i = 0; i < count; i++ ) {
    for ( Size j = 0; j < dim; j++ ) {
      fprintf( handle, " %.12g", *pos++ );
    }
    if ( rot != NULL ) {
      if ( *rot == CoordMax ) {
        rot += dim * dim;
      } else {
        fputs( "   ", handle );
        for ( Size j = 0; j < dim * dim; j++ ) {
          fprintf( handle, " %.12g", *rot++ );
        }
      }
    }
    fputc( '\n', handle );
  }

  if ( fclose( handle ) ) {
    return pushexceptionmsg( E_ERRNO, ", ", path, NULL );
  }

  return E_NONE;

}


extern Status GuigtkDisplayStat
              (GuigtkDisplay *display)

{
  GuigtkDisplayImage *dsp = &display->dsp;
  char buf[128];
  Status status = E_NONE;

  display->stat = StatInitializer;

  if ( TypeIsNumeric( dsp->dscr.type ) ) {

    status = Minmaxmean( dsp->dscr.type, dsp->size, dsp->addr, &display->stat, NULL );
    if ( status ) return status;

    sprintf( buf, "min %"CoordG"  max %"CoordG"  mean %"CoordG"  sd %"CoordG, display->stat.min, display->stat.max, display->stat.mean, display->stat.sd );
    GuigtkMessage( display->status & GuigtkDisplayLog, NULL, buf, NULL );

    if ( display->status & GuigtkDisplayRnge ) {
      display->status &= ~GuigtkDisplayRnge;
    } else {
      display->range[0] = display->stat.min;
      display->range[1] = display->stat.max;
    }
    display->thresh = ( display->range[0] + display->range[1] ) / 2;

    display->histomin = display->stat.min;

    switch ( dsp->dscr.type) {
      case TypeReal32:
      case TypeImag32:
      case TypeReal64:
      case TypeImag64:
        display->histostep = ( display->stat.max - display->stat.min ) / ( NHISTO - 1 ); break;
      default:
        display->histostep = ( display->stat.max - display->stat.min + 1 ) / NHISTO; break;
    }
  }

  return status;

}


extern Status GuigtkDisplayHistogram
              (GuigtkDisplay *display)

{
  Status status = E_NONE;

  display->histomaxcount = 0;
  if ( display->histostep > 0 ) {
    GuigtkDisplayImage *dsp = &display->dsp;
    Type type = dsp->dscr.type;
    Coord hmin = display->histomin;
    Coord hmax = hmin + NHISTO * display->histostep;
    Bool change = False;
    if ( display->range[0] < hmin ) {
      hmin = display->range[0]; change = True;
    }
    if ( display->range[1] > hmax ) {
      hmax = display->range[1]; change = True;
    }
    if ( change ) {
      display->histomin = hmin;
      switch ( type ) {
        case TypeReal32:
        case TypeImag32:
        case TypeReal64:
        case TypeImag64:
          display->histostep = ( hmax - hmin ) / ( NHISTO - 1 ); break;
        default:
          display->histostep = ( hmax - hmin + 1 ) / NHISTO; break;
      }
    }
    status = Histogram( type, dsp->size, dsp->addr, display->histomin, display->histostep, NHISTO, display->histo, NULL, NULL );
    if ( status ) return status;
    /* max histo count */
    for ( Size i = 0; i < NHISTO; i++ ) {
      if ( display->histo[i] > display->histomaxcount ) display->histomaxcount = display->histo[i];
    }
  }

  return status;

}


extern void GuigtkDisplaySetSize
            (GuigtkDisplay *display)

{
  Size sx = gdk_screen_width();
  Size sy = gdk_screen_height();

  sx *= 0.75; sy *= 0.75;
  if ( sx && sy ) {
    Coord zoom = 0;
    Size nx = display->img.len[0];
    Size ny = display->img.len[1];
    if ( nx > sx ) {
      zoom = sx; zoom /= nx;
      nx = sx;
    }
    if ( ny > sy ) {
      Coord z = sy; z /= ny;
      if ( z < zoom ) z = zoom;
      ny = sy;
    }
    if ( display->zoom <= 0 ) {
      display->zoom = ( zoom > 0 ) ? zoom : 1;
      GuigtkDisplayMessageZoom( display );
    }
    GtkWidget *widget = display->area->widget;
    gtk_widget_set_size_request( widget, nx, ny );
    gtk_widget_show( display->top );
    gtk_widget_set_size_request( widget, -1, -1 );
  }

}


extern void GuigtkDisplayButtons
            (GuigtkDisplay *display)

{
  static const char *item[] = { "real_part", "imaginary_part", "modulus", "log_modulus" };

  if ( display->func < GuigtkDisplayFuncMax ) {
    GtkCheckMenuItem *widget = GTK_CHECK_MENU_ITEM( lookup_widget( display->top, item[display->func] ) );
    gtk_check_menu_item_set_active( widget, TRUE );
  }

}


extern void GuigtkDisplaySensitivity
            (GuigtkDisplay *display)

{
  GtkWidget *widget;
  gboolean disp = FALSE;
  gboolean imag = FALSE;
  gboolean cmplx = FALSE;

  if ( display->status & GuigtkDisplayDisp ) disp = TRUE;
  if ( display->dsp.addr != NULL ) imag = TRUE;
  if ( imag && TypeIsCmplx( display->img.dscr.type ) ) cmplx = TRUE;

  widget = lookup_widget( display->top, "close" );
  gtk_widget_set_sensitive( widget, imag );

  widget = lookup_widget( display->top, "histogram" );
  gtk_widget_set_sensitive( widget, imag );
  widget = lookup_widget( display->top, "threshold" );
  gtk_widget_set_sensitive( widget, imag );

  widget = lookup_widget( display->top, "real_part" );
  gtk_widget_set_sensitive( widget, cmplx );
  widget = lookup_widget( display->top, "imaginary_part" );
  gtk_widget_set_sensitive( widget, cmplx );
  widget = lookup_widget( display->top, "modulus" );
  gtk_widget_set_sensitive( widget, cmplx );
  widget = lookup_widget( display->top, "log_modulus" );
  gtk_widget_set_sensitive( widget,cmplx );

  widget = lookup_widget( display->top, "zoom_reset" );
  gtk_widget_set_sensitive( widget,disp );
  widget = lookup_widget( display->top, "zoom_in" );
  gtk_widget_set_sensitive( widget, disp );
  widget = lookup_widget( display->top, "zoom_out" );
  gtk_widget_set_sensitive( widget, disp );

}


extern void GuigtkDisplayTitle
            (GuigtkDisplay *display)

{
  const char *name = display->name;
  char *title = display->title;

  char *sep = NULL;
  if ( name == NULL ) {
    name = title;
  } else if ( title != NULL ) {
    sep = " - ";
  }

  title = StringConcat( name, sep, title, NULL );
  if ( title != NULL ) {
    gtk_window_set_title( GTK_WINDOW(display->top), title );
    free( title );
  }

}


extern void GuigtkDisplayDisplay
            (GuigtkDisplay *display,
             Bool clear)

{

  if ( clear || ( display->dsp.addr == NULL ) ) {
    display->status &= ~( GuigtkDisplayDisp | GuigtkDisplayHist );
  } else {
    display->status |= GuigtkDisplayDisp | GuigtkDisplayHist;
  }
  GuigtkDisplayTitle( display );
  if ( display->his != NULL ) {
    GuigtkDisplayHistogramInit( display );
    GuigtkDisplayHistogramDraw( display );
    gtk_widget_queue_draw( display->his );
  }
  gtk_widget_queue_draw( display->area->widget );

}


extern void GuigtkDisplayMessagePos
            (GuigtkDisplay *display,
             Coord x,
             Coord y)

{
  Coord bignum = 99999999;
  char buf[128];

  if ( ( Fabs( x ) <= bignum ) && ( Fabs( y ) <= bignum ) ) {
    Coord z = display->z; z += display->dsp.low[2];
    if ( display->dsp.dscr.attr & ImageFourspc ) {
      x /= display->dsp.len[0];
      y /= display->dsp.len[1];
      z /= display->dsp.len[2];
      if ( display->dsp.len[2] > 1 ) {
        sprintf( buf, "spatial frequency x=%.4"CoordF" y=%.4"CoordF" z=%.4"CoordF" r=%.4"CoordF"", x, y, z, Sqrt( x*x + y*y + z*z ) );
      } else {
        sprintf( buf, "spatial frequency x=%.4"CoordF" y=%.4"CoordF" r=%.4"CoordF"", x, y, Sqrt( x*x + y*y ) );
      }
    } else {
      if ( display->dsp.len[2] > 1 ) {
        sprintf( buf,"x=%.1"CoordF" y=%.1"CoordF" z=%.1"CoordF, x, y, z );
      } else {
        sprintf( buf,"x=%.1"CoordF" y=%.1"CoordF, x, y );
      }
    }
    GuigtkMessage( display->status & GuigtkDisplayLog, display->bar, buf, NULL );
/*
    if ( print && ( display->flags & AppCoout ) ) {
      if ( display->dsp.dscr.attr & ImageFourspc ) {
        if ( display->dsp.len[2] > 1 ) {
          printf( "%10.6lf %10.6lf %10.6lf\n", x, y, z );
        } else {
          printf( "%10.6lf %10.6lf\n", x, y );
        }
      } else {
        if ( display->dsp.len[2] > 1 ) {
          printf( "%10.3lf %10.3lf %10.3lf\n", x, y, z );
        } else {
          printf( "%10.3lf %10.3lf\n", x, y );
        }
      }
    }
*/
  }

}


extern void GuigtkDisplayMessagePosz
            (GuigtkDisplay *display)

{
  char buf[64];

  Coord z = display->z; z += display->dsp.low[2];
  sprintf( buf, "z=%"CoordG, z );
  GuigtkMessage( display->status & GuigtkDisplayLog, display->bar, buf, NULL );

}


extern void GuigtkDisplayMessageZoom
            (GuigtkDisplay *display)

{
  char buf[64];

  sprintf( buf, "zoom=%-.3"CoordF, display->zoom );
  GuigtkMessage( display->status & GuigtkDisplayLog, display->bar, buf, NULL );

}


extern void GuigtkDisplayMessageKey
            (GuigtkDisplay *display,
             const char *msg,
             GuigtkDisplayStatus mask)

{
  char buf[128];

  sprintf( buf, "%s: %s", msg, ( display->status & mask ) ? "on" : "off" );
  GuigtkMessage( display->status & GuigtkDisplayLog, display->bar, buf, NULL );

}


extern Bool GuigtkDisplayFinal
            (GuigtkDisplay *display)

{
  Bool quit = False;

  if ( ( display->status & ( GuigtkDisplayPosMem | GuigtkDisplayPosMod ) ) == GuigtkDisplayPosMod ) {

    GtkWidget *dialog = create_savedialog( display );
    if ( dialog == NULL ) {
      GuigtkMessage( True, display->bar, "could not open save dialog", NULL );
    } else {
      GuigtkMessage( display->status & GuigtkDisplayLog, display->bar, "saving position list", NULL );
      gtk_widget_show( dialog );
    }

  } else {

    GuigtkDisplayUnloadImage( display );
    GuigtkDisplayDisplay( display, True );
    GuigtkDisplaySensitivity( display );
    if ( display->status & GuigtkDisplayExit ) quit = True;

  }

  return quit;

}
