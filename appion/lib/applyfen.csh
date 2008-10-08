#! /bin/csh -f
# apply amplitude correction curve to data

if ($#argv != 2) then
  echo "usage: applyabc <input> <output>"
  exit
endif

rm -rf results.*
rm -rf LOG.*

spider bat/spi <<eof

FR G
<vol>$1

FR G
<fen>fen

FR G
<fvol>$2 ; output corrected volume

;------------------------------------------------------

echo amplitude curve to volume
 
; Amplitude correct volume
FD
<vol>    ; input volume
<fvol>   ; output corrected volume
<fen> ; doc file with filter values

EN D
eof
