/*----------------------------------------------------------------------------*
*
*  imageattr.c  -  image: images
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "image.h"
#include "exception.h"


/* functions */

extern Status ImageAttrCopy
              (Type srctype,
               ImageAttr srcattr,
               Type *dsttype,
               ImageAttr *dstattr,
               ImageMode mode)

{
  Type type;
  ImageAttr attr;

  if ( ( mode & ( ImageModeSym | ImageModeFou ) ) == ( ImageModeSym | ImageModeFou ) ) {
    return exception( E_ARGVAL );
  }

  if ( srcattr & ~ImageAttrMask ) {
    return exception( E_IMAGE_ATTR );
  }

  if ( !TypeIsNumeric( srctype ) && ( srcattr & ImageAttrMask ) ) {
    return exception( E_IMAGE_ATTR );
  }

  if ( mode & ImageModeSym ) {

    type = srctype;
    attr = mode & ImageSymMask;

    if ( srcattr & ImageSymMask ) {

      if ( attr && ( attr != ( srcattr & ImageSymMask ) ) ) {
        return exception( E_IMAGE_ATTR );
      }

    } else if ( attr ) {

      if ( TypeIsReal( srctype ) ) {

        switch ( attr ) {
          case ImageSymEven: break;
          case ImageSymOdd:  break;
          case ImageSymHerm: attr = ImageSymEven; break;
          default: return exception( E_IMAGE_ATTR );
        }

      } else if ( TypeIsImag( srctype ) ) {

        switch ( attr ) {
          case ImageSymEven:  break;
          case ImageSymOdd:   break;
          case ImageSymAHerm: attr = ImageSymOdd; break;
          default: return exception( E_IMAGE_ATTR );
        }

      } else if ( TypeIsCmplx( srctype ) ) {

        switch ( attr ) {
          case ImageSymEven:
          case ImageSymOdd:
          case ImageSymHerm:
          case ImageSymAHerm: break;
          default: return exception( E_IMAGE_ATTR );
        }

      }

    }

    if ( dsttype != NULL ) *dsttype = type;
    if ( dstattr != NULL ) *dstattr = attr | ( srcattr & ImageFourspc );

  } else if ( mode & ImageModeFou ) {

    if ( TypeIsReal( srctype ) ) {

      switch ( srcattr & ImageSymMask ) {
        case ImageAsym:    type = TypeCmplx; attr = ImageSymHerm; break;
        case ImageSymEven: type = TypeReal;  attr = ImageSymEven; break;
        case ImageSymOdd:  type = TypeImag;  attr = ImageSymOdd;  break;
        default: return exception( E_IMAGE_ATTR );
      }

    } else if ( TypeIsImag( srctype ) ) {

      switch ( srcattr & ImageSymMask ) {
        case ImageAsym:    type = TypeCmplx; attr = ImageSymAHerm; break;
        case ImageSymEven: type = TypeImag;  attr = ImageSymEven;  break;
        case ImageSymOdd:  type = TypeReal;  attr = ImageSymOdd;   break;
        default: return exception( E_IMAGE_ATTR );
      }

    } else if ( TypeIsCmplx( srctype ) ) {

      switch ( srcattr & ImageSymMask ) {
        case ImageAsym:     type = TypeCmplx; attr = ImageAsym;    break;
        case ImageSymEven:  type = TypeCmplx; attr = ImageSymEven; break;
        case ImageSymOdd:   type = TypeCmplx; attr = ImageSymOdd;  break;
        case ImageSymHerm:  type = TypeReal;  attr = ImageAsym;    break;
        case ImageSymAHerm: type = TypeImag;  attr = ImageAsym;    break;
        default: return exception( E_IMAGE_ATTR );
      }

    } else {

      return exception( E_IMAGE_TYPE );

    }

    srcattr ^= ImageFourspc;
    if ( dsttype != NULL ) *dsttype = type;
    if ( dstattr != NULL ) *dstattr = attr | ( srcattr & ImageFourspc );

  } else {

    if ( dsttype != NULL ) *dsttype = srctype;
    if ( dstattr != NULL ) *dstattr = srcattr;

  }

  return E_NONE;

}
