/*----------------------------------------------------------------------------*
*
*  tomotiltlexer.l  -  tomography: tilt series
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

#include "tomotiltcommon.h"
#include "tomotiltparser.tab.h"
#include "exception.h"
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


/* macros */

#define PARSE        tiltparse->parse

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

#define YY_DECL extern int tomotilt_yylex( YYSTYPE *lvalp, TomotiltParse *tiltparse )
YY_DECL;


/* variables */

extern int tomotilt_yydebug;

}


%option prefix="tomotilt_yy"

%option nounput

%option noinput

%s NORMAL
%x COMMENT

IDENT    ([A-Za-z][-/0-9A-Za-z_.]*)
INTEGER  ([0-9]+)
REAL     (([-+]?)(([0-9]+)|([0-9]*\.[0-9]+))([Ee][-+]?[0-9]+)?)


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
                             ParseError( PARSE, &PARSE->buf.loc, exception( E_TOMOTILT ) );
                             return EOFTOKEN;
                           }
                         }

<COMMENT>.               { BUFNEW; }

\n                       { BUFSWITCH; BEGIN( INITIAL ); }

[ \t\r]+                 { BUFINC; /* whitespace */ }


ABERRATION               { TOKEN( ABERRATION ) }
AMPLITUDE                { TOKEN( AMPLITUDE ) }
ANGLE                    { TOKEN( ANGLE ) }
ASTIGMATISM              { TOKEN( ASTIGMATISM ) }
AXIS                     { TOKEN( AXIS ) }
AZIMUTH                  { TOKEN( AZIMUTH ) }
CONTRAST                 { TOKEN( CONTRAST ) }
CORRECTION               { TOKEN( CORRECTION ) }
DEFOCUS                  { TOKEN( DEFOCUS ) }
DIVERGENCE               { TOKEN( DIVERGENCE ) }
ELEVATION                { TOKEN( ELEVATION ) }
END                      { TOKEN( ENDTOKEN ) }
FILE                     { TOKEN( FILENAME ) }
FOCUS                    { TOKEN( FOCUS ) }
HIGH                     { TOKEN( HIGH ) }
ILLUMINATION             { TOKEN( ILLUMINATION ) }
IMAGE                    { TOKEN( IMAGE ) }
OFFSET                   { TOKEN( OFFSET ) }
ORIENTATION              { TOKEN( ORIENTATION ) }
ORIGIN                   { TOKEN( ORIGIN ) }
PARAMETER                { TOKEN( PARAMETER ) }
PHI                      { TOKEN( PHI ) }
PIXEL                    { TOKEN( PIXEL ) }
PSI                      { TOKEN( PSI ) }
REFERENCE                { TOKEN( REFERENCE ) }
ROTATION                 { TOKEN( ROTATION ) }
SCALE                    { TOKEN( SCALE ) }
SERIES                   { TOKEN( SERIES ) }
SIZE                     { TOKEN( SIZE ) }
SPHERICAL                { TOKEN( SPHERICAL ) }
SPREAD                   { TOKEN( SPREAD ) }
TENSION                  { TOKEN( TENSION ) }
THETA                    { TOKEN( THETA ) }
TILT                     { TOKEN( TILT ) }
WAVELENGTH               { TOKEN( WAVELENGTH ) }
mrad                     { TOKEN( MILLIRAD ) }
mm                       { TOKEN( MILLIMETER ) }
nm                       { TOKEN( NANOMETER ) }
V                        { TOKEN( VOLT ) }
kV                       { TOKEN( KILOVOLT ) }

{IDENT}                  { TOKEN( IDENT ) }

{INTEGER}                { TOKEN( INTCONST ) }

{REAL}                   { TOKEN( REALCONST ) }

[\[\]]                   { TOKEN( yytext[0] ) }

[\000-\037\177]          { BUFNEW; ParseError( PARSE, &PARSE->buf.loc, E_PARSE_CTRCHR ); }

.                        { BUFNEW; ParseError( PARSE, &PARSE->buf.loc, E_PARSE_SYNTAX ); }

<<EOF>>                  { PARSE->buf.loc = ParseLocInitializer;
                           lvalp->symb.loc = PARSE->locp;
                           return EOFTOKEN;
                         }


%%


int tomotilt_yywrap()

{

  return 1;

}


extern void TomotiltLexInit( TomotiltParse *tiltparse )

{

  tomotilt_yy_flex_debug = 0;
#ifdef PARSEDEBUG
  if ( ParseLexDebug ) tomotilt_yy_flex_debug = 1;
#endif

  tomotilt_yyin = ( PARSE->handle == NULL ) ? stdin : PARSE->handle;

  PARSE->buf.loc.line = 1;
  PARSE->buf.loc.pos = 1;

  BEGIN( INITIAL );

}
