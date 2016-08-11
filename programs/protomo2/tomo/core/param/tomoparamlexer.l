/*----------------------------------------------------------------------------*
*
*  tomoparamlexer.l  -  tomography: parameter files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

%top{

#include "tomoparamcommon.h"
#include "tomoparamparser.tab.h"
#include "exception.h"
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


/* macros */

#define PARSE        tomoparam->parse

#define BUFRESET     if ( PARSE->buf.ptr  != NULL ) free( PARSE->buf.ptr );    \
                     if ( PARSE->bufp.ptr != NULL ) free( PARSE->bufp.ptr );   \
                     PARSE->buf = PARSE->bufp = ParseBufInitializer;           \


#define BUFSWITCH    if ( PARSE->buf.ptr != NULL ) {                           \
                       if ( PARSE->bufp.ptr != NULL ) free( PARSE->bufp.ptr ); \
                       PARSE->bufp = PARSE->buf;                               \
                       PARSE->buf.ptr = NULL;                                  \
                     }                                                         \
                     PARSE->buf.len = 0;                                       \
                     PARSE->buf.loc.line++;                                    \
                     PARSE->buf.loc.pos = 1;                                   \

#define BUFINC       PARSE->buf.loc.pos += PARSE->buf.len;                     \
                     PARSE->buf.len = yyleng;                                  \

#define BUFNEW       BUFINC;                                                   \
                     PARSE->locp.line = PARSE->buf.loc.line;                   \
                     PARSE->locp.pos = PARSE->buf.loc.pos + PARSE->buf.len;    \

#define TOKEN(tok)   BUFNEW;                                                   \
                     lvalp->symb.txt = yytext;                                 \
                     lvalp->symb.len = yyleng;                                 \
                     lvalp->symb.loc = PARSE->buf.loc;                         \
                     return tok;                                               \

#define YY_DECL extern int tomoparam_yylex( YYSTYPE *lvalp, Tomoparam *tomoparam )
YY_DECL;


/* variables */

extern int tomoparam_yydebug;

}


%option prefix="tomoparam_yy"

%option nounput

%option noinput

%s NORMAL
%x COMMENT

IDENT    ([A-Za-z][0-9A-Za-z_]*)
UINT     ([0-9]+)
REAL     ((([0-9]+)|([0-9]*\.[0-9]+))([Ee][-+]?[0-9]+)?)
STRING   (["][^"\n]*["]+)


%%

<INITIAL>.*              {
                           char *txt = yytext;
                           char *ptr = malloc( yyleng + 1 );
                           if ( ptr == NULL ) {
                             ParseError( PARSE, &lvalp->symb.loc, exception( E_MALLOC ) );
                             BUFRESET;
                             return EOFTOKEN;
                           }
                           PARSE->buf.ptr = ptr;
                           PARSE->buf.len = 0;
                           while ( isspace( *txt ) ) {
                             *ptr++ = *txt++;
                           }
                           if ( *txt ) {
                             while ( *txt ) {
                               *ptr++ = *txt++;
                             }
                             *ptr = 0;
                             yyless( 0 );
                             if ( PARSE->level ) {
                               BEGIN( COMMENT );
                             } else {
                               BEGIN( NORMAL );
                             }
                           } else {
                             free( PARSE->buf.ptr ); PARSE->buf.ptr = NULL;
                           }
                         }

<INITIAL,COMMENT>\n      { BUFSWITCH; }

<NORMAL,COMMENT>"(*"     { BUFNEW;
                           if ( !PARSE->level++ ) PARSE->locc = PARSE->buf.loc;
                           BEGIN( COMMENT );
                         }

<NORMAL,COMMENT>"*)"     {
                           PARSE->level--;
                           if ( PARSE->level > 0 ) {
                             BUFNEW;
                             BEGIN( COMMENT );
                           } else if ( PARSE->level == 0 ) {
                             PARSE->locc = ParseLocInitializer;
                             BUFNEW;
                             BEGIN( NORMAL );
                           } else {
                             ParseError( PARSE, &PARSE->buf.loc, exception( E_TOMOPARAM ) );
                             return EOFTOKEN;
                           }
                         }

<COMMENT>.               { BUFNEW; }

\n                       { BUFSWITCH; BEGIN( INITIAL ); }

[ \t\r]+                 { BUFINC; /* whitespace */ }

dim                      { TOKEN( DIM ) }
len                      { TOKEN( LEN ) }
inv                      { TOKEN( INV ) }
trn                      { TOKEN( TRN ) }

not                      { TOKEN( NOT ) }
and                      { TOKEN( AND ) }
or                       { TOKEN( OR  ) }

"<>"                     { TOKEN( NEQ ) }
"<="                     { TOKEN( LEQ ) }
">="                     { TOKEN( GEQ ) }

print                    { TOKEN( PRINT ) }

true                     { TOKEN( TRUE ) }
false                    { TOKEN( FALSE ) }

{IDENT}                  { TOKEN( IDENT ) }
{UINT}                   { TOKEN( UINTCONST ) }
{REAL}                   { TOKEN( REALCONST ) }
{STRING}                 { TOKEN( STRLITERAL ) }

[{}()+\-*/?,=:]          { TOKEN( yytext[0] ) }

[\000-\037\177]          { BUFNEW; ParseError( PARSE, &PARSE->buf.loc, E_PARSE_CTRCHR ); }

.                        { BUFNEW; ParseError( PARSE, &PARSE->buf.loc, E_PARSE_UNCHR ); }

<<EOF>>                  { PARSE->buf.loc = ParseLocInitializer;
                           lvalp->symb.loc = PARSE->locp;
                           return EOFTOKEN;
                         }


%%


int tomoparam_yywrap()

{

  return 1;

}


extern void TomoparamLexInit( Tomoparam *tomoparam )

{

  tomoparam_yy_flex_debug = 0;
#ifdef PARSEDEBUG
  if ( ParseLexDebug ) tomoparam_yy_flex_debug = 1;
#endif

  tomoparam_yyin = ( PARSE->handle == NULL ) ? stdin : PARSE->handle;

  PARSE->buf.loc.line = 1;
  PARSE->buf.loc.pos = 1;

  BEGIN( INITIAL );

}
