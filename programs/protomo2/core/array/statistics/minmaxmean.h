/*----------------------------------------------------------------------------*
*
*  minmaxmean.h  -  array: statistics
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef minmaxmean_h_
#define minmaxmean_h_

#include "statistics.h"
#include "mathdefs.h"


/* macros */

#define statfloat( type, typemin, typemax )                 \
  {                                                         \
    type min = typemax, max = typemin;                      \
    Coord sum = 0, sum2 = 0, mean = 0, sd = 0;              \
    if ( flags & StatImag ) {                               \
      min = 0; max = 0;                                     \
    } else if ( count && ( flags & StatAll ) ) {            \
      const type *s = src; s += count;                      \
      do {                                                  \
        s--;                                                \
        if ( *s < min ) min = *s;                           \
        if ( *s > max ) max = *s;                           \
        sum += *s;                                          \
      } while ( s != src );                                 \
      mean = sum / count;                                   \
      if ( flags & ( StatMean | StatSd ) ) {                \
        Coord sum0 = 0;                                     \
        s = src; s += count;                                \
        do {                                                \
          Coord s0 = (*--s) - mean;                         \
          sum0 += s0;                                       \
        } while ( s != src );                               \
        sum += sum0;                                        \
        mean = sum / count;                                 \
        if ( flags & StatSd ) {                             \
          s = src; s += count;                              \
          do {                                              \
            Coord s0 = (*--s) - mean;                       \
            sum2 += s0 * s0;                                \
          } while ( s != src );                             \
          sd = sqrt( sum2 / count );                        \
        }                                                   \
      }                                                     \
    }                                                       \
    dst->count = count;                                     \
    if ( flags & StatMin )  dst->min = min;                 \
    if ( flags & StatMax )  dst->max = max;                 \
    if ( flags & StatNoNrm ) {                              \
      if ( flags & StatMean ) dst->mean = sum;              \
      if ( flags & StatSd )   dst->sd = sum2;               \
    } else {                                                \
      if ( flags & StatMean ) dst->mean = mean;             \
      if ( flags & StatSd )   dst->sd = sd;                 \
    }                                                       \
  }                                                         \


#define statcmplx( type, typemin, typemax )                 \
  {                                                         \
    Coord min = typemax, max = typemin;                     \
    Coord sum = 0, sum2 = 0, mean = 0, sd = 0;              \
    if ( count && ( flags & StatAll ) ) {                   \
      if ( flags & StatModul ) {                            \
        const type *s = src; s += count + count;            \
        do {                                                \
          Coord im = *--s, re = *--s;                       \
          Coord modul = sqrt( re * re + im * im );          \
          if ( modul < min ) min = modul;                   \
          if ( modul > max ) max = modul;                   \
          sum += modul;                                     \
        } while ( s != src );                               \
        mean = sum / count;                                 \
        if ( flags & ( StatMean | StatSd ) ) {              \
          Coord sum0 = 0;                                   \
          s = src; s += count + count;                      \
          do {                                              \
            Coord im = *--s, re = *--s;                     \
            Coord modul = sqrt( re * re + im * im );        \
            sum0 += modul - mean;                           \
          } while ( s != src );                             \
          sum += sum0;                                      \
          mean = sum / count;                               \
          if ( flags & StatSd ) {                           \
            s = src; s += count + count;                    \
            do {                                            \
              Coord im = *--s, re = *--s;                   \
              Coord modul = sqrt( re * re + im * im );      \
              modul -= mean;                                \
              sum2 += modul * modul;                        \
            } while ( s != src );                           \
            sd = sqrt( sum2 / count );                      \
          }                                                 \
        }                                                   \
      } else {                                              \
        const type *s = src;                                \
        if ( flags & StatImag ) {                           \
          src = ++s;                                        \
        }                                                   \
        s += count + count;                                 \
        do {                                                \
          s--; s--;                                         \
          if ( *s < min ) min = *s;                         \
          if ( *s > max ) max = *s;                         \
          sum += *s;                                        \
        } while ( s != src );                               \
        mean = sum / count;                                 \
        if ( flags & ( StatMean | StatSd ) ) {              \
          Coord sum0 = 0;                                   \
          s = src; s += count + count;                      \
          do {                                              \
            Coord s0;                                       \
            s--; s--;                                       \
            s0 = *s-mean;                                   \
            sum0 += s0;                                     \
          } while ( s != src );                             \
          sum += sum0;                                      \
          mean = sum / count;                               \
          if ( flags & StatSd ) {                           \
            s = src; s += count + count;                    \
            do {                                            \
              Coord s0;                                     \
              s--; s--;                                     \
              s0 = *s - mean;                               \
              sum2 += s0 * s0;                              \
            } while ( s != src );                           \
            sd = sqrt( sum2 / count );                      \
          }                                                 \
        }                                                   \
      }                                                     \
    }                                                       \
    dst->count = count;                                     \
    if ( flags & StatMin )  dst->min = min;                 \
    if ( flags & StatMax )  dst->max = max;                 \
    if ( flags & StatNoNrm ) {                              \
      if ( flags & StatMean ) dst->mean = sum;              \
      if ( flags & StatSd )   dst->sd = sum2;               \
    } else {                                                \
      if ( flags & StatMean ) dst->mean = mean;             \
      if ( flags & StatSd )   dst->sd = sd;                 \
    }                                                       \
  }                                                         \

#endif
