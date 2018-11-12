/*----------------------------------------------------------------------------*
*
*  sample_3d.h  -  array: sampling
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

/* template */

{
  const SRCTYPE *src = srcaddr;
  DSTTYPE *dst = dstaddr;
  DSTTYPE fill = 0;
  Coord thrmin = -RealMax;
  Coord thrmax = +RealMax;
  Coord bias = 0, scale = 1;
  Size srcoffs[3];
  Size dstoffs[3];
  Size dstbox[3];
  Stat *stat = NULL;
  Size nstat = 0;
  Coord min = +RealMax;
  Coord max = -RealMax;
  Coord sum = 0, sum2 = 0;
  SampleFlags flags = 0;
  Status status;

  if ( argcheck( srclen == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( smp    == NULL ) ) return exception( E_ARGVAL );
  if ( argcheck( dstlen == NULL ) ) return exception( E_ARGVAL );

  if ( param != NULL ) {
    Coord fillval = fill;
    TransferParam *transf =  param->transf;
    if ( transf != NULL ) {
      if ( transf->flags & TransferThr ) {
        thrmin = transf->thrmin;
        thrmax = transf->thrmax;
        if ( thrmax > DSTTYPEMAX ) thrmax = DSTTYPEMAX;
        if ( thrmin < DSTTYPEMIN ) thrmin = DSTTYPEMIN;
      }
      if ( transf->flags & TransferBias)  bias  = transf->bias;
      if ( transf->flags & TransferScale) scale = transf->scale;
    }
    flags = param->flags;
    if ( flags & SampleFill ) fillval = param->fill;
    if ( fillval > DSTTYPEMAX ) fillval = DSTTYPEMAX;
    if ( fillval < DSTTYPEMIN ) fillval = DSTTYPEMIN;
    fill = fillval;
    stat = param->stat;
  }

  if ( flags & SampleConvol ) {
    bias  *= smp[0] * smp[1] * smp[2];
    scale /= smp[0] * smp[1] * smp[2];
  }

  status = SampleBox( 3, srclen, smp, b, dstlen, c, srcoffs, dstoffs, dstbox );
  if ( status ) {
    if ( ( status != E_SAMPLE_CLIP ) || ( ~flags & SampleClip ) ) {
      return exception( status );
    }
  }

  {
    const SRCTYPE *srcz = src + srcoffs[2] * srclen[1] * srclen[0];
    Size iz = 0;

    if ( dst == NULL ) {
      iz = dstoffs[1];
    } else {
      while ( iz < dstoffs[2] ) {
        Size i = dstlen[1] * dstlen[0];
        while ( i-- ) *dst++ = fill;
        iz++;
      } /* end while iz */
    }

    if ( flags & SampleConvol ) {

      while ( iz < dstoffs[2] + dstbox[2] ) {
        const SRCTYPE *srcy = srcz + srcoffs[1] * srclen[0];
        Size iy = 0;

        if ( dst == NULL ) {
          iy = dstoffs[1];
        } else {
          while ( iy < dstoffs[1] ) {
            Size i = dstlen[0];
            while ( i-- ) *dst++ = fill;
            iy++;
          } /* end while iy */
        }

        while ( iy < dstoffs[1] + dstbox[1] ) {
          const SRCTYPE *srcx = srcy + srcoffs[0];
          Size ix = 0;

          if ( dst == NULL ) {
            ix = dstoffs[0];
          } else {
            while ( ix < dstoffs[0] ) {
              *dst++ = fill;
              ix++;
            } /* end while ix */
          }

          if ( src == NULL ) {
            if ( ix < dstoffs[0] + dstbox[0] ) {
              if ( dst != NULL ) {
                dst += dstoffs[0] + dstbox[0] - ix;
              }
              ix = dstoffs[0] + dstbox[0];
            }
          } else {
            if ( ix < dstoffs[0] + dstbox[0] ) {
              nstat += dstoffs[0] + dstbox[0] - ix;
            }
            while ( ix < dstoffs[0] + dstbox[0] ) {
              Coord d = 0;
              Size x;
              for ( x = 0; x < smp[0]; x++ ) {
                const SRCTYPE *sy = srcx++;
                Size y;
                for ( y = 0; y < smp[1]; y++ ) {
                  const SRCTYPE *sz = sy;
                  Size z;
                  for ( z = 0; z < smp[2]; z++ ) {
                    d += *sz;
                    sz += srclen[1] * srclen[0];
                  }
                  sy += srclen[0];
                }
              }
              d = ( d - bias ) * scale;
              if ( d < thrmin ) {
                d = thrmin;
              } else if ( d > thrmax ) {
                d = thrmax;
              }
              if ( stat != NULL ) {
                if ( d < min ) min = d;
                if ( d > max ) max = d;
                sum += d;
                sum2 += d * d;
              }
              if ( dst != NULL ) {
                *dst++ = d;
              }
              ix++;
            } /* end while ix */
          } /* end if src */

          if ( dst != NULL ) {
            while ( ix < dstlen[0]) {
              *dst++ = fill;
              ix++;
            } /* end while ix */
          }

          srcy += srclen[0] * smp[1];
          iy++;

        } /* end while iy */

        if ( dst != NULL ) {
          while ( iy < dstlen[1] ) {
            Size i = dstlen[0];
            while ( i-- ) *dst++ = fill;
            iy++;
          } /* end while iy */
        }

        srcz += srclen[0] * srclen[1] * smp[2];
        iz++;

      } /* end while iz */

    } else {

      while ( iz < dstoffs[2] + dstbox[2] ) {
        const SRCTYPE *srcy = srcz + srcoffs[1] * srclen[0];
        Size iy = 0;

        if ( dst == NULL ) {
          iy = dstoffs[1];
        } else {
          while ( iy < dstoffs[1] ) {
            Size i = dstlen[0];
            while ( i-- ) *dst++ = fill;
            iy++;
          } /* end while iy */
        }

        while ( iy < dstoffs[1] + dstbox[1] ) {
          const SRCTYPE *srcx = srcy + srcoffs[0];
          Size ix = 0;

          if ( dst == NULL ) {
            ix = dstoffs[0];
          } else {
            while ( ix < dstoffs[0] ) {
              *dst++ = fill;
              ix++;
            } /* end while ix */
          }

          if ( src == NULL ) {
            if ( ix < dstoffs[0] + dstbox[0] ) {
              if ( dst != NULL ) {
                dst += dstoffs[0] + dstbox[0] - ix;
              }
              ix = dstoffs[0] + dstbox[0];
            }
          } else {
            if ( ix < dstoffs[0] + dstbox[0] ) {
              nstat += dstoffs[0] + dstbox[0] - ix;
            }
            if ( scale == 1 ) {
              while ( ix < dstoffs[0] + dstbox[0] ) {
                Coord d = *srcx;
                d -= bias;
                if ( d < thrmin ) {
                  d = thrmin;
                } else if ( d > thrmax ) {
                  d = thrmax;
                }
                if ( stat != NULL ) {
                  if ( d < min ) min = d;
                  if ( d > max ) max = d;
                  sum += d;
                  sum2 += d * d;
                }
                if ( dst != NULL ) {
                  *dst++ = d;
                }
                srcx += smp[0];
                ix++;
              } /* end while ix */
            } else {
              while ( ix < dstoffs[0] + dstbox[0] ) {
                Coord d = *srcx;
                d = ( d - bias ) * scale;
                if ( d < thrmin ) {
                  d = thrmin;
                } else if ( d > thrmax ) {
                  d = thrmax;
                }
                if ( stat != NULL ) {
                  if ( d < min ) min = d;
                  if ( d > max ) max = d;
                  sum += d;
                  sum2 += d * d;
                }
                if ( dst != NULL ) {
                  *dst++ = d;
                }
                srcx += smp[0];
                ix++;
              } /* end while ix */
            } /* end if scale */
          } /* end if src */

          if ( dst != NULL ) {
            while ( ix < dstlen[0] ) {
              *dst++ = fill;
              ix++;
            } /* end while ix */
          }

          srcy += srclen[0] * smp[1];
          iy++;

        } /* end while iy */

        if ( dst != NULL ) {
          while ( iy < dstlen[1] ) {
            Size i = dstlen[0];
            while ( i-- ) *dst++ = fill;
            iy++;
          } /* end while iy */
        }

        srcz += srclen[0] * srclen[1] * smp[2];
        iz++;

      } /* end while iz */

    } /* end if flags */

    if ( dst != NULL ) {
      while ( iz < dstlen[2]) {
        Size i = dstlen[1] * dstlen[0];
        while ( i-- ) *dst++ = fill;
        iz++;
      } /* end while iz */
    }

  }

  if ( stat != NULL ) {
    stat->count = nstat;
    stat->min = min;
    stat->max = max;
    stat->mean = sum / nstat;
    stat->sd = sum2;
    stat->sd = nstat * sum2 - sum * sum;
    stat->sd = ( (stat->sd > 0 ) && nstat ) ? ( sqrt( stat->sd ) / nstat ) : 0;
  }

  return status;

}
