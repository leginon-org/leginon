; reference-based alignment with the reference refinement

x99=8026  ; number of particles
x98=1     ; number of reference images
x97=5     ; first ring for rotational alignment
x96=36    ; last ring for rotational alignment
x95=6     ; translational search range (in pixels)
x93=6     ; c-symmetry (rotational symmetry to be applied, 1 if none)

; last ring + translational search range MUST be < (box size/2)-1
FR G ; stack file
[stack]start

FR G ; aligned file
[aligned]aligned

FR G ; starting reference
[ref]reference

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

CP
[ref]@1
ref001

VM
echo "aligning particles to reference"
; do the alignment
AP MQ
ref***    ; template for reference image
selref                  ; file containing list of reference files
(x95,1)                 ; translational search range, step size
x97,x96                 ; first & last ring
[stack]@******          ; stack containing images to be aligned
select                  ; list of particles for alignment
apmq   ; output angles

VM
echo "creating new aligned stack"
;rotate and shift images according to the parameters from AP MQ alignment

DO LB11 x11=1,x99
  ; Format of the transformation parameters doc file is:
  ;       angle, Sx, Sy, 0-1 flag for Y-mirror (0-no mirror; 1-mirror)
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
LB11

DE
_1

UD ICE
apmq

VM
echo "creating resulting template"
; get the refined reference
AS R
[aligned]@******        ; input file name
(1-x99)                 ; list of particles to use
A                       ; all images will be added
refali001    ; new refined reference
varali001    ; new refined variance

IF (x93.gt.1) THEN
  VM
  echo "applying c{**x93} symmetry"

  CP
  refali001
  refali001_nosym

  CP
  varali001
  varali001_nosym

  SY DOC
  sym
  C
  x93
    
  DO LB3 x11=1,x93
    UD IC,x11,x12,x12,x13
    sym
      
    ; create a stack containing all rotated orientations
    RT
    refali001
    symmetrize@{**x11}
    x13

    ; average them together
    AS
    symmetrize@**
    (1-x93)
    A
    refali001
    varali001
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
echo "computing the resolution"
; get the resolution
AS R
[aligned]@******        ; input file name
(1-x99)                 ; list of particles to use
O                       ; 2 sub-averages will be calculated, one for odd, one for even
avgodd    ; file receiving odd average
varodd    ; file receiving odd variance
avgeven   ; file receiving even average
vareven   ; file receiving even variance

; computes fourier shell coefficient
RF
avgodd    ; first file
avgeven   ; second file
(0.5)     ; ring width
(0.2,2)   ; scale factor (lower, upper)
rff       ; output file
  
LB5

EN D

