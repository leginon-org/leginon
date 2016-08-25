/*----------------------------------------------------------------------------*
*
*  exception.c  -  core: exception handling
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "exception.h"
#include "message.h"
#include "signals.h"
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


/* exception stack */

typedef struct {
  Status code;
  const char *ident;
  const char *message;
  Bool alloc;
} Exception;

typedef struct {
  Exception *stack;
  Size size;
  Size top;
} ExceptionStack;

static ExceptionStack Stack = { NULL, 0, 0 };
#define ExceptionGetStack()  ( &Stack )


/* lists of messages */

typedef struct {
  const ExceptionMessage *list;
  Status length;
  Status module;
} ExceptionList;

static ExceptionList *ExceptionTable = NULL;
static Size ExceptionTableSize = 0;


/* functions */


extern Status ExceptionRegister
              (const ExceptionMessage *list,
               Status min,
               Status max)

{

  if ( max <= min ) return pushexception( E_BASE );
  if ( min != ( min & ~ExceptionIndexMask ) ) return pushexception( E_BASE );
  if ( ( max & ~ExceptionIndexMask ) != ( min & ~ExceptionIndexMask ) ) return pushexception( E_BASE );

  Size size = ExceptionTableSize + 1;
  ExceptionList *new = realloc( ExceptionTable, size * sizeof(ExceptionList) );
  if ( new == NULL ) {
    return pushexception( E_MALLOC );
  }
  new[ExceptionTableSize].list = list;
  new[ExceptionTableSize].length = max - min;
  new[ExceptionTableSize].module = min;
  ExceptionTable = new;
  ExceptionTableSize = size;

  return E_NONE;

}


static Exception *ExceptionPushSub
                  (Status status)

{
  Exception *exc = NULL, *ptr;
  const char *ident, *msg;

  ExceptionStack *stack = ExceptionGetStack();
  if ( stack == NULL ) goto error;

  Size newsize = stack->top + 1;
  if ( newsize > stack->size ) {
    ptr = realloc( stack->stack, newsize * sizeof(Exception) );
    if ( ptr == NULL ) goto error;
    stack->stack = ptr;
    stack->size = newsize;
    ptr += stack->top;
  } else {
    ptr = stack->stack;
    if ( ptr == NULL ) goto error;
    ptr += stack->top;
    if ( ptr->alloc ) free( (char *)ptr->message );
  }
  stack->top = newsize;

  Status code = status & ExceptionCodeMask;

  if ( code == E_SIGNAL ) {
    ident = "E_SIGNAL";
    msg = SignalString( SignalInterrupt );
    exc = ptr;
    goto exit;
  }

  if ( code == E_ERRNO ) {
    switch ( errno ) {
      case ENOENT:  code = E_FILENOTFOUND; break;
      case EEXIST:  code = E_FILEEXISTS;   break;
      case EISDIR:  code = E_FILEISDIR;    break;
      case ENOTDIR: code = E_FILENODIR;    break;
      case EACCES:  code = E_FILEACCESS;   break;
      default: {
        ident = "E_ERRNO";
        msg = strerror( errno ); /* allocate and copy ? */
        exc = ptr;
        goto exit;
      }
    }
  }

  Status module = code & ExceptionModuleMask;
  Status index  = code & ExceptionIndexMask;

  for ( Size i = 0; i < ExceptionTableSize; i++ ) {
    if ( ExceptionTable[i].module == module ) {
      if ( index < ExceptionTable[i].length ) {
        const ExceptionMessage *list = ExceptionTable[i].list;
        ident = list[index].ident;
        msg = list[index].msg;
        exc = ptr;
      } else {
        ident = "E_ERR";
        msg = "invalid message code";
      }
      goto exit;
    }
  }
  ident = "E_ERR";
  msg = "unknown message code";

  exit:

  ptr->code = code;
  ptr->ident = ident;
  ptr->message = msg;
  ptr->alloc = False;

  return exc;

  error:
  MessageFormat( "cannot push [%x]\n", status );
  return NULL;

}


extern Status ExceptionPush
              (Status status)

{

  ExceptionPushSub( status );

  return status;

}


extern Status ExceptionPushMsg
              (Status status,
               ...)

{
  const char *msg;
  Size len = 0;
  va_list ap;

  Exception *ptr = ExceptionPushSub( status );
  if ( ptr == NULL ) return status;

  va_start( ap, status );
  msg = va_arg( ap, const char * );
  while ( msg != NULL ) {
    len += strlen( msg );
    msg = va_arg( ap, const char * );
  }
  va_end( ap );
  if ( !len ) return status;

  msg = ptr->message;
  if ( msg == NULL ) {
    msg = "";
  } else {
    len += strlen( msg );
  }

  char *msgptr = malloc( len + 1 );
  if ( msgptr == NULL ) return E_MALLOC;
  char *message = msgptr;

  va_start( ap, status );
  while ( msg != NULL ) {
    len = strlen( msg );
    if ( len ) {
      memcpy( msgptr, msg, len );
      msgptr += len;
    }
    msg = va_arg( ap, const char * );
  }
  va_end( ap );
  *msgptr = 0;

  if ( ptr->alloc ) {
    free( (char *)ptr->message );
  }
  ptr->message = message;
  ptr->alloc = True;

  return status;

}


extern Status ExceptionAppend
              (const char *msg)

{
  Status status = E_NONE;

  if ( ( msg != NULL ) && *msg ) {

    ExceptionStack *stack = ExceptionGetStack();
    if ( stack == NULL ) return exception( E_BASE );

    Size top = stack->top;
    if ( !top-- ) return exception( E_EXCEPT );
    Exception *ptr = stack->stack + top;

    Size len1 = strlen( ptr->message );
    Size len2 = strlen( msg ) + 1;
    char *new = realloc( ptr->alloc ? (char *)ptr->message : NULL, len1 + len2 );
    if ( new == NULL ) return exception( E_MALLOC );
    if ( !ptr->alloc ) memcpy( new, ptr->message, len1 );
    memcpy( new + len1, msg, len2 );
    ptr->message = new;
    ptr->alloc = True;
    status = ptr->code;

  }

  return status;

}


extern Status ExceptionGet
              (Bool err)

{
  Status status;

  ExceptionStack *stack = ExceptionGetStack();
  if ( stack == NULL ) return exception( E_BASE );

  Size top = stack->top;
  if ( top-- ) {
    status = stack->stack[top].code;
  } else {
    status = E_NONE;
  }

  if ( err && !status ) {
    status = ExceptionPush( E_EXCEPT );
  }

  return status;

}


extern const char *ExceptionGetMsg()

{
  const char *message;

  ExceptionStack *stack = ExceptionGetStack();
  if ( stack == NULL ) return NULL;

  Size top = stack->top;
  if ( top-- ) {
    message = stack->stack[top].message;
  } else {
    message = NULL;
  }

  return message;

}


extern Status ExceptionPop()

{
  Status status;

  ExceptionStack *stack = ExceptionGetStack();
  if ( stack == NULL ) return exception( E_BASE );

  Size top = stack->top;
  if ( top-- ) {
    status = stack->stack[top].code | ExceptionPopstack;
    stack->top = top;
  } else {
    status = E_NONE;
  }

  return status;

}


extern Status ExceptionClear()

{
  Status status;

  ExceptionStack *stack = ExceptionGetStack();
  if ( stack == NULL ) return exception( E_BASE );

  if ( stack->top ) {
    status = stack->stack->code;
  } else {
    status = E_NONE;
  }

  stack->top = 0;

  return status;

}


static void ExceptionReportDefault
            (Status code,
             const char *ident,
             const char *msg,
             void *data)

{

  if ( code == E_SIGNAL ) fputc( '\r', stderr );

  Message( msg, "\n" );

}


static void (*ExceptionReportFunction)(Status, const char *, const char *, void *) = ExceptionReportDefault;


extern Status ExceptionReport
              (void *data)

{
  Status status;

  ExceptionStack *stack = ExceptionGetStack();
  if ( stack == NULL ) return exception( E_BASE );

  if ( stack->top ) {
    Exception *ptr = stack->stack;
    for ( Size e = 0; e < stack->top; e++, ptr++ ) {
      if ( ptr->code != E_DUMMY ) {
        ExceptionReportFunction( ptr->code, ptr->ident, ptr->message, data );
      }
    }
    stack->top = 0;
    status = stack->stack->code;
  } else {
    status = E_NONE;
  }

  return status;

}


extern void ExceptionReportRegister
            (void (*function)(Status, const char *, const char *, void *))

{

   ExceptionReportFunction = ( function == NULL ) ? ExceptionReportDefault : function;

}


