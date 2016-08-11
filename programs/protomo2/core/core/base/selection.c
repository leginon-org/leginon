/*----------------------------------------------------------------------------*
*
*  selection.c  -  core: selection
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

extern Bool Select
            (const Size *selection,
             Size number)

{

  if ( selection == NULL ) return True;

  Size count = *selection++;

  if ( !count ) return True;

  while ( count-- ) {
    Size min = *selection++;
    Size max = *selection++;
    if ( ( number >= min ) && ( number <= max ) ) return True;
  }

  return False;

}


extern Bool Exclude
            (const Size *exclusion,
             Size number)

{

  if ( exclusion == NULL ) return True;

  Size count = *exclusion++;

  while ( count-- ) {
    Size min = *exclusion++;
    Size max = *exclusion++;
    if ( ( number >= min ) && ( number <= max ) ) return False;
  }

  return True;

}


extern Bool SelectExclude
            (const Size *selection,
             const Size *exclusion,
             Size number)

{

  return Select( selection, number ) && Exclude( exclusion, number );

}
