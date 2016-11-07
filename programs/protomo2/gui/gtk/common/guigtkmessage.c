/*----------------------------------------------------------------------------*
*
*  guigtkmessage.c  -  guigtk: common routines
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
#include "message.h"
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>


/* functions */

extern void GuigtkMessage
            (Size prt,
             GtkWidget *bar,
             const char *str,
             ...)

{
  char *msg = NULL;

  if ( str != NULL ) {

    Size len = 1;
    const char *s = str;
    va_list ap;
    va_start( ap, str );
    do {
      len += strlen(s);
      s = va_arg( ap, const char * );
    } while ( s != NULL );
    va_end( ap );

    msg = malloc( len );
    if ( msg != NULL ) {
      const char *s = str;
      char *m = msg;
      va_list ap;
      va_start( ap, str );
      while ( s != NULL ) {
        while ( *s ) {
          *m++ = *s++;
        }
        s = va_arg( ap, const char * );
      }
      *m = 0;
      va_end( ap );
    }

  }

  if ( prt && ( msg != NULL ) ) {
    Message(  msg, "\n" );
  }

  if ( bar != NULL ) {
    GtkStatusbar *stb = GTK_STATUSBAR( bar );
    gtk_statusbar_pop( stb, 0 );
    gtk_statusbar_push( stb, 0, ( msg == NULL ) ? " " : msg );
  }

  if ( msg != NULL ) free( msg );

}
