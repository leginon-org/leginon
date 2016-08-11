/*----------------------------------------------------------------------------*
*
*  tomotiltparser.y  -  tomography: tilt series
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

#include "tomotiltsemant.h"
#include "exception.h"

%}

%file-prefix="tomotiltparser"

%name-prefix="tomotilt_yy"

%pure-parser

%parse-param { TomotiltParse *tiltparse }

%lex-param { TomotiltParse *tiltparse }

%union {
  ParseSymb symb;
  Size uinteger;
  Index integer;
  Coord real;
  Coord realvec[3];
}

%initial-action {

  TomotiltLexInit( tiltparse );
  tomotilt_yydebug = 0;
#ifdef PARSEDEBUG
  if ( ParseDebug ) tomotilt_yydebug = 1;
#endif

}


%{

extern int tomotilt_yylex( YYSTYPE *lvalp, TomotiltParse *tiltparse );

static void tomotilt_yyerror( TomotiltParse *tiltparse, char *msg );

%}


%token <symb> ABERRATION
%token <symb> AMPLITUDE
%token <symb> ANGLE
%token <symb> ASTIGMATISM
%token <symb> AXIS
%token <symb> AZIMUTH
%token <symb> CONTRAST
%token <symb> CORRECTION
%token <symb> DEFOCUS
%token <symb> DIVERGENCE
%token <symb> ELEVATION
%token <symb> ENDTOKEN
%token <symb> EOFTOKEN
%token <symb> FILENAME
%token <symb> FOCUS
%token <symb> HIGH
%token <symb> IDENT
%token <symb> ILLUMINATION
%token <symb> IMAGE
%token <symb> INTCONST
%token <symb> KILOVOLT
%token <symb> MILLIMETER
%token <symb> MILLIRAD
%token <symb> NANOMETER
%token <symb> OFFSET
%token <symb> ORIENTATION
%token <symb> ORIGIN
%token <symb> PARAMETER
%token <symb> PHI
%token <symb> PIXEL
%token <symb> PSI
%token <symb> REALCONST
%token <symb> REFERENCE
%token <symb> ROTATION
%token <symb> SCALE
%token <symb> SERIES
%token <symb> SIZE
%token <symb> SPHERICAL
%token <symb> SPREAD
%token <symb> TENSION
%token <symb> THETA
%token <symb> TILT
%token <symb> VOLT
%token <symb> WAVELENGTH
%token <symb> '['
%token <symb> ']'

%type <uinteger> uintconst
%type <integer>  intconst
%type <integer>  fileoffs
%type <real>     arc
%type <real>     arcunit
%type <real>     length
%type <real>     lengthunit
%type <realvec>  real2
%type <realvec>  real3
%type <real>     realconst
%type <real>     tension
%type <real>     tensionunit


%%


start:               TILT SERIES IDENT                 { if ( TomotiltParseInit( tiltparse, $3.txt ) ) YYABORT; }
                     paramlist
                     sectionlist
                     ENDTOKEN                          { TomotiltParseEnd( tiltparse, &$1 ); }
                     EOFTOKEN                          { if ( TomotiltParseCommit( tiltparse ) ) YYABORT;
                                                         YYACCEPT;
                                                       }
                   ;

paramlist:           /* empty */                       { }
                   | paramlist PARAMETER paramdef      { }
                   ;

paramdef:            param                             { }
                   | paramdef param                    { }
                   ;

param:               PSI realconst                     { TomotiltParseStoreParam( tiltparse, FIELD_PSI0,   &$1, &$2 ); }
                   | THETA realconst                   { TomotiltParseStoreParam( tiltparse, FIELD_THE0,   &$1, &$2 ); }
                   | PHI realconst                     { TomotiltParseStoreParam( tiltparse, FIELD_PHI0,   &$1, &$2 ); }
                   | ORIGIN '[' real3 ']'              { TomotiltParseStoreParam( tiltparse, FIELD_ORI0,   &$1,  $3 ); }
                   | SPHERICAL ABERRATION length       { TomotiltParseStoreParam( tiltparse, FIELD_CS,     &$1, &$3 ); }
                   | HIGH TENSION tension              { TomotiltParseStoreParam( tiltparse, FIELD_HT,     &$1, &$3 ); }
                   | WAVELENGTH length                 { TomotiltParseStoreParam( tiltparse, FIELD_LAMBDA, &$1, &$2 ); }
                   | ILLUMINATION DIVERGENCE arc       { TomotiltParseStoreParam( tiltparse, FIELD_BETA,   &$1, &$3 ); }
                   | FOCUS SPREAD length               { TomotiltParseStoreParam( tiltparse, FIELD_FS,     &$1, &$3 ); }
                   | PIXEL SIZE length                 { TomotiltParseStoreParam( tiltparse, FIELD_PIXEL0, &$1, &$3 ); }
                   ;

sectionlist:         section                           { }
                   | sectionlist section               { }
                   ;

section:             axislist orientsectionlist        { }
                   | axislist imagesectionlist         { }
                   ;

axislist:            AXIS axisdef                      { }
                   | axislist AXIS axisdef             { }
                   ;

axisdef:             axis                              { }
                   | axisdef axis                      { }
                   ;

axis:                TILT AZIMUTH realconst            { TomotiltParseStoreAxis( tiltparse, FIELD_AZIM, &$1, $3 ); }
                   | TILT ELEVATION realconst          { TomotiltParseStoreAxis( tiltparse, FIELD_ELEV, &$1, $3 ); }
                   | TILT OFFSET realconst             { TomotiltParseStoreAxis( tiltparse, FIELD_OFFS, &$1, $3 ); }
                   ;

orientsectionlist:   orientsection                     { }
                   | orientsectionlist orientsection   { }
                   ;

orientsection:       orientlist imagelist              { }
                   ;

orientlist:          ORIENTATION orientdef             { }
                   | orientlist ORIENTATION orientdef  { }
                   ;

orientdef:           orient                            { }
                   | orientdef orient                  { }
                   ;

orient:              PSI realconst                     { TomotiltParseStoreOrient( tiltparse, FIELD_PSI, &$1, $2 ); }
                   | THETA realconst                   { TomotiltParseStoreOrient( tiltparse, FIELD_THE, &$1, $2 ); }
                   | PHI realconst                     { TomotiltParseStoreOrient( tiltparse, FIELD_PHI, &$1, $2 ); }
                   ;

imagesectionlist:    imagelist                         { }
                   | imagelist orientsectionlist       { }
                   ;

imagelist:           image                             { }
                   | imagelist image                   { }
                   ;

image:               IMAGE uintconst                   { TomotiltParseImage( tiltparse, &$1, $2 ); }
                     imageparamdef                     { }
                   ;

imageparamdef:       /* empty */                       { }
                   | imageparamdef imageparam          { }
                   ;

imageparam:          FILENAME IDENT                    { TomotiltParseStoreFile( tiltparse, &$1, &$2 ); }
                     fileoffs                          { TomotiltParseStoreFileOffs( tiltparse, &$1, $4 ); }
                   | TILT ANGLE realconst              { TomotiltParseStoreImage( tiltparse, FIELD_THETA, &$1, &$3, NULL ); }
                   | ROTATION realconst                { TomotiltParseStoreImage( tiltparse, FIELD_ALPHA, &$1, &$2, NULL ); }
                   | CORRECTION real3                  { TomotiltParseStoreImage( tiltparse, FIELD_CORR,  &$1,  $2, NULL ); }
                   | SCALE realconst                   { TomotiltParseStoreImage( tiltparse, FIELD_SCALE, &$1, &$2, NULL ); }
                   | ORIGIN '[' real2 ']'              { TomotiltParseStoreImage( tiltparse, FIELD_ORIG,  &$1,  $3, NULL ); }
                   | PIXEL SIZE length                 { TomotiltParseStoreImage( tiltparse, FIELD_PIXEL, &$1, &$3, NULL ); }
                   | DEFOCUS length '[' real2 ']'      { TomotiltParseStoreImage( tiltparse, FIELD_DEFOC, &$1, &$2, $4   ); }
                   | ASTIGMATISM real2                 { TomotiltParseStoreImage( tiltparse, FIELD_ASTIG, &$1,  $2, NULL ); }
                   | AMPLITUDE CONTRAST realconst      { TomotiltParseStoreImage( tiltparse, FIELD_AMPCO, &$1, &$3, NULL ); }
                   | REFERENCE IMAGE uintconst         { TomotiltParseImage( tiltparse, &$1, $3 );
                                                         TomotiltParseStoreImage( tiltparse, FIELD_REF, &$1, NULL, NULL ); }
                   ;

fileoffs:            /* empty */                       { $$ = IndexMax; }
                   | '[' intconst ']'                  { $$ = $2; }
                   ;

arc:                 realconst arcunit                 { $$ = $1 * $2; }
                   ;

arcunit:             MILLIRAD                          { $$ = 1e-3; }
                   ;

length:              realconst lengthunit              { $$ = $1 * $2; }
                   ;

lengthunit:          MILLIMETER                        { $$ = 1e-3; }
                   | NANOMETER                         { $$ = 1e-9; }
                   ;

tension:             realconst tensionunit             { $$ = $1 * $2; }
                   ;

tensionunit:         VOLT                              { $$ = 1e+0; }
                   | KILOVOLT                          { $$ = 1e+3; }
                   ;

real2:               realconst
                     realconst                         { $$[0] = $1; $$[1] = $2; $$[2] = 0; }
                   ;

real3:               realconst
                     realconst
                     realconst                         { $$[0] = $1; $$[1] = $2; $$[2] = $3; }
                   ;

realconst:           INTCONST                          { $$ = TomotiltParseToReal( tiltparse, &$1 ); }
                   | REALCONST                         { $$ = TomotiltParseToReal( tiltparse, &$1 ); }
                   ;

uintconst:           INTCONST                          { $$ = TomotiltParseToUint( tiltparse, &$1 ); }
                   ;

intconst:            INTCONST                          { $$ = TomotiltParseToInt( tiltparse, &$1 ); }
                   ;

%%


static void tomotilt_yyerror
            (TomotiltParse *tiltparse,
             char *msg)

{
  Parse *parse = tiltparse->parse;
  ParseLoc *loc = &parse->buf.loc;

  if ( loc->line ) {
    ParseError( parse, loc, E_PARSE_SYNTAX );
  }

}
