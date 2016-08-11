/*----------------------------------------------------------------------------*
*
*  exception.h  -  core: exception handling
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef exception_h_
#define exception_h_

#include "base.h"
#include <errno.h>


/* macros */

#define exception( status )              ( status )

#define logexception( status )

#define popexception( status )           ( ( status ) ? ExceptionPop() : E_NONE )

#define pushexception( status )          ( ( status ) ? ExceptionPush( status ) : E_NONE )

#define pushexceptionmsg( status, ... )  ( ( status ) ? ExceptionPushMsg( status, __VA_ARGS__, NULL ) : E_NONE )

#define testcondition( cond )            ( ( cond ) ? ExceptionGet( True ) : E_NONE )

#define popcondition( cond )             ( ( cond ) ? ExceptionPop() : E_NONE )

#define appendexception( msg )           ExceptionAppend( msg )

#define userexception( msg )             pushexceptionmsg( E_USER, msg )

#define userexceptionmsg( msg, ... )     pushexceptionmsg( E_USER, msg, __VA_ARGS__, NULL )


#define ExceptionModuleMask  0x0fffff00
#define ExceptionIndexMask   0x000000ff
#define ExceptionCodeMask    ( ExceptionModuleMask | ExceptionIndexMask )
#define ExceptionFlags       0xf0000000
#define ExceptionOnstack     0x80000000
#define ExceptionPopstack    0x40000000



/* data structures */

typedef struct {
  const char *ident;
  const char *msg;
} ExceptionMessage;


/* prototypes */

extern Status ExceptionRegister
              (const ExceptionMessage *table,
               Status min,
               Status max);

extern Status ExceptionPush
              (Status status);

extern Status ExceptionPushMsg
              (Status status,
               ...);

extern Status ExceptionAppend
              (const char *msg);

extern Status ExceptionGet
              (Bool err);

extern const char *ExceptionGetMsg();

extern Status ExceptionPop();

extern Status ExceptionClear();

extern Status ExceptionReport
              (void *data);

extern void ExceptionReportRegister
            (void (*function)(Status, const char *, const char *, void *));


#endif
