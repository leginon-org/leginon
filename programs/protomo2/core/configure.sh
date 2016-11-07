#!/bin/sh
#
# Copyright © 2012 Hanspeter Winkler
#

# version 2.4

set -e


comp="gcc4"
opts="opt"
thr="false"
fftw2thr="false"

features=""
config=""
libraries=""
deps="/usr/local"
inst="/usr/local/i3d-inst"

while [ ${1} ]; do

  case "${1}" in
    gcc) comp="gcc4" ;;
    opt) opts="opt" ;;
    dbg) opts="dbg" ;;
    threads)       features="${features} ${1}"; thr="true" ;;
    fftw2_threads) features="${features} ${1}"; thr="true"; fftw2thr="fftw2" ;;
    largefiles)    features="${features} ${1}" ;;
    fftpack)       libraries="${libraries} ${1}" ;;
    fftw2)         libraries="${libraries} ${1}" ;;
    djbfft)        libraries="${libraries} ${1}" ;;
    gslfft)        libraries="${libraries} ${1}" ;;
    dierckx)       libraries="${libraries} ${1}" ;;
    minpack)       libraries="${libraries} ${1}" ;;
    lapack)        libraries="${libraries} ${1}" ;;
    blas)          libraries="${libraries} ${1}" ;;
    ranlib)        libraries="${libraries} ${1}" ;;
    *)
      eval $( echo ${1} | awk '{ i=index( $0, "=/" ); print "key="substr( $0, 1, i-1 ); print "val="substr( $0, i+1 ) }' )
      case ${key} in
        libs) deps=${val} ;;
        inst) inst=${val} ;;
        *) echo "$( basename ${0} ): unknown option ${1}" >&2; exit 1 ;;
      esac
    ;;
  esac

  shift

done

if [ x"${features}" = x ]; then
  features="largefiles"
fi

if [ x"${libraries}" = x ]; then
  libraries="fftpack fftw2 djbfft dierckx minpack lapack blas ranlib"
fi
libraries="${libraries} tiff"

config="${config} ${features} ${libraries}"


root="make"

. ${root}/osarch.sh

echo "os:           " ${OS}
echo "arch:         " ${ARCH}
echo "compiler:     " ${comp}
echo "options:      " ${opts}
echo "features:     " ${features}
echo "libraries:    " ${libraries}
echo "dependencies: " ${deps}
echo "install:      " ${inst}


(
  echo "#"
  echo "# Makedefs: make definitions"
  echo "#"
  echo "# Copyright © 2012 Hanspeter Winkler"
  echo "#"
  echo
  echo "OS = ${OS}"
  echo
  echo "ARCH = ${ARCH}"
  echo
  echo "INSTROOT = ${inst}"
  echo
  echo "LIBROOT = ${deps}"
  echo
) >Maketop

(
  cat Maketop
  echo "LIBPRFX = i3"
  echo
  echo 'LIBINCS = $(LIBROOT)/include/$(OS)/$(ARCH)'
  echo 'LIBPATH = $(LIBROOT)/lib/$(OS)/$(ARCH)'
  echo
  for lib in ${libraries}; do
    if [ ${lib} = ${fftw2thr} ]; then
      ${root}/findlib.sh ${root} ${lib}thr ${link}
    fi
    ${root}/findlib.sh ${root} ${lib} ${link}
  done |
  ${root}/getopt.sh
  echo
  cat ${root}/${OS}/Makedefs
  echo
  cat ${root}/${OS}/Makedefs.dynamic
  echo
  cat ${root}/${OS}/${comp}/Makedefs-${ARCH}-${opts}
) >Makedefs


(
  cat ${root}/config.h
  echo "#define OS \"${OS}\""
  echo "#define ARCH \"${ARCH}\""
  [ ${opts} = dbg ] && cat ${root}/debug.h
  echo "#define ENABLE_DYNAMIC"
  for c in $( echo ${config} | tr '[:lower:]' '[:upper:]' ); do
    echo "#define ENABLE_${c}"
  done
  echo
  cat ${root}/${OS}/config.h
  echo
  cat ${root}/${OS}/${comp}/config.h
  echo; echo "#endif"
) >config.h

mv -f config.h core/config

(
  echo "#!/bin/sh"
  echo
  echo "# installation root directory"
  echo
  echo "export I3ROOT=\"${inst}\""
  echo
  echo "# libraries and paths"
  echo
  echo '. ${I3ROOT}/bin/osarch.sh'
  echo
  echo 'I3LIB="${I3ROOT}/lib/${OS}/${ARCH}"'
  echo
  echo 'I3DEPLIB="'${deps}'/lib/${OS}/${ARCH}"'
  echo
  echo 'I3LIBPATH="${I3LIB}:${I3DEPLIB}"'
  echo
  echo 'I3EXEPATH="${I3ROOT}/bin/${OS}/${ARCH}:${I3ROOT}/bin"'
) >setup-i3d.sh

(
  cat make/${OS}/syspath
  echo
  echo "# export variables"
  echo
  echo 'export LD_LIBRARY_PATH="${I3LIBPATH}:${2}"'
  echo
  echo 'export PATH=".:${I3EXEPATH}:${1}"'
) >setup-sys.sh

chmod +x setup-i3d.sh setup-sys.sh
