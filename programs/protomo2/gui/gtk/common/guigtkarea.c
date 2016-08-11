/*----------------------------------------------------------------------------*
*
*  guigtkarea.c  -  guigtk: common routines
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
#include "graph.h"
#include "exception.h"
#include "message.h"
#include <stdlib.h>


/* functions */

extern GuigtkArea *GuigtkAreaCreate
                   (const Size viewport[2])

{

  GuigtkArea *area = malloc( sizeof(GuigtkArea) );
  if ( area == NULL ) { pushexception( E_MALLOC ); return NULL; }

  /* query OpenGL extension version */
  if ( GraphLog ) {
    Size major, minor;
    if ( !GraphGetVersion( &major, &minor ) ) {
      MessageFormat( "OpenGL extension version: %"SizeU".%"SizeU"\n", major, minor );
    }
  }

  /* try double-buffered visual first, then single-buffered one */
  area->config = gdk_gl_config_new_by_mode( GDK_GL_MODE_RGB | GDK_GL_MODE_DEPTH | GDK_GL_MODE_DOUBLE );
  if ( area->config == NULL ) {
    if ( GraphLog ) {
      Message( "double-buffered visual not found, trying single-buffered visual", "\n" );
    }
    area->config = gdk_gl_config_new_by_mode( GDK_GL_MODE_RGB | GDK_GL_MODE_DEPTH );
    if ( area->config == NULL ) { pushexception( E_GUIGTK_VISUAL ); goto error1; }
  }

  area->widget = gtk_drawing_area_new();
  if ( area->widget == NULL ) { pushexception( E_GUIGTK ); goto error1; }

  /* Set OpenGL-capability to the widget. */
  if ( !gtk_widget_set_gl_capability( area->widget, area->config, NULL, TRUE, GDK_GL_RGBA_TYPE ) ) {
    pushexception( E_GUIGTK_GLCAP ); goto error2;
  }

  gtk_widget_show( area->widget );

  if ( viewport == NULL ) {
    area->viewport[0] = 0;
    area->viewport[1] = 0;
  } else {
    area->viewport[0] = viewport[0];
    area->viewport[1] = viewport[1];
    gtk_widget_set_size_request( area->widget, area->viewport[0], area->viewport[1] );
  }

  return area;

  error2: gtk_widget_destroy( area->widget );
  error1: free( area );

  return NULL;

}


extern GuigtkArea *GuigtkAreaDestroy
                   (GuigtkArea *area)

{

  if ( area != NULL ) {

    if ( area->widget != NULL ) {
      gtk_widget_destroy( area->widget );
    }

    free( area );

  }

  return E_NONE;

}


extern Status GuigtkAreaBegin
              (GuigtkArea *area)

{

  area->context = gtk_widget_get_gl_context( area->widget );
  area->drawable = gtk_widget_get_gl_drawable( area->widget );

  if ( !gdk_gl_drawable_gl_begin( area->drawable, area->context ) ) {
    return pushexception( E_GUIGTK_GLDRAW );
  }

  return E_NONE;

}


extern void GuigtkAreaDraw
            (GuigtkArea *area)

{

  if ( gdk_gl_drawable_is_double_buffered( area->drawable ) ) {
    gdk_gl_drawable_swap_buffers( area->drawable );
  } else {
    glFlush();
  }

}


extern void GuigtkAreaEnd
            (GuigtkArea *area)

{

  gdk_gl_drawable_gl_end( area->drawable );

}
