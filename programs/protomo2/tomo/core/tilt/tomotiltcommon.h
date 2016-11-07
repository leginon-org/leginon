/*----------------------------------------------------------------------------*
*
*  tomotiltcommon.h  -  tomography: tilt series
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef tomotiltcommon_h_
#define tomotiltcommon_h_

#include "tomotilt.h"
#include "parse.h"


/* macros */

#define STATE_UNDEF   0x00
#define STATE_PARAM   0x01
#define STATE_AXIS    0x02
#define STATE_ORIENT  0x04
#define STATE_IMAGE   0x08
#define STATE_END     0x10


/* types */

typedef struct {
  Tomotilt *tomotilt;
  Size imageindex;
  Size axisindex;
  Size orientindex;
  Size state;
  Parse *parse;
} TomotiltParse;


/* constants */

#define TomotiltParseInitializer  (TomotiltParse){ NULL, TomotiltImageMax, TomotiltImageMax, TomotiltImageMax, STATE_UNDEF, NULL }


/* prototypes */

extern Status TomotiltParseInit
              (TomotiltParse *tiltparse,
               const char *ident);

extern Status TomotiltParseFinal
              (TomotiltParse *tiltparse);

extern void TomotiltLexInit
            (TomotiltParse *tiltparse);

extern int tomotilt_yyparse
           (TomotiltParse *tiltparse);


#endif
