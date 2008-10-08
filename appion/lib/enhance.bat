MD
SET MP
0

FR G
[vol]???     ; input volume to correct/enhance

FR G
[outvol]???  ; output enhanced volume

FR G
[scatter]??? ; input amplitude curve

; resolution limit (from scattering file)
x99 = ??   ; box size in pixels
x98 = ??   ; filter limit in angstroms
x80 = ??   ; pixel size

FR G
[pow]rojo     ; output 1D power spectrum of input volume

FR G
[out]fen      ; output enhancement curve

FR G
[applyfen]applyfen.csh ; apply curve to data script

x35 = x99*x80/x98   ; filter limit (in pixels). Filter the data out to point P,
                    ; where P < (volume_diameter / 2)
                    ; E.g., resolution cutoff

VM
echo "box size:  {***x99}"
VM
echo "filter to: {***x35}"
; -------------------------------------------------
; create a doc file with a 1D power spectrum of the input volume
PW
<vol>
_1

SQ
_1
_2

RO
_2
_3

DE
<pow>

LI D
_3
<pow>
r
1

UD N,x66
<pow>

; create the output enhancement curve
x21=1

DE
<out>

DO LB1 x21=2,x35   ; curve goes out to filter limit

UD IC,x21,x51
<pow>

x55=(x21-1)/(2*(x66-1))
x56=x80/x55

@pwsc[x56,x77]
<scatter>

; Xray/EM
x77=SQR(x77/X51)
x78=LON(X77)

SD x21,x77,x55,x56,X78
<out>

LB1

VM
<applyfen>.csh <vol>.spi <outvol>.spi

DE
<pow>

DE
filter

DE
vars

VM
rm -f fit.log fen.spi

EN D

