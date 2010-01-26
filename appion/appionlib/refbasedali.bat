; reference-based alignment with the reference refinement

x99=500   ; number of particles
x98=3     ; number of reference images
x97=25    ; first ring for rotational alignment
x96=55    ; last ring for rotational alignment
x95=6     ; translational search range (in pixels)
x93=1     ; c-symmetry (rotational symmetry to be applied, 1 if none)
x92=4     ; iteration number
x37=0     ; last ring + translational search range MUST be < (box size/2)-1

VM
echo "running iteration {**x92}"

FR G ; stack file
[stack]start
FR G
[aligned]aligned
FR G
[alistack]aligned
FR G
[prevaliparams]apmq
FR G
[ref]reference
; create the selection document file.
; The image series is consecutive

DOC CREATE
select
1
1-x99

IF (x92.ne.1) GOTO LB27		;for the first iteration
  DOC CREATE			;create ref selection file for all templates	
  selref
  1
  1-x98
  FR G				
  [refstack]refstack
  DO LB34, x11=1,x98		;copy references into a stack
    CP
    [ref]{***x11}
    [refstack]@{***x11}
  LB34
GOTO LB25

LB27				;for iterations after 1st:

  FR G
  [refstack][ref]
  DO LB39,x11=1,x98		
    IQ FI x39
    [refstack]@{***x11}
    IF (x39.eq.1) THEN
      x37=x37+1	      
      SD x37,x11		;write ref selection file for only valid templates
      selref
    ENDIF
  LB39
	
LB25

VM
mkdir -p rff/

VM
mkdir -p refselect/


VM
echo "  aligning particles to reference"

VM
echo "  ** may crash if no particles align to a template"

; do the alignment
AP MQ
[refstack]@***    ; template for reference image
selref            ; file containing list of reference files
(x95,1)           ; translational search range, step size
x97,x96           ; first & last ring
[alistack]@****** ; stack containing images to be aligned
select            ; list of particles for alignment
apmq			      ; output angles

VM
echo "  creating new aligned stack"
;rotate and shift images according to the parameters from AP MQ alignment

;if it is the first iteration proceed to RT SQ function
if(x92.eq.1) GOTO LB23

;if it is the 2nd iteration, get paramaters from previous iteration
if(x92.eq.2) GOTO LB24

GOTO LB29

LB23

DO LB19, x11=1,x99
  UD IC,x11,x41,x42,x43,x44,x45,x46
   apmq
  
  IF (x41.gt.0) THEN
    RT SQ
    [stack]@{****x46}
    [aligned]@{****x46}
    x43
    x44,x45
  ELSE
    RT SQ
    [stack]@{****x46}
    _1
    x43
    x44,x45  
    MR
    _1
    [aligned]@{****x46}
    y 
  ENDIF
DE  
_1  
LB19
GOTO LB88

LB24
DO LB11 x11=1,x99
  ; Format of the transformation parameters doc file is:
  ;       angle, Sx, Sy, 0-1 flag for Y-mirror (0-no mirror; 1-mirror)
  UD IC,x11,x41,x42,x43,x44,x45,x46
  apmq

  do lb26,x12=1,x99     
     UD IC x12,x61,x62,x63,x64,x65,x66
      [prevaliparams]
      IF(x66.ne.x46)goto lb26
     SA P x73,x74,x75
     x63,x64,x65
     x43,x44,x45
     SD x11,x73,x74,x75,x46
     apmqSUM
    lb26
  IF (x41.gt.0) THEN
    RT SQ
    [stack]@{****x46}
    [aligned]@{****x46}
    x73
    x74,x75
  ELSE
    RT SQ
    [stack]@{****x46}
    _1
    x73
    x74,x75
    MR
    _1
    [aligned]@{****x46}
    y
  ENDIF
  DE
  _1
LB11
GOTO LB88

LB29
DO LB18, x11=1,x99
  UD IC,x11,x41,x42,x43,x44,x45,x46
  apmq
  do lb28, x12=1,x99
      UD IC x12,x63,x64,x65,x66
      [prevaliparams]
      IF (x66.ne.x46)goto lb28
      SA P x73,x74,x75
      x63,x64,x65
      x43,x44,x45
      SD x11,x73,x74,x75,x46,x41
      apmqSUM
  lb28
  IF (x41.gt.0) THEN
    RT SQ
    [stack]@{****x46}
    [aligned]@{****x46}
    x73
    x74,x75
  ELSE
    RT SQ
    [stack]@{****x46}
    _1
    x73
    x74,x75
    MR
    _1
    [aligned]@{****x46}
    y
  ENDIF
  DE
  _1
LB18

LB88
do LB12,x11=1,x98
  x17=0
  do lb13, x15=1,x99
  ud ic,x15,x41,x42,x43,x44,x45,x46
  apmq
  x16=abs(x41)
  IF (x16.eq.x11) THEN
    x17=x17+1
    sd x17,x46,x41
    refselect/refselect{***x11}
  ENDIF
  lb13
LB12


UD ICE
apmq
UD ICE
[prevaliparams]
UD ICE



VM
echo "  creating resulting template(s)"



do lb35, x33=1,x98

IQ FI x34				   ;check to see if selection file exists	
refselect/refselect{***x33}

IF (x34.eq.0) GOTO LB35			   ;if no selection file, cycle	

AS R
[aligned]@******        		    ; input file name
refselect/refselect{***x33}                 ; list of particles to use
A                       		    ; all images will be added
refali@{***x33}    			    ; new refined reference
varali@{***x33}    			    ; new refined variance



IF (x93.gt.1) THEN
  VM
  echo "  applying c{**x93} symmetry"

  CP
  refali@{***x33}
  refali_nosym@{***x33}

  CP
  varali@{***x33}
  varali_nosym@{***x33}
  
  SY DOC
  sym
  C
  x93
    
  DO LB3 x11=1,x93
    UD IC,x11,x12,x12,x13
    sym
      
    ; create a stack containing all rotated orientations
    RT
    refali@{***x33}
    symmetrize@{***x33}@{**x11}
    x13

    ; average them together
    AS
    symmetrize@{***x33}@**
    (1-x93)
    A
    refali@{***x33}
    varali@{***x33}
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
echo "  computing the resolution for class {***x33}"
; get the resolution
AS R
[aligned]@******             ; input file name
refselect/refselect{***x33}  ; list of particles to use
O                            ; 2 sub-averages will be calculated, one for odd, one for even
rff/avgodd@{***x33}          ; file receiving odd average
rff/varodd@{***x33}          ; file receiving odd variance
rff/avgeven@{***x33}         ; file receiving even average
rff/vareven@{***x33}         ; file receiving even variance

; computes fourier shell coefficient
RF
rff/avgodd@{***x33}  ; first file
rff/avgeven@{***x33} ; second file
(0.5)                ; ring width
(0.2,2)              ; scale factor (lower, upper)
rff/rff{***x33}      ; output file

LB35


EN D


