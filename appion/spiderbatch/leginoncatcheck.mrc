; 20061103 leginon doc compare
; to compare list of leginon frames with handpicmics category file
; useful for checking for redundancy and absence of files from these docs
;
; notes to make leginon list file ...this template must be tailored to specific fields and characters
; ls -1 /ami/data01/leginon/06mar14a/rawdata/*en.mrc | cut -d'_' -f2 | cut -c1-5 > mics/leginongr.mrc
; ls -1 /ami/data01/leginon/06mar14a/rawdata/*en.mrc | cut -d'_' -f3 | cut -c1-5 > mics/leginonsq.mrc
; ls -1 /ami/data01/leginon/06mar14a/rawdata/*en.mrc | cut -d'_' -f4 | cut -c1-5 > mics/leginonhl.mrc
; ls -1 /ami/data01/leginon/06mar14a/rawdata/*en.mrc | cut -d'_' -f5 | cut -c1-5 > mics/leginonen.mrc
; paste -d' ' mics/leginongr.mrc mics/leginonsq.mrc mics/leginonhl.mrc mics/leginonen.mrc \
; | nl -s '  4 ' > mics/leginondoc.mrc
; WARNING THIS NO LONGER WORKS SINCE "_" NO LONGER DELIMITS GR SQ HL AND EN
; USE IMAGE ASSESSOR INSTEAD

MD
VB OFF

FR
?IN.LIST OF LEGINON FRAMES (dir/doc has 4 registers)?<leginon>
FR
?IN.LIST WITH CATEGORIES (dir/handpicmics has 5 registers)?<category>
; ~~~~~ start ~~~~~
UD N x21
<leginon>

UD N x22
<category>

;IF LEGINON LIST IS LONGER
IF(x21.gt.x22)THEN
x23=x21-x22
VM
echo CATEGORY LIST LACKS {%F7.1%x23} LINES...FIND MISSING FILE NAMES
; x24=x22 ; loops to perform
ENDIF

;IF LEGINON LIST IS SHORTER OR EQUAL LENGTH
IF(x21.lt.x22)THEN
x23=x22-x21
VM
echo LEGINON LIST LACKS {%F7.1%x23} LINES...FIND MISSING FILE NAMES
; x24=x21 ; loops to perform
ENDIF
IF(x21.eq.x22)THEN
VM
echo DOCS HAVE SAME NUMBER OF FILES...CHECK TO BE SURE SAME FILE NAMES
; x24=x21 ; loops to perform
ENDIF

x25=0 ; not found file counter
; FOR EACH ITEM IN LEGINON LIST
DO LB1 x11=1,x21
UD IC x11,x31,x32,x33,x34
<leginon> 

x26=0 ; found particle index
; FIND ITEM IN CATEGORY LIST
DO LB2 x12=1,x22
UD IC x12,x40,x41,x42,x43,x44
<category>

IF(x31.eq.x41)THEN ;GR
 IF(x32.eq.x42)THEN ;SQ
  IF(x33.eq.x43)THEN ;HL
   IF(x34.eq.x44)THEN ;EN
    IF(x26.gt.0)THEN; SCANNING FOR REDUNDANT ENTRIES
VM
echo {*****x41}gr_{*****x42}sq_{*****x43}hl_{*****x44}en FOUND AGAIN IN CATEGORY LIST LINE {%F7.1%x12}
    ENDIF
x26=1; FILE IS IN BOTH DOCS
   ENDIF
  ENDIF
 ENDIF
ENDIF

LB2 ; next category list entry x12

IF(x26.eq.0)THEN ; FILE NOT FOUND IN CATEGORY DOC
x25=x25+1
VM
echo {*****x31}gr_{*****x32}sq_{*****x33}hl_{*****x34}en MISSING FROM CATEGORY LIST
ENDIF

LB1 ; next leginon list entry x11

;;;;;;;;;;;;;
x27=0 ; not found file counter
; FOR EACH ITEM IN CATEGORY LIST
DO LB3 x13=1,x22
UD IC x13,x40,x41,x42,x43,x44
<category>

x26=0 ; found particle index
; FIND ITEM IN LEGINON LIST
DO LB4 x14=1,x21
UD IC x14,x31,x32,x33,x34
<leginon> 

IF(x31.eq.x41)THEN ;GR
 IF(x32.eq.x42)THEN ;SQ
  IF(x33.eq.x43)THEN ;HL
   IF(x34.eq.x44)THEN ;EN
    IF(x26.gt.0)THEN; SCANNING FOR REDUNDANT ENTRIES
VM
echo {*****x41}gr_{*****x42}sq_{*****x43}hl_{*****x44}en FOUND AGAIN IN LEGINON LIST LINE {%F7.1%x14}
    ENDIF
x26=1; FILE IS IN BOTH DOCS
   ENDIF
  ENDIF
 ENDIF
ENDIF

LB4 ; next leginon list entry x14

IF(x26.eq.0)THEN ; FILE NOT FOUND IN LEGINONDOC
x27=x27+1
VM
echo {*****x41}gr_{*****x42}sq_{*****x43}hl_{*****x44}en MISSING FROM LEGINON LIST
ENDIF

LB3 ; next category list entry x13

UD ICE
<leginon>
UD ICE
<category>

RE

