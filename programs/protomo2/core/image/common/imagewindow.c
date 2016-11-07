/*----------------------------------------------------------------------------*
*
*  imagewindow.c  -  image: images
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
#include "baselib.h"
#include "exception.h"


/* functions */

extern Status ImageWindow
              (const Image *src,
               const Size windim,
               const Size *winlen,
               const Index *winlow,
               Size *dstlen,
               Index *dstlow,
               ImageAttr *dstattr,
               Size *dstori,
               Size *dstsize)

{
  Index wlo, low;
  Size win, len, ori, off;
  Size size = windim ? 1 : 0;
  Status status = E_NONE;

  if ( src == NULL ) return exception( E_ARGVAL );
  if ( src->low == NULL ) return exception( E_ARGVAL );
  if ( src->len == NULL ) return exception( E_ARGVAL );

  if ( windim > src->dim ) return exception( E_IMAGE_DIM );

  ImageAttr attr = src->attr;

  for ( Size d = 0; d < windim; d++ ) {

    low = src->low[d];
    len = src->len[d];

    win = ( winlen == NULL ) ? len : winlen[d];

    if ( attr & ImageSymMask ) {

      if ( d ) {
        if ( low && ( low != -(Index)( len / 2 ) ) ) return exception( E_IMAGE_SYM );
      } else {
        if ( low ) return exception( E_IMAGE_SYM );
      }

      if ( winlow == NULL ) {
        if ( d ) {
          if ( !low ) return exception( E_IMAGE_WINDOW );
          wlo = -(Index)( win / 2 );
        } else {
          wlo = 0;
        }
      } else {
        wlo = winlow[d];
      }

      if ( wlo < low ) {
        if ( !status ) status = exception( E_IMAGE_BOUNDS );
        ori = 0;
        off = low - wlo;
        if ( off < win ) {
          win -= off;
        } else {
          win = 0;
        }
        attr &= ~( ImageSymMask | ImageNodd );
      } else {
        ori = wlo - low;
        low = wlo;
        if ( ori < len ) {
          len -= ori;
        } else {
          len = 0;
        }
        if ( d ) {
          if ( ( win > 1 ) && ( low != -(Index)( win / 2 ) ) ) {
            attr &= ~( ImageSymMask | ImageNodd );
          }
        } else {
          if ( win != src->len[d] ) {
            attr &= ~( ImageSymMask | ImageNodd );
          }
        }
      }

    } else {

      if ( winlow == NULL ) {

        if ( win / 2 > len / 2 ) {
          if ( !status ) status = exception( E_IMAGE_BOUNDS );
          ori = 0;
          off = win / 2 - len / 2;
          if ( off < win ) {
            win -= off;
          } else {
            win = 0;
          }
        } else {
          ori = len / 2 - win / 2;
          low += ori;
          if ( low < src->low[d] ) return exception( E_INTOVFL );
          len -= ori;
        }

      } else {

        if ( winlow[d] < low ) {
          if ( !status ) status = exception( E_IMAGE_BOUNDS );
          ori = 0;
          off = low - winlow[d];
          if ( off < win ) {
            win -= off;
          } else {
            win = 0;
          }
        } else {
          ori = winlow[d] - low;
          low = winlow[d];
          if ( ori < len ) {
            len -= ori;
          } else {
            len = 0;
          }
        }

      }

    }

    if ( win > len ) {
      if ( !status ) status = exception( E_IMAGE_BOUNDS );
      win = len;
      attr &= ~( ImageSymMask | ImageNodd );
    }

    if ( dstlen != NULL ) dstlen[d] = win;
    if ( dstlow != NULL ) dstlow[d] = low;
    if ( dstori != NULL ) dstori[d] = ori;

    if ( MulSize( size, win, &size ) ) return exception( E_INTOVFL );

  }

  if ( dstattr != NULL ) *dstattr = attr;

  if ( dstsize == NULL ) {
    if ( !status && !size ) {
      status = exception( E_IMAGE_ZERO );
    }
  } else {
    *dstsize = size;
  }

  return status;

}


extern Status ImageWindowCyc
              (const Image *src,
               const Size windim,
               const Size *winlen,
               const Index *winlow,
               Size *dstlen,
               Index *dstlow,
               ImageAttr *dstattr,
               Size *dstori,
               Size *dstsize)

{
  Index wlo, low;
  Size win, len, ori;
  Size size = windim ? 1 : 0;
  Status status = E_NONE;

  if ( src == NULL ) return exception( E_ARGVAL );
  if ( src->low == NULL ) return exception( E_ARGVAL );
  if ( src->len == NULL ) return exception( E_ARGVAL );

  if ( windim > src->dim ) return exception( E_IMAGE_DIM );

  ImageAttr attr = src->attr;

  for ( Size d = 0; d < windim; d++ ) {

    low = src->low[d];
    len = src->len[d];

    win = ( winlen == NULL ) ? len : winlen[d];

    if ( attr & ImageSymMask ) {

      if ( d ) {
        if ( low && ( low != -(Index)( len / 2 ) ) ) return exception( E_IMAGE_SYM );
      } else {
        if ( low ) return exception( E_IMAGE_SYM );
      }

      if ( winlow == NULL ) {
        if ( d ) {
          if ( !low ) return exception( E_IMAGE_WINDOW );
          wlo = -(Index)( win / 2 );
        } else {
          wlo = 0;
          if ( win > len ) {
            return exception( E_IMAGE_WINDOW );
          }
        }
      } else {
        wlo = winlow[d];
        if ( !d ) {
          if ( wlo < low ) {
            return exception( E_IMAGE_WINDOW );
          }
          win -= wlo - low;
          if ( win > len ) {
            return exception( E_IMAGE_WINDOW );
          }
        }
      }

      if ( wlo < low ) {
        ori = low - wlo;
        ori = len - ori % len;
        if ( ori == len ) ori = 0;
      } else {
        ori = wlo - low;
        ori = ori % len;
      }
      low = wlo;

      if ( d ) {
        if ( ( win > 1 ) && ( low != -(Index)( win / 2 ) ) ) {
          attr &= ~( ImageSymMask | ImageNodd );
        }
      } else {
        if ( win != src->len[d] ) {
          attr &= ~( ImageSymMask | ImageNodd );
        }
      }

    } else {

      if ( winlow == NULL ) {

        if ( win / 2 > len / 2 ) {
          ori = win / 2 - len / 2;
          ori = len - ori % len;
          if ( ori == len ) ori = 0;
          low -= ori;
          if ( low > src->low[d] ) return exception( E_INTOVFL );
        } else {
          ori = len / 2 - win / 2;
          low += ori;
          if ( low < src->low[d] ) return exception( E_INTOVFL );
        }

      } else {

        if ( winlow[d] < low ) {
          ori = low - winlow[d];
          ori = len - ori % len;
          if ( ori == len ) ori = 0;
        } else {
          ori = winlow[d] - low;
          ori = ori % len;
        }
        low = winlow[d];

      }

      len -= ori;

    }

    if ( dstlen != NULL ) dstlen[d] = win;
    if ( dstlow != NULL ) dstlow[d] = low;
    if ( dstori != NULL ) dstori[d] = ori;

    if ( MulSize( size, win, &size ) ) return exception( E_INTOVFL );

  }

  if ( dstattr != NULL ) *dstattr = attr;

  if ( dstsize == NULL ) {
    if ( !size ) {
      status = exception( E_IMAGE_ZERO );
    }
  } else {
    *dstsize = size;
  }

  return status;

}
