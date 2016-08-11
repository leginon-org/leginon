/*----------------------------------------------------------------------------*
*
*  tomoparamset.c  -  tomography: parameter files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoparamcommon.h"
#include "exception.h"
#include <ctype.h>
#include <stdlib.h>
#include <string.h>


/* types */

typedef struct {
  TomoparamType type;
  TomoparamVal val;
} TomoparamParseVal;


/* functions */

static Status TomoparamParseValue
              (const char *str,
               const char **end,
               const char array,
               TomoparamParseVal *val)

{

  if ( *str == 'f' ) {

    if ( *++str != 'a' ) return exception( E_VAL );
    if ( *++str != 'l' ) return exception( E_VAL );
    if ( *++str != 's' ) return exception( E_VAL );
    if ( *++str != 'e' ) return exception( E_VAL );
    char c = *++str;
    if ( !c || isspace( c ) || ( c == array ) ) {
      *end = str;
      val->type = TomoparamBool;
      val->val.bool = False;
    } else {
      return exception( E_VAL );
    }

  } else if ( *str == 't' ) {

    if ( *++str != 'r' ) return exception( E_VAL );
    if ( *++str != 'u' ) return exception( E_VAL );
    if ( *++str != 'e' ) return exception( E_VAL );
    char c = *++str;
    if ( !c || isspace( c ) || ( c == array ) ) {
      *end = str;
      val->type = TomoparamBool;
      val->val.bool = True;
    } else {
      return exception( E_VAL );
    }

  } else {

    const char *ptr = str;
    char sign = 0;
    if ( ( *ptr == '+' ) || ( *ptr == '-' ) ) {
      sign = *ptr++;
    }

    Size count = 0, num = 0;
    while ( ( *ptr >= '0' ) && ( *ptr <= '9' ) ) {
      Size new = 10 * num;
      if ( new / 10 != num ) { count = 0; break; }
      num = new + *ptr++ - '0';
      if ( ( num < new ) || ( num > IndexMax ) ) { count = 0; break; }
      count++;
    }

    if ( count && ( !*ptr || isspace( *ptr ) || ( *ptr == array ) ) ) {

      *end = ptr;
      if ( sign ) {
        val->type = TomoparamSint;
        val->val.sint = num; if ( sign == '-' ) val->val.sint = -val->val.sint;
      } else {
        val->type = TomoparamUint;
        val->val.uint = num;
      }

    } else {

      char *ptr;
      double num = strtod( str, &ptr );
      if ( ( ptr != str ) && ( !*ptr || isspace( *ptr ) || ( *ptr == array ) ) ) {
        *end = ptr;
        val->type = TomoparamReal;
        val->val.real = num;
      } else {
        return exception( E_VAL );
      }

    } 

  }

  return E_NONE;

}


static Status TomoparamParseString
              (Tomoparam *tomoparam,
               const char *str,
               const char **end,
               const char array,
               TomoparamParseVal *val)

{
  Status status;

  if ( array ) return exception( E_TOMOPARAM );

  while ( isspace( *str ) ) str++;

  const char *ptr = str, *txt = NULL;
  while ( *ptr ) {
    if ( !isspace( *ptr ) ) txt = ptr;
    ptr++;
  }
  if ( txt == NULL ) return exception( E_VAL );

  Size len = txt - str + 1;
  char *buf = malloc( len + 1 );
  if ( buf == NULL ) return exception( E_MALLOC );
  memcpy( buf, str, len );
  buf[len] = 0;

  status =  StringTableInsert( &tomoparam->strlit, buf, &val->val.index );
  free( buf );
  if ( status && ( status != E_STRINGTABLE_EXISTS ) ) return exception( status );
  val->type = TomoparamStr;

  *end = ptr;

  return E_NONE;

}


static Status TomoparamParseGet
              (Tomoparam *tomoparam,
               const char *str,
               const char **end,
               const char array,
               const TomoparamType type,
               TomoparamParseVal **valptr,
               int *lenptr)

{
  TomoparamParseVal v;
  Status status;

  if ( type == TomoparamStr ) {

    status = TomoparamParseString( tomoparam, str, end, array, &v );
    if ( status ) return status;

  } else {

    status = TomoparamParseValue( str, end, array, &v );
    if ( status ) return status;

    switch ( v.type ) {
      case TomoparamReal: if ( type != TomoparamReal ) return exception( E_TOMOPARAM_TYPE ); break;
      case TomoparamSint: if ( type == TomoparamUint ) return exception( E_TOMOPARAM_TYPE );
      case TomoparamUint: if ( type == TomoparamBool ) return exception( E_TOMOPARAM_TYPE ); break;
      case TomoparamBool: if ( type != TomoparamBool ) return exception( E_TOMOPARAM_TYPE ); break;
      case TomoparamStr:  if ( type != TomoparamStr  ) return exception( E_TOMOPARAM_TYPE ); break;
      default: return exception( E_TOMOPARAM_DAT );
    }

  }

  int len = *lenptr + 1;
  TomoparamParseVal *val = realloc( *valptr, len * sizeof(*val) );
  if ( val == NULL ) return exception( E_MALLOC );
  *valptr = val;

  val[*lenptr] = v;
  *lenptr = len;

  return E_NONE;

}


static Status TomoparamParseSet
              (const TomoparamType type,
               TomoparamParseVal *val,
               int len)

{

  switch ( type ) {

    case TomoparamUint: {
      Size *vd = (Size *)val;
      for ( int i = 0; i < len; i++ ) {
        TomoparamVal vs = val[i].val;
        switch ( val[i].type ) {
          case TomoparamUint: *vd++ = vs.uint; break;
          case TomoparamSint: *vd++ = vs.sint; break;
          case TomoparamReal: *vd++ = vs.real; break;
          default: *vd++ = 0; break;
        }
      }
      break;
    }

    case TomoparamSint: {
      Index *vd = (Index *)val;
      for ( int i = 0; i < len; i++ ) {
        TomoparamVal vs = val[i].val;
        switch ( val[i].type ) {
          case TomoparamUint: *vd++ = vs.uint; break;
          case TomoparamSint: *vd++ = vs.sint; break;
          case TomoparamReal: *vd++ = vs.real; break;
          default: *vd++ = 0; break;
        }
      }
      break;
    }

    case TomoparamReal: {
      Coord *vd = (Coord *)val;
      for ( int i = 0; i < len; i++ ) {
        TomoparamVal vs = val[i].val;
        switch ( val[i].type ) {
          case TomoparamUint: *vd++ = vs.uint; break;
          case TomoparamSint: *vd++ = vs.sint; break;
          case TomoparamReal: *vd++ = vs.real; break;
          default: *vd++ = 0; break;
        }
      }
      break;
    }

    case TomoparamBool: {
      Bool *vd = (Bool *)val;
      for ( int i = 0; i < len; i++ ) {
        TomoparamVal vs = val[i].val;
        *vd++ = vs.bool;
      }
      break;
    }

    default: return exception( E_TOMOPARAM_DAT );

  }

  return E_NONE;

}


extern Status TomoparamParseType
              (Tomoparam *tomoparam,
               const char *str,
               const TomoparamType type,
               void **val,
               int *len)

{
  TomoparamParseVal *v = NULL;
  int l = 0;
  Status status;

  while ( isspace( *str ) ) str++;

  if ( *str == '{' ) {

    str++;
    while ( isspace( *str ) ) str++;

    while ( *str && ( *str != '}' ) ) {
      status = TomoparamParseGet( tomoparam, str, &str, '}', type, &v, &l );
      if ( status ) goto error;
      while ( isspace( *str ) ) str++;
    }

    if ( *str == '}' ) {
      str++;
    } else {
      status = exception( E_VAL ); goto error;
    }

    status = TomoparamParseSet( type, v, l );
    if ( status ) goto error;

  } else {

    status = TomoparamParseGet( tomoparam, str, &str, 0, type, &v, &l );
    if ( status ) goto error;
    l = -1;

    TomoparamVal *vd = (TomoparamVal *)v;
    TomoparamVal vs = v->val;
    *vd = vs;

  }

  while ( isspace( *str ) ) str++;
  if ( *str ) { status = exception( E_VAL ); goto error; }

  *val = v;
  *len = l;

  return E_NONE;

  error: if ( v != NULL ) free( v );

  return status;

}


static Status TomoparamParseGetNumeric
              (const char *str,
               const char **end,
               const char array,
               TomoparamType *type,
               TomoparamParseVal **valptr,
               int *lenptr)

{
  TomoparamParseVal v;
  Status status;

  status = TomoparamParseValue( str, end, array, &v );
  if ( status ) return status;

  if ( *type == TomoparamUndef ) *type = v.type;

  switch ( v.type ) {
    case TomoparamUint:
    case TomoparamSint:
    case TomoparamReal: if ( *type == TomoparamBool ) return exception( E_TOMOPARAM_TYPE ); break;
    case TomoparamBool: if ( *type != TomoparamBool ) return exception( E_TOMOPARAM_TYPE ); break;
    default: return exception( E_TOMOPARAM_DAT );
  }

  switch ( v.type ) {
    case TomoparamUint: break;
    case TomoparamSint: if ( *type == TomoparamUint ) *type = TomoparamSint; break;
    case TomoparamReal: *type = TomoparamReal; break;
    default: break;
  }

  int len = *lenptr + 1;
  TomoparamParseVal *val = realloc( *valptr, len * sizeof(*val) );
  if ( val == NULL ) return exception( E_MALLOC );
  *valptr = val;

  val[*lenptr] = v;
  *lenptr = len;

  return E_NONE;

}


extern Status TomoparamParseNumeric
              (const char *str,
               TomoparamType *type,
               void **val,
               int *len)

{
  TomoparamType t = TomoparamUndef;
  TomoparamParseVal *v = NULL;
  int l = 0;
  Status status;

  while ( isspace( *str ) ) str++;

  if ( *str == '{' ) {

    str++;
    while ( isspace( *str ) ) str++;

    while ( *str && ( *str != '}' ) ) {
      status = TomoparamParseGetNumeric( str, &str, '}', &t, &v, &l );
      if ( status ) goto error;
      while ( isspace( *str ) ) str++;
    }

    if ( *str == '}' ) {
      str++;
    } else {
      status = exception( E_VAL ); goto error;
    }

    status = TomoparamParseSet( t, v, l );
    if ( status ) goto error;

  } else {

    status = TomoparamParseGetNumeric( str, &str, 0, &t, &v, &l );
    if ( status ) goto error;
    l = -1;

    TomoparamVal *vd = (TomoparamVal *)v;
    TomoparamVal vs = v->val;
    *vd = vs;

  }

  while ( isspace( *str ) ) str++;
  if ( *str ) { status = exception( E_VAL ); goto error; }

  *type = t;
  *val = v;
  *len = l;

  return E_NONE;

  error: if ( v != NULL ) free( v );

  return status;

}
