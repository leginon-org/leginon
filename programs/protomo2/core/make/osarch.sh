#!/bin/sh
#
# Copyright © 2012 Hanspeter Winkler
#

OS=$( uname -s )
ARCH=$( uname -m )

case "${OS}" in

  FreeBSD)

    OS="freebsd"

    case "${ARCH}" in
      i686)  ARCH="i686"   ;;
      amd64) ARCH="x86-64" ;;
      *) echo "$( basename ${0} ): unknown architecture ${ARCH}" >&2; exit 1 ;;
    esac
    
    ;;
    
  Linux)

    OS="linux"

    case "${ARCH}" in
      i686)   ARCH="i686"   ;;
      x86_64) ARCH="x86-64" ;;
      *) echo "$( basename ${0} ): unknown architecture ${ARCH}" >&2; exit 1 ;;
    esac
    
    ;;

  *) echo "$( basename ${0} ): unknown operating system ${OS}" >&2; exit 1 ;;
     
esac
