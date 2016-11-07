/*----------------------------------------------------------------------------*
*
*  fouriercenter.h  -  fourier: common routines
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

/* functions */

static void CONCAT( FourierCenterSub, TYPE )
            (Size n,
             const TYPE *src,
             Size sinc,
             TYPE *dst,
             Size dinc,
             Size count)

{

  if ( src == dst ) {

    if ( n % 2 ) {

      while ( count-- ) {

        TYPE *de = dst + ( n / 2 ) * sinc;

        TYPE *d2 = de;

        TYPE *d = dst;

        TYPE tmp = *d2;

        while ( d < de ) {
          *d2 = *d;
          d2 += sinc;
          *d = *d2;
          d += sinc;
        }

        *d2 = tmp;

        src += dinc;
        dst += dinc;

      }

    } else {

      while ( count-- ) {

        TYPE *d2 = dst + ( n / 2 ) * sinc;

        TYPE *d = dst;

        TYPE *de = d2;

        while ( d < de ) {
          TYPE t = *d;
          *d = *d2;
          *d2 = t;
          d += sinc; d2 += sinc;
        }

        src += dinc;
        dst += dinc;

      }

    }

  } else {

    while ( count-- ) {

      const TYPE *se = src + n * sinc;

      const TYPE *s2 = src + ( ( n + 1 ) / 2 ) * sinc;

      TYPE *d = dst;

      for ( const TYPE *s = s2; s < se; s += sinc, d += sinc ) {
        *d = *s;
      }

      for ( const TYPE *s = src; s < s2; s += sinc, d += sinc ) {
        *d = *s;
      }

      src += dinc;
      dst += dinc;

    }

  }

}


static void CONCAT( FourierUncenterSub, TYPE )
            (Size n,
             const TYPE *src,
             Size sinc,
             TYPE *dst,
             Size dinc,
             Size count)

{

  if ( src == dst ) {

    if ( n % 2 ) {

      while ( count-- ) {

        TYPE *d2 = dst + ( n - 1 ) * sinc;

        TYPE *d = dst + ( n / 2 ) * sinc;

        TYPE tmp = *d2;

        while ( d > dst ) {
          d -= sinc;
          *d2 = *d;
          d2 -= sinc;
          *d = *d2;
        }

        *d2 = tmp;

        src += dinc;
        dst += dinc;

      }

    } else {

      while ( count-- ) {

        TYPE *d2 = dst + ( n / 2 ) * sinc;

        TYPE *d = dst;

        TYPE *de = d2;

        while ( d < de ) {
          TYPE t = *d;
          *d = *d2;
          *d2 = t;
          d += sinc; d2 += sinc;
        }

        src += dinc;
        dst += dinc;

      }

    }

  } else {

    while ( count-- ) {

      const TYPE *se = src + n * sinc;

      const TYPE *s2 = src + ( n / 2 ) * sinc;

      TYPE *d = dst;

      for ( const TYPE *s = s2; s < se; s += sinc, d += sinc ) {
        *d = *s;
      }

      for ( const TYPE *s = src; s < s2; s += sinc, d += sinc ) {
        *d = *s;
      }

      src += dinc;
      dst += dinc;

    }

  }

}


extern void CONCAT( FourierCenterAsym, TYPE )
            (Size dim,
             const Size *n,
             const TYPE *src,
             TYPE *dst)

{

  switch ( dim ) {

    case 1: {
      CONCAT( FourierCenterSub, TYPE )( n[0], src, 1, dst, n[0], 1 );
      break;
    }

    case 2: {
      CONCAT( FourierCenterSub, TYPE )( n[0], src, 1, dst, n[0], n[1] );
      CONCAT( FourierCenterSub, TYPE )( n[1], dst, n[0], dst, 1, n[0] );
      break;
    }

    case 3: {
      CONCAT( FourierCenterSub, TYPE )( n[0], src, 1, dst, n[0], n[1] * n[2] );
      for ( Size i = 0; i < n[2]; i++ ) {
        TYPE *ptr = dst + i * n[0] * n[1];
        CONCAT( FourierCenterSub, TYPE )( n[1], ptr, n[0], ptr, 1, n[0] );
      }
      CONCAT( FourierCenterSub, TYPE )( n[2], dst, n[0] * n[1], dst, 1, n[0] * n[1] );
      break;
    }

    default: pushexception( E_FOURIER_DIM ); exit( EXIT_FAILURE );

  }

}


extern void CONCAT( FourierCenterSym, TYPE )
            (Size dim,
             const Size *n,
             const TYPE *src,
             TYPE *dst)

{
  Size n02 = n[0] / 2 + 1;


  switch ( dim ) {

    case 1: {
      if ( src != dst ) {
        memcpy( dst, src, n02 * sizeof(TYPE) );
      }
      break;
    }

    case 2: {
      CONCAT( FourierCenterSub, TYPE )( n[1], src, n02, dst, 1, n02 );
      break;
    }

    case 3: {
      for ( Size i = 0; i < n[2]; i++ ) {
        const TYPE *s = src + i * n02 * n[1];
        TYPE *d = dst + i * n02 * n[1];
        CONCAT( FourierCenterSub, TYPE )( n[1], s, n02, d, 1, n02 );
      }
      CONCAT( FourierCenterSub, TYPE )( n[2], dst, n02 * n[1], dst, 1, n02 * n[1] );
      break;
    }

    default: pushexception( E_FOURIER_DIM ); exit( EXIT_FAILURE );

  }

}


extern void CONCAT( FourierUncenterAsym, TYPE )
            (Size dim,
             const Size *n,
             const TYPE *src,
             TYPE *dst)

{

  switch ( dim ) {

    case 1: {
      CONCAT( FourierUncenterSub, TYPE )( n[0], src, 1, dst, n[0], 1 );
      break;
    }

    case 2: {
      CONCAT( FourierUncenterSub, TYPE )( n[1], src, n[0], dst, 1, n[0] );
      CONCAT( FourierUncenterSub, TYPE )( n[0], dst, 1, dst, n[0], n[1] );
      break;
    }

    case 3: {
      CONCAT( FourierUncenterSub, TYPE )( n[2], src, n[0] * n[1], dst, 1, n[0] * n[1] );
      for ( Size i = 0; i < n[2]; i++ ) {
        TYPE *ptr = dst + i * n[0] * n[1];
        CONCAT( FourierUncenterSub, TYPE )( n[1], ptr, n[0], ptr, 1, n[0] );
      }
      CONCAT( FourierUncenterSub, TYPE )( n[0], dst, 1, dst, n[0], n[1] * n[2] );
      break;
    }

    default: pushexception( E_FOURIER_DIM ); exit( EXIT_FAILURE );

  }

}


extern void CONCAT( FourierUncenterSym, TYPE )
            (Size dim,
             const Size *n,
             const TYPE *src,
             TYPE *dst)

{
  Size n02 = n[0] / 2 + 1;


  switch ( dim ) {

    case 1: {
      if ( src != dst ) {
        memcpy( dst, src, n02 * sizeof(TYPE) );
      }
      break;
    }

    case 2: {
      CONCAT( FourierUncenterSub, TYPE )( n[1], src, n02, dst, 1, n02 );
      break;
    }

    case 3: {
      CONCAT( FourierUncenterSub, TYPE )( n[2], src, n02 * n[1], dst, 1, n02 * n[1] );
      for ( Size i = 0; i < n[2]; i++ ) {
        TYPE *d = dst + i * n02 * n[1];
        CONCAT( FourierUncenterSub, TYPE )( n[1], d, n02, d, 1, n02 );
      }
      break;
    }

    default: pushexception( E_FOURIER_DIM ); exit( EXIT_FAILURE );

  }

}
