/*----------------------------------------------------------------------------*
*
*  tomoparamsemant.c  -  tomography: parameter files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomoparamsemant.h"
#include "message.h"
#include "matn.h"
#include "exception.h"
#include <stdlib.h>
#include <string.h>


/* macros */

#define TomoparamCheckArg( expr )  ( ( expr ) ? ( tomoparam->parse->status = pushexception( E_TOMOPARAM ) ) : E_NONE )

#define SRC( v, t )  ( ( (t) == TomoparamReal ) ? ( (v).real ) : ( ( (t) == TomoparamUint ) ? ( (v).uint ) : ( (v).sint ) ) )

#define UOP( d, td, op, s, ts )                                             \
  switch ( td ) {                                                           \
    case TomoparamUint: (d).uint = op SRC( s, ts ); break;                  \
    case TomoparamSint: (d).sint = op SRC( s, ts ); break;                  \
    case TomoparamReal: (d).real = op SRC( s, ts ); break;                  \
    default: break;                                                         \
  }                                                                         \

#define BOP( d, td, s1, t1, op, s2, t2 )                                    \
  switch ( td ) {                                                           \
    case TomoparamUint: (d).uint = SRC( s1, t1 ) op SRC( s2, t2 ); break;   \
    case TomoparamSint: (d).sint = SRC( s1, t1 ) op SRC( s2, t2 ); break;   \
    case TomoparamReal: (d).real = SRC( s1, t1 ) op SRC( s2, t2 ); break;   \
    default: break;                                                         \
  }                                                                         \

#define TomoparamDebug( str, ... ) if ( debug ) MessageString( str, __VA_ARGS__, "\n", NULL )


/* functions */

static void TomoparamMatTransp
            (Size m,
             Size n,
             const TomoparamVal *A,
             TomoparamVal *B)

{
  TomoparamVal Bbuf[m*n];

  TomoparamVal *Bij = Bbuf;

  for ( Size j = 0; j < n; j++ ) {

    const TomoparamVal *Aij = A + j;
    for ( Size i = 0; i < m; i++ ) {
      *Bij++ = *Aij;
      Aij += n;
    }

  }

  memcpy( B, Bbuf, sizeof(Bbuf) );

}


static void TomoparamMatMul
            (const Tomoparam *tomoparam,
             const TomoparamVar *A,
             const TomoparamVar *B,
             TomoparamVar *C)

{
  const TomoparamVal *Alen = TomoparamGetLen( *A );
  const TomoparamVal *Blen = TomoparamGetLen( *B );
  Size m = ( A->dim == 1 ) ? 1 : Alen[1].uint;
  Size n = Alen[0].uint;
  Size l = Blen[0].uint;

  TomoparamVal Cbuf[m*l];

  const TomoparamVal *Ai = TomoparamGetVal( *A );
  const TomoparamVal *B0 = TomoparamGetVal( *B );
  TomoparamVal *C0 = TomoparamGetVal( *C );
  TomoparamVal *Cij = Cbuf;
  TomoparamVal cij;

  for ( Size i = 0; i < m; i++ ) {

    for ( Size j = 0; j < l; j++ ) {

      const TomoparamVal *Bij = B0 + j;
      switch ( C->type ) {
        case TomoparamUint: {
          cij.uint = 0;
          for ( Size k = 0; k < n; k++ ) {
            cij.uint += SRC( Ai[k], A->type ) * SRC( *Bij, B->type );
            Bij += l;
          }
          *Cij++ = cij;
          break;
        }
        case TomoparamSint: {
          cij.sint = 0;
          for ( Size k = 0; k < n; k++ ) {
            cij.sint += SRC( Ai[k], A->type ) * SRC( *Bij, B->type );
            Bij += l;
          }
          *Cij++ = cij;
          break;
        }
        case TomoparamReal: {
          cij.real = 0;
          for ( Size k = 0; k < n; k++ ) {
            cij.real += SRC( Ai[k], A->type ) * SRC( *Bij, B->type );
            Bij += l;
          }
          *Cij++ = cij;
          break;
        }
        default: break;                                                         \
      }                                                                         \

    }

    Ai += n;

  }

  memcpy( C0, Cbuf, sizeof(Cbuf) );

}


static TomoparamVal *TomoparamVarAlloc
                     (Tomoparam *tomoparam,
                      Size len,
                      TomoparamVal *dst)

{
  TomoparamVal *val = tomoparam->valtab;
  Size vallen = SizeMax;

  if ( len ) {
    vallen = tomoparam->vallen;
    val = realloc( val, ( vallen + len ) * sizeof(TomoparamVal) );
    if ( val == NULL ) return NULL;
    tomoparam->valtab = val;
    val += vallen;
    tomoparam->vallen += len;
  }

  if ( dst != NULL ) {
    dst->uint = vallen;
  }

  return val;

}


static TomoparamVal *TomoparamTmpAlloc
                     (Tomoparam *tomoparam,
                      Size len,
                      TomoparamVal *dst)

{
  TomoparamVal *tmp = tomoparam->tmptab;
  Size tmplen = SizeMax;

  if ( len ) {
    tmplen = tomoparam->tmplen;
    tmp = realloc( tmp, ( tmplen + len ) * sizeof(TomoparamVal) );
    if ( tmp == NULL ) return NULL;
    tomoparam->tmptab = tmp;
    tmp += tmplen;
    tomoparam->tmplen += len;
  }

  if ( dst != NULL ) {
    dst->uint = tmplen;
  }

  return tmp;

}


extern void TomoparamPushStk
            (Tomoparam *tomoparam,
             const ParseSymb *symb)

{

  if ( TomoparamCheckArg( tomoparam == NULL ) ) return;
  if ( TomoparamCheckArg( symb == NULL ) ) return;

  if ( tomoparam->parse->status ) return;

  TomoparamStk *stk = realloc( tomoparam->stk, ( tomoparam->stklen + 1 ) * sizeof(TomoparamStk) );
  if ( stk == NULL ) {
    ParseError( tomoparam->parse, &symb->loc, E_MALLOC ); return;
  }
  tomoparam->stk = stk;

  stk += tomoparam->stklen;
  tomoparam->stklen++;

  stk->dim = SizeMax;
  stk->type = TomoparamUndef;
  stk->tmplen = tomoparam->tmplen;
  stk->elelen = tomoparam->elelen;

}


extern void TomoparamPopStk
            (Tomoparam *tomoparam,
             const ParseSymb *symb)

{
  if ( TomoparamCheckArg( tomoparam == NULL ) ) return;
  if ( TomoparamCheckArg( symb == NULL ) ) return;

  if ( tomoparam->parse->status ) return;

  if ( !tomoparam->stklen ) {
    ParseError( tomoparam->parse, &symb->loc, E_TOMOPARAM ); return;
  }

  TomoparamStk *stk = tomoparam->stk + --tomoparam->stklen;

  tomoparam->tmplen = stk->tmplen;
  tomoparam->elelen = stk->elelen;

}


static Status TomoparamPushSectionLoc
              (Tomoparam *tomoparam,
               const ParseLoc *loc)

{
  const Parse *parse = tomoparam->parse;

  ParseBuf *buf = realloc( tomoparam->sav, ( tomoparam->savlen + 1 ) * sizeof(*buf) );
  if ( buf == NULL ) return exception( E_MALLOC );
  tomoparam->sav = buf;

  buf += tomoparam->savlen;

  if ( loc->line == parse->bufp.loc.line ) {
    *buf = parse->bufp;
  } else if ( loc->line == parse->buf.loc.line ) {
    *buf = parse->buf;
  } else {
    *buf = ParseBufInitializer;
  }
  buf->loc = *loc;

  if ( buf->ptr != NULL ) {
    Size len = strlen( buf->ptr );
    char *ptr = malloc( len + 1 );
    if ( ptr == NULL ) return exception( E_MALLOC );
    memcpy( ptr, buf->ptr, len ); ptr[len] = 0;
    buf->ptr = ptr;
  } else {
    buf->ptr = NULL;
  }

  tomoparam->savlen++;

  return E_NONE;

}


static Status TomoparamPopSectionLoc
              (Tomoparam *tomoparam)

{

  if ( !tomoparam->savlen ) return exception( E_TOMOPARAM );

  tomoparam->savlen--;

  ParseBuf *buf = tomoparam->sav + tomoparam->savlen;

  if ( buf->ptr != NULL ) free( buf->ptr );

  return E_NONE;

}


extern void TomoparamPushSection
            (Tomoparam *tomoparam,
             const ParseSymb *symb,
             const ParseSymb *start)

{
  Status status;

  if ( TomoparamCheckArg( tomoparam == NULL ) ) return;
  if ( TomoparamCheckArg( symb == NULL ) ) return;

  if ( tomoparam->parse->status ) return;

  if ( !*symb->txt || !symb->len ) {
    status = exception( E_TOMOPARAM ); goto error;
  }

  status = TomoparamExtend( tomoparam, symb->txt, symb->len );
  if ( exception( status ) ) goto error;
  TomoparamDebug( "push sect  ", tomoparam->sname );

  Size index;
  status = StringTableInsert( &tomoparam->sect, tomoparam->sname, &index );
  if ( status == E_STRINGTABLE_EXISTS ) {
    status = exception( E_TOMOPARAM_EXISTS ); goto error;
  }
  if ( exception( status ) ) goto error;

  status = TomoparamPushSectionLoc( tomoparam, &start->loc );
  if ( exception( status ) ) goto error;

  return;

  error: ParseError( tomoparam->parse, &symb->loc, status );
  return;

}


extern void TomoparamPopSection
            (Tomoparam *tomoparam,
             const ParseSymb *symb)

{
  Status status;

  if ( TomoparamCheckArg( tomoparam == NULL ) ) return;
  if ( TomoparamCheckArg( symb == NULL ) ) return;

  if ( tomoparam->parse->status ) return;

  char *sname = tomoparam->sname;
  if ( ( sname == NULL ) || !*sname || ( *sname == '.' ) ) {
    status = exception( E_TOMOPARAM ); goto error;
  }
  TomoparamRemove( sname );
  TomoparamDebug( "pop  sect  ", *sname ? sname : "<nil>" );

  status = TomoparamPopSectionLoc( tomoparam );
  if ( exception( status ) ) goto error;

  return;

  error: ParseError( tomoparam->parse, &symb->loc, status );
  return;

}


extern void TomoparamSetVar
            (Tomoparam *tomoparam,
             const ParseSymb *id,
             const ParseSymb *op,
             const TomoparamVar *src)

{
  TomoparamVar *dst;
  Status status;

  if ( TomoparamCheckArg( tomoparam == NULL ) ) return;
  if ( TomoparamCheckArg( id == NULL ) ) return;
  if ( TomoparamCheckArg( op == NULL ) ) return;
  if ( TomoparamCheckArg( src == NULL ) ) return;

  if ( tomoparam->parse->status ) return;

  Bool param = ( *op->txt == ':' );

  Size index;
  status = TomoparamLookupIdent( tomoparam, id->txt, id->len, param, &index );
  if ( status != E_STRINGTABLE_NOTFOUND ) {
    if ( exception( status ) ) goto error;
  }

  const TomoparamVal *srclen = TomoparamGetLen( *src );
  const TomoparamVal *srcval = TomoparamGetVal( *src );
  TomoparamVal *dstlen = NULL;
  TomoparamVal *dstval = NULL;

  if ( status == E_STRINGTABLE_NOTFOUND ) {

    TomoparamVar *vartab = realloc( tomoparam->vartab, ( tomoparam->varlen + 1 ) * sizeof(TomoparamVar) );
    if ( vartab == NULL ) { status = exception( E_MALLOC ); goto error; }
    tomoparam->vartab = vartab;

    dst = vartab + tomoparam->varlen;

    dst->dim = src->dim;
    dst->count = src->count;
    dst->len = src->len;
    dst->val = src->val;
    dst->type = src->type;
    dst->tmplen = False;
    dst->tmpval = False;
    dst->param = param;

    if ( src->dim ) {
      if ( src->tmplen && ( src->dim > 1 ) ) {
        dstlen = TomoparamVarAlloc( tomoparam, src->dim, &dst->len );
        if ( dstlen == NULL ) { status = exception( E_MALLOC ); goto error; }
      }
      if ( src->tmpval ) {
        dstval = TomoparamVarAlloc( tomoparam, src->count, &dst->val );
        if ( dstval == NULL ) { status = exception( E_MALLOC ); goto error; }
      }
    }

    status = TomoparamInsertIdent( tomoparam, id->txt, id->len, &dst->name );
    if ( exception( status ) ) goto error;

    tomoparam->varlen++;

  } else {

    dst = TomoparamLookupVar( tomoparam, index );
    if ( ( dst == NULL ) || dst->tmplen || dst->tmpval ) {
      status = exception( E_TOMOPARAM ); goto error;
    }
    if ( dst->param ) {
      status = exception( E_TOMOPARAM_EXISTS ); goto error;
    }
    if ( ( dst->dim != src->dim ) || ( dst->count < src->count ) ) {
      status = exception( E_TOMOPARAM_LEN ); goto error;
    }

    dst->type = src->type;

    dstlen = TomoparamGetLen( *dst );
    dstval = TomoparamGetVal( *dst );

  }

  dst->loc = id->loc;

  if ( dstlen != NULL ) memcpy( dstlen, srclen, src->dim * sizeof(TomoparamVal) );
  if ( dstval != NULL ) memcpy( dstval, srcval, src->count * sizeof(TomoparamVal) );

  return;

  error: ParseError( tomoparam->parse, &id->loc, status );
  return;

}


extern TomoparamVar TomoparamGetVar
                    (const Tomoparam *tomoparam,
                     const ParseSymb *id)

{
  Status status;

  if ( TomoparamCheckArg( tomoparam == NULL ) ) return TomoparamVarInitializer;
  if ( TomoparamCheckArg( id == NULL ) ) return TomoparamVarInitializer;

  if ( tomoparam->parse->status ) return TomoparamVarInitializer;

  Size index;
  status = TomoparamLookupIdent( tomoparam, id->txt, id->len, False, &index );
  if ( status == E_STRINGTABLE_NOTFOUND ) {
    status = exception( E_TOMOPARAM_IDENT ); goto error;
  } else {
    if ( exception( status ) ) goto error;
  }

  TomoparamVar *var = TomoparamLookupVar( tomoparam, index );
  if ( ( var == NULL ) || var->tmplen || var->tmpval ) {
    status = exception( E_TOMOPARAM ); goto error;
  }
  var->loc = id->loc;

  return *var;

  error: ParseError( tomoparam->parse, &id->loc, status );
  return TomoparamVarInitializer;

}


extern TomoparamVar TomoparamGetArray
                    (Tomoparam *tomoparam,
                     const ParseSymb *symb)

{

  if ( TomoparamCheckArg( tomoparam == NULL ) ) return TomoparamVarInitializer;
  if ( TomoparamCheckArg( symb == NULL ) ) return TomoparamVarInitializer;

  if ( tomoparam->parse->status ) return TomoparamVarInitializer;

  if ( !tomoparam->stklen ) {
    ParseError( tomoparam->parse, &symb->loc, E_TOMOPARAM ); return TomoparamVarInitializer;
  }

  TomoparamStk *stk = tomoparam->stk + tomoparam->stklen - 1;
  Size count = tomoparam->elelen - stk->elelen;

  TomoparamVar var;
  var.dim = stk->dim + 1;
  var.count = count;
  var.len.uint = count;
  var.type = stk->type;
  var.loc = symb->loc;
  var.name = SizeMax;
  var.tmplen = True;
  var.tmpval = True;
  var.param = False;

  if ( ( var.type != TomoparamUndef ) && var.count ) {

    TomoparamVar *ele = tomoparam->eletab, *elend = ele + tomoparam->elelen;

    if ( var.dim == 1 ) {

      TomoparamVal *val = TomoparamTmpAlloc( tomoparam, var.count, &var.val );
      if ( val == NULL ) goto error;

      while ( ele < elend ) {
        UOP( *val, var.type, , ele->val, ele->type );
        val++; ele++;
      }

    } else {

      TomoparamVal *varlen = TomoparamTmpAlloc( tomoparam, var.dim, &var.len );
      if ( varlen == NULL ) goto error;

      TomoparamVal *vlen = varlen;
      TomoparamVal *elen = TomoparamGetLen( *ele );
      for ( Size i = 0; i < stk->dim; i++, vlen++, elen++ ) {
        vlen->uint = elen->uint;
      }
      vlen->uint = elen->uint;
      var.count *= ele->count;

      TomoparamVal *vval = TomoparamTmpAlloc( tomoparam, var.count, &var.val );
      if ( vval == NULL ) goto error;

      while ( ele < elend ) {
        vlen = varlen;
        elen = TomoparamGetLen( *ele );
        for ( Size i = 0; i < stk->dim; i++, vlen++, elen++ ) {
          if ( vlen->uint != elen->uint ) {
            ParseError( tomoparam->parse, &ele->loc, E_TOMOPARAM_LEN );
            var.type = TomoparamUndef;
            return var;
          }
        }
        TomoparamVal *eval = TomoparamGetVal( *ele );
        for ( Size i = 0; i < ele->count; i++, vval++, eval++ ) {
          UOP( *vval, var.type, , *eval, ele->type );
        }
        ele++;
      }
    }

  }

  return var;

  error: ParseError( tomoparam->parse, &symb->loc, E_MALLOC );
  return var;

}


extern void TomoparamElement
            (Tomoparam *tomoparam,
             const TomoparamVar *var)

{

  if ( TomoparamCheckArg( tomoparam == NULL ) ) return;
  if ( TomoparamCheckArg( var == NULL ) ) return;

  if ( tomoparam->parse->status ) return;

  TomoparamVar *ele = realloc( tomoparam->eletab, ( tomoparam->elelen + 1 ) * sizeof(TomoparamVar) );
  if ( ele == NULL ) {
    ParseError( tomoparam->parse, &var->loc, E_MALLOC ); return;
  }
  tomoparam->eletab = ele;

  if ( !tomoparam->stklen ) {
    ParseError( tomoparam->parse, &var->loc, E_TOMOPARAM ); return;
  }
  TomoparamStk *stk = tomoparam->stk + tomoparam->stklen - 1;

  if ( ( stk->type >= TomoparamTypeMax ) || ( var->type >= TomoparamTypeMax ) ) {
    ParseError( tomoparam->parse, &var->loc, E_TOMOPARAM ); return;
  }

  static TomoparamType tab[TomoparamTypeMax][TomoparamTypeMax] = {
    { TomoparamUndef, TomoparamUint,    TomoparamSint,    TomoparamReal,    TomoparamBool,    TomoparamStr     },
    { TomoparamUint,  TomoparamUint,    TomoparamTypeMax, TomoparamReal,    TomoparamTypeMax, TomoparamTypeMax },
    { TomoparamSint,  TomoparamTypeMax, TomoparamSint,    TomoparamReal,    TomoparamTypeMax, TomoparamTypeMax },
    { TomoparamReal,  TomoparamReal,    TomoparamReal,    TomoparamReal,    TomoparamTypeMax, TomoparamTypeMax },
    { TomoparamBool,  TomoparamTypeMax, TomoparamTypeMax, TomoparamTypeMax, TomoparamBool,    TomoparamTypeMax },
    { TomoparamStr,   TomoparamTypeMax, TomoparamTypeMax, TomoparamTypeMax, TomoparamTypeMax, TomoparamStr     }
  };
  if ( tab[stk->type][var->type] == TomoparamTypeMax ) {
    ParseError( tomoparam->parse, &var->loc, E_TOMOPARAM_TYPE );
  } else {
    stk->type = tab[stk->type][var->type];
  }

  if ( stk->dim == SizeMax ) {
    stk->dim = var->dim;
  } else if ( stk->dim != var->dim ) {
    ParseError( tomoparam->parse, &var->loc, E_TOMOPARAM_DIM );
  }

  ele[tomoparam->elelen++] = *var;

}


extern TomoparamVar TomoparamUnOp
                    (Tomoparam *tomoparam,
                     const ParseSymb *op,
                     TomoparamVar *src)

{
  Status status;

  if ( TomoparamCheckArg( tomoparam == NULL ) ) return TomoparamVarInitializer;
  if ( TomoparamCheckArg( op  == NULL ) ) return TomoparamVarInitializer;
  if ( TomoparamCheckArg( src == NULL ) ) return TomoparamVarInitializer;

  if ( tomoparam->parse->status ) return TomoparamVarInitializer;

  TomoparamVar dst = *src;

  char oper = *op->txt;
  switch ( src->type ) {
    case TomoparamUndef: return dst;
    case TomoparamBool:  if ( oper != 'n' ) oper = 'n'; else break;
    case TomoparamUint:
    case TomoparamSint:
    case TomoparamReal: if ( oper != 'n' ) break;
    default: status = exception( E_TOMOPARAM_OPER ); goto error1;
  }

  switch ( *op->txt ) {

    case '+': break;

    case '-': {

      if ( src->type == TomoparamUint ) dst.type = TomoparamSint;
      if ( src->dim == 0 ) {
        UOP( dst.val, dst.type, - , src->val, src->type );
      } else {
        TomoparamVal *d, *s = TomoparamGetVal( *src );
        if ( src->tmpval ) {
          d = s;
        } else {
          d = TomoparamTmpAlloc( tomoparam, src->count, &dst.val );
          if ( d == NULL ) goto error2;
          dst.tmpval = True;
        }
        for ( Size i = 0; i < src->count; i++ ) {
          UOP( d[i], dst.type, - , s[i], src->type );
        }
      }
      break;

    }

    case 't': {

      if ( src->dim != 2 ) {
        status = exception( E_TOMOPARAM_DIM ); goto error1;
      }
      TomoparamVal *len = TomoparamGetLen( *src );
      Size m = len[1].uint;
      Size n = len[0].uint;
      len = TomoparamTmpAlloc( tomoparam, 2, &dst.len );
      if ( len == NULL ) goto error2;
      dst.tmplen = True;
      len[1].uint = n;
      len[0].uint = m;
      TomoparamVal *d = TomoparamTmpAlloc( tomoparam, src->count, &dst.val );
      if ( d == NULL ) goto error2;
      dst.tmpval = True;
      const TomoparamVal *s = TomoparamGetVal( *src );
      TomoparamMatTransp( m, n, s, d );
      break;

    }

    case 'i': {

      dst.type = TomoparamReal;
      if ( src->dim != 2 ) {
        status = exception( E_TOMOPARAM_DIM ); goto error1;
      }
      const TomoparamVal *len = TomoparamGetLen( *src );
      Size m = len[1].uint;
      Size n = len[0].uint;
      if ( m != n ) {
        status = exception( E_TOMOPARAM_MAT ); goto error1;
      }
      Coord *c = malloc( src->count * sizeof(Coord) );
      if ( c == NULL ) goto error2;
      TomoparamVal *d, *s = TomoparamGetVal( *src );
      for ( Size i = 0; i < src->count; i++ ) {
        c[i] = SRC( s[i], src->type );
      }
      status = MatnInv( n, c, c, NULL );
      if ( exception( status ) ) { free( c ); goto error1; }
      if ( !src->tmpval ) {
        d = TomoparamTmpAlloc( tomoparam, src->count, &dst.val );
        if ( d == NULL ) goto error2;
        dst.tmpval = True;
      } else {
        d = s;
      }
      for ( Size i = 0; i < src->count; i++ ) {
        d[i].real = c[i];
      }
      free( c );
      break;

    }

    case 'd': {

      dst.dim = 0;
      dst.count = 1;
      dst.len.uint = SizeMax;
      dst.val.uint = src->dim;
      dst.type = TomoparamUint;
      dst.loc = src->loc;
      dst.name = SizeMax;
      dst.tmplen = True;
      dst.tmpval = True;
      dst.param = False;
      break;

    }

    case 'l': {

      dst.dim = 1;
      dst.count = src->dim;
      dst.len.uint = src->dim;
      dst.val = src->len;
      dst.type = TomoparamUint;
      dst.loc = src->loc;
      dst.name = SizeMax;
      dst.tmplen = True;
      dst.tmpval = src->tmplen;
      dst.param = False;
      break;

    }

    default: {

      dst.loc = op->loc;
      status = exception( E_TOMOPARAM_OPER );
      goto error1;

    }

  }

  return dst;

  error2: status = exception( E_MALLOC );
  error1: ParseError( tomoparam->parse, &dst.loc, status );
  dst.type = TomoparamUndef;
  return dst;

}


static Status TomoparamCompatSize
              (const Tomoparam *tomoparam,
               const TomoparamVar *src1,
               const TomoparamVar *src2,
               TomoparamVar *dst)

{
  const TomoparamVar *scalar = NULL;
  const TomoparamVar *array = src1;

  dst->dim = src1->dim;
  if ( src1->dim != src2->dim ) {
    if ( !src1->dim ) {
      dst->dim = src2->dim;
      scalar = src1;
      array = src2;
    } else if ( !src2->dim ) {
      scalar = src2;
      array = src1;
    } else {
      dst->loc = src2->loc;
      return E_TOMOPARAM_DIM;
    }
  }

  if ( dst->dim == 0 ) {
    dst->count = 1;
  } else if ( dst->dim == 1 ) {
    dst->count = array->count;
    dst->len = array->len;
    dst->val = array->val;
    dst->tmplen = array->tmplen;
    dst->tmpval = array->tmpval;
    if ( scalar == NULL ) {
      if ( src1->count != src2->count ) {
        dst->loc = src2->loc;
        return E_TOMOPARAM_LEN;
      }
      array = NULL;
    }
  } else {
    dst->count = array->count;
    dst->len = array->len;
    dst->val = array->val;
    dst->tmplen = array->tmplen;
    dst->tmpval = array->tmpval;
    if ( scalar == NULL ) {
      const TomoparamVal *len1 = TomoparamGetLen( *src1 );
      const TomoparamVal *len2 = TomoparamGetLen( *src2 );
      for ( Size i = 0; i < dst->dim; i++, len1++, len2++ ) {
        if ( len1->uint != len2->uint ) {
          dst->loc = src2->loc;
          return E_TOMOPARAM_LEN;
        }
      }
      array = NULL;
    }
  }

  if ( array == NULL ) {
    if ( src1->tmpval ) {
      dst->val = src1->val;
      dst->tmpval = True;
    } else if ( src2->tmpval ) {
      dst->val = src2->val;
      dst->tmpval = True;
    }
  }

  return E_NONE;

}


static Status TomoparamCompatSizeMat
              (Tomoparam *tomoparam,
               const TomoparamVar *src1,
               const TomoparamVar *src2,
               TomoparamVar *dst)

{
  const TomoparamVar *scalar = NULL;
  const TomoparamVar *array = src1;

  dst->dim = src1->dim;
  if ( src1->dim != src2->dim ) {
    if ( !src1->dim ) {
      dst->dim = src2->dim;
      scalar = src1;
      array = src2;
    } else if ( !src2->dim ) {
      scalar = src2;
      array = src1;
    } else if ( src1->dim != 2 ) {
      dst->loc = src1->loc;
      return E_TOMOPARAM_DIM;
    } else if ( src2->dim != 1 ) {
      dst->loc = src2->loc;
      return E_TOMOPARAM_DIM;
    }
  }

  if ( dst->dim == 0 ) {
    dst->count = 1;
  } else if ( dst->dim == 1 ) {
    if ( scalar == NULL ) {
      if ( src1->count != src2->count ) goto error;
      dst->dim = 0;
      dst->count = 1;
      dst->len.uint = SizeMax;
    } else {
      dst->count = array->count;
      dst->len = array->len;
      dst->val = array->val;
      dst->tmplen = array->tmplen;
      dst->tmpval = array->tmpval;
    }
  } else if ( dst->dim == 2 ) {
    dst->count = array->count;
    dst->len = array->len;
    dst->val = array->val;
    dst->tmplen = array->tmplen;
    dst->tmpval = array->tmpval;
    if ( scalar == NULL ) {
      const TomoparamVal *s1 = TomoparamGetLen( *src1 );
      const TomoparamVal *s2 = TomoparamGetLen( *src2 );
      if ( src2->dim == 1 ) {
        if ( s1->uint != s2->uint ) goto error;
        dst->dim = 1;
        dst->count = s1->uint;
        dst->len.uint = s1->uint;
        if ( src1->tmpval ) {
          dst->val = src1->val;
          dst->tmpval = True;
        } else if ( src2->tmpval ) {
          dst->val = src2->val;
          dst->tmpval = True;
        }
      } else {
        Size s1m = s1[1].uint, s1n = s1[0].uint;
        Size s2m = s1[1].uint, s2n = s2[0].uint;
        if ( s1n != s2m ) goto error;
        TomoparamVal *dstlen = TomoparamTmpAlloc( tomoparam, 2, &dst->len );
        if ( dstlen == NULL ) {
          dst->loc = src1->loc;
          return E_MALLOC;
        }
        dst->tmplen = True;
        dstlen[1].uint = s1m;
        dstlen[0].uint = s2n;
        dst->count = s1m * s2n;
        if ( src1->tmpval && ( s1n >= s2n ) ) {
          dst->val = src1->val;
          dst->tmpval = True;
        } else if ( src2->tmpval && ( s2m >= s1m ) ) {
          dst->val = src2->val;
          dst->tmpval = True;
        } else {
          dst->tmpval = False;
        }
      }
    }
  } else {
    dst->loc = array->loc;
    return E_TOMOPARAM_DIM;
  }

  return E_NONE;

  error:
  dst->loc = src2->loc;
  return E_TOMOPARAM_LEN;

}


extern TomoparamVar TomoparamBinOp
                    (Tomoparam *tomoparam,
                     TomoparamVar *src1,
                     const ParseSymb *op,
                     TomoparamVar *src2)

{
  Status status;

  if ( TomoparamCheckArg( tomoparam == NULL ) ) return TomoparamVarInitializer;
  if ( TomoparamCheckArg( src1 == NULL ) ) return TomoparamVarInitializer;
  if ( TomoparamCheckArg( op   == NULL ) ) return TomoparamVarInitializer;
  if ( TomoparamCheckArg( src2 == NULL ) ) return TomoparamVarInitializer;

  if ( tomoparam->parse->status ) return TomoparamVarInitializer;

  TomoparamVar dst = TomoparamVarInitializer;

  TomoparamType type = TomoparamUndef;

  switch ( src1->type ) {
    case TomoparamUndef: return dst;
    case TomoparamUint:
    case TomoparamSint:
    case TomoparamReal:
    case TomoparamBool:
    case TomoparamStr:  type = src1->type; break;
    default: status = exception( E_TOMOPARAM_OPER ); dst.loc = src1->loc; goto error;
  }

  switch ( src2->type ) {
    case TomoparamUndef: return dst;
    case TomoparamReal: if ( ( type == TomoparamUint ) || ( type == TomoparamSint ) ) type = TomoparamReal;
    case TomoparamUint:
    case TomoparamSint: if ( type == TomoparamReal ) break;
    case TomoparamBool:
    case TomoparamStr:  if ( type == src2->type ) break;
    default: status = exception( E_TOMOPARAM_OPER ); dst.loc = src2->loc; goto error;
  }

  char oper = *op->txt;
  dst.type = type;

  if ( type == TomoparamStr ) {

    dst.loc = src1->loc;
    dst.len.uint = 1;

    if ( src1->dim || src2->dim ) {
      status = exception( E_TOMOPARAM_DIM ); if ( !src1->dim ) dst.loc = src2->loc; goto error;
    }

    switch ( oper ) {
      case ',': {
        const char *str = tomoparam->strlit;
        Size len = StringTableSize( str );
        if ( ( str == NULL ) || ( src1->val.index >= len ) || ( src2->val.index >= len ) ) {
          status = exception( E_TOMOPARAM ); if ( src1->val.index < len ) dst.loc = src2->loc; goto error;
        }
        Size len1 = strlen( str + src1->val.index );
        Size len2 = strlen( str + src2->val.index );
        char *cat = malloc( len1 + len2 + 1 );
        if ( cat == NULL ) {
          status = exception( E_MALLOC ); goto error;
        }
        memcpy( cat, str + src1->val.index, len1 );
        memcpy( cat + len1, str + src2->val.index, len2 );
        cat[len1+len2] = 0;
        status = StringTableInsert( &tomoparam->strlit, cat, &dst.val.index );
        if ( status == E_STRINGTABLE_EXISTS ) status = E_NONE;
        free( cat );
        if ( exception( status ) ) goto error;
        break;
      }
      default: status = exception( E_TOMOPARAM_OPERAT ); dst.loc = op->loc; goto error;
    }

  } else if ( oper == ',' ) {

    dst.count = src1->count + src2->count;
    dst.loc = src1->loc;

    if ( ( src1->dim <= 1 ) && ( src2->dim <= 1 ) ) {

      dst.dim = 1;
      dst.len.uint = dst.count;

    } else if ( src1->dim == src2->dim ) {

      dst.dim = src1->dim;

      TomoparamVal *len = TomoparamTmpAlloc( tomoparam, dst.dim, &dst.len );
      if ( len == NULL ) {
        status = exception( E_MALLOC ); goto error;
      }
      dst.tmplen = True;

      const TomoparamVal *len1 = TomoparamGetLen( *src1 );
      const TomoparamVal *len2 = TomoparamGetLen( *src2 );
      for ( Size i = 0; i < dst.dim - 1; i++, len++, len1++, len2++ ) {
        if ( len1->uint != len2->uint ) {
          status = exception( E_TOMOPARAM_LEN ); dst.loc = src2->loc; goto error;
        }
        len->uint = len1->uint;
      }
      len->uint = len1->uint + len2->uint;

    } else {

      dst.loc = src2->loc;
      status = exception( E_TOMOPARAM_DIM );
      goto error;

    }

    TomoparamVal *d = TomoparamTmpAlloc( tomoparam, dst.count, &dst.val );
    if ( d == NULL ) {
      status = exception( E_MALLOC ); goto error;
    }
    dst.tmpval = True;

    const TomoparamVal *s1 = TomoparamGetVal( *src1 );
    for ( Size i = 0; i < src1->count; i++ ) {
      *d++ = *s1++;
    }
    const TomoparamVal *s2 = TomoparamGetVal( *src2 );
    for ( Size i = 0; i < src2->count; i++ ) {
      *d++ = *s2++;
    }

  } else {

    status = TomoparamCompatSize( tomoparam, src1, src2, &dst );
    if ( exception( status ) ) goto error;

    dst.loc = src1->loc;

    if ( dst.dim == 0 ) {

      switch ( oper ) {
        case '+': BOP( dst.val, dst.type, src1->val, src1->type, + , src2->val, src2->type ); break;
        case '-': BOP( dst.val, dst.type, src1->val, src1->type, - , src2->val, src2->type ); break;
        case '*': BOP( dst.val, dst.type, src1->val, src1->type, * , src2->val, src2->type ); break;
        case '/': BOP( dst.val, dst.type, src1->val, src1->type, / , src2->val, src2->type ); break;
        default: status = exception( E_TOMOPARAM_OPERAT ); dst.loc = op->loc; goto error;
      }

    } else {

      TomoparamVal *d;
      if ( dst.tmpval ) {
        d = TomoparamGetVal( dst );
      } else {
        d = TomoparamTmpAlloc( tomoparam, dst.count, &dst.val );
        if ( d == NULL ) {
          status = exception( E_MALLOC ); goto error;
        }
        dst.tmpval = True;
      }

      const TomoparamVal *s1 = TomoparamGetVal( *src1 );
      const TomoparamVal *s2 = TomoparamGetVal( *src2 );

      for ( Size i = 0; i < dst.count; i++, d++ ) {
        switch ( oper ) {
          case '+': BOP( *d, dst.type, *s1, src1->type, + , *s2, src2->type ); break;
          case '-': BOP( *d, dst.type, *s1, src1->type, - , *s2, src2->type ); break;
          case '*': BOP( *d, dst.type, *s1, src1->type, * , *s2, src2->type ); break;
          case '/': BOP( *d, dst.type, *s1, src1->type, / , *s2, src2->type ); break;
          default: status = exception( E_TOMOPARAM_OPERAT ); dst.loc = op->loc; goto error;
        }
        if ( src1->dim ) s1++;
        if ( src2->dim ) s2++;
      }

    }

  }

  return dst;

  error:
  ParseError( tomoparam->parse, &dst.loc, status );
  dst.type = TomoparamUndef;
  dst.loc = src1->loc;
  return dst;

}


extern TomoparamVar TomoparamMulOp
                    (Tomoparam *tomoparam,
                     TomoparamVar *src1,
                     TomoparamVar *src2)

{
  Status status;

  if ( TomoparamCheckArg( tomoparam == NULL ) ) return TomoparamVarInitializer;
  if ( TomoparamCheckArg( src1 == NULL ) ) return TomoparamVarInitializer;
  if ( TomoparamCheckArg( src2 == NULL ) ) return TomoparamVarInitializer;

  if ( tomoparam->parse->status ) return TomoparamVarInitializer;

  TomoparamVar dst = TomoparamVarInitializer;

  switch ( src1->type ) {
    case TomoparamUndef: return dst;
    case TomoparamUint:
    case TomoparamSint:
    case TomoparamReal: dst.type = src1->type; break;
    case TomoparamBool:
    default: status = exception( E_TOMOPARAM_OPER ); dst.loc = src1->loc; goto error;
  }

  switch ( src2->type ) {
    case TomoparamUndef: return dst;
    case TomoparamReal: dst.type = TomoparamReal; break;
    case TomoparamUint:
    case TomoparamSint: if ( dst.type == TomoparamReal ) break;
    case TomoparamBool: if ( dst.type == src2->type ) break;
    default: status = exception( E_TOMOPARAM_OPER ); dst.loc = src2->loc; goto error;
  }

  status = TomoparamCompatSizeMat( tomoparam, src1, src2, &dst );
  if ( exception( status ) ) goto error;

  dst.loc = src1->loc;

  if ( dst.type != TomoparamUndef ) {

    if ( dst.dim == 0 ) {

      BOP( dst.val, dst.type, src1->val, src1->type, * , src2->val, src2->type );

    } else {

      TomoparamVal *d;
      if ( dst.tmpval ) {
        d = TomoparamGetVal( dst );
      } else {
        d = TomoparamTmpAlloc( tomoparam, dst.count, &dst.val );
        if ( d == NULL ) {
          status = exception( E_MALLOC ); goto error;
        }
        dst.tmpval = True;
      }

      if ( ( ( src1->dim == 2 ) && ( ( src2->dim == 2 ) || ( src2->dim == 1 ) ) ) || ( ( src1->dim == 1 ) && ( src2->dim == 1 ) ) ) {

        TomoparamMatMul( tomoparam, src1, src2, &dst );

      } else {

        const TomoparamVal *s1 = TomoparamGetVal( *src1 );
        const TomoparamVal *s2 = TomoparamGetVal( *src2 );

        for ( Size i = 0; i < dst.count; i++, d++ ) {
          BOP( *d, dst.type, *s1, src1->type, * , *s2, src2->type );
          if ( src1->dim ) s1++;
          if ( src2->dim ) s2++;
        }

      }

    }

  }

  return dst;

  error:
  ParseError( tomoparam->parse, &dst.loc, status );
  dst.type = TomoparamUndef;
  dst.loc = src1->loc;
  return dst;

}
