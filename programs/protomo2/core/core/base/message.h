/*----------------------------------------------------------------------------*
*
*  message.h  -  core: print diagnostic/error messages
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef message_h_
#define message_h_

#include "base.h"


/* macros */

#define Message( msg, ... )        MessageString( msg, __VA_ARGS__, NULL )

#define MessageBegin( msg, ... )   MessageStringBegin( msg, __VA_ARGS__, NULL )

#define MessageHeadr( msg, ... )   MessageStringHeadr( msg, __VA_ARGS__, NULL )

#define MessagePrint( msg, ... )   MessageStringPrint( msg, __VA_ARGS__, NULL )

#define MessageEnd( msg, ... )     MessageStringEnd( msg, __VA_ARGS__, NULL )

#define MessageLock
#define MessageUnlock


/* prototypes */

extern void MessageString
            (const char *msg, ...);

extern void MessageStringBegin
            (const char *msg, ...);

extern void MessageStringHeadr
            (const char *msg, ...);

extern void MessageStringPrint
            (const char *msg, ...);

extern void MessageStringEnd
            (const char *msg, ...);

extern void MessageStringLock();

extern void MessageStringUnlock();

extern void MessageFormat
            (const char *fmt, ...);

extern void MessageFormatBegin
            (const char *fmt, ...);

extern void MessageFormatHeadr
            (const char *fmt, ...);

extern void MessageFormatPrint
            (const char *fmt, ...);

extern void MessageFormatEnd
            (const char *fmt, ...);


#endif
