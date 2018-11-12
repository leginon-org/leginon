/*----------------------------------------------------------------------------*
*
*  scale.h  -  array: pixel value transfer
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#ifndef scale_h_
#define scale_h_

#include "transfer.h"


/* macros */

#define scale_int_dec( type, typemin, typemax )                 \
  {                                                             \
    type *d0 = dst, *d = d0 + count;                            \
    Coord thrmin = typemin, thrmax = typemax;                   \
    Coord bias = 0;                                             \
    TransferFlags flags = ( param == NULL ) ? 0 : param->flags; \
    if ( flags & TransferThr ) {                                \
      if ( param->thrmin > thrmin ) thrmin = param->thrmin;     \
      if ( param->thrmax < thrmax ) thrmax = param->thrmax;     \
    }                                                           \
    if ( flags & TransferBias ) {                               \
      bias = param->bias;                                       \
    }                                                           \
    s += count;                                                 \
    if ( flags & TransferScale ) {                              \
      Coord scale = param->scale;                               \
      while ( --d >= d0 ) {                                     \
        Coord v = *--s;                                         \
        v = ( v - bias ) * scale;                               \
        if ( v <= thrmin ) {                                    \
          *d = thrmin;                                          \
        } else if ( v >= thrmax ) {                             \
          *d = thrmax;                                          \
        } else {                                                \
          *d = v;                                               \
        }                                                       \
      }                                                         \
    } else if ( flags & TransferBias ) {                        \
      while ( --d >= d0 ) {                                     \
        Coord v = *--s;                                         \
        v -= bias;                                              \
        if ( v <= thrmin ) {                                    \
          *d = thrmin;                                          \
        } else if ( v >= thrmax ) {                             \
          *d = thrmax;                                          \
        } else {                                                \
          *d = v;                                               \
        }                                                       \
      }                                                         \
    } else {                                                    \
      while ( --d >= d0 ) {                                     \
        Coord v = *--s;                                         \
        if ( v <= thrmin ) {                                    \
          *d = thrmin;                                          \
        } else if ( v >= thrmax ) {                             \
          *d = thrmax;                                          \
        } else {                                                \
          *d = v;                                               \
        }                                                       \
      }                                                         \
    }                                                           \
  }

#define scale_int_inc( type, typemin, typemax )                 \
  {                                                             \
    type *d = dst, *d1 = d + count;                             \
    Coord thrmin = typemin, thrmax = typemax;                   \
    Coord bias = 0;                                             \
    TransferFlags flags = ( param == NULL ) ? 0 : param->flags; \
    if ( flags & TransferThr ) {                                \
      if ( param->thrmin > thrmin ) thrmin = param->thrmin;     \
      if ( param->thrmax < thrmax ) thrmax = param->thrmax;     \
    }                                                           \
    if ( flags & TransferBias ) {                               \
      bias = param->bias;                                       \
    }                                                           \
    if ( flags & TransferScale ) {                              \
      Coord scale = param->scale;                               \
      while ( d < d1 ) {                                        \
        Coord v = *s++;                                         \
        v = ( v - bias ) * scale;                               \
        if ( v <= thrmin ) {                                    \
          *d = thrmin;                                          \
        } else if ( v >= thrmax ) {                             \
          *d = thrmax;                                          \
        } else {                                                \
          *d = v;                                               \
        }                                                       \
        d++;                                                    \
      }                                                         \
    } else if ( flags & TransferBias ) {                        \
      while ( d < d1 ) {                                        \
        Coord v = *s++;                                         \
        v -= bias;                                              \
        if ( v <= thrmin ) {                                    \
          *d = thrmin;                                          \
        } else if ( v >= thrmax ) {                             \
          *d = thrmax;                                          \
        } else {                                                \
          *d = v;                                               \
        }                                                       \
        d++;                                                    \
      }                                                         \
    } else {                                                    \
      while ( d < d1 ) {                                        \
        Coord v = *s++;                                         \
        if ( v <= thrmin ) {                                    \
          *d = thrmin;                                          \
        } else if ( v >= thrmax ) {                             \
          *d = thrmax;                                          \
        } else {                                                \
          *d = v;                                               \
        }                                                       \
        d++;                                                    \
      }                                                         \
    }                                                           \
  }

#define scale_flt_dec( type  )                                  \
  {                                                             \
    type *d0 = dst, *d = d0 + count;                            \
    Coord bias = 0;                                             \
    TransferFlags flags = ( param == NULL ) ? 0 : param->flags; \
    if ( flags & TransferBias ) {                               \
      bias = param->bias;                                       \
    }                                                           \
    s += count;                                                 \
    if ( flags & TransferThr ) {                                \
      Coord thrmin = param->thrmin;                             \
      Coord thrmax = param->thrmax;                             \
      if ( flags & TransferScale ) {                            \
        Coord scale = param->scale;                             \
        while ( --d >= d0 ) {                                   \
          Coord v = *--s;                                       \
          v = ( v - bias ) * scale;                             \
          if ( v <= thrmin ) {                                  \
            *d = thrmin;                                        \
          } else if ( v >= thrmax ) {                           \
            *d = thrmax;                                        \
          } else {                                              \
            *d = v;                                             \
          }                                                     \
        }                                                       \
      } else if ( flags & TransferBias ) {                      \
        while ( --d >= d0 ) {                                   \
          Coord v = *--s;                                       \
          v -= bias;                                            \
          if ( v <= thrmin ) {                                  \
            *d = thrmin;                                        \
          } else if ( v >= thrmax ) {                           \
            *d = thrmax;                                        \
          } else {                                              \
            *d = v;                                             \
          }                                                     \
        }                                                       \
      } else {                                                  \
        while ( --d >= d0 ) {                                   \
          Coord v = *--s;                                       \
          if ( v <= thrmin ) {                                  \
            *d = thrmin;                                        \
          } else if ( v >= thrmax ) {                           \
            *d = thrmax;                                        \
          } else {                                              \
            *d = v;                                             \
          }                                                     \
        }                                                       \
      }                                                         \
    } else {                                                    \
      if ( flags & TransferScale ) {                            \
        Coord scale = param->scale;                             \
        while ( --d >= d0 ) {                                   \
          Coord v = *--s;                                       \
          *d = ( v - bias ) * scale;                            \
        }                                                       \
      } else if ( flags & TransferBias ) {                      \
        while ( --d >= d0 ) {                                   \
          Coord v = *--s;                                       \
          *d = v - bias;                                        \
        }                                                       \
      } else {                                                  \
        while ( --d >= d0 ) {                                   \
          *d = *--s;                                            \
        }                                                       \
      }                                                         \
    }                                                           \
  }

#define scale_flt_inc( type  )                                  \
  {                                                             \
    type *d = dst, *d1 = d + count;                             \
    Coord bias = 0;                                             \
    TransferFlags flags = ( param == NULL ) ? 0 : param->flags; \
    if ( flags & TransferBias ) {                               \
      bias = param->bias;                                       \
    }                                                           \
    if ( flags & TransferThr ) {                                \
      Coord thrmin = param->thrmin;                             \
      Coord thrmax = param->thrmax;                             \
      if ( flags & TransferScale ) {                            \
        Coord scale = param->scale;                             \
        while ( d < d1 ) {                                      \
          Coord v = *s++;                                       \
          v = ( v - bias ) * scale;                             \
          if ( v <= thrmin ) {                                  \
            *d++ = thrmin;                                      \
          } else if ( v >= thrmax ) {                           \
            *d++ = thrmax;                                      \
          } else {                                              \
            *d++ = v;                                           \
          }                                                     \
        }                                                       \
      } else if ( flags & TransferBias ) {                      \
        while ( d < d1 ) {                                      \
          Coord v = *s++;                                       \
          v -= bias;                                            \
          if ( v <= thrmin ) {                                  \
            *d++ = thrmin;                                      \
          } else if ( v >= thrmax ) {                           \
            *d++ = thrmax;                                      \
          } else {                                              \
            *d++ = v;                                           \
          }                                                     \
        }                                                       \
      } else {                                                  \
        while ( d < d1 ) {                                      \
          Coord v = *s++;                                       \
          if ( v <= thrmin ) {                                  \
            *d++ = thrmin;                                      \
          } else if ( v >= thrmax ) {                           \
            *d++ = thrmax;                                      \
          } else {                                              \
            *d++ = v;                                           \
          }                                                     \
        }                                                       \
      }                                                         \
    } else {                                                    \
      if ( flags & TransferScale ) {                            \
        Coord scale = param->scale;                             \
        while ( d < d1 ) {                                      \
          Coord v = *s++;                                       \
          *d++ = ( v - bias ) * scale;                          \
        }                                                       \
      } else if ( flags & TransferBias ) {                      \
        while ( d < d1 ) {                                      \
          Coord v = *s++;                                       \
          *d++ = v - bias;                                      \
        }                                                       \
      } else {                                                  \
        while ( d < d1 ) {                                      \
          *d++ = *s++;                                          \
        }                                                       \
      }                                                         \
     }                                                          \
  }

#define scale_rset( d, v )  Cset( d, v, 0 )

#define scale_iset( d, v )  Cset( d, 0, v )

#define scale_fc_dec( type, typemin, typemax, set )             \
  {                                                             \
    type *d0 = dst, *d = d0 + count;                            \
    Coord bias = 0;                                             \
    TransferFlags flags = ( param == NULL ) ? 0 : param->flags; \
    if ( flags & TransferBias ) {                               \
      bias = param->bias;                                       \
    }                                                           \
    s += count;                                                 \
    if ( flags & TransferThr ) {                                \
      Coord thrmin = param->thrmin;                             \
      Coord thrmax = param->thrmax;                             \
      if ( flags & TransferScale ) {                            \
        Coord scale = param->scale;                             \
        while ( --d >= d0 ) {                                   \
          Coord v = *--s;                                       \
          v = ( v - bias ) * scale;                             \
          if ( v <= thrmin ) {                                  \
            v = thrmin;                                         \
          } else if ( v >= thrmax ) {                           \
            v = thrmax;                                         \
          }                                                     \
          set( *d, v );                                         \
        }                                                       \
      } else if ( flags & TransferBias ) {                      \
        while ( --d >= d0 ) {                                   \
          Coord v = *--s;                                       \
          v -= bias;                                            \
          if ( v <= thrmin ) {                                  \
            v = thrmin;                                         \
          } else if ( v >= thrmax ) {                           \
            v = thrmax;                                         \
          }                                                     \
          set( *d, v );                                         \
        }                                                       \
      } else {                                                  \
        while ( --d >= d0 ) {                                   \
          Coord v = *--s;                                       \
          if ( v <= thrmin ) {                                  \
            v = thrmin;                                         \
          } else if ( v >= thrmax ) {                           \
            v = thrmax;                                         \
          }                                                     \
          set( *d, v );                                         \
        }                                                       \
      }                                                         \
    } else {                                                    \
      if ( flags & TransferScale ) {                            \
        Coord scale = param->scale;                             \
        while ( --d >= d0 ) {                                   \
          Coord v = *--s;                                       \
          set( *d, ( v - bias ) * scale );                      \
        }                                                       \
      } else if ( flags & TransferBias ) {                      \
        while ( --d >= d0 ) {                                   \
          Coord v = *--s;                                       \
          set( *d, v - bias );                                  \
        }                                                       \
      } else {                                                  \
        while ( --d >= d0 ) {                                   \
          set( *d, *--s );                                      \
        }                                                       \
      }                                                         \
    }                                                           \
  }

#define scale_fc_inc( type, typemin, typemax, set )             \
  {                                                             \
    type *d = dst, *d1 = d + count;                             \
    Coord bias =0 ;                                             \
    TransferFlags flags = ( param == NULL ) ? 0 : param->flags; \
    if ( flags & TransferBias ) {                               \
      bias = param->bias;                                       \
    }                                                           \
    if ( flags & TransferThr ) {                                \
      Coord thrmin = param->thrmin;                             \
      Coord thrmax = param->thrmax;                             \
      if ( flags & TransferScale ) {                            \
        Coord scale = param->scale;                             \
        while ( d < d1 ) {                                      \
          Coord v = *s++;                                       \
          v = ( v - bias ) * scale;                             \
          if ( v <= thrmin ) {                                  \
            v = thrmin;                                         \
          } else if (v >= thrmax) {                             \
            v = thrmax;                                         \
          }                                                     \
          set( *d, v );                                         \
          d++;                                                  \
        }                                                       \
      } else if ( flags & TransferBias ) {                      \
        while ( d < d1 ) {                                      \
          Coord v = *s++;                                       \
          v -= bias;                                            \
          if ( v <= thrmin ) {                                  \
            v = thrmin;                                         \
          } else if ( v >= thrmax ) {                           \
            v = thrmax;                                         \
          }                                                     \
          set( *d, v );                                         \
          d++;                                                  \
        }                                                       \
      } else {                                                  \
        while ( d < d1 ) {                                      \
          Coord v = *s++;                                       \
          if ( v <= thrmin ) {                                  \
            v = thrmin;                                         \
          } else if ( v >= thrmax ) {                           \
            v = thrmax;                                         \
          }                                                     \
          set( *d, v );                                         \
          d++;                                                  \
        }                                                       \
      }                                                         \
    } else {                                                    \
      if ( flags & TransferScale ) {                            \
        Coord scale = param->scale;                             \
        while ( d < d1 ) {                                      \
          Coord v = *s++;                                       \
          set( *d, ( v - bias ) * scale );                      \
          d++;                                                  \
        }                                                       \
      } else if ( flags & TransferBias ) {                      \
        while ( d < d1 ) {                                      \
          Coord v = *s++;                                       \
          set( *d, v - bias );                                  \
          d++;                                                  \
        }                                                       \
      } else {                                                  \
        while ( d < d1 ) {                                      \
          set( *d, *s++ );                                      \
          d++;                                                  \
        }                                                       \
      }                                                         \
    }                                                           \
  }


#define scale_cc_dec( type )                                    \
  {                                                             \
    type *d0 = dst, *d = d0 + count;                            \
    Coord bias = 0;                                             \
    TransferFlags flags = ( param == NULL ) ? 0 : param->flags; \
    if ( flags & TransferBias ) {                               \
      bias = param->bias;                                       \
    }                                                           \
    s += count;                                                 \
    if ( flags & TransferScale ) {                              \
      Coord scale = param->scale;                               \
      while ( --d >= d0 ) {                                     \
        Coord re = Re( *s ), im = Im( *s ); --s;                \
        Cset( *d, ( re - bias ) * scale, im * scale );          \
      }                                                         \
    } else if ( flags & TransferBias ) {                        \
      while ( --d >= d0 ) {                                     \
        Coord re = Re( *s ), im = Im( *s ); --s;                \
        Cset( *d, re - bias, im );                              \
      }                                                         \
    } else {                                                    \
      while ( --d >= d0 ) {                                     \
        *d = *--s;                                              \
      }                                                         \
    }                                                           \
  }

#define scale_cc_inc( type )                                    \
  {                                                             \
    type *d = dst, *d1 = d + count;                             \
    Coord bias =0 ;                                             \
    TransferFlags flags = ( param == NULL ) ? 0 : param->flags; \
    if ( flags & TransferBias ) {                               \
      bias = param->bias;                                       \
    }                                                           \
    if ( flags & TransferScale ) {                              \
      Coord scale = param->scale;                               \
      while ( d < d1 ) {                                        \
        Coord re = Re( *s ), im = Im( *s ); s++;                \
        Cset( *d, ( re - bias ) * scale, im * scale );          \
        d++;                                                    \
      }                                                         \
    } else if ( flags & TransferBias ) {                        \
      while ( d < d1 ) {                                        \
        Coord re = Re( *s ), im = Im( *s ); s++;                \
        Cset( *d, re - bias, im );                              \
        d++;                                                    \
      }                                                         \
    } else {                                                    \
      while ( d < d1 ) {                                        \
        *d++ = *s++;                                            \
      }                                                         \
    }                                                           \
  }


#endif
