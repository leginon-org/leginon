/*----------------------------------------------------------------------------*
*
*  guigtkdisplay.c  -  guigtk: EM image viewer
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
#include "array.h"
#include "stringparse.h"
#include "textio.h"
#include "exception.h"
#include "mathdefs.h"
#include "message.h"
#include "interface.h"
#include "support.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <gdk/gdkkeysyms.h>
#include <gtk/gtkgl.h>
#include <GL/glext.h>



/* functions */

void
on_drawingarea_realize                 (GtkWidget       *widget,
                                        gpointer         user_data)

{
  GuigtkDisplay *display = user_data;

  if ( !GuigtkAreaBegin( display->area ) ) {

    glShadeModel( GL_FLAT );
    glMatrixMode( GL_MODELVIEW );
    glLoadIdentity();

    GuigtkAreaEnd( display->area );

  }

}


/* change size */

gboolean
on_drawingarea_configure_event         (GtkWidget       *widget,
                                        GdkEventConfigure *event,
                                        gpointer         user_data)

{
  GuigtkDisplay *display = user_data;

  if ( GuigtkAreaBegin( display->area ) ) return FALSE;

  GLint wx = widget->allocation.width;
  GLint wy = widget->allocation.height;
  glMatrixMode( GL_PROJECTION );
  glLoadIdentity();
  glOrtho( 0, wx - 1, 0, wy - 1, -1, 1 );
  glViewport( 0, 0, wx, wy );

  GuigtkAreaEnd( display->area );

  if ( display->dsp.addr != NULL ) display->status |= GuigtkDisplaySize;

  return TRUE;

}


gboolean
on_drawingarea_enter_notify_event      (GtkWidget       *widget,
                                        GdkEventCrossing *event,
                                        gpointer         user_data)

{

  gtk_grab_add( widget );

  return TRUE;

}



gboolean
on_drawingarea_leave_notify_event      (GtkWidget       *widget,
                                        GdkEventCrossing *event,
                                        gpointer         user_data)

{

  gtk_grab_remove( widget );

  return TRUE;

}



#define W 1.0
#define L (4*W)

gboolean
on_drawingarea_expose_event            (GtkWidget       *widget,
                                        GdkEventExpose  *event,
                                        gpointer         user_data)

{
  GuigtkDisplay *display = user_data;
  Size *len = display->dsp.len;

  if ( GuigtkAreaBegin( display->area ) ) return FALSE;

  glMatrixMode( GL_MODELVIEW );
  glClearColor( 0, 0.12, 0.12, 0 );
  glClear( GL_COLOR_BUFFER_BIT );
  glEnableClientState( GL_VERTEX_ARRAY );

  if ( display->status & GuigtkDisplayDisp ) {

    /* image size */
    Size nx = len[0];
    Size ny = len[1];
    /* window size */
    Size wx = widget->allocation.width;
    Size wy = widget->allocation.height;
    /* bottom left of window in array coos, assuming 0,0 array origin */
    Coord zoom = display->zoom;
    Coord rx = display->dx - ( wx / 2 ) / zoom;
    Coord ry = display->dy - ( wy / 2 ) / zoom;
    /* corresponding integer point must lie within window */
    Index sx, sy;
    { Coord r = Ceil( rx ); sx = ( r < IndexMax ) ? r : IndexMax; }
    { Coord r = Ceil( ry ); sy = ( r < IndexMax ) ? r : IndexMax; }
    /* asjust if outside window */
    if ( sx < 0 ) {
      rx = -rx;
      sx = 0;
    } else {
      Coord hx = Ceil( rx + wx / zoom );
      nx = ( hx < nx ) ? ( hx - sx + 1 ) : ( nx - sx );
      rx = sx - rx;
    }
    if ( sy < 0 ) {
      ry = -ry;
      sy = 0;
    } else {
      Coord hy = Ceil( ry + wy / zoom );
      ny = ( hy < ny ) ? ( hy - sy + 1 ) : ( ny - sy );
      ry = sy - ry;
    }
    rx *= zoom;
    ry *= zoom;
    /* draw black rectangle */
    glColor3f( 0, 0.2, 0.2 );
    glBegin( GL_QUADS );
    glVertex2d( rx, ry );
    glVertex2d( rx + nx * zoom, ry );
    glVertex2d( rx + nx * zoom, ry + ny * zoom );
    glVertex2d( rx, ry + ny * zoom );
    glEnd();
    /* max size ?? */
    if ( (GLint)nx > display->maxviewport[0] ) nx = display->maxviewport[0];
    if ( (GLint)ny > display->maxviewport[1] ) ny = display->maxviewport[1];
    /* array address */
    uint8_t *addr = display->dsp.addr;
    if ( ( len[2] > 1 ) && display->z ) {
      addr += TypeGetSize(display->dsp.dscr.type) * display->z * len[1] * len[0];
    }
    /* pixel transfer */
    GLfloat min, max, scale = 1, bias = 0;
    if ( display->status & GuigtkDisplayThrs ) {
      min = display->thresh;
      max = display->thresh + display->histostep / 100;
    } else {
      min = display->range[0];
      max = display->range[1];
    }
    if ( max > min ) {
      switch ( display->dsp.dscr.type ) {
        case TypeRGB:
        case TypeUint8:  min /= 255.0;                         max /= 255.0;                         break;
        case TypeUint16: min /= 65535.0;                       max /= 65535.0;                       break;
        case TypeUint32: min /= 4294967295.0;                  max /= 4294967295.0;                  break;
        case TypeInt8:   min = ( 2 * min + 1 ) / 255.0;        max = ( 2 * max + 1 ) / 255.0;        break;
        case TypeInt16:  min = ( 2 * min + 1 ) / 65535.0;      max = ( 2 * max + 1 ) / 65535.0;      break;
        case TypeInt32:  min = ( 2 * min + 1 ) / 4294967295.0; max = ( 2 * max + 1 ) / 4294967295.0; break;
        case TypeReal32:
        case TypeReal64:
        case TypeImag32:
        case TypeImag64: break;
        default: scale = min = max = 0;
      }
      if ( max > min ) {
        scale = 1 / ( max - min );
        bias = ( 1 - ( max + min ) * scale ) / 2;
      }
    }
    glPixelTransferf( GL_RED_SCALE,  scale );
    glPixelTransferf( GL_GREEN_SCALE,scale );
    glPixelTransferf( GL_BLUE_SCALE, scale );
    glPixelTransferf( GL_RED_BIAS,   bias );
    glPixelTransferf( GL_GREEN_BIAS, bias );
    glPixelTransferf( GL_BLUE_BIAS,  bias );
    glRasterPos2d( rx, ry );
    glPixelZoom( zoom, zoom );
    glPixelStorei( GL_UNPACK_ALIGNMENT, 1 );
    glPixelStorei( GL_UNPACK_ROW_LENGTH, len[0] );
    glPixelStorei( GL_UNPACK_SKIP_PIXELS, sx );
    glPixelStorei( GL_UNPACK_SKIP_ROWS, sy );
    glDrawPixels( nx, ny, display->fmt, display->glt, addr );

    if ( ( display->status & GuigtkDisplayPosDisp ) && ( display->pos != NULL ) ) {
      static GLfloat abov[] = { 0.3, 0.9, 0.3, 1.0 };
      static GLfloat belo[] = { 0.0, 0.7, 1.0, 1.0 };
      static GLfloat curr[] = { 1.0, 0.8, 0.0, 1.0 };
      Coord *pos = display->pos;
      Size dim = display->dsp.dscr.dim;
      for ( Size i = 0; i < display->count; i++, pos += dim ) {
        Coord x = ( pos[0] - display->dsp.low[0] - display->dx ) * zoom + ( wx / 2 );
        Coord y = ( pos[1] - display->dsp.low[1] - display->dy ) * zoom + ( wy / 2 );
        if ( dim == 3 ) {
          Coord z = Round( pos[2] - display->dsp.low[2] );
          if ( z == display->z ) {
            glColor4fv( curr );
          } else if ( z < display->z ) {
            if ( display->status & GuigtkDisplayPosCurr ) continue;
            glColor4fv( belo );
          } else {
            if ( display->status & GuigtkDisplayPosCurr ) continue;
            glColor4fv( abov );
          }
        } else {
          glColor4fv( curr );
        }
        glPushMatrix();
        glTranslatef( x, y, 0 );
        if ( display->status & GuigtkDisplayPosSqr ) {
          static GLfloat v[4][2] = {
            { -L, -L },
            {  L, -L },
            {  L,  L },
            { -L,  L },
          };
          glVertexPointer( 2, GL_FLOAT, 0, v );
          glDrawArrays( GL_QUADS, 0, 4 );
        } else {
          static GLfloat v[8][2] = {
            { -L, -W },
            {  L, -W },
            {  L,  W },
            { -L,  W },
            { -W, -L },
            {  W, -L },
            {  W,  L },
            { -W,  L },
          };
          glVertexPointer( 2, GL_FLOAT, 0, v );
          glDrawArrays( GL_QUADS, 0, 8 );
        }
        glPopMatrix();
      }
    }

  }

  GuigtkAreaDraw( display->area );

  GuigtkAreaEnd( display->area );

  return TRUE;

}


static void insertpos
            (GuigtkDisplay *display,
             Coord r[3])

{
  Size dim = display->dsp.dscr.dim;

  Coord *pos = realloc( display->pos, ( display->count + 1 ) * dim * sizeof(Coord) );
  if ( pos == NULL ) return;

  display->pos = pos;

  pos += display->count * dim;

  pos[0] = r[0];
  pos[1] = r[1];
  if ( dim > 2 ) pos[2] = r[2];

  if ( display->rot != NULL ) {

    Coord *rot = realloc( display->rot, ( display->count + 1 ) * dim * dim * sizeof(Coord) );
    if ( rot == NULL ) return;

    display->rot = rot;

    rot += display->count * dim * dim;

    rot[0] = CoordMax;

  }

  display->count++;
  display->status |= GuigtkDisplayPosMod;

}


static void setrot
            (GuigtkDisplay *display,
             Coord r[3])

{
  Size dim = display->dsp.dscr.dim;
  Coord a, b, x[3];

  if ( !display->count ) return;

  Coord *rot = display->rot;
  if ( rot == NULL ) {
    rot = malloc( display->count * dim * dim * sizeof(Coord) );
    if ( rot == NULL ) return;
    display->rot = rot;
    for ( Size i = 0; i < display->count; i++, rot += dim * dim ) {
      *rot = CoordMax;
    }
  }
  rot = display->rot + ( display->count - 1 ) * dim * dim;

  Coord *pos = display->pos + ( display->count - 1 ) * dim;

  if ( dim == 3 ) {

    x[0] = r[0] - pos[0];
    x[1] = r[1] - pos[1];
    x[2] = r[2] - pos[2];

    a = Sqrt( x[0] * x[0] + x[1] * x[1] + x[2] * x[2] );

    if ( a > 0 ) {

      b = Sqrt( x[0] * x[0] + x[1] * x[1] );

      if ( b > 0 ) {

        rot[0] =  x[1] / b;
        rot[1] = -x[0] / b;
        rot[2] =  0;

        rot[3] = ( x[0] * x[2] ) / ( a * b );
        rot[4] = ( x[1] * x[2] ) / ( a * b );
        rot[5] = -b / a;

        rot[6] = x[0] / a;
        rot[7] = x[1] / a;
        rot[8] = x[2] / a;

      }

    }

  } else if ( dim == 2 ) {

    x[0] = r[0] - pos[0];
    x[1] = r[1] - pos[1];

    a = Sqrt( x[0] * x[0] + x[1] * x[1] );

    if ( a > 0 ) {

      rot[0] = x[0] / a;
      rot[1] = x[1] / a;
      rot[2] =  rot[1];
      rot[3] = -rot[0];

    }

  }

}


static void deletepos
            (GuigtkDisplay *display,
             Coord r[3])

{
  Coord *pos = display->pos;
  Coord *rot = display->rot;
  Size dim = display->dsp.dscr.dim;
  Coord tol = 8 / ( display->zoom * display->zoom );

  for ( Size i = 0; i < display->count; i++, pos += dim, rot += dim * dim ) {
    Coord d2 = 0;
    for ( Size j = 0; j < dim; j++ ) {
      Coord d = r[j] - pos[j];
      d2 += d * d;
    }
    if ( d2 < tol ) {
      Coord *ptr = pos + dim;
      for ( Size k = i + 1; k < display->count; k++ ) {
        for ( Size j = 0; j < dim; j++ ) {
          *pos++ = *ptr++;
        }
      }
      if ( display->rot != NULL ) {
        ptr = rot + dim * dim;
        for ( Size k = i + 1; k < display->count; k++ ) {
          for ( Size j = 0; j < dim * dim; j++ ) {
            *rot++ = *ptr++;
          }
        }
      }
      display->count--;
      display->status |= GuigtkDisplayPosMod;
      break;
    }
  }

}


gboolean
on_drawingarea_button_press_event      (GtkWidget       *widget,
                                        GdkEventButton  *event,
                                        gpointer         user_data)

{
  GuigtkDisplay *display = user_data;
  guint state = event->state; /* mask */
  guint button = event->button; /* button 1 to 5 */

  if ( display->dsp.addr != NULL ) {

    Bool redraw = False;
    Bool clear = True;

    switch ( event->type ) {
      case GDK_BUTTON_PRESS:
      case GDK_2BUTTON_PRESS:
      case GDK_3BUTTON_PRESS: {
        display->mouse_x = event->x;
        display->mouse_y = event->y;
        switch ( button ) {
          case 1: {
            /* window system: origin is top left */
            Size wx = widget->allocation.width;
            Size wy = widget->allocation.height;
            /* window pos relative to window center */
            Coord px = event->x - ( wx / 2 );
            Coord py = ( wy - 1 - event->y ) - ( wy / 2 );
            /* convert to image coos */
            Coord p[3];
            p[0] = px / display->zoom + display->dx + display->dsp.low[0];
            p[1] = py / display->zoom + display->dy + display->dsp.low[1];
            p[2] = display->z; p[2] += display->dsp.low[2];
            if ( display->dsp.dscr.dim < 3 ) p[2] = 0;
            GuigtkDisplayMessagePos( display, p[0], p[1] );
            if ( state & GDK_SHIFT_MASK ) {
              if ( display->status & GuigtkDisplayPosRot ) {
                if ( display->status & GuigtkDisplayPosOri ) {
                  setrot( display, p );
                } else {
                  insertpos( display, p );
                  display->status |= GuigtkDisplayPosOri;
                  clear = False;
                }
              } else {
                insertpos( display, p );
              }
              display->status |= GuigtkDisplayPosDisp;
              redraw = True;
            } else if ( state & GDK_CONTROL_MASK ) {
              deletepos( display, p );
              display->status |= GuigtkDisplayPosDisp;
              redraw = True;
            }
            break;
          }
          case 2: {
            GuigtkDisplayMessageZoom( display ); break;
          }
        } /* end switch button */
        break;
      }
      case GDK_BUTTON_RELEASE: {
        break;
      }
      default: break;
    } /* end switch event->type */

    if ( redraw ) {
      gtk_widget_queue_draw( display->area->widget );
    }
    if ( clear ) {
      display->status &= ~GuigtkDisplayPosOri;
    }

  }

  return FALSE;

}


gboolean
on_drawingarea_motion_notify_event     (GtkWidget       *widget,
                                        GdkEventMotion  *event,
                                        gpointer         user_data)

{
  GuigtkDisplay *display = user_data;

  if ( display->dsp.addr != NULL ) {
    Bool redraw = False;
    /* left button moves image */
    if ( event->state & GDK_BUTTON1_MASK ) {
      Coord dx = event->x - display->mouse_x;
      Coord dy = display->mouse_y - event->y; /* mouse origin is top left in window */
      if ( ( dx != 0 ) || ( dy != 0 ) ) {
        dx /= display->zoom;
        dy /= display->zoom;
        display->dx -= dx;
        display->dy -= dy;
        redraw = True;
      }
    }
    /* middle button zooms image */
    if ( event->state & GDK_BUTTON2_MASK ) {
/*    Coord dx = event->x - display->mouse_x; unused */
      Coord dy = display->mouse_y - event->y; /* mouse origin is top left in window */
      display->zoom *= Exp( -0.002 * dy );
      GuigtkDisplayMessageZoom( display );
      redraw = True;
    }
    /* update mouse pos */
    display->mouse_x = event->x;
    display->mouse_y = event->y;
    /* redraw image if moved */
    if ( redraw ) {
      gtk_widget_queue_draw( display->area->widget );
    }
  }
  return TRUE;

}


gboolean
on_drawingarea_key_press_event         (GtkWidget       *widget,
                                        GdkEventKey     *event,
                                        gpointer         user_data)

{
  GuigtkDisplay *display = user_data;
  gboolean ret = FALSE;

  if ( display->dsp.addr != NULL ) {

    Bool redraw = False;

    if ( event->type == GDK_KEY_PRESS ) {
      switch ( event->keyval ) {
        case GDK_Down: {
          if ( ( display->dsp.len[2] > 1 ) && display->z ) {
            display->z--;
            GuigtkDisplayMessagePosz( display );
            redraw = True;
          }
          break;
        }
        case GDK_Up: {
          if ( ( display->dsp.len[2] > 1 ) && ( display->z < display->dsp.len[2] - 1 ) ) {
            display->z++;
            GuigtkDisplayMessagePosz( display );
            redraw = True;
          }
          break;
        }
        case GDK_L:
        case GDK_l: {
          display->status ^= GuigtkDisplayPosCurr;
          GuigtkDisplayMessageKey( display, "current level", GuigtkDisplayPosCurr );
          redraw = True;
          break;
        }
        case GDK_P:
        case GDK_p: {
          display->status ^= GuigtkDisplayPosDisp;
          GuigtkDisplayMessageKey( display, "markers", GuigtkDisplayPosDisp );
          redraw = True;
          break;
        }
        case GDK_Q:
        case GDK_q: {
          display->status ^= GuigtkDisplayPosSqr;
          GuigtkDisplayMessageKey( display, "square markers", GuigtkDisplayPosSqr );
          redraw = True;
          break;
        }
        case GDK_R:
        case GDK_r: {
          display->status ^= GuigtkDisplayPosRot;
          GuigtkDisplayMessageKey( display, "store rotation", GuigtkDisplayPosRot );
          redraw = True;
          break;
        }
      } /* end switch */
    } /* end if event->type */

    if ( redraw ) {
      gtk_widget_queue_draw( display->area->widget );
    }

  }

  return ret;

}


static GuigtkDisplay *GuigtkDisplayAlloc
                      (const GuigtkDisplayParam *param)

{

  GuigtkDisplay *display = malloc( sizeof(GuigtkDisplay) );
  if ( display == NULL ) return NULL;
  memset( display, 0, sizeof(*display) );

  display->name = NULL;
  display->handle = NULL;
  display->iopar = ImageioParamDefault;
  display->func = GuigtkDisplayFuncMax;
  display->count = 0;
  display->pos = NULL;
  display->rot = NULL;
  display->gcfore = NULL;
  display->gcback = NULL;
  display->hmap = NULL;
  display->hbot = NULL;

  if ( param != NULL ) {
    if ( param->iopar != NULL ) display->iopar = *param->iopar;
    if ( param->zoom > 0 ) display->zoom = param->zoom;
    if ( param->range[0] <= param->range[1] ) {
      display->range[0] = param->range[0];
      display->range[1] = param->range[1];
      display->status |= GuigtkDisplayRnge;
    }
    if ( param->func < GuigtkDisplayFuncMax ) {
      display->func = param->func;
    }
    if ( param->flags & GuigtkDisplayLogging ) display->status |= GuigtkDisplayLog;
    if ( param->flags & GuigtkDisplayDetach )  display->status |= GuigtkDisplayDupl;
  }

  return display;

}


static Status GuigtkDisplayExec
              (GuigtkDisplay *display,
               const Image *image,
               const void *addr,
               GuigtkDisplayTransf *transf)

{
  Status status;

  /* init */

  if ( transf == NULL ) {
    display->status &= ~GuigtkDisplayPosMem;
  } else {
    display->status |= GuigtkDisplayPosMem;
    transf->dim = image->dim;
    transf->count = 0;
    transf->pos = NULL;
    transf->rot = NULL;
  }

  /* detached process */

  pid_t pid = 1;
  if ( display->status & GuigtkDisplayDupl ) {
    pid = fork();
    if ( pid < 0 ) {
      status = pushexception( E_ERRNO ); goto exit1;
    } else if ( pid > 0 ) {
      /* parent */
      int wstat;
      waitpid( pid, &wstat, 0 );
      return E_NONE;
    } else {
      /* child */
      if ( fork() ) {
        _exit( EXIT_SUCCESS );
      }
    }
  }

  /* interface */

  status = GuigtkInit();
  if ( exception( status ) ) goto exit1;

  display->area = GuigtkAreaCreate( NULL );
  if ( testcondition( display->area == NULL ) ) goto exit1;

  GtkWidget *widget = display->area->widget;

  display->top = create_top( display );
  display->bar = lookup_widget( display->top, "appbar" );
  display->title = strdup( gtk_window_get_title( GTK_WINDOW(display->top) ) );

  GtkWidget *viewport = lookup_widget( display->top, "viewport" );
  gtk_container_add( GTK_CONTAINER(viewport), widget );

  gtk_widget_add_events( widget, GDK_EXPOSURE_MASK | GDK_BUTTON1_MOTION_MASK | GDK_BUTTON2_MOTION_MASK
                               | GDK_BUTTON_PRESS_MASK | GDK_KEY_PRESS_MASK
                               | GDK_ENTER_NOTIFY_MASK | GDK_LEAVE_NOTIFY_MASK);

  g_signal_connect_after( G_OBJECT(widget), "realize",       G_CALLBACK(on_drawingarea_realize),             display );
  g_signal_connect( G_OBJECT(widget), "configure_event",     G_CALLBACK(on_drawingarea_configure_event),     display );
  g_signal_connect( G_OBJECT(widget), "enter_notify_event",  G_CALLBACK(on_drawingarea_enter_notify_event),  display );
  g_signal_connect( G_OBJECT(widget), "leave_notify_event",  G_CALLBACK(on_drawingarea_leave_notify_event),  display );
  g_signal_connect( G_OBJECT(widget), "expose_event",        G_CALLBACK(on_drawingarea_expose_event),        display );
  g_signal_connect( G_OBJECT(widget), "button_press_event",  G_CALLBACK(on_drawingarea_button_press_event),  display );
  g_signal_connect( G_OBJECT(widget), "motion_notify_event", G_CALLBACK(on_drawingarea_motion_notify_event), display );
  g_signal_connect( G_OBJECT(widget), "key_press_event",     G_CALLBACK(on_drawingarea_key_press_event),     display );

  gtk_widget_realize( widget );

  status = GuigtkAreaBegin( display->area );
  if ( status ) goto exit2;
  glGetIntegerv( GL_MAX_VIEWPORT_DIMS, display->maxviewport );
  GuigtkAreaEnd( display->area );
  GraphErrorClear();

  GuigtkDisplayButtons( display );

  display->status |= GuigtkDisplayInit;

  GuigtkDisplaySensitivity( display );

  if ( display->status & GuigtkDisplayDisp ) {
    GuigtkDisplaySetSize( display );
    display->status |= GuigtkDisplaySize;
  }

  GuigtkDisplayTitle( display );

  gtk_widget_show( display->top );

  gtk_main();

  if ( display->status & GuigtkDisplayPosMem ) {
    transf->count = display->count;
    transf->pos = display->pos;
    transf->rot = display->rot;
    display->count = 0;
    display->pos = NULL;
    display->rot = NULL;
  }

  exit2:

  GuigtkAreaDestroy( display->area );
  if ( display->title != NULL ) free( display->title );

  exit1:

  if ( ( display->img.alloc ) && ( display->img.addr != NULL ) ) free( display->img.addr );
  if ( ( display->dsp.alloc ) && ( display->dsp.addr != NULL ) ) free( display->dsp.addr );

  GuigtkDisplayClose( display );

  if ( !pid ) _exit( EXIT_SUCCESS ); /* if detached */

  return status;

}


extern Status GuigtkDisplayCreate
              (const Image *image,
               const void *addr,
               const GuigtkDisplayParam *param)

{
  Status status;

  if ( image == NULL ) return pushexception( E_ARGVAL );
  if ( addr == NULL ) return pushexception( E_ARGVAL );

  if ( ( image->dim < 2 ) || ( image->dim > 3 ) ) {
    return pushexception( E_ARRAY_DIM );
  }

  GuigtkDisplay *display = GuigtkDisplayAlloc( param );
  if ( display == NULL ) return pushexception( E_MALLOC );

  status = GuigtkDisplayLoadImage( display, image, addr );
  if ( pushexception( status ) ) goto exit1;

  status = GuigtkDisplayExec( display, image, addr, NULL );
  if ( exception( status ) ) goto exit2;

  exit2: if ( display->pos != NULL ) free( display->pos );
         if ( display->rot != NULL ) free( display->rot );

  exit1: free( display );

  return status;

}


static Status GuigtkDisplayLoadTransf
              (GuigtkDisplay *display,
               const GuigtkDisplayTransf *transf,
               const Size dim)

{

  if ( transf == NULL ) return E_NONE;
  if ( !transf->dim ) return E_NONE;
  if ( !transf->count ) return E_NONE;
  if ( transf->pos == NULL ) return E_ARGVAL;

  Coord *pos = malloc( transf->count * dim * sizeof(Coord) );
  if ( pos == NULL ) return E_MALLOC;

  memset( pos, 0, transf->count * dim * sizeof(Coord) );
  display->count = transf->count;
  display->pos = pos;
  display->rot = NULL;

  Size posdim = ( transf->dim < dim ) ? transf->dim : dim;
  const Coord *poslist = transf->pos;

  for ( Size i = 0; i < transf->count; i++, poslist += transf->dim, pos += dim  ) {
    for ( Size j = 0; j < posdim; j++ ) {
      pos[j] = poslist[j];
    }
  }

  display->status |= GuigtkDisplayPosDisp;
  display->status &= ~GuigtkDisplayPosMod;

  return E_NONE;

}


extern Status GuigtkDisplayCreatePos
              (const Image *image,
               const void *addr,
               const GuigtkDisplayTransf *posin,
               GuigtkDisplayTransf *posout,
               const GuigtkDisplayParam *param)

{
  Status status;

  if ( image == NULL ) return pushexception( E_ARGVAL );
  if ( addr == NULL ) return pushexception( E_ARGVAL );

  if ( ( image->dim < 2 ) || ( image->dim > 3 ) ) {
    return pushexception( E_ARRAY_DIM );
  }

  GuigtkDisplay *display = GuigtkDisplayAlloc( param );
  if ( display == NULL ) return pushexception( E_MALLOC );

  status = GuigtkDisplayLoadTransf( display, posin, image->dim );
  if ( pushexception( status ) ) goto exit1;

  status = GuigtkDisplayLoadImage( display, image, addr );
  if ( pushexception( status ) ) goto exit2;

  status = GuigtkDisplayExec( display, image, addr, posout );
  if ( exception( status ) ) goto exit2;

  exit2: if ( display->pos != NULL ) free( display->pos );
         if ( display->rot != NULL ) free( display->rot );

  exit1: free( display );

  return status;

}


extern Status GuigtkDisplayCreateFile
              (const char *path,
               const char *posin,
               const char *posout,
               const GuigtkDisplayParam *param)

{
  GuigtkDisplayTransf transf;
  Status status;

  if ( path == NULL ) return pushexception( E_ARGVAL );

  GuigtkDisplay *display = GuigtkDisplayAlloc( param );
  if ( display == NULL ) return pushexception( E_MALLOC );

  status = GuigtkDisplayOpen( path, display );
  if ( exception( status ) ) goto exit1;

  Image *image = &display->img.dscr;
  void *addr = display->img.addr;

  if ( posin != NULL ) {
    void *pos; Size count;
    status = TextioImportList( posin, StringParseCoord, image->dim, &pos, &count );
    if ( exception( status ) ) goto exit1;
    display->count = count;
    display->pos = pos;
    display->rot = NULL;
    display->status |= GuigtkDisplayPosDisp;
    display->status &= ~GuigtkDisplayPosMod;
  }

  status = GuigtkDisplayLoadImage( display, image, addr );
  if ( pushexception( status ) ) goto exit2;

  status = GuigtkDisplayExec( display, image, addr, ( posout == NULL ) ? NULL : &transf );
  if ( exception( status ) ) goto exit2;

  if ( posout != NULL ) {
    status = GuigtkDisplayTransfFile( posout, transf.dim, transf.count, transf.pos, transf.rot );
    if ( transf.pos != NULL ) free( transf.pos );
    if ( transf.rot != NULL ) free( transf.rot );
    if ( exception( status ) ) goto exit2;
  }

  exit2: if ( display->pos != NULL ) free( display->pos );
         if ( display->rot != NULL ) free( display->rot );

  exit1: free( display );

  return status;

}
