; reference-based alignment with the reference refinement

x99=500   ; number of particles
x98=3     ; number of reference images
x97=25    ; first ring for rotational alignment
x96=55    ; last ring for rotational alignment
x95=6     ; translational search range (in pixels)
x93=13    ; c-symmetry (rotational symmetry to be applied, 1 if none)
x92=4     ; iteration number
x91=x92-1

; last ring + translational search range MUST be < (box size/2)-1

FR G ; stack file
[rawparticles]start

FR G
[reference]reference

;if you mess with file defs below this batch file won't run!!!;;;;;;

FR G
[alinew]aligned{**x92}

FR G
[refselect]refselect/{**x92}refselect

FR G
[ref]{**x91}avgali

IF(x92.gt.1) THEN
FR G
[aliold]aligned{**x91}
GOTO LB69
ELSE
FR G
[aliold][rawparticles]
ENDIF

; create the selection document file.
; The image series is consecutive
DOC CREATE
select
1
1-x99

DOC CREATE
selref
1
1-x98

VM
mkdir -p rff/

VM
mkdir -p refselect/

do lb34, x11=1,x98
CP
[reference]@{**x11}
[ref]@{***x11}
lb34

LB69



VM
echo "aligning particles to reference"
; do the alignment
AP MQ
[ref]@***    ; template for reference image
selref                  ; file containing list of reference files
(x95,1)                 ; translational search range, step size
x97,x96                 ; first & last ring
[aliold]@******          ; stack containing images to be aligned
select                  ; list of particles for alignment
apmq{**x92}   ; output angles

VM
echo "creating new aligned stack"
;rotate and shift images according to the parameters from AP MQ alignment
LB68

IQ FI,x20
  apmqSUM{**x91}
  IF (x20.eq.1) GOTO LB25

IQ FI,x19
  apmq{**x91}

  IF (x19.eq.1) GOTO LB24

GOTO LB27

LB24

DO LB11 x11=1,x99
  ; Format of the transformation parameters doc file is:
  ;       angle, Sx, Sy, 0-1 flag for Y-mirror (0-no mirror; 1-mirror)
  UD IC,x11,x41,x42,x43,x44,x45,x46
  apmq{**x92}
  do lb26,x12=1,x99     
     UD IC x12,x61,x62,x63,x64,x65,x66
      apmq{**x91}
      IF(x66.ne.x46)goto lb26
     SA P x73,x74,x75
     x63,x64,x65
     x43,x44,x45
     SD x11,x73,x74,x75,x46
     apmqSUM{**x92}
    lb26
  IF (x41.gt.0) THEN
    RT SQ
    [rawparticles]@{****x46}
    [alinew]@{****x46}
    x73
    x74,x75
  ELSE
    RT SQ
    [rawparticles]@{****x46}
    _1
    x73
    x74,x75
    MR
    _1
    [alinew]@{****x46}
    y
  ENDIF
  DE
  _1
LB11
GOTO LB88

LB25
DO LB18, x11=1,x99
  UD IC,x11,x41,x42,x43,x44,x45,x46
  apmq{**x92}
  do lb28, x12=1,x99
      UD IC x12,x63,x64,x65,x66
      apmqSUM{**x91}
      IF (x66.ne.x46)goto lb28
      SA P x73,x74,x75
      x63,x64,x65
      x43,x44,x45
      SD x11,x73,x74,x75,x46,x41
      apmqSUM{**x92}
  lb28
  IF (x41.gt.0) THEN
    RT SQ
    [rawparticles]@{****x46}
    [alinew]@{****x46}
    x73
    x74,x75
  ELSE
    RT SQ
    [rawparticles]@{****x46}
    _1
    x73
    x74,x75
    MR
    _1
    [alinew]@{****x46}
    y
  ENDIF
  DE
  _1
LB18
GOTO LB88

LB27
DO LB19, x11=1,x99
  UD IC,x11,x41,x42,x43,x44,x45,x46
   apmq{**x92}

  IF (x41.gt.0) THEN
    RT SQ
    [rawparticles]@{****x46}
    [alinew]@{****x46}
    x43
    x44,x45
  ELSE
    RT SQ
    [rawparticles]@{****x46}
    _1
    x43
    x44,x45
    MR
    _1
    [alinew]@{****x46}
    y
  ENDIF
DE
_1
LB19

LB88

do LB12,x11=1,x98
  x17=0
  do lb13, x15=1,x99
  ud ic,x15,x41,x42,x43,x44,x45,x46
  apmq{**x92}
  x16=abs(x41)
  IF (x16.eq.x11) THEN
    x17=x17+1
    sd x17,x46,x41
    [refselect]{***x11}
  ENDIF
  lb13
LB12


UD ICE
apmq{**x92}
UD ICE
apmq{**x91}
UD ICE
apmqSUM{**x91}
UD ICE
apmqSUM{**X92}



VM
echo "creating resulting template(s)"

x94=x92+1

do lb35, x33=1,x98
AS R
[alinew]@******        ; input file name
[refselect]{***x33}                 ; list of particles to use
A                       ; all images will be added
{**x92}avgali@{***x33}    ; new refined reference
{**x92}varali@{***x33}    ; new refined variance



IF (x93.gt.1) THEN
  VM
  echo "applying c{**x93} symmetry"

  CP
  {**x92}avgali@{***x33}
  {**x92}avgali_nosym@{***x33}

  CP
  {**x92}varali@{***x33}
  {**x92}varali_nosym@{***x33}
  
  SY DOC
  sym
  C
  x93
    
  DO LB3 x11=1,x93
    UD IC,x11,x12,x12,x13
    sym
      
    ; create a stack containing all rotated orientations
    RT
    {**x92}avgali@{***x33}
    {**x92}symmetrize@{***x33}@{**x11}
    x13

    ; average them together
    AS
    {**x92}symmetrize@{***x33}@**
    (1-x93)
    A
    {**x92}avgali@{***x33}
    {**x92}varali@{***x33}
  LB3
    
  UD ICE
  sym

  ;cleanup symmetry stuff

  DE
  symmetrize
  DE
  sym


ENDIF
  
VM
echo "computing the resolution for class{%F5.0%x33}"
; get the resolution
AS R
[alinew]@******        ; input file name
[refselect]{***x33}                 ; list of particles to use
O                       ; 2 sub-averages will be calculated, one for odd, one for even
rff/{**x92}avgodd@{***x33}    ; file receiving odd average
rff/{**x92}varodd@{***x33}    ; file receiving odd variance
rff/{**x92}avgeven@{***x33}   ; file receiving even average
rff/{**x92}vareven@{***x33}   ; file receiving even variance

; computes fourier shell coefficient
RF
rff/{**x92}avgodd@{***x33}    ; first file
rff/{**x92}avgeven@{***x33}   ; second file
(0.5)     ; ring width
(0.2,2)   ; scale factor (lower, upper)
rff/{**x92}rff{***x33}       ; output file

LB35

DE A
refselect/{**x91}refselect001

DE A
rff/{**x91}avgodd

DE A
rff/{**x91}avgeven

DE A
rff/{**x91}varodd

DE A
rff/{**x91}vareven

DE A
rff/{**x91}rff001

DE A
{**x91}varali

DE 
aligned{**x91}

DE
apmqSUM{**x91}
 
IF(x91.eq.0) THEN
DE 
{**x91}[ref]
ENDIF

IF(x93.gt.1) THEN
DE 
{**x91}varali_nosym
DE
{**x91}symmetrize
ENDIF

EN D


