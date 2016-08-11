/*----------------------------------------------------------------------------*
*
*  timeget.c  -  core: system time and date
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
#include <time.h>
#include <sys/time.h>


/* functions */

extern Time TimeGet()

{
  struct timeval tv;
  Time t = { 0, 0 };

  if ( !gettimeofday( &tv, NULL ) ) {
    struct tm *tl = localtime( &tv.tv_sec );
    int i = 1900 + tl->tm_year;
    t.date |= ( i / 1000 ) % 10; t.date <<= 4;
    t.date |= ( i / 100 ) % 10;  t.date <<= 4;
    t.date |= ( i / 10 ) % 10;   t.date <<= 4;
    t.date |= ( i ) % 10;        t.date <<= 4;

    i = tl->tm_mon + 1;
    t.date |= ( i / 10 ) % 10;   t.date <<= 4;
    t.date |= ( i ) % 10;        t.date <<= 4;

    i = tl->tm_mday;
    t.date |= ( i / 10 ) % 10;   t.date <<= 4;
    t.date |= ( i ) % 10;

    t.time = tl->tm_hour;
    t.time *= 60;
    t.time += tl->tm_min;
    t.time *= 60;
    t.time += tl->tm_sec;
    t.time *= 1000;
    t.time += ( tv.tv_usec / 1000);
  }

  return t;

}


