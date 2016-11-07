/*----------------------------------------------------------------------------*
*
*  tomoparamwrite.c  -  tomography: parameter files
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
#include "array.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* functions */

extern Status TomoparamWrite
              (Tomoparam *tomoparam,
               const char *ident,
               TomoparamType type,
               Size dim,
               const Size *len,
               const void *val)

{
  TomoparamVal *valtab;
  Size typesize, count = 1;
  Size valinc = 0;
  Status status;

  if ( tomoparam == NULL ) return exception( E_ARGVAL );
  if ( ( ident == NULL ) || !*ident ) return exception( E_ARGVAL );
  if ( dim && ( len == NULL ) ) return exception( E_ARGVAL );
  if ( val == NULL ) return exception( E_ARGVAL );

  if ( dim ) {
    status = ArraySize( dim, len, sizeof(TomoparamVal), &count );
    if ( exception( status ) ) return status;
    valinc = count;
    if ( dim > 1 ) valinc += dim;
  }

  Size index;
  status = TomoparamLookupIdent( tomoparam, ident, strlen( ident ), True, &index );
  if ( status != E_STRINGTABLE_NOTFOUND ) {
    if ( exception( status ) ) return status;
  }

  switch ( type ) {
    case TomoparamUint: typesize = sizeof( valtab->uint ); break;
    case TomoparamSint: typesize = sizeof( valtab->sint ); break;
    case TomoparamReal: typesize = sizeof( valtab->real ); break;
    case TomoparamBool: typesize = sizeof( valtab->bool ); break;
    case TomoparamStr:  typesize = sizeof( TomoparamVal ); break;
    default: return exception( E_TOMOPARAM_DAT );
  }

  TomoparamVar *dst;
  status = TomoparamLookup( tomoparam, ident, &dst );
  if ( status && ( status != E_TOMOPARAM_UNDEF ) ) return exception( status );

  if ( status ) {

    TomoparamVar *vartab = realloc( tomoparam->vartab, ( tomoparam->varlen + 1 ) * sizeof(TomoparamVar) );
    if ( vartab == NULL ) return exception( E_MALLOC );
    tomoparam->vartab = vartab;

    dst = vartab + tomoparam->varlen;

    *dst = TomoparamVarInitializer;

    dst->dim = dim;
    dst->count = count;
    dst->type = type;
    dst->param = True;

    if ( dim ) {

      Size vallen = tomoparam->vallen;
      valtab = realloc( tomoparam->valtab, ( vallen + valinc ) * sizeof(TomoparamVal) );
      if ( valtab == NULL ) return exception( E_MALLOC );
      tomoparam->valtab = valtab;
      valtab += vallen;

      if ( dim == 1 ) {
        dst->len.uint = *len;
      } else {
        dst->len.uint = vallen;
        for ( Size d = 0; d < dim; d++, valtab++ ) {
          valtab->uint = len[d];
        }
      }

      const char *valptr = val;
      for ( Size i = 0; i < count; i++, valtab++, valptr += typesize ) {
        memcpy( valtab, valptr, typesize );
      }

    } else {

      dst->len.uint = 0;
      memcpy( &dst->val, val, typesize );

    }

    status = TomoparamInsertIdent( tomoparam, ident, strlen( ident ), &dst->name );
    if ( exception( status ) ) return status;

    tomoparam->vallen += valinc;
    tomoparam->varlen++;

  } else {

    if ( dst->tmplen || dst->tmpval ) {
      return exception( E_TOMOPARAM );
    }
    if ( ( dst->dim != dim ) || ( dst->count != count ) ) {
      return exception( E_TOMOPARAM_LEN );
    }
    if ( dim > 1 ) {
      const TomoparamVal *dstlen = tomoparam->valtab + dst->len.uint;
      for ( Size d = 0; d < dim; d++, dstlen++ ) {
        if ( dstlen->uint != len[d] ) return exception( E_TOMOPARAM_LEN );
      }
    }
    if ( dst->type != type ) {
      return exception( E_TOMOPARAM_TYPE );
    }

    const char *valptr = val;
    valtab = TomoparamGetVal( *dst );
    for ( Size i = 0; i < count; i++, valtab++, valptr += typesize ) {
      memcpy( valtab, valptr, typesize );
    }

  }

  return E_NONE;

}


extern Status TomoparamWriteParam
              (Tomoparam *tomoparam,
               const char *ident,
               const char *val)

{
  TomoparamVar *var;
  void *par = NULL;
  int len;
  Status status;

  if ( tomoparam == NULL ) return exception( E_ARGVAL );
  if ( ( ident == NULL ) || !*ident ) return exception( E_ARGVAL );
  if ( val == NULL ) return exception( E_ARGVAL );

  status = TomoparamLookup( tomoparam, ident, &var );
  if ( exception( status ) ) return status;

  status = TomoparamParseType( tomoparam, val, var->type, &par, &len );
  if ( exception( status ) ) return status;

  Size ulen = len;
  status = TomoparamWrite( tomoparam, ident, var->type, ( len < 0 ) ? 0 : 1, &ulen, par );
  logexception( status );

  if ( par != NULL ) free( par );

  return status;

}
