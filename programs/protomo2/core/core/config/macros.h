/*----------------------------------------------------------------------------*
*
*  macros.h  -  common macros
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef macros_h_
#define macros_h_


/* minimum and maximum */

#define MIN( a, b )  ( ( (a) < (b) ) ? (a) : (b) )
#define MAX( a, b )  ( ( (a) > (b) ) ? (a) : (b) )

/* overflow test */

#define OFFSETADDOVFL( a, b )                            \
  (                                                      \
    (                                                    \
      ( ( (a) > 0 ) && ( (b) > ( OffsetMax - (a) ) ) )   \
      ||                                                 \
      ( ( (a) < 0 ) && ( (b) < ( OffsetMin - (a) ) ) )   \
    ) ? True : False                                     \
  )

/* stringification */

#define STRING( s )  STRINGX( s )
#define STRINGX( s ) #s

/* concatenation */

#define CONCAT( s, t )  CONCATX( s, t )
#define CONCATX( s, t ) s##t


#endif
