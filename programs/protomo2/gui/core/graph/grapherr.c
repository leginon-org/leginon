/*----------------------------------------------------------------------------*
*
*  grapherr.c  -  graph: opengl graphics
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "graph.h"
#include "exception.h"


/* functions */

extern Status GraphError()

{

  switch ( glGetError() ) {
    case GL_NO_ERROR:          return E_NONE;
    case GL_INVALID_ENUM:      return E_GRAPH_ENUM;
    case GL_INVALID_VALUE:     return E_GRAPH_VAL;
    case GL_INVALID_OPERATION: return E_GRAPH_OP;
    case GL_STACK_OVERFLOW:    return E_GRAPH_OVFL;
    case GL_STACK_UNDERFLOW:   return E_GRAPH_UNFL;
    case GL_OUT_OF_MEMORY:     return E_GRAPH_MEM;
    case GL_TABLE_TOO_LARGE:   return E_GRAPH_TAB;
  }
  return E_GRAPH_NOMSG;

}


extern void GraphErrorClear()

{

  glGetError();

}
