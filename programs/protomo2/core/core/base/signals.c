/*----------------------------------------------------------------------------*
*
*  signals.c  -  core: signals
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "signals.h"
#include "exception.h"
#include <signal.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>


/* macros */

#define SignalMax 32


/* types */

typedef struct {
  int flag;
  struct sigaction act;
} Signal;


/* variables */

int SignalInterrupt = 0;

int SignalCatch = 0;

static Signal SignalSIGINT;
static Signal SignalSIGQUIT;
static Signal SignalSIGTERM;
static Signal SignalSIGXCPU;
static Signal SignalSIGXFSZ;

static const char *SignalStr[SignalMax] = {
  [SIGHUP]  = "SIGHUP",
  [SIGINT]  = "SIGINT (keyboard interrupt)",
  [SIGQUIT] = "SIGQUIT (keyboard quit)",
  [SIGILL]  = "SIGILL (illegal instruction)",
  [SIGABRT] = "SIGABRT (abort)",
  [SIGFPE]  = "SIGFPE (floating point exception)",
  [SIGSEGV] = "SIGSEGV (segmentation fault)",
  [SIGPIPE] = "SIGPIPE (broken pipe)",
  [SIGALRM] = "SIGALRM (timer alarm)",
  [SIGTERM] = "SIGTERM (termination signal)",
  [SIGUSR1] = "SIGUSR1",
  [SIGUSR2] = "SIGUSR2",
  [SIGCHLD] = "SIGCHLD",
  [SIGBUS]  = "SIGBUS (bus error)",
  [SIGXCPU] = "SIGXCPU (CPU time limit exceeded)",
  [SIGXFSZ] = "SIGXFSZ (file size limit exceeded)",
};


/* functions */

extern const char *SignalString
                   (int sig)

{
  static char msg[16] = "signal ";
  const char *str = msg;

  if ( ( sig > 0 ) && ( sig < SignalMax ) ) {

    if ( SignalStr[sig] != NULL ) {
      str = SignalStr[sig];
    } else {
      sprintf( msg + 7, "%-d%c", sig, 0 );
    }

  } else {
    msg[7] = '?';
    msg[8] = 0;
  }

  return str;

}


static void SignalMessage
            (int sig)

{

  fprintf( stderr, "\r%s: terminated by signal %s\n", Main, SignalString( sig ) );

}


static void SignalAbort
            (int sig)

{

  SignalMessage( sig );

  fprintf( stderr, "%s: send bug reports to bugs@electrontomography.org\n", Main );

  _exit( EXIT_FAILURE );

}


static void SignalTerm
            (int sig)

{

  SignalMessage( sig );

  exit( EXIT_FAILURE );

}


static void SignalInt
            (int sig)

{
  Signal *signal;

  if ( SignalInterrupt != SIGINT ) SignalInterrupt = sig;

  switch ( sig ) {
    case SIGQUIT: signal = &SignalSIGQUIT; break;
    case SIGTERM: signal = &SignalSIGTERM; break;
    case SIGXCPU: signal = &SignalSIGXCPU; break;
    case SIGXFSZ: signal = &SignalSIGXFSZ; break;
    default: return;
  }

  if ( signal->flag ) {
    void (*handler)(int) = signal->act.sa_handler;
    if ( handler == SIG_DFL ) {
      SignalTerm( sig );
    } else if ( ( handler != NULL ) && ( handler != SIG_IGN ) ) {
      handler( sig );
    }
  }

}


static Status SignalHandlerInstall
              (int sig,
               void (*handler)(int),
               struct sigaction *sav)

{
  struct sigaction act;

  if ( ( sig > 0 ) && ( sig < SignalMax ) ) {

    if ( handler == NULL ) handler = SignalTerm;

    memset( &act, 0, sizeof(act) );
    act.sa_handler = handler;
    sigfillset( &act.sa_mask );
    if ( sigaction( sig, &act, sav ) ) {
      return E_ERRNO;
    }

  }

  return E_NONE;

}


static Status SignalHandlerSet
              (int sig,
               Signal *signal)

{
  Status status = E_NONE;

  if ( !signal->flag ) {

    status = SignalHandlerInstall( sig, SignalInt, &signal->act );
    if ( !status ) signal->flag = -1;

  }

  return status;

}


static Status SignalHandlerRestore
              (int sig,
               Signal *signal)

{
  Status status = E_NONE;

  if ( signal->flag ) {

    if ( sigaction( sig, &signal->act, NULL ) ) {
      status = E_ERRNO;
    } else {
      signal->flag = 0;
    }

  }

  return status;

}


extern Status SignalInit()

{
  Status stat, status = E_NONE;

  if ( !SignalCatch ) {

    stat = SignalHandlerInstall( SIGINT,  SignalTerm, NULL ); if ( exception( stat ) ) status = stat;
    stat = SignalHandlerInstall( SIGQUIT, SignalTerm, NULL ); if ( exception( stat ) ) status = stat;
    stat = SignalHandlerInstall( SIGTERM, SignalTerm, NULL ); if ( exception( stat ) ) status = stat;
    stat = SignalHandlerInstall( SIGXCPU, SignalTerm, NULL ); if ( exception( stat ) ) status = stat;
    stat = SignalHandlerInstall( SIGXFSZ, SignalTerm, NULL ); if ( exception( stat ) ) status = stat;

    stat = SignalHandlerInstall( SIGHUP,  SIG_IGN, NULL ); if ( exception( stat ) ) status = stat;
    stat = SignalHandlerInstall( SIGPIPE, SIG_IGN, NULL ); if ( exception( stat ) ) status = stat;
    stat = SignalHandlerInstall( SIGALRM, SIG_IGN, NULL ); if ( exception( stat ) ) status = stat;
    stat = SignalHandlerInstall( SIGUSR1, SIG_IGN, NULL ); if ( exception( stat ) ) status = stat;
    stat = SignalHandlerInstall( SIGUSR2, SIG_IGN, NULL ); if ( exception( stat ) ) status = stat;

  }

  stat = SignalHandlerInstall( SIGILL,  SignalAbort, NULL ); if ( exception( stat ) ) status = stat;
  stat = SignalHandlerInstall( SIGABRT, SignalAbort, NULL ); if ( exception( stat ) ) status = stat;
  stat = SignalHandlerInstall( SIGFPE,  SignalAbort, NULL ); if ( exception( stat ) ) status = stat;
  stat = SignalHandlerInstall( SIGSEGV, SignalAbort, NULL ); if ( exception( stat ) ) status = stat;
  stat = SignalHandlerInstall( SIGBUS,  SignalAbort, NULL ); if ( exception( stat ) ) status = stat;

  SignalSIGINT.flag = 0;
  SignalSIGQUIT.flag = 0;
  SignalSIGTERM.flag = 0;
  SignalSIGXCPU.flag = 0;
  SignalSIGXFSZ.flag = 0;

  return status;

}


extern Status SignalSet()

{
  Status stat, status = E_NONE;

  SignalInterrupt = 0;

  stat = SignalHandlerSet( SIGINT,  &SignalSIGINT  ); if ( exception( stat ) ) status = stat;
  stat = SignalHandlerSet( SIGQUIT, &SignalSIGQUIT ); if ( exception( stat ) ) status = stat;
  stat = SignalHandlerSet( SIGTERM, &SignalSIGTERM ); if ( exception( stat ) ) status = stat;
  stat = SignalHandlerSet( SIGXCPU, &SignalSIGXCPU ); if ( exception( stat ) ) status = stat;
  stat = SignalHandlerSet( SIGXFSZ, &SignalSIGXFSZ ); if ( exception( stat ) ) status = stat;

  return status;

}


extern Status SignalRestore()

{
  Status stat, status = E_NONE;

  stat = SignalHandlerRestore( SIGINT,  &SignalSIGINT  ); if ( exception( stat ) ) status = stat;
  stat = SignalHandlerRestore( SIGQUIT, &SignalSIGQUIT ); if ( exception( stat ) ) status = stat;
  stat = SignalHandlerRestore( SIGTERM, &SignalSIGTERM ); if ( exception( stat ) ) status = stat;
  stat = SignalHandlerRestore( SIGXCPU, &SignalSIGXCPU ); if ( exception( stat ) ) status = stat;
  stat = SignalHandlerRestore( SIGXFSZ, &SignalSIGXFSZ ); if ( exception( stat ) ) status = stat;

  return status;

}
