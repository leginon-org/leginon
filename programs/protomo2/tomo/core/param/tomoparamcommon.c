/*----------------------------------------------------------------------------*
*
*  tomoparamcommon.c  -  tomography: parameter files
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
#include "message.h"
#include "exception.h"
#include "baselib.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern void TomoparamSetLog
            (Tomoparam *tomoparam)

{

  if ( tomoparam != NULL ) {
    tomoparam->logparam = True;
  }

}


extern void TomoparamClearLog
            (Tomoparam *tomoparam)

{

  if ( tomoparam != NULL ) {
    tomoparam->logparam = False;
  }

}


extern Status TomoparamExtend
              (Tomoparam *tomoparam,
               const char *ident,
               Size len)

{

  char *sname = tomoparam->sname;
  Size slen = ( sname == NULL ) ? 0 : strlen( sname );
  Size ilen = slen + len + 1;

  sname = realloc( sname, ilen + 1 );
  if ( sname == NULL ) return E_MALLOC;
  tomoparam->sname = sname;

  if ( slen ) {
    sname += slen;
    *sname++ = '.';
  }

  memcpy( sname, ident, len );
  sname[len] = 0;

  return E_NONE;

}


extern char *TomoparamAppend
             (const char *section,
              const char *ident,
              Size len)

{

  Size slen = ( section == NULL ) ? 0 : strlen( section );
  Size ilen = slen + len + 1;

  char *id = malloc( ilen + 1 );
  if ( id == NULL ) return NULL;

  char *iptr = id;

  if ( slen ) {
    memcpy( iptr, section, slen ); iptr += slen;
    *iptr++ = '.';
  }

  memcpy( iptr, ident, len ); iptr += len;
  *iptr = 0;

  return id;

}


extern void TomoparamRemove
            (char *ident)

{

  Size ilen = ( ident == NULL ) ? 0 : strlen( ident );

  if ( ilen ) {
    char *id = ident + ilen - 1;
    if ( *id != '.' ) {
      while ( ( id != ident ) && ( *--id != '.' ) );
    }
    *id = 0;
  }

}


extern Status TomoparamLookup
              (const Tomoparam *tomoparam,
               const char *ident,
               TomoparamVar **var)

{
  Status status;

  Size index;
  status = TomoparamLookupIdent( tomoparam, ident, strlen( ident ), True, &index );
  if ( status == E_STRINGTABLE_NOTFOUND ) return exception( E_TOMOPARAM_UNDEF );
  if ( exception( status ) ) return status;

  *var = TomoparamLookupVar( tomoparam, index );
  if ( *var == NULL ) return exception( E_TOMOPARAM );
  if ( !(*var)->param )  return exception( E_TOMOPARAM_UNDEF );

  return E_NONE;

}


extern Status TomoparamInsertIdent
              (Tomoparam *tomoparam,
               const char *ident,
               Size len,
               Size *index)

{
  Status status;

  if ( tomoparam == NULL ) return exception( E_ARGVAL );
  if ( ident == NULL ) return exception( E_ARGVAL );
  if ( len == 0 ) return exception( E_ARGVAL );
  if ( index == NULL ) return exception( E_ARGVAL );

  char *id = TomoparamAppend( tomoparam->sname, ident, len );
  if ( id == NULL ) return exception( E_MALLOC );

  status = StringTableInsert( &tomoparam->ident, id, index );
  logexception( status );

  free( id );

  return E_NONE;

}


extern Status TomoparamLookupIdent
              (const Tomoparam *tomoparam,
               const char *ident,
               Size len,
               Bool param,
               Size *index)

{
  Status status;

  if ( tomoparam == NULL ) return exception( E_ARGVAL );
  if ( ident == NULL ) return exception( E_ARGVAL );
  if ( len == 0 ) return exception( E_ARGVAL );
  if ( index == NULL ) return exception( E_ARGVAL );

  char *id = TomoparamAppend( tomoparam->sname, ident, len );
  if ( id == NULL ) return exception( E_MALLOC );

  status = StringTableLookup( tomoparam->ident, id, index );
  if ( status && ( status != E_STRINGTABLE_NOTFOUND ) ) { logexception( status ); goto exit; }

  if ( !param && status ) {

    Size slen = ( tomoparam->sname == NULL ) ? 0 : strlen( tomoparam->sname );

    if ( slen ) {

      char *end = id + slen;

      do {

        while ( ( end != id ) && ( *--end != '.' ) );
        char *ptr = ( end != id ) ? end + 1 : end;
        for ( Size i = 0; i < len; i++ ) *ptr++ = ident[i];
        *ptr = 0;

        status = StringTableLookup( tomoparam->ident, id, index );
        if ( status && ( status != E_STRINGTABLE_NOTFOUND ) ) { logexception( status ); goto exit; }

      } while ( ( end != id ) && status );

    }

  }

  exit:

  free( id );

  return status;

}


static Status TomoparamInsertVar
              (Tomoparam *tomoparam,
               const char *ident,
               Size len,
               const TomoparamVar *var)

{
  Size index;
  Status status;

  TomoparamVar *vartab = realloc( tomoparam->vartab, ( tomoparam->varlen + 1 ) * sizeof(TomoparamVar) );
  if ( vartab == NULL ) return exception( E_MALLOC );
  tomoparam->vartab = vartab;

  status = TomoparamInsertIdent( tomoparam, ident, len, &index );
  if ( exception( status ) ) return status;

  vartab += tomoparam->varlen++;

  *vartab = *var;

  vartab->name = index;

  return E_NONE;

}


extern Status TomoparamInsertString
              (Tomoparam *tomoparam,
               const char *ident,
               const char *val)

{
  Status status;

  TomoparamVar var = TomoparamVarInitializer;
  var.dim = 0;
  var.count = 1;
  var.type = TomoparamStr;
  var.param = False;

  status = StringTableInsert( &tomoparam->strlit, val, &var.val.index );
  if ( exception( status ) ) return status;

  status = TomoparamInsertVar( tomoparam, ident, strlen( ident ), &var );
  if ( exception( status ) ) return status;

  return E_NONE;

}


extern TomoparamVar *TomoparamLookupVar
                     (const Tomoparam *tomoparam,
                      Size index)

{

  if ( tomoparam == NULL ) return NULL;

  TomoparamVar *var = tomoparam->vartab;
  if ( var == NULL ) return NULL;

  for ( Size i = 0; i < tomoparam->varlen; i++, var++ ) {
    if ( var->name == index ) return var;
  }

  return NULL;

}


static void TomoparamPrintVal
            (const Tomoparam *tomoparam,
             Size dim,
             const TomoparamVal *len,
             const TomoparamVal **valaddr,
             TomoparamType type)

{

  if ( ( dim == 0 ) || ( dim == SizeMax ) ) {

    const TomoparamVal *val = (*valaddr)++;
    switch ( type ) {
      case TomoparamUint: MessageFormatPrint( " %"SizeU,  val->uint ); break;
      case TomoparamSint: MessageFormatPrint( " %"IndexD, val->sint ); break;
      case TomoparamReal: MessageFormatPrint( " %.16"CoordG, val->real ); break;
      case TomoparamBool: MessageFormatPrint( " %s", val->bool ? "true" : "false" ); break;
      case TomoparamStr: {
        const char *str = tomoparam->strlit;
        if ( ( str == NULL ) || ( val->index >= StringTableSize( str ) ) ) {
          str = "?";
        } else {
          str += val->index;
        }
        MessageFormatPrint( " \"%s\"", str );
        break;
      }
      default: MessageFormatPrint( " %s", "undef" );
    }

  } else {

    MessageStringPrint( " {", NULL );
    for ( Size i = 0; i < len[dim-1].uint; i++ ) {
      TomoparamPrintVal( tomoparam, dim - 1, len, valaddr, type );
    }
    MessageStringPrint( " }", NULL );
  }

}


static void TomoparamPrintVal2
            (const Tomoparam *tomoparam,
             Size dim,
             const TomoparamVal *len,
             const TomoparamVal **valaddr,
             TomoparamType type,
             FILE *stream)

{

  if ( ( dim == 0 ) || ( dim == SizeMax ) ) {

    const TomoparamVal *val = (*valaddr)++;
    switch ( type ) {
      case TomoparamUint: fprintf( stream, " %"SizeU,  val->uint ); break;
      case TomoparamSint: fprintf( stream, " %"IndexD, val->sint ); break;
      case TomoparamReal: fprintf( stream, " %.16"CoordG, val->real ); break;
      case TomoparamBool: fprintf( stream, " %s", val->bool ? "true" : "false" ); break;
      case TomoparamStr: {
        const char *str = tomoparam->strlit;
        if ( ( str == NULL ) || ( val->index >= StringTableSize( str ) ) ) {
          str = "?";
        } else {
          str += val->index;
        }
        fprintf( stream, " \"%s\"", str );
        break;
      }
      default: fputs( " undef", stream );
    }

  } else {

    fputs( " {", stream );
    for ( Size i = 0; i < len[dim-1].uint; i++ ) {
      TomoparamPrintVal2( tomoparam, dim - 1, len, valaddr, type, stream );
    }
    fputs( " }", stream );
  }

}


extern Status TomoparamPrintVar
              (const Tomoparam *tomoparam,
               const TomoparamVar *var,
               const char *section,
               FILE *stream)

{
  const char *ident = "<tmp>";

  if ( argcheck( tomoparam == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( var == NULL ) ) return exception( E_ARGVAL );

  if ( var->name != SizeMax ) {
    ident = tomoparam->ident;
    if ( ( ident == NULL ) || ( var->name >= StringTableSize( ident ) ) ) {
      return exception( E_TOMOPARAM );
    }
    ident += var->name;
    if ( section != NULL ) {
      const char *ptr = ident;
      while ( *section && *ptr && ( *section == *ptr ) && ( *section != '.' ) ) {
        section++; ptr++;
      }
      if ( ( !*section || ( *section == '.' ) ) && ( *ptr == '.' ) ) {
        ptr++; if ( *ptr ) ident = ptr;
      }
    }
  }

  const TomoparamVal *len = TomoparamGetLen( *var );
  const TomoparamVal *val = TomoparamGetVal( *var );

  if ( stream == NULL ) {

    MessageBegin( ident, var->param ? ":" : " =" );
    TomoparamPrintVal( tomoparam, var->dim, len, &val, var->type );
    MessageEnd( "\n", NULL );

  } else {

    fputs( ident, stream );
    fputs( var->param ? ":" : " =", stream );
    TomoparamPrintVal2( tomoparam, var->dim, len, &val, var->type, stream );
    fputs( "\n", stream );

  }

  return E_NONE;

}
