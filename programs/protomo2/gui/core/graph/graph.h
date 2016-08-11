/*----------------------------------------------------------------------------*
*
*  graph.h  -  graph: opengl graphics
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef graph_h_
#define graph_h_

#include "guidefs.h"
#include <GL/gl.h>

#define GraphName   "graph"
#define GraphVers   GUIVERS"."GUIBUILD
#define GraphCopy   GUICOPY


/* exception codes */

enum {
  E_GRAPH = GraphModuleCode,
  E_GRAPH_ENUM,
  E_GRAPH_VAL,
  E_GRAPH_OP,
  E_GRAPH_OVFL,
  E_GRAPH_UNFL,
  E_GRAPH_MEM,
  E_GRAPH_TAB,
  E_GRAPH_NOMSG,
  E_GRAPH_VERS,
  E_GRAPH_MAXCODE
};


/* variables */

extern Bool GraphLog;


/* prototypes */

extern Status GraphError();

extern void GraphErrorClear();

extern Status GraphGetVersion
              (Size *major,
               Size *minor);

extern GLenum GraphDataFormat
              (Type type);

extern GLenum GraphDataType
              (Type type);

extern GLuint GraphDataLen
              (Type type);


#endif
