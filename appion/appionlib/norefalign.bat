; Reference free class alignment
; must have centered & rotationally averaged image saved as tmplt001.spi
; if the reference-free alignment has already been performed, and
; an aligned stack has been written out, the alignment step is skipped.

MD ; verbose off in spider log file
VB OFF

x99=3000  ; number of particles in stack
x98=128   ; box size
x97=45    ; expected diameter of particle (in pixels)
x96=5     ; first ring radii
x95=62    ; last ring radii
x94=50    ; mask radius (in pixels)
x93=40    ; desired # of classes (will get as close to this # as possible)
x92=10    ; additive constant for hierarchical clustering

FR G ; stack file
[stack]start

FR G ; aligned stack file
[aligned]aligned

FR G ; template used to center the image
[tmplt]template

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

FR G ; where to write class lists
[clhc_cls]classes/clhc_cls

FR G ; where to write alignment data
[ali]alignment/

FR G ; where to write coran data
[corandir]coran/

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; skip over previously done sections ;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

IQ FI x11
[aligned]

IF (x11.EQ.1) THEN GOTO LB11

CP
[tmplt]@1
_9

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; REFERENCE-FREE ALIGNMENT                                                ;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

VM
echo "Performing reference-free alignment"

VM
rm -rf alignment
VM
mkdir alignment

AP SR        ; reference-free alignment of an image series
[stack]@*****      ; stack to align
1-x99        ; particles in stack to use
x97          ; expected size of the particle (in pixels
x96,x95      ; first and last ring radii
_9           ; image used to center the average
[ali]avg***  ; file containing averages
[ali]prm***  ; output parameter file


; Find out the number of outputs from AP SR
DO LB5 x11=1,999
  IQ FI x12     ; check if file exists
  [ali]prm{***x11}
  IF (x12.EQ.0) GOTO LB6
LB5
LB6

x45 = x11-1  ; number of parameter files

VM
echo "  writing out aligned stack"

; write out aligned stack
DO LB10 x11=1,x99
  UD IC,x11,x21,x22,x23
  [ali]prm{***x45}

  RT SQ        ; rotate and shift the raw data
  [stack]@{*****x11}
  [aligned]@{*****x11}
  x21          ; rotation angle, scale
  x22,x23      ; x, y shift
LB10

UD ICE ; close inline file
[ali]prm{***x45}


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; create the sequential file and then use that file and do a hierarchical ;;
;; clustering. Run clhd and clhe to classify the particles into different  ;;
;; groups.                                                                 ;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;LB11

DE
_9 

VM
echo "  making template file"

MO      ; make mask template
_9      ; save template in memory
x98,x98 ; box size
c       ; circle
x94     ; radius of mask


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; CORRESPONDENCE ANALYSIS                                                 ;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

VM
echo "Performing correspondence analysis (long wait)"

VM
rm -rf coran
VM
mkdir coran


CA S            ; do correspondence analysis
[aligned]@***** ; aligned stack
1-x99           ; particles to use
_9              ; mask file
20              ; number of factors to be used
C               ; Coran analysis
x92             ; additive constant (since coran can't have negative values)
[corandir]coran ; output file prefix

DO LB14 x11=1,20
	CA SRE
	[corandir]coran
	x11
	[corandir]eigenimg@{***x11}
LB14


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; CLUSTERING                                                              ;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;


VM
echo "Performing hierarchical clustering"
VM
echo "  clustering..."

CL HC          ; do hierarchical clustering
[corandir]coran_IMC ; coran image factor coordinate file
1-3            ; factor numbers to be included in clustering algorithm
1.00           ; factor weights 
1.00           ; for each factor number
1.00
5              ; use Ward's method
Y              ; make a postscript of dendogram
[corandir]clhc.ps   ; dendogram image file
Y              ; save dendogram doc file
[corandir]clhc_doc  ; dendogram doc file
 
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Determine the cutoff for the desired number of classes ;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

LB11

VM
echo "  determining threshold cutoff for number of classes"

x20 = 0.5   ; initial threshold cutoff
x21 = (x20/2) ; initial increment for determining threshold

DO LB13 x11=0,100
  x13=x20 ; set the threshold

  DE
  tmpclhc_classes

  CL HD
  x13             ; threshold value
  [corandir]clhc_doc   ; dendogram file 
  tmpclhc_classes ; classes files
  
  UD N,x12        ; get number of determined classes
  tmpclhc_classes

  IF (x12.EQ.x93) GOTO LB15     ; found threshold for # of classes
  IF (x12.GT.x93) x20=(x20+x21) ; too many classes: increase threshold
  IF (x12.LE.x93) x20=(x20-x21) ; too few classes: decrease threshold
  x21=(x21/2)                   ; decrease threshold increment
LB13

DE
tmpclhc_classes

VM
echo "  could not be reached, increase # of possible classes"
EN D

LB15

DE
tmpclhc_classes

VM
rm -rf classes
VM
rm -f classes_avg.spi
VM
rm -f classes_var.spi
VM
mkdir classes

VM
echo "  creating {%F5.1%x12} classes using a threshold of {%F7.5%x13}"
CL HE         ; generate doc files containing particle numbers for classes
x13           ; threshold (closer to 0=more classes)
[corandir]clhc_doc      ; dendogram doc file
[clhc_cls]****  ; selection doc file that will contain # of objects for classes

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; average aligned particles together ;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

VM
echo "  averaging particles into classes"

DO LB20 x81=1,x12
  AS R
  [aligned]@*****
  [clhc_cls]{****x81}
  A
  classes_avg@{****x81}
  classes_var@{****x81}
LB20
 
EN D
