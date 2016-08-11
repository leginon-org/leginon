/*----------------------------------------------------------------------------*
*
*  histogram.h  -  array: statistics
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef histogram_h_
#define histogram_h_

#include "statistics.h"


/* macros */

#define ihisto( type )                          \
  {                                             \
    const type *s = src, *s1 = s + count;       \
    Size lo = 0, hi = 0;                        \
    if ( n ) {                                  \
      if ( step > 0 ) {                         \
        Coord m = n;                            \
        Coord f = 1.0 / step;                   \
        while ( s < s1 ) {                      \
          Coord v = ( (*s++) - min ) * f;       \
          if ( v < 0 ) {                        \
            lo++;                               \
          } else if ( v < m ) {                 \
            Size i = v;                         \
            histo[i]++;                         \
          } else {                              \
            hi++;                               \
          }                                     \
        }                                       \
      }                                         \
    }                                           \
    if ( lower  != NULL ) *lower  += lo;        \
    if ( higher != NULL ) *higher += hi;        \
  }                                             \


#define fhisto( type )                          \
  {                                             \
    const type *s = src, *s1 = s + count;       \
    Size lo = 0, hi = 0;                        \
    if ( n ) {                                  \
      if ( step > 0 ) {                         \
        Coord m = n;                            \
        Coord f = 1.0 / step;                   \
        while ( s < s1 ) {                      \
          Coord v = ( (*s++) - min ) * f;       \
          if ( v < 0 ) {                        \
            lo++;                               \
          } else if ( v < m ) {                 \
            Size i = v;                         \
            histo[i]++;                         \
          } else if ( v == m ) {                \
            histo[n-1]++;                       \
          } else {                              \
            hi++;                               \
          }                                     \
        }                                       \
      }                                         \
    }                                           \
    if ( lower  != NULL ) *lower  += lo;        \
    if ( higher != NULL ) *higher += hi;        \
  }                                             \


#endif
