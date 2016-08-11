/*----------------------------------------------------------------------------*
*
*  i3data.c  -  io: i3 data
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "i3data.h"
#include "exception.h"


/* variables */

#define I3dataTableListSize 4
static Size I3dataTableListLen = 0;
static const I3dataDscr *I3dataTableList[I3dataTableListSize];


/* functions */

extern Status I3dataRegister
              (const I3dataDscr table[])

{

  Size len = I3dataTableListLen + 1;
  if ( len >= I3dataTableListSize ) return exception( E_I3DATA );

  const I3dataDscr *dscr = table;
  I3dataCode start = dscr->code;
  for ( Index i = 0; dscr->name != NULL; i++, dscr++ ) {
    if ( dscr->code != start + i ) return exception( E_I3DATA );
  }

  I3dataTableList[I3dataTableListLen] = table;
  I3dataTableListLen = len;

  return E_NONE;

}


extern const I3dataDscr *I3dataGetDscr
                         (int code)

{

  for ( Size i = 0; i < I3dataTableListLen; i++ ) {

    const I3dataDscr *dscr = I3dataTableList[i];

    for ( Size j = 0; dscr->name != NULL; j++, dscr++ ) {

      if ( code == dscr->code ) return dscr;

    }

  }

  return NULL;

}


extern Status I3dataIter
              (Status (*call)(const I3dataDscr *, const void *, void * ),
               const void *src,
               void *dst,
               I3dataFlags flags)

{
  Status status;

  for ( Size i = 0; i < I3dataTableListLen; i++ ) {

    const I3dataDscr *dscr = I3dataTableList[i];

    for ( Size j = 0; dscr->name != NULL; j++, dscr++ ) {

      status = call( dscr, src, dst );
      if ( exception( status ) ) return status;

    }

  }

  return E_NONE;

}
