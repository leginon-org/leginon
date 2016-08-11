/*----------------------------------------------------------------------------*
*
*  factor.c  -  core: prime factors
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "baselib.h"


/* functions */

extern Size Factor
            (Size val)

{
  Size d, f, q;

  if ( val == 0 ) return 1;
  if ( val == 1 ) return 1;

  f = 2; if ( ( val % f ) == 0 ) return f;
  f = 3; if ( ( val % f ) == 0 ) return f;
  f = 5; if ( ( val % f ) == 0 ) return f;
  f = 7; if ( ( val % f ) == 0 ) return f;

  f = 11;

  do {

    if ( ( val % f ) == 0 ) return f;

    do {

      next: f += 2;

      d = 1;
      do {
        d += 2;
        q = f / d;
        if ( q * d == f ) goto next;
      } while ( d < q );

      break;

    } while ( True );

  } while ( True );

}


extern Size FactorLE
            (Size val,
             Size maxfact)

{
  Size f, v;

  while ( val > 1 ) {

    v = val;
    while ( v > 1 ) {
      f = Factor( v );
      if ( f > maxfact ) goto next;
      v /= f;
    }
    return val;

    next: val--;

  }

  return 1;

}


extern Size FactorLE2
            (Size val,
             Size maxfact)

{
  Size f, v;

  while ( val > 1 ) {

    f = Factor( val );

    if ( f == 2 ) {

      v = val / 2;
      while ( v > 1 ) {
        f = Factor( v );
        if ( f > maxfact ) goto next;
        v /= f;
      }
      return val;

    }

    next: val--;

  }

  return 1;

}


extern Size FactorGE
            (Size val,
             Size maxfact)

{
  Size f, v;

  while ( True ) {

    v = val;
    while ( v > 1 ) {
      f = Factor( v );
      if ( f > maxfact ) goto next;
      v /= f;
    }
    return val;

    next: val++;

  }

}


extern Size FactorGE2
            (Size val,
             Size maxfact)

{
  Size f, v;

  while ( True ) {

    f = Factor( val );

    if ( f == 2 ) {

      v = val / 2;
      while ( v > 1 ) {
        f = Factor( v );
        if ( f > maxfact ) goto next;
        v /= f;
      }
      return val;

    }

    next: val++;

  }

}
