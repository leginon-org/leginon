/*----------------------------------------------------------------------------*
*
*  tomoparamread.c  -  tomography: parameter files
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
#include "stringparse.h"
#include "exception.h"
#include <ctype.h>
#include <stdlib.h>
#include <string.h>


/* functions */

extern const char *TomoparamSname
                   (const Tomoparam *tomoparam)

{
  static const char nil[] = "";

  if ( tomoparam == NULL ) return nil;

  return tomoparam->sname;

}


extern Status TomoparamSet
              (Tomoparam *tomoparam,
               const char *section,
               const char **sname)

{
  Size index;
  char *sect = NULL;
  Size len = 0;
  Status status = E_NONE;

  if ( argcheck( tomoparam == NULL ) ) return exception( E_ARGVAL );

  if ( ( section != NULL ) && *section ) {
    status = StringTableLookup( tomoparam->sect, section, &index );
    if ( status == E_STRINGTABLE_NOTFOUND ) {
      status = ( sname == NULL ) ? E_TOMOPARAM_UNSEC : E_NONE;
      goto exit;
    }
    if ( exception( status ) ) return status;
    len = strlen( section );
  }

  sect = realloc( tomoparam->sname, len + 1 );
  if ( sect == NULL ) return exception( E_MALLOC );
  tomoparam->sname = sect;

  memcpy( sect, section, len );
  sect[len] = 0;

  exit:
  if ( sname != NULL ) *sname = sect;

  return status;

}


extern Status TomoparamPush
              (Tomoparam *tomoparam,
               const char *ident,
               const char **sname)

{
  Size index;
  Status status;

  if ( argcheck( tomoparam == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( ident == NULL ) ) return exception( E_ARGVAL );

  status = TomoparamExtend( tomoparam, ident, strlen( ident ) );
  if ( exception( status ) ) return status;

  char *sect = tomoparam->sname;

  status = StringTableLookup( tomoparam->sect, sect, &index );
  if ( status ) {
    TomoparamRemove( sect );
    if ( status == E_STRINGTABLE_NOTFOUND ) {
      status = E_NONE;
    } else {
      return exception( status );
    }
    sect = NULL;
  }

  if ( sname != NULL ) *sname = sect;

  return E_NONE;

}


extern Status TomoparamPop
              (Tomoparam *tomoparam,
               const char **sname)

{

  if ( argcheck( tomoparam == NULL ) ) return exception( E_ARGVAL );

  char *sect = tomoparam->sname;
  if ( sect == NULL ) return exception( E_TOMOPARAM );

  TomoparamRemove( sect );

  if ( sname != NULL ) *sname = sect;

  return E_NONE;

}


extern Status TomoparamReadMeta
              (const Tomoparam *tomoparam,
               const char *ident,
               Size *dim,
               Size **lenaddr,
               TomoparamType *type)

{
  Status status;

  if ( tomoparam == NULL ) return exception( E_ARGVAL );
  if ( ( ident == NULL ) || !*ident ) return exception( E_ARGVAL );

  TomoparamVar *var;
  status = TomoparamLookup( tomoparam, ident, &var );
  if ( exception( status ) ) return status;

  if ( lenaddr != NULL ) {

    Size *len = malloc( ( var->dim ? var->dim : 1 ) * sizeof(Size) );
    if ( len == NULL ) return exception( E_MALLOC );

    TomoparamVal *varlen = TomoparamGetLen( *var );

    len[0] = 0;
    for ( Size i = 0; i < var->dim; i++ ) {
      len[i] = varlen[i].uint;
    }

  }

  if ( dim != NULL ) *dim = var->dim;
  if ( type != NULL ) *type = var->type;

  return E_NONE;

}


extern Status TomoparamReadSize
              (const Tomoparam *tomoparam,
               const char *ident,
               Size *dim,
               Size **len,
               Size **val,
               Size *count)

{
  Status status;

  if ( tomoparam == NULL ) return exception( E_ARGVAL );
  if ( ( ident == NULL ) || !*ident ) return exception( E_ARGVAL );

  TomoparamVar *var;
  status = TomoparamLookup( tomoparam, ident, &var );
  if ( exception( status ) ) return status;

  if ( var->type != TomoparamUint ) return exception( E_TOMOPARAM_DAT );

  Size cnt =  var->count ? var->count : 1;
  if ( cnt == SizeMax ) return exception( E_TOMOPARAM );

  Size *lenbuf = NULL;
  if ( ( len != NULL ) && var->dim ) {
    lenbuf = malloc( var->dim * sizeof(Size) );
    if ( lenbuf == NULL ) return exception( E_MALLOC );
    TomoparamVal *varlen = TomoparamGetLen( *var );
    for ( Size i = 0; i < var->dim; i++ ) {
      lenbuf[i] = varlen[i].uint;
    }
  }

  Size *valbuf;
  if ( val != NULL ) {
    valbuf = malloc( cnt * sizeof(*valbuf) );
    if ( valbuf == NULL ) {
      if ( lenbuf != NULL ) free( lenbuf );
      return exception( E_MALLOC );
    }
  }

  if ( tomoparam->logparam ) {
    TomoparamPrintVar( tomoparam, var, tomoparam->sname, NULL );
  }

  if ( dim != NULL ) *dim = var->dim;

  if ( len != NULL ) *len = lenbuf;

  if ( val != NULL ) {
    TomoparamVal *varval = TomoparamGetVal( *var );
    valbuf[0] = 0;
    for ( Size i = 0; i < var->count; i++ ) {
      valbuf[i] = varval[i].uint;
    }
    *val = valbuf;
  }

  if ( count != NULL ) *count = var->count;

  return E_NONE;

}


extern Status TomoparamReadIndex
              (const Tomoparam *tomoparam,
               const char *ident,
               Size *dim,
               Size **len,
               Index **val,
               Size *count)

{
  Status status;

  if ( tomoparam == NULL ) return exception( E_ARGVAL );
  if ( ( ident == NULL ) || !*ident ) return exception( E_ARGVAL );

  TomoparamVar *var;
  status = TomoparamLookup( tomoparam, ident, &var );
  if ( exception( status ) ) return status;

  if ( var->type != TomoparamSint ) return exception( E_TOMOPARAM_DAT );

  Size cnt =  var->count ? var->count : 1;
  if ( cnt == SizeMax ) return exception( E_TOMOPARAM );

  Size *lenbuf = NULL;
  if ( ( len != NULL ) && var->dim ) {
    lenbuf = malloc( var->dim * sizeof(Size) );
    if ( lenbuf == NULL ) return exception( E_MALLOC );
    TomoparamVal *varlen = TomoparamGetLen( *var );
    for ( Size i = 0; i < var->dim; i++ ) {
      lenbuf[i] = varlen[i].uint;
    }
  }

  Index *valbuf;
  if ( val != NULL ) {
    valbuf = malloc( cnt * sizeof(*valbuf) );
    if ( valbuf == NULL ) {
      if ( lenbuf != NULL ) free( lenbuf );
      return exception( E_MALLOC );
    }
  }

  if ( tomoparam->logparam ) {
    TomoparamPrintVar( tomoparam, var, tomoparam->sname, NULL );
  }

  if ( dim != NULL ) *dim = var->dim;

  if ( len != NULL ) *len = lenbuf;

  if ( val != NULL ) {
    TomoparamVal *varval = TomoparamGetVal( *var );
    valbuf[0] = 0;
    for ( Size i = 0; i < var->count; i++ ) {
      valbuf[i] = varval[i].sint;
    }
    *val = valbuf;
  }

  if ( count != NULL ) *count = var->count;

  return E_NONE;

}


extern Status TomoparamReadCoord
              (const Tomoparam *tomoparam,
               const char *ident,
               Size *dim,
               Size **len,
               Coord **val,
               Size *count)

{
  Status status;

  if ( tomoparam == NULL ) return exception( E_ARGVAL );
  if ( ( ident == NULL ) || !*ident ) return exception( E_ARGVAL );

  TomoparamVar *var;
  status = TomoparamLookup( tomoparam, ident, &var );
  if ( exception( status ) ) return status;

  switch ( var->type ) {
    case TomoparamUint:
    case TomoparamSint:
    case TomoparamReal: break;
    default: return exception( E_TOMOPARAM_DAT );
  }

  Size cnt =  var->count ? var->count : 1;
  if ( cnt == SizeMax ) return exception( E_TOMOPARAM );

  Size *lenbuf = NULL;
  if ( ( len != NULL ) && var->dim ) {
    lenbuf = malloc( var->dim * sizeof(Size) );
    if ( lenbuf == NULL ) return exception( E_MALLOC );
    TomoparamVal *varlen = TomoparamGetLen( *var );
    for ( Size i = 0; i < var->dim; i++ ) {
      lenbuf[i] = varlen[i].uint;
    }
  }

  Coord *valbuf;
  if ( val != NULL ) {
    valbuf = malloc( cnt * sizeof(*valbuf) );
    if ( valbuf == NULL ) {
      if ( lenbuf != NULL ) free( lenbuf );
      return exception( E_MALLOC );
    }
  }

  if ( tomoparam->logparam ) {
    TomoparamPrintVar( tomoparam, var, tomoparam->sname, NULL );
  }

  if ( dim != NULL ) *dim = var->dim;

  if ( len != NULL ) *len = lenbuf;

  if ( val != NULL ) {
    TomoparamVal *varval = TomoparamGetVal( *var );
    valbuf[0] = 0;
    switch ( var->type ) {
      case TomoparamUint: {
        for ( Size i = 0; i < var->count; i++ ) {
          valbuf[i] = varval[i].uint;
        }
        break;
      }
      case TomoparamSint: {
        for ( Size i = 0; i < var->count; i++ ) {
          valbuf[i] = varval[i].sint;
        }
        break;
      }
      case TomoparamReal: {
        for ( Size i = 0; i < var->count; i++ ) {
          valbuf[i] = varval[i].real;
        }
        break;
      }
      default: return exception( E_TOMOPARAM_DAT );
    }
    *val = valbuf;
  }

  if ( count != NULL ) *count = var->count;

  return E_NONE;

}


extern Status TomoparamReadScalarSize
              (const Tomoparam *tomoparam,
               const char *ident,
               Size *scalar)

{
  Status status;

  if ( tomoparam == NULL ) return exception( E_ARGVAL );
  if ( ( ident == NULL ) || !*ident ) return exception( E_ARGVAL );

  TomoparamVar *var;
  status = TomoparamLookup( tomoparam, ident, &var );
  if ( exception( status ) ) return status;

  if ( var->dim ) return exception( E_TOMOPARAM_DIM );
  if ( var->type != TomoparamUint ) return exception( E_TOMOPARAM_DAT );

  if ( tomoparam->logparam ) TomoparamPrintVar( tomoparam, var, tomoparam->sname, NULL );

  if ( scalar != NULL ) *scalar = var->val.uint;

  return E_NONE;

}


extern Status TomoparamReadScalarIndex
              (const Tomoparam *tomoparam,
               const char *ident,
               Index *scalar)

{
  Status status;

  if ( tomoparam == NULL ) return exception( E_ARGVAL );
  if ( ( ident == NULL ) || !*ident ) return exception( E_ARGVAL );

  TomoparamVar *var;
  status = TomoparamLookup( tomoparam, ident, &var );
  if ( exception( status ) ) return status;

  if ( var->dim ) return exception( E_TOMOPARAM_DIM );
  if ( var->type != TomoparamSint ) return exception( E_TOMOPARAM_DAT );

  if ( tomoparam->logparam ) TomoparamPrintVar( tomoparam, var, tomoparam->sname, NULL );

  if ( scalar != NULL ) *scalar = var->val.sint;

  return E_NONE;

}


extern Status TomoparamReadScalarCoord
              (const Tomoparam *tomoparam,
               const char *ident,
               Coord *scalar)

{
  Status status;

  if ( tomoparam == NULL ) return exception( E_ARGVAL );
  if ( ( ident == NULL ) || !*ident ) return exception( E_ARGVAL );

  TomoparamVar *var;
  status = TomoparamLookup( tomoparam, ident, &var );
  if ( exception( status ) ) return status;

  if ( var->dim ) return exception( E_TOMOPARAM_DIM );

  Coord val;
  switch ( var->type ) {
    case TomoparamUint: val = var->val.uint; break;
    case TomoparamSint: val = var->val.sint; break;
    case TomoparamReal: val = var->val.real; break;
    default: return exception( E_TOMOPARAM_DAT );
  }

  if ( tomoparam->logparam ) TomoparamPrintVar( tomoparam, var, tomoparam->sname, NULL );

  if ( scalar != NULL ) *scalar = val;

  return E_NONE;

}


extern Status TomoparamReadScalarBool
              (const Tomoparam *tomoparam,
               const char *ident,
               Bool *scalar)

{
  Status status;

  if ( tomoparam == NULL ) return exception( E_ARGVAL );
  if ( ( ident == NULL ) || !*ident ) return exception( E_ARGVAL );

  TomoparamVar *var;
  status = TomoparamLookup( tomoparam, ident, &var );
  if ( exception( status ) ) return status;

  if ( var->dim ) return exception( E_TOMOPARAM_DIM );
  if ( var->type != TomoparamBool ) return exception( E_TOMOPARAM_DAT );

  if ( tomoparam->logparam ) TomoparamPrintVar( tomoparam, var, tomoparam->sname, NULL );

  if ( scalar != NULL ) *scalar = var->val.bool;

  return E_NONE;

}


extern Status TomoparamReadScalarString
              (const Tomoparam *tomoparam,
               const char *ident,
               char **scalar)

{
  Status status;

  if ( tomoparam == NULL ) return exception( E_ARGVAL );
  if ( ( ident == NULL ) || !*ident ) return exception( E_ARGVAL );

  TomoparamVar *var;
  status = TomoparamLookup( tomoparam, ident, &var );
  if ( exception( status ) ) return status;

  if ( var->dim ) return exception( E_TOMOPARAM_DIM );
  if ( var->type != TomoparamStr ) return exception( E_TOMOPARAM_DAT );

  const char *src = tomoparam->strlit;
  if ( ( src == NULL ) || ( var->val.index >= StringTableSize( src ) ) ) {
    return exception( E_TOMOPARAM );
  }
  src += var->val.index;

  if ( tomoparam->logparam ) TomoparamPrintVar( tomoparam, var, tomoparam->sname, NULL );

  if ( scalar != NULL ) {
    char *dst = strdup( src );
    if ( dst == NULL ) return exception( E_MALLOC );
    *scalar = dst;
  }

  return E_NONE;

}


extern Status TomoparamReadArraySize
              (const Tomoparam *tomoparam,
               const char *ident,
               Size *array,
               Size len,
               Size *outlen)

{
  Status status;

  if ( tomoparam == NULL ) return exception( E_ARGVAL );
  if ( ( ident == NULL ) || !*ident ) return exception( E_ARGVAL );

  TomoparamVar *var;
  status = TomoparamLookup( tomoparam, ident, &var );
  if ( exception( status ) ) return status;

  if ( var->dim != 1 ) return exception( E_TOMOPARAM_DIM );
  if ( var->type != TomoparamUint ) return exception( E_TOMOPARAM_DAT );
  if ( var->len.uint > len ) return exception( E_TOMOPARAM_LEN );
  if ( ( outlen != NULL ) && !*outlen ) {
    *outlen = var->len.uint;
  } else {
    if ( outlen != NULL ) len = *outlen;
    if ( var->len.uint != len ) return exception( E_TOMOPARAM_LEN );
  }

  if ( tomoparam->logparam ) TomoparamPrintVar( tomoparam, var, tomoparam->sname, NULL );

  if ( array != NULL ) {
    TomoparamVal *val = TomoparamGetVal( *var );
    for ( Size i = 0; i < var->count; i++ ) {
      array[i] = val[i].uint;
    }

  }

  return E_NONE;

}


extern Status TomoparamReadArrayIndex
              (const Tomoparam *tomoparam,
               const char *ident,
               Index *array,
               Size len,
               Size *outlen)

{
  Status status;

  if ( tomoparam == NULL ) return exception( E_ARGVAL );
  if ( ( ident == NULL ) || !*ident ) return exception( E_ARGVAL );

  TomoparamVar *var;
  status = TomoparamLookup( tomoparam, ident, &var );
  if ( exception( status ) ) return status;

  if ( var->dim != 1 ) return exception( E_TOMOPARAM_DIM );
  if ( var->type != TomoparamSint ) return exception( E_TOMOPARAM_DAT );
  if ( var->len.uint > len ) return exception( E_TOMOPARAM_LEN );
  if ( ( outlen != NULL ) && !*outlen ) {
    *outlen = var->len.uint;
  } else {
    if ( outlen != NULL ) len = *outlen;
    if ( var->len.uint != len ) return exception( E_TOMOPARAM_LEN );
  }

  if ( tomoparam->logparam ) TomoparamPrintVar( tomoparam, var, tomoparam->sname, NULL );

  if ( array != NULL ) {
    TomoparamVal *val = TomoparamGetVal( *var );
    for ( Size i = 0; i < var->count; i++ ) {
      array[i] = val[i].sint;
    }

  }

  return E_NONE;

}


extern Status TomoparamReadArrayCoord
              (const Tomoparam *tomoparam,
               const char *ident,
               Coord *array,
               Size len,
               Size *outlen)

{
  Status status;

  if ( tomoparam == NULL ) return exception( E_ARGVAL );
  if ( ( ident == NULL ) || !*ident ) return exception( E_ARGVAL );

  TomoparamVar *var;
  status = TomoparamLookup( tomoparam, ident, &var );
  if ( exception( status ) ) return status;

  if ( var->dim != 1 ) return exception( E_TOMOPARAM_DIM );
  switch ( var->type ) {
    case TomoparamUint:
    case TomoparamSint:
    case TomoparamReal: break;
    default: return exception( E_TOMOPARAM_DAT );
  }
  if ( var->len.uint > len ) return exception( E_TOMOPARAM_LEN );
  if ( ( outlen != NULL ) && !*outlen ) {
    *outlen = var->len.uint;
  } else {
    if ( outlen != NULL ) len = *outlen;
    if ( var->len.uint != len ) return exception( E_TOMOPARAM_LEN );
  }

  if ( tomoparam->logparam ) TomoparamPrintVar( tomoparam, var, tomoparam->sname, NULL );

  if ( array != NULL ) {
    TomoparamVal *val = TomoparamGetVal( *var );
    switch ( var->type ) {
     case  TomoparamUint: {
        for ( Size i = 0; i < var->count; i++ ) {
          array[i] = val[i].uint;
        }
        break;
      }
      case TomoparamSint: {
        for ( Size i = 0; i < var->count; i++ ) {
          array[i] = val[i].sint;
        }
        break;
      }
      case TomoparamReal: {
        for ( Size i = 0; i < var->count; i++ ) {
          array[i] = val[i].real;
        }
        break;
      }
      default: return exception( E_TOMOPARAM_DAT );
    }
  }

  return E_NONE;

}


extern Status TomoparamReadMat
              (const Tomoparam *tomoparam,
               const char *ident,
               Coord *array,
               const Size *len,
               Size *outlen)

{
  Status status;

  if ( tomoparam == NULL ) return exception( E_ARGVAL );
  if ( ( ident == NULL ) || !*ident ) return exception( E_ARGVAL );

  TomoparamVar *var;
  status = TomoparamLookup( tomoparam, ident, &var );
  if ( exception( status ) ) return status;

  if ( var->dim != 2 ) return exception( E_TOMOPARAM_DIM );
  switch ( var->type ) {
    case TomoparamUint:
    case TomoparamSint:
    case TomoparamReal: break;
    default: return exception( E_TOMOPARAM_DAT );
  }
  TomoparamVal *varlen = TomoparamGetLen( *var );
  if ( ( varlen[0].uint > len[0] ) || ( varlen[1].uint > len[1] ) ) return exception( E_TOMOPARAM_LEN );
  if ( ( outlen != NULL ) && !outlen[0] && !outlen[1] ) {
    outlen[0] = varlen[0].uint;
    outlen[1] = varlen[1].uint;
  } else {
    if ( outlen != NULL ) len = outlen;
    if ( ( varlen[0].uint != len[0] ) || ( varlen[1].uint != len[1] ) ) return exception( E_TOMOPARAM_LEN );
  }

  if ( tomoparam->logparam ) TomoparamPrintVar( tomoparam, var, tomoparam->sname, NULL );

  if ( array != NULL ) {
    TomoparamVal *val = TomoparamGetVal( *var );
    switch ( var->type ) {
     case  TomoparamUint: {
        for ( Size i = 0; i < var->count; i++ ) {
          array[i] = val[i].uint;
        }
        break;
      }
      case TomoparamSint: {
        for ( Size i = 0; i < var->count; i++ ) {
          array[i] = val[i].sint;
        }
        break;
      }
      case TomoparamReal: {
        for ( Size i = 0; i < var->count; i++ ) {
          array[i] = val[i].real;
        }
        break;
      }
      default: return exception( E_TOMOPARAM_DAT );
    }
  }

  return E_NONE;

}


extern Status TomoparamReadMatn
              (const Tomoparam *tomoparam,
               const char *ident,
               Coord *array,
               Size len,
               Size *outlen)

{
  Status status;

  if ( tomoparam == NULL ) return exception( E_ARGVAL );
  if ( ( ident == NULL ) || !*ident ) return exception( E_ARGVAL );

  TomoparamVar *var;
  status = TomoparamLookup( tomoparam, ident, &var );
  if ( exception( status ) ) return status;

  if ( var->dim != 2 ) return exception( E_TOMOPARAM_DIM );
  switch ( var->type ) {
    case TomoparamUint:
    case TomoparamSint:
    case TomoparamReal: break;
    default: return exception( E_TOMOPARAM_DAT );
  }
  TomoparamVal *varlen = TomoparamGetLen( *var );
  if ( ( varlen[0].uint != varlen[1].uint ) || ( varlen[0].uint > len ) ) return exception( E_TOMOPARAM_LEN );
  if ( ( outlen != NULL ) && !*outlen ) {
    *outlen = varlen[0].uint;
  } else {
    if ( outlen != NULL ) len = *outlen;
    if ( varlen[0].uint != len ) return exception( E_TOMOPARAM_LEN );
  }

  if ( tomoparam->logparam ) TomoparamPrintVar( tomoparam, var, tomoparam->sname, NULL );

  if ( array != NULL ) {
    TomoparamVal *val = TomoparamGetVal( *var );
    switch ( var->type ) {
     case  TomoparamUint: {
        for ( Size i = 0; i < var->count; i++ ) {
          array[i] = val[i].uint;
        }
        break;
      }
      case TomoparamSint: {
        for ( Size i = 0; i < var->count; i++ ) {
          array[i] = val[i].sint;
        }
        break;
      }
      case TomoparamReal: {
        for ( Size i = 0; i < var->count; i++ ) {
          array[i] = val[i].real;
        }
        break;
      }
      default: return exception( E_TOMOPARAM_DAT );
    }
  }

  return E_NONE;

}


extern Status TomoparamReadSelection
              (const Tomoparam *tomoparam,
               const char *ident,
               Size **selection)

{
  Size *sel = NULL;
  Status status;

  if ( tomoparam == NULL ) return exception( E_ARGVAL );
  if ( ( ident == NULL ) || !*ident ) return exception( E_ARGVAL );

  char *string;
  status = TomoparamReadScalarString( tomoparam, ident, &string );
  if ( exception( status ) ) return status;

  char *str = string + strlen( string );
  while ( ( str != string ) && isspace( *--str ) ) *str = 0;
  str = string;
  while ( isspace( *str ) ) str++;

  if ( *str ) {

    const char *end;
    StringParseParam parseparam;
    parseparam.selection.count = SizeMax;
    parseparam.selection.space = True;

    status = StringParseSelection( str, &end, NULL, &parseparam );
    if ( ( status == E_STRINGPARSE_NOPARSE ) && !*end ) status = E_NONE;
    if ( status ) goto exit;
    if ( *end ) { status = exception( E_TOMOPARAM_SEL ); goto exit; }
    if ( parseparam.selection.count ) {
      sel = malloc( ( 2 * parseparam.selection.count + 1 ) * sizeof(*sel) );
      if ( sel == NULL ) { status = exception( E_MALLOC ); goto exit; }
      status = StringParseSelection( str, &end, sel + 1, &parseparam );
      if ( exception( status ) ) goto error;
      if ( parseparam.selection.empty ) { status = exception( E_TOMOPARAM_SEL ); goto error; }
      *sel = parseparam.selection.count;
    }

  }

  if ( selection != NULL ) {
    *selection = sel;
  }

  exit: free( string );

  return status;

  /* error handling */

  error: free( sel );
  goto exit;

}
