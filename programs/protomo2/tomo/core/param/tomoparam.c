/*----------------------------------------------------------------------------*
*
*  tomoparam.c  -  tomography: parameter files
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
#include "io.h"
#include "strings.h"
#include <stdlib.h>
#include <string.h>


/* functions */

static void TomoparamDestroySav
            (ParseBuf *sav,
             Size savlen)

{

  while ( savlen-- ) {
    if ( sav[savlen].ptr != NULL ) free( sav[savlen].ptr );
  }

  free( sav );

}


extern Tomoparam *TomoparamParse
                 (const char *path)

{
  Status status;

  Parse parse;
  status = ParseInit( &parse, path );
  if ( exception( status ) ) return NULL;

  Tomoparam *tomoparam = malloc( sizeof(Tomoparam) );
  if ( tomoparam == NULL ) { pushexception( E_MALLOC ); goto exit; }
  *tomoparam = TomoparamInitializer;
  tomoparam->parse = &parse;

  if ( parse.handle != NULL ) {
    tomoparam->prfx = IOPathName( path );
    char *ptr = strchr( tomoparam->prfx, '.' );
    if ( ptr != NULL ) *ptr = 0;
  }

  int stat = tomoparam_yyparse( tomoparam );
  status = ParseStatus( &parse, stat );
  if ( exception( status ) ) {
    TomoparamDestroy( tomoparam );
    tomoparam = NULL;
    goto exit;
  }

  if ( tomoparam->sname != NULL ) free( tomoparam->sname );
  tomoparam->sname = NULL;

  if ( tomoparam->tmptab != NULL ) free( tomoparam->tmptab );
  tomoparam->tmptab = NULL;

  if ( tomoparam->eletab != NULL ) free( tomoparam->eletab );
  tomoparam->eletab = NULL;

  if ( tomoparam->stk != NULL ) free( tomoparam->stk );
  tomoparam->stk = NULL;

  if ( tomoparam->sav != NULL ) TomoparamDestroySav( tomoparam->sav, tomoparam->savlen );
  tomoparam->sav = NULL;

  tomoparam->parse = NULL;

  exit:

  status = ParseFinal( &parse );
  logexception( status );

  return tomoparam;

}


extern void TomoparamDestroy
            (Tomoparam *tomoparam)

{

  if ( tomoparam != NULL ) {

    if ( tomoparam->sav != NULL ) TomoparamDestroySav( tomoparam->sav, tomoparam->savlen );

    if ( tomoparam->stk != NULL ) free( tomoparam->stk );

    if ( tomoparam->eletab != NULL ) free( tomoparam->eletab );

    if ( tomoparam->tmptab != NULL ) free( tomoparam->tmptab );

    if ( tomoparam->valtab != NULL ) free( tomoparam->valtab );

    if ( tomoparam->vartab != NULL ) free( tomoparam->vartab );

    if ( tomoparam->sname != NULL ) free( tomoparam->sname );

    StringTableFree( &tomoparam->strlit ); 

    StringTableFree( &tomoparam->ident ); 

    StringTableFree( &tomoparam->sect ); 

    if ( tomoparam->prfx != NULL ) free( (char *)tomoparam->prfx );

    free( tomoparam );

  }

}


extern char *TomoparamGetPrfx
             (const Tomoparam *tomoparam)

{
  char *prfx = NULL;

  if ( ( tomoparam != NULL ) && ( tomoparam->prfx != NULL ) ) {
    prfx = strdup( tomoparam->prfx );
  }

  return prfx;

}


static void TomoparamGetValueSub
            (const Tomoparam *tomoparam,
             const Size dim,
             const TomoparamVal *len,
             const TomoparamVal **valaddr,
             const TomoparamType type,
             char **value)

{
  char buf[128];
  char *ptr = buf;

  if ( ( dim == 0 ) || ( dim == SizeMax ) ) {

    const TomoparamVal *val = (*valaddr)++;
    switch ( type ) {
      case TomoparamUint: sprintf( buf, " %"SizeU,  val->uint ); break;
      case TomoparamSint: sprintf( buf, " %"IndexD, val->sint ); break;
      case TomoparamReal: sprintf( buf, " %.12"CoordG, val->real ); break;
      case TomoparamBool: ptr = val->bool ? " true" : " false";  break;
      case TomoparamStr: {
        const char *str = tomoparam->strlit;
        if ( ( str == NULL ) || ( val->index >= StringTableSize( str ) ) ) {
          str = "";
        } else {
          str += val->index;
        }
        ptr = StringConcat( *value, " \"", str, "\"", NULL );
        if ( ptr == NULL ) goto error;
        goto exit;
      }
      default: ptr = " undef";
    }
    ptr = StringConcat( *value, ptr, NULL );
    if ( ptr == NULL ) goto error;

  } else {

    ptr = StringConcat( *value, " {", NULL );
    if ( ptr == NULL ) goto error;
    *value = ptr;
    for ( Size i = 0; i < len[dim-1].uint; i++ ) {
      TomoparamGetValueSub( tomoparam, dim - 1, len, valaddr, type, value );
      if ( *value == NULL ) return;
    }
    ptr = StringConcat( *value, " }", NULL );
    if ( ptr == NULL ) goto error;
  }

  exit: *value = ptr;

  return;

  error: free( *value ); *value = NULL;

  return;

}


extern char *TomoparamGetValue
             (const Tomoparam *tomoparam,
              const char *ident)

{
  TomoparamVar *var;
  Status status;

  if ( tomoparam == NULL ) return NULL;
  if ( ident == NULL ) return NULL;

  status = TomoparamLookup( tomoparam, ident, &var );
  if ( exception( status ) ) return NULL;

  const TomoparamVal *len = TomoparamGetLen( *var );
  const TomoparamVal *val =TomoparamGetVal( *var );

  char *value = strdup( "" );
  if ( value == NULL ) return NULL;

  TomoparamGetValueSub( tomoparam, var->dim, len, &val, var->type, &value );

  return value;

}


extern Status TomoparamList
              (const Tomoparam *tomoparam,
               const char *ident,
               const char *section,
               FILE *stream)

{
  TomoparamVar *var;
  Status status;

  if ( ident == NULL ) {

    var = tomoparam->vartab;
    if ( ( var == NULL ) && tomoparam->varlen ) {
      return exception( E_TOMOPARAM );
    }

    for ( Size i = 0; i < tomoparam->varlen; i++, var++ ) {
      if ( var->param ) {
        status = TomoparamPrintVar( tomoparam, var, section, stream );
        if ( exception( status ) ) return status;
      }
    }

  } else {

    status = TomoparamLookup( tomoparam, ident, &var );
    if ( exception( status ) ) return status;

    status = TomoparamPrintVar( tomoparam, var, section, stream );
    if ( exception( status ) ) return status;

  }

  return E_NONE;

}
