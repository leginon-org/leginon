/*----------------------------------------------------------------------------*
*
*  tomocacheget.c  -  series: image file i/o
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "tomocache.h"
#include "exception.h"


/* functions */

extern Status TomocacheGetImage
              (const Tomocache *cache,
               const Size index,
               const Size number,
               Image *img)

{

  if ( argcheck( cache == NULL ) ) return pushexception( E_ARGVAL );

  if ( index >= cache->images ) return pushexception( E_ARGVAL );

  const TomocacheDscr *dscr = cache->dscr + index;

  if ( dscr->number != number ) return pushexception( E_TOMOCACHE );

  img->dim = 2;
  img->len[0] = dscr->len[0];
  img->len[1] = dscr->len[1];
  img->low[0] = dscr->low[0];
  img->low[1] = dscr->low[1];
  img->type = dscr->type;
  img->attr = dscr->attr;

  return E_NONE;

}
