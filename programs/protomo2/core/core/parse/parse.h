/*----------------------------------------------------------------------------*
*
*  parse.h  -  core: auxiliary parser routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef parse_h_
#define parse_h_

#include "defs.h"
#include <stdio.h>

#define ParseName   "parse"
#define ParseVers   COREVERS"."COREBUILD
#define ParseCopy   CORECOPY


/* exception codes */

enum {
  E_PARSE = ParseModuleCode,
  E_PARSE_NO,  
  E_PARSE_EOF,
  E_PARSE_UNCOM,
  E_PARSE_UNSTR,
  E_PARSE_UNCHR,
  E_PARSE_CTRCHR,
  E_PARSE_SYNTAX,
  E_PARSE_MAXCODE
};


/* types */

typedef struct {
  Size line;
  Size pos;
} ParseLoc;

typedef struct {
  char *txt;
  Size len;
  ParseLoc loc;
} ParseSymb;

typedef struct {
  char *ptr;
  Size len;
  ParseLoc loc;
} ParseBuf;

typedef struct {
  FILE *handle;
  ParseBuf buf;
  ParseBuf bufp;
  ParseLoc locp;
  ParseLoc locc;
  int level;
  Status status;
} Parse;


/* constants */

#define ParseLocInitializer  (ParseLoc){ 0, 0 }

#define ParseBufInitializer  (ParseBuf){ NULL, 0, ParseLocInitializer }

#define ParseInitializer  (Parse){ NULL, ParseBufInitializer, ParseBufInitializer, ParseLocInitializer, ParseLocInitializer, 0, E_PARSE_NO }



/* prototypes */

extern Status ParseInit
              (Parse *parse,
               const char *path);

extern Status ParseFinal
              (Parse *parse);

extern Status ParseStatus
              (Parse *parse,
               int retstat);

extern void ParseReset
            (Parse *parse);

extern char *ParseGetBuf
             (const Parse *parse,
              Size line);

extern void ParseError
            (Parse *parse,
             const ParseLoc *loc,
             Status status);


#endif
