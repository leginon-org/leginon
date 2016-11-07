/*----------------------------------------------------------------------------*
*
*  tomoparamparser.y  -  tomography: parameter files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

%{

#include "tomoparamsemant.h"
#include "stringparse.h"
#include "exception.h"

%}


%file-prefix="tomoparamparser"

%name-prefix="tomoparam_yy"

%pure-parser

%parse-param { Tomoparam *tomoparam }

%lex-param { Tomoparam *tomoparam }

%union {
  ParseSymb symb;
  TomoparamScalar scalar;
  TomoparamVar var;
}

%initial-action {

  tomoparam_yydebug = 0;
#ifdef PARSEDEBUG
  if ( ParseDebug ) tomoparam_yydebug = 1;
#endif
  TomoparamLexInit( tomoparam );
  if ( ( tomoparam->prfx != NULL ) && *tomoparam->prfx ) {
    tomoparam->parse->status = TomoparamInsertString( tomoparam, "PREFIX", tomoparam->prfx );
    pushexception( tomoparam->parse->status );
  }

}


%{

extern int tomoparam_yylex( YYSTYPE *lvalp, Tomoparam *tomoparam );

static void tomoparam_yyerror( Tomoparam *tomoparam, char *msg );

%}


%token <symb> DIM
%token <symb> LEN
%token <symb> INV
%token <symb> TRN

%token <symb> NOT
%token <symb> AND
%token <symb> OR

%token <symb> NEQ
%token <symb> LEQ
%token <symb> GEQ

%token <symb> PRINT

%token <symb> TRUE
%token <symb> FALSE

%token <symb> IDENT
%token <symb> REALCONST
%token <symb> UINTCONST
%token <symb> STRLITERAL

%token <symb> EOFTOKEN

%token <symb> '{' '}'
%token <symb> '(' ')'
%token <symb> '+' '-'
%token <symb> '*' '/'
%token <symb> '<' '>'
%token <symb> '?'
%token <symb> ','
%token <symb> '='
%token <symb> ':'

%type <var>    arrayconstant
%type <scalar> constant
%type <var>    elementlist
%type <var>    statement
%type <var>    expression
%type <var>    mulexpression
%type <var>    unaryexpression
%type <var>    primaryexpression


%%


start:               EOFTOKEN                            { YYACCEPT; }
                   | unitlist EOFTOKEN                   { if ( tomoparam->parse->status ) YYABORT;
                                                           YYACCEPT;
                                                         }
                   ;

unitlist:            unit                                { }
                   | unitlist unit                       { }
                   ;

unit:                section                             { }
                   | parameter                           { }
                   | assignment                          { }
                   | statement                           { }
                   ;

section:             IDENT '{'                           { TomoparamPushSection( tomoparam, &$1, &$2 ); }
                           '}'                           { TomoparamPopSection( tomoparam, &$2 ); }
                   | IDENT '{'                           { TomoparamPushSection( tomoparam, &$1, &$2 ); }
                     unitlist '}'                        { TomoparamPopSection( tomoparam, &$2 ); }
                   ;

parameter:           IDENT ':'                           { TomoparamPushStk( tomoparam, &$2 ); }
                     expression                          { TomoparamSetVar( tomoparam, &$1, &$2, &$4 );
                                                           TomoparamPopStk( tomoparam, &$2 ); }
                   ;

assignment:          IDENT '='                           { TomoparamPushStk( tomoparam, &$2 ); }
                     expression                          { TomoparamSetVar( tomoparam, &$1, &$2, &$4 );
                                                           TomoparamPopStk( tomoparam, &$2 ); }
                   ;

statement:           PRINT IDENT                         { $$ = TomoparamGetVar( tomoparam, &$2 );
                                                           Status status = TomoparamPrintVar( tomoparam, &$$, NULL, NULL );
                                                           if ( exception( status ) ) {
                                                             ParseError( tomoparam->parse, &$1.loc, status );
                                                           }
                                                         }
                   ;

expression:          mulexpression                       { $$ = $1; }
                   | expression '+' mulexpression        { $$ = TomoparamBinOp( tomoparam, &$1, &$2, &$3 ); }
                   | expression '-' mulexpression        { $$ = TomoparamBinOp( tomoparam, &$1, &$2, &$3 ); }
                   ;

mulexpression:       unaryexpression                     { $$ = $1; }
                   | mulexpression '*' unaryexpression   { $$ = TomoparamMulOp( tomoparam, &$1, &$3 ); }
                   | mulexpression '/' unaryexpression   { if ( $1.dim && $3.dim ) {
                                                             ParseError( tomoparam->parse, &$3.loc, exception( E_TOMOPARAM_DIM ) );
                                                             $$ = $1; $$.type = TomoparamUndef;
                                                           } else {
                                                             $$ = TomoparamBinOp( tomoparam, &$1, &$2, &$3 );
                                                           }
                                                         }
                   ;

unaryexpression:     primaryexpression                   { $$ = $1; }
                   | '+' unaryexpression                 { $$ = TomoparamUnOp( tomoparam, &$1, &$2 ); }
                   | '-' unaryexpression                 { $$ = TomoparamUnOp( tomoparam, &$1, &$2 ); }
                   | TRN unaryexpression                 { $$ = TomoparamUnOp( tomoparam, &$1, &$2 ); }
                   | INV unaryexpression                 { $$ = TomoparamUnOp( tomoparam, &$1, &$2 ); }
                   | DIM unaryexpression                 { $$ = TomoparamUnOp( tomoparam, &$1, &$2 ); }
                   | LEN unaryexpression                 { $$ = TomoparamUnOp( tomoparam, &$1, &$2 ); }
                   ;

primaryexpression:   IDENT                               { $$ = TomoparamGetVar( tomoparam, &$1 ); }
                   | constant                            { $$ = TomoparamVarInitializer; $$.dim = 0; $$.count = 1; $$.len.uint = 1; $$.val = $1.val; $$.type = $1.type; $$.loc = $1.loc; }
                   | arrayconstant                       { $$ = $1; }
                   | '(' expression ')'                  { $$ = $2; $$.loc = $1.loc; }
                   ;

constant:            FALSE                               { $$.type = TomoparamBool; $$.val.bool = False; $$.loc = $1.loc; }
                   | TRUE                                { $$.type = TomoparamBool; $$.val.bool = True;  $$.loc = $1.loc; }

                   | UINTCONST                           { $$.type = TomoparamUint; $$.loc = $1.loc; Index val;
                                                           if ( StringParseIndex( $1.txt, NULL, &val, NULL ) ) {
                                                             ParseError( tomoparam->parse, &$1.loc, E_TOMOPARAM_UINT );
                                                           }
                                                           $$.val.uint = val;
                                                         }

                   | REALCONST                           { $$.type = TomoparamReal; $$.loc = $1.loc;
                                                           if ( StringParseCoord( $1.txt, NULL, &$$.val.real, NULL ) ) {
                                                             ParseError( tomoparam->parse, &$1.loc, E_TOMOPARAM_REAL );
                                                           }
                                                         }

                   | STRLITERAL                          { $$.type = TomoparamStr; $$.loc = $1.loc;
                                                           char *txt = $1.txt;
                                                           if ( ( $1.len <= 1 ) || ( txt[$1.len-1] != '"' ) ) {
                                                             ParseError( tomoparam->parse, &$1.loc, E_PARSE_UNSTR );
                                                           } else {
                                                             if ( $1.len ) txt[$1.len-1] = 0;
                                                           }
                                                           if ( $1.len > 1 ) txt++;
                                                           Status status = StringTableInsert( &tomoparam->strlit, txt, &$$.val.index );
                                                           if ( status && ( status != E_STRINGTABLE_EXISTS ) ) {
                                                             ParseError( tomoparam->parse, &$1.loc, E_TOMOPARAM );
                                                           }
                                                         }
                   ;

arrayconstant:       '{'                                 { TomoparamPushStk( tomoparam, &$1 ); }
                     elementlist '}'                     { $$ = TomoparamGetArray( tomoparam, &$1 );
                                                           TomoparamPopStk( tomoparam, &$4 ); }
                   ;

elementlist:         expression                          { TomoparamElement( tomoparam, &$1 ); }
                   | elementlist ',' expression          { TomoparamElement( tomoparam, &$3 ); }
                   ;

%%


static void tomoparam_yyerror
            (Tomoparam *tomoparam,
             char *msg)

{
  Parse *parse = tomoparam->parse;
  ParseLoc *loc = &parse->buf.loc;

  if ( loc->line ) {

    ParseError( parse, loc, E_PARSE_SYNTAX );

  } else {

    ParseBuf buf = parse->buf;

    if ( tomoparam->savlen ) {
      parse->buf = tomoparam->sav[tomoparam->savlen-1];
      ParseError( parse, loc, E_TOMOPARAM_OPSEC );
    }

    parse->buf = buf;

  }

}
