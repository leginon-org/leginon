/*----------------------------------------------------------------------------*
*
*  graph.c  -  graph: opengl graphics
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


/* variables */

Bool GraphLog = False;


/* functions */

extern GLenum GraphDataFormat
              (Type type)

{

  switch ( type ) {
    case TypeRGB: return GL_RGB;
    case TypeUint8:
    case TypeUint16:
    case TypeUint32:
    case TypeInt8:
    case TypeInt16:
    case TypeInt32:
    case TypeReal32:
    case TypeReal64:
    case TypeImag32:
    case TypeImag64:
    case TypeCmplx32:
    case TypeCmplx64: return GL_LUMINANCE;
    default: break;
  }

  return 0;

}


extern GLenum GraphDataType
              (Type type)

{

  switch ( type ) {
    case TypeRGB:
    case TypeUint8:   return GL_UNSIGNED_BYTE;
    case TypeUint16:  return GL_UNSIGNED_SHORT;
    case TypeUint32:  return GL_UNSIGNED_INT;
    case TypeInt8:    return GL_BYTE;
    case TypeInt16:   return GL_SHORT;
    case TypeInt32:   return GL_INT;
    case TypeReal32:  return GL_FLOAT;
    case TypeReal64:  return GL_DOUBLE;
    case TypeImag32:  return GL_FLOAT;
    case TypeImag64:  return GL_DOUBLE;
    case TypeCmplx32: return GL_FLOAT;
    case TypeCmplx64: return GL_DOUBLE;
    default: break;
  }

  return 0;

}


extern GLuint GraphDataLen
              (Type type)

{

  switch ( type ) {
    case TypeRGB: return 3;
    case TypeUint8:
    case TypeUint16:
    case TypeUint32:
    case TypeInt8:
    case TypeInt16:
    case TypeInt32:
    case TypeReal32:
    case TypeReal64:
    case TypeImag32:
    case TypeImag64: return 1;
    case TypeCmplx32:
    case TypeCmplx64: return 2;
    default: break;
  }

  return 0;

}
