/*----------------------------------------------------------------------------*
*
*  imagicio.c  -  imageio: imagic files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "imagicio.h"
#include "imageiocommon.h"
#include "exception.h"
#include "baselib.h"


/* header layout

  nr offs size  type name
   0    0    4  int32_t imn
   1    4    4  int32_t ifol
   2    8    4  int32_t ierror
   3   12    4  int32_t nblocks
   4   16    4  int32_t nday
   5   20    4  int32_t nmonth
   6   24    4  int32_t nyear
   7   28    4  int32_t nhour
   8   32    4  int32_t nminut
   9   36    4  int32_t nsec
  10   40    4  int32_t rsize
  11   44    4  int32_t izold
  12   48    4  int32_t ixlp
  13   52    4  int32_t iylp
  14   56    4  char type[4]
  15   60    4  int32_t ixold
  16   64    4  int32_t iyold
  17   68    4  Real32 avdens
  18   72    4  Real32 sigma
  19   76    4  Real32 user1
  20   80    4  Real32 user2
  21   84    4  Real32 densmax
  22   88    4  Real32 densmin
  23   92    4  int32_t cmplx
  24   96    4  Real32 defocus1
  25  100    4  Real32 defocus2
  26  104    4  Real32 defangle
  27  108    4  Real32 sinostrt
  28  112    4  Real32 sinoend
  29  116   80  char name[80]
  30  196    4  Real32 ccc3d
  31  200    4  int32_t ref3d
  32  204    4  int32_t mident
  33  208    4  int32_t ezshift
  34  212    4  Real32 ealpha
  35  216    4  Real32 ebeta
  36  220    4  Real32 egamma
  37  224    4  int32_t ref3dold
  38  228    4  int32_t active
  39  232    4  int32_t nalisum
  40  236    4  int32_t pgroup
  41  240    4  int32_t izlp
  42  244    4  int32_t i4lp
  43  248    4  int32_t i5lp
  44  252    4  int32_t i6lp
  45  256    4  Real32 alpha
  46  260    4  Real32 beta
  47  264    4  Real32 gamma
  48  268    4  int32_t imavers
  49  272    4  int32_t realtype
  50  276  116  int32_t bufvar[29]
  51  392    4  int32_t ronly
  52  396    4  Real32 angle
  53  400    4  Real32 voltage
  54  404    4  Real32 spaberr
  55  408    4  Real32 focdist
  56  412    4  Real32 ccc
  57  416    4  Real32 errar
  58  420    4  Real32 err3d
  59  424    4  int32_t ref
  60  428    4  Real32 classno
  61  432    4  Real32 locold
  62  436    4  Real32 repqual
  63  440    4  Real32 zshift
  64  444    4  Real32 xshift
  65  448    4  Real32 yshift
  66  452    4  Real32 numcls
  67  456    4  Real32 ovqual
  68  460    4  Real32 eangle
  69  464    4  Real32 exshift
  70  468    4  Real32 eyshift
  71  472    4  Real32 cmtotvar
  72  476    4  Real32 informat
  73  480    4  int32_t numeigen
  74  484    4  int32_t niactive
  75  488    4  Real32 resol
  76  492    4  Real32 reserved124
  77  496    4  Real32 reserved125
  78  500    4  Real32 alpha2
  79  504    4  Real32 beta2
  80  508    4  Real32 gamma2
  81  512    4  Real32 nmetric
  82  516    4  Real32 actmsa
  83  520  276  Real32 coosmsa[69]
  84  796  228  char history[228]
  85      1024  ImagicHdr
*/


/* functions */

static void ImagicHeaderPack
            (ImagicHeader *hdr)

{
  char *f,*h=(char *)hdr;

  f=(char *)&hdr->imn;
  if (f != h+0) { h[0]=f[0]; h[1]=f[1]; h[2]=f[2]; h[3]=f[3]; }

  f=(char *)&hdr->ifol;
  if (f != h+4) { h[4]=f[0]; h[5]=f[1]; h[6]=f[2]; h[7]=f[3]; }

  f=(char *)&hdr->ierror;
  if (f != h+8) { h[8]=f[0]; h[9]=f[1]; h[10]=f[2]; h[11]=f[3]; }

  f=(char *)&hdr->nblocks;
  if (f != h+12) { h[12]=f[0]; h[13]=f[1]; h[14]=f[2]; h[15]=f[3]; }

  f=(char *)&hdr->nday;
  if (f != h+16) { h[16]=f[0]; h[17]=f[1]; h[18]=f[2]; h[19]=f[3]; }

  f=(char *)&hdr->nmonth;
  if (f != h+20) { h[20]=f[0]; h[21]=f[1]; h[22]=f[2]; h[23]=f[3]; }

  f=(char *)&hdr->nyear;
  if (f != h+24) { h[24]=f[0]; h[25]=f[1]; h[26]=f[2]; h[27]=f[3]; }

  f=(char *)&hdr->nhour;
  if (f != h+28) { h[28]=f[0]; h[29]=f[1]; h[30]=f[2]; h[31]=f[3]; }

  f=(char *)&hdr->nminut;
  if (f != h+32) { h[32]=f[0]; h[33]=f[1]; h[34]=f[2]; h[35]=f[3]; }

  f=(char *)&hdr->nsec;
  if (f != h+36) { h[36]=f[0]; h[37]=f[1]; h[38]=f[2]; h[39]=f[3]; }

  f=(char *)&hdr->rsize;
  if (f != h+40) { h[40]=f[0]; h[41]=f[1]; h[42]=f[2]; h[43]=f[3]; }

  f=(char *)&hdr->izold;
  if (f != h+44) { h[44]=f[0]; h[45]=f[1]; h[46]=f[2]; h[47]=f[3]; }

  f=(char *)&hdr->ixlp;
  if (f != h+48) { h[48]=f[0]; h[49]=f[1]; h[50]=f[2]; h[51]=f[3]; }

  f=(char *)&hdr->iylp;
  if (f != h+52) { h[52]=f[0]; h[53]=f[1]; h[54]=f[2]; h[55]=f[3]; }

  f=(char *)hdr->type;
  if (f != h+56) { h[56]=f[0]; h[57]=f[1]; h[58]=f[2]; h[59]=f[3]; }

  f=(char *)&hdr->ixold;
  if (f != h+60) { h[60]=f[0]; h[61]=f[1]; h[62]=f[2]; h[63]=f[3]; }

  f=(char *)&hdr->iyold;
  if (f != h+64) { h[64]=f[0]; h[65]=f[1]; h[66]=f[2]; h[67]=f[3]; }

  f=(char *)&hdr->avdens;
  if (f != h+68) { h[68]=f[0]; h[69]=f[1]; h[70]=f[2]; h[71]=f[3]; }

  f=(char *)&hdr->sigma;
  if (f != h+72) { h[72]=f[0]; h[73]=f[1]; h[74]=f[2]; h[75]=f[3]; }

  f=(char *)&hdr->user1;
  if (f != h+76) { h[76]=f[0]; h[77]=f[1]; h[78]=f[2]; h[79]=f[3]; }

  f=(char *)&hdr->user2;
  if (f != h+80) { h[80]=f[0]; h[81]=f[1]; h[82]=f[2]; h[83]=f[3]; }

  f=(char *)&hdr->densmax;
  if (f != h+84) { h[84]=f[0]; h[85]=f[1]; h[86]=f[2]; h[87]=f[3]; }

  f=(char *)&hdr->densmin;
  if (f != h+88) { h[88]=f[0]; h[89]=f[1]; h[90]=f[2]; h[91]=f[3]; }

  f=(char *)&hdr->cmplx;
  if (f != h+92) { h[92]=f[0]; h[93]=f[1]; h[94]=f[2]; h[95]=f[3]; }

  f=(char *)&hdr->defocus1;
  if (f != h+96) { h[96]=f[0]; h[97]=f[1]; h[98]=f[2]; h[99]=f[3]; }

  f=(char *)&hdr->defocus2;
  if (f != h+100) { h[100]=f[0]; h[101]=f[1]; h[102]=f[2]; h[103]=f[3]; }

  f=(char *)&hdr->defangle;
  if (f != h+104) { h[104]=f[0]; h[105]=f[1]; h[106]=f[2]; h[107]=f[3]; }

  f=(char *)&hdr->sinostrt;
  if (f != h+108) { h[108]=f[0]; h[109]=f[1]; h[110]=f[2]; h[111]=f[3]; }

  f=(char *)&hdr->sinoend;
  if (f != h+112) { h[112]=f[0]; h[113]=f[1]; h[114]=f[2]; h[115]=f[3]; }

  f=(char *)hdr->name;
  if (f != h+116) { size_t i=0; while (i < 80) { h[i+116]=f[i]; i++; } }

  f=(char *)&hdr->ccc3d;
  if (f != h+196) { h[196]=f[0]; h[197]=f[1]; h[198]=f[2]; h[199]=f[3]; }

  f=(char *)&hdr->ref3d;
  if (f != h+200) { h[200]=f[0]; h[201]=f[1]; h[202]=f[2]; h[203]=f[3]; }

  f=(char *)&hdr->mident;
  if (f != h+204) { h[204]=f[0]; h[205]=f[1]; h[206]=f[2]; h[207]=f[3]; }

  f=(char *)&hdr->ezshift;
  if (f != h+208) { h[208]=f[0]; h[209]=f[1]; h[210]=f[2]; h[211]=f[3]; }

  f=(char *)&hdr->ealpha;
  if (f != h+212) { h[212]=f[0]; h[213]=f[1]; h[214]=f[2]; h[215]=f[3]; }

  f=(char *)&hdr->ebeta;
  if (f != h+216) { h[216]=f[0]; h[217]=f[1]; h[218]=f[2]; h[219]=f[3]; }

  f=(char *)&hdr->egamma;
  if (f != h+220) { h[220]=f[0]; h[221]=f[1]; h[222]=f[2]; h[223]=f[3]; }

  f=(char *)&hdr->ref3dold;
  if (f != h+224) { h[224]=f[0]; h[225]=f[1]; h[226]=f[2]; h[227]=f[3]; }

  f=(char *)&hdr->active;
  if (f != h+228) { h[228]=f[0]; h[229]=f[1]; h[230]=f[2]; h[231]=f[3]; }

  f=(char *)&hdr->nalisum;
  if (f != h+232) { h[232]=f[0]; h[233]=f[1]; h[234]=f[2]; h[235]=f[3]; }

  f=(char *)&hdr->pgroup;
  if (f != h+236) { h[236]=f[0]; h[237]=f[1]; h[238]=f[2]; h[239]=f[3]; }

  f=(char *)&hdr->izlp;
  if (f != h+240) { h[240]=f[0]; h[241]=f[1]; h[242]=f[2]; h[243]=f[3]; }

  f=(char *)&hdr->i4lp;
  if (f != h+244) { h[244]=f[0]; h[245]=f[1]; h[246]=f[2]; h[247]=f[3]; }

  f=(char *)&hdr->i5lp;
  if (f != h+248) { h[248]=f[0]; h[249]=f[1]; h[250]=f[2]; h[251]=f[3]; }

  f=(char *)&hdr->i6lp;
  if (f != h+252) { h[252]=f[0]; h[253]=f[1]; h[254]=f[2]; h[255]=f[3]; }

  f=(char *)&hdr->alpha;
  if (f != h+256) { h[256]=f[0]; h[257]=f[1]; h[258]=f[2]; h[259]=f[3]; }

  f=(char *)&hdr->beta;
  if (f != h+260) { h[260]=f[0]; h[261]=f[1]; h[262]=f[2]; h[263]=f[3]; }

  f=(char *)&hdr->gamma;
  if (f != h+264) { h[264]=f[0]; h[265]=f[1]; h[266]=f[2]; h[267]=f[3]; }

  f=(char *)&hdr->imavers;
  if (f != h+268) { h[268]=f[0]; h[269]=f[1]; h[270]=f[2]; h[271]=f[3]; }

  f=(char *)&hdr->realtype;
  if (f != h+272) { h[272]=f[0]; h[273]=f[1]; h[274]=f[2]; h[275]=f[3]; }

  f=(char *)hdr->bufvar;
  if (f != h+276) { size_t i=0; while (i < 120) { h[i+276]=f[i]; i++; } }

  f=(char *)&hdr->angle;
  if (f != h+396) { h[396]=f[0]; h[397]=f[1]; h[398]=f[2]; h[399]=f[3]; }

  f=(char *)&hdr->voltage;
  if (f != h+400) { h[400]=f[0]; h[401]=f[1]; h[402]=f[2]; h[403]=f[3]; }

  f=(char *)&hdr->spaberr;
  if (f != h+404) { h[404]=f[0]; h[405]=f[1]; h[406]=f[2]; h[407]=f[3]; }

  f=(char *)&hdr->focdist;
  if (f != h+408) { h[408]=f[0]; h[409]=f[1]; h[410]=f[2]; h[411]=f[3]; }

  f=(char *)&hdr->ccc;
  if (f != h+412) { h[412]=f[0]; h[413]=f[1]; h[414]=f[2]; h[415]=f[3]; }

  f=(char *)&hdr->errar;
  if (f != h+416) { h[416]=f[0]; h[417]=f[1]; h[418]=f[2]; h[419]=f[3]; }

  f=(char *)&hdr->err3d;
  if (f != h+420) { h[420]=f[0]; h[421]=f[1]; h[422]=f[2]; h[423]=f[3]; }

  f=(char *)&hdr->ref;
  if (f != h+424) { h[424]=f[0]; h[425]=f[1]; h[426]=f[2]; h[427]=f[3]; }

  f=(char *)&hdr->classno;
  if (f != h+428) { h[428]=f[0]; h[429]=f[1]; h[430]=f[2]; h[431]=f[3]; }

  f=(char *)&hdr->locold;
  if (f != h+432) { h[432]=f[0]; h[433]=f[1]; h[434]=f[2]; h[435]=f[3]; }

  f=(char *)&hdr->repqual;
  if (f != h+436) { h[436]=f[0]; h[437]=f[1]; h[438]=f[2]; h[439]=f[3]; }

  f=(char *)&hdr->zshift;
  if (f != h+440) { h[440]=f[0]; h[441]=f[1]; h[442]=f[2]; h[443]=f[3]; }

  f=(char *)&hdr->xshift;
  if (f != h+444) { h[444]=f[0]; h[445]=f[1]; h[446]=f[2]; h[447]=f[3]; }

  f=(char *)&hdr->yshift;
  if (f != h+448) { h[448]=f[0]; h[449]=f[1]; h[450]=f[2]; h[451]=f[3]; }

  f=(char *)&hdr->numcls;
  if (f != h+452) { h[452]=f[0]; h[453]=f[1]; h[454]=f[2]; h[455]=f[3]; }

  f=(char *)&hdr->ovqual;
  if (f != h+456) { h[456]=f[0]; h[457]=f[1]; h[458]=f[2]; h[459]=f[3]; }

  f=(char *)&hdr->eangle;
  if (f != h+460) { h[460]=f[0]; h[461]=f[1]; h[462]=f[2]; h[463]=f[3]; }

  f=(char *)&hdr->exshift;
  if (f != h+464) { h[464]=f[0]; h[465]=f[1]; h[466]=f[2]; h[467]=f[3]; }

  f=(char *)&hdr->eyshift;
  if (f != h+468) { h[468]=f[0]; h[469]=f[1]; h[470]=f[2]; h[471]=f[3]; }

  f=(char *)&hdr->cmtotvar;
  if (f != h+472) { h[472]=f[0]; h[473]=f[1]; h[474]=f[2]; h[475]=f[3]; }

  f=(char *)&hdr->informat;
  if (f != h+476) { h[476]=f[0]; h[477]=f[1]; h[478]=f[2]; h[479]=f[3]; }

  f=(char *)&hdr->numeigen;
  if (f != h+480) { h[480]=f[0]; h[481]=f[1]; h[482]=f[2]; h[483]=f[3]; }

  f=(char *)&hdr->niactive;
  if (f != h+484) { h[484]=f[0]; h[485]=f[1]; h[486]=f[2]; h[487]=f[3]; }

  f=(char *)&hdr->resol;
  if (f != h+488) { h[488]=f[0]; h[489]=f[1]; h[490]=f[2]; h[491]=f[3]; }

  f=(char *)&hdr->reserved124;
  if (f != h+492) { h[492]=f[0]; h[493]=f[1]; h[494]=f[2]; h[495]=f[3]; }

  f=(char *)&hdr->reserved125;
  if (f != h+496) { h[496]=f[0]; h[497]=f[1]; h[498]=f[2]; h[499]=f[3]; }

  f=(char *)&hdr->alpha2;
  if (f != h+500) { h[500]=f[0]; h[501]=f[1]; h[502]=f[2]; h[503]=f[3]; }

  f=(char *)&hdr->beta2;
  if (f != h+504) { h[504]=f[0]; h[505]=f[1]; h[506]=f[2]; h[507]=f[3]; }

  f=(char *)&hdr->gamma2;
  if (f != h+508) { h[508]=f[0]; h[509]=f[1]; h[510]=f[2]; h[511]=f[3]; }

  f=(char *)&hdr->nmetric;
  if (f != h+512) { h[512]=f[0]; h[513]=f[1]; h[514]=f[2]; h[515]=f[3]; }

  f=(char *)&hdr->actmsa;
  if (f != h+516) { h[516]=f[0]; h[517]=f[1]; h[518]=f[2]; h[519]=f[3]; }

  f=(char *)hdr->coosmsa;
  if (f != h+520) { size_t i=0; while (i < 276) { h[i+520]=f[i]; i++; } }

  f=(char *)hdr->history;
  if (f != h+796) { size_t i=0; while (i < 228) { h[i+796]=f[i]; i++; } }

}


static void ImagicHeaderUnpack
            (ImagicHeader *hdr)

{
  char *f,*h=(char *)hdr;

  f=(char *)hdr->history;
  if (f != h+796) { size_t i=228; while (i) { --i; f[i]=h[i+796]; } }

  f=(char *)hdr->coosmsa;
  if (f != h+520) { size_t i=276; while (i) { --i; f[i]=h[i+520]; } }

  f=(char *)&hdr->actmsa;
  if (f != h+516) { f[3]=h[519]; f[2]=h[518]; f[1]=h[517]; f[0]=h[516]; }

  f=(char *)&hdr->nmetric;
  if (f != h+512) { f[3]=h[515]; f[2]=h[514]; f[1]=h[513]; f[0]=h[512]; }

  f=(char *)&hdr->gamma2;
  if (f != h+508) { f[3]=h[511]; f[2]=h[510]; f[1]=h[509]; f[0]=h[508]; }

  f=(char *)&hdr->beta2;
  if (f != h+504) { f[3]=h[507]; f[2]=h[506]; f[1]=h[505]; f[0]=h[504]; }

  f=(char *)&hdr->alpha2;
  if (f != h+500) { f[3]=h[503]; f[2]=h[502]; f[1]=h[501]; f[0]=h[500]; }

  f=(char *)&hdr->reserved125;
  if (f != h+496) { f[3]=h[499]; f[2]=h[498]; f[1]=h[497]; f[0]=h[496]; }

  f=(char *)&hdr->reserved124;
  if (f != h+492) { f[3]=h[495]; f[2]=h[494]; f[1]=h[493]; f[0]=h[492]; }

  f=(char *)&hdr->resol;
  if (f != h+488) { f[3]=h[491]; f[2]=h[490]; f[1]=h[489]; f[0]=h[488]; }

  f=(char *)&hdr->niactive;
  if (f != h+484) { f[3]=h[487]; f[2]=h[486]; f[1]=h[485]; f[0]=h[484]; }

  f=(char *)&hdr->numeigen;
  if (f != h+480) { f[3]=h[483]; f[2]=h[482]; f[1]=h[481]; f[0]=h[480]; }

  f=(char *)&hdr->informat;
  if (f != h+476) { f[3]=h[479]; f[2]=h[478]; f[1]=h[477]; f[0]=h[476]; }

  f=(char *)&hdr->cmtotvar;
  if (f != h+472) { f[3]=h[475]; f[2]=h[474]; f[1]=h[473]; f[0]=h[472]; }

  f=(char *)&hdr->eyshift;
  if (f != h+468) { f[3]=h[471]; f[2]=h[470]; f[1]=h[469]; f[0]=h[468]; }

  f=(char *)&hdr->exshift;
  if (f != h+464) { f[3]=h[467]; f[2]=h[466]; f[1]=h[465]; f[0]=h[464]; }

  f=(char *)&hdr->eangle;
  if (f != h+460) { f[3]=h[463]; f[2]=h[462]; f[1]=h[461]; f[0]=h[460]; }

  f=(char *)&hdr->ovqual;
  if (f != h+456) { f[3]=h[459]; f[2]=h[458]; f[1]=h[457]; f[0]=h[456]; }

  f=(char *)&hdr->numcls;
  if (f != h+452) { f[3]=h[455]; f[2]=h[454]; f[1]=h[453]; f[0]=h[452]; }

  f=(char *)&hdr->yshift;
  if (f != h+448) { f[3]=h[451]; f[2]=h[450]; f[1]=h[449]; f[0]=h[448]; }

  f=(char *)&hdr->xshift;
  if (f != h+444) { f[3]=h[447]; f[2]=h[446]; f[1]=h[445]; f[0]=h[444]; }

  f=(char *)&hdr->zshift;
  if (f != h+440) { f[3]=h[443]; f[2]=h[442]; f[1]=h[441]; f[0]=h[440]; }

  f=(char *)&hdr->repqual;
  if (f != h+436) { f[3]=h[439]; f[2]=h[438]; f[1]=h[437]; f[0]=h[436]; }

  f=(char *)&hdr->locold;
  if (f != h+432) { f[3]=h[435]; f[2]=h[434]; f[1]=h[433]; f[0]=h[432]; }

  f=(char *)&hdr->classno;
  if (f != h+428) { f[3]=h[431]; f[2]=h[430]; f[1]=h[429]; f[0]=h[428]; }

  f=(char *)&hdr->ref;
  if (f != h+424) { f[3]=h[427]; f[2]=h[426]; f[1]=h[425]; f[0]=h[424]; }

  f=(char *)&hdr->err3d;
  if (f != h+420) { f[3]=h[423]; f[2]=h[422]; f[1]=h[421]; f[0]=h[420]; }

  f=(char *)&hdr->errar;
  if (f != h+416) { f[3]=h[419]; f[2]=h[418]; f[1]=h[417]; f[0]=h[416]; }

  f=(char *)&hdr->ccc;
  if (f != h+412) { f[3]=h[415]; f[2]=h[414]; f[1]=h[413]; f[0]=h[412]; }

  f=(char *)&hdr->focdist;
  if (f != h+408) { f[3]=h[411]; f[2]=h[410]; f[1]=h[409]; f[0]=h[408]; }

  f=(char *)&hdr->spaberr;
  if (f != h+404) { f[3]=h[407]; f[2]=h[406]; f[1]=h[405]; f[0]=h[404]; }

  f=(char *)&hdr->voltage;
  if (f != h+400) { f[3]=h[403]; f[2]=h[402]; f[1]=h[401]; f[0]=h[400]; }

  f=(char *)&hdr->angle;
  if (f != h+396) { f[3]=h[399]; f[2]=h[398]; f[1]=h[397]; f[0]=h[396]; }

  f=(char *)hdr->bufvar;
  if (f != h+276) { size_t i=120; while (i) { --i; f[i]=h[i+276]; } }

  f=(char *)&hdr->realtype;
  if (f != h+272) { f[3]=h[275]; f[2]=h[274]; f[1]=h[273]; f[0]=h[272]; }

  f=(char *)&hdr->imavers;
  if (f != h+268) { f[3]=h[271]; f[2]=h[270]; f[1]=h[269]; f[0]=h[268]; }

  f=(char *)&hdr->gamma;
  if (f != h+264) { f[3]=h[267]; f[2]=h[266]; f[1]=h[265]; f[0]=h[264]; }

  f=(char *)&hdr->beta;
  if (f != h+260) { f[3]=h[263]; f[2]=h[262]; f[1]=h[261]; f[0]=h[260]; }

  f=(char *)&hdr->alpha;
  if (f != h+256) { f[3]=h[259]; f[2]=h[258]; f[1]=h[257]; f[0]=h[256]; }

  f=(char *)&hdr->i6lp;
  if (f != h+252) { f[3]=h[255]; f[2]=h[254]; f[1]=h[253]; f[0]=h[252]; }

  f=(char *)&hdr->i5lp;
  if (f != h+248) { f[3]=h[251]; f[2]=h[250]; f[1]=h[249]; f[0]=h[248]; }

  f=(char *)&hdr->i4lp;
  if (f != h+244) { f[3]=h[247]; f[2]=h[246]; f[1]=h[245]; f[0]=h[244]; }

  f=(char *)&hdr->izlp;
  if (f != h+240) { f[3]=h[243]; f[2]=h[242]; f[1]=h[241]; f[0]=h[240]; }

  f=(char *)&hdr->pgroup;
  if (f != h+236) { f[3]=h[239]; f[2]=h[238]; f[1]=h[237]; f[0]=h[236]; }

  f=(char *)&hdr->nalisum;
  if (f != h+232) { f[3]=h[235]; f[2]=h[234]; f[1]=h[233]; f[0]=h[232]; }

  f=(char *)&hdr->active;
  if (f != h+228) { f[3]=h[231]; f[2]=h[230]; f[1]=h[229]; f[0]=h[228]; }

  f=(char *)&hdr->ref3dold;
  if (f != h+224) { f[3]=h[227]; f[2]=h[226]; f[1]=h[225]; f[0]=h[224]; }

  f=(char *)&hdr->egamma;
  if (f != h+220) { f[3]=h[223]; f[2]=h[222]; f[1]=h[221]; f[0]=h[220]; }

  f=(char *)&hdr->ebeta;
  if (f != h+216) { f[3]=h[219]; f[2]=h[218]; f[1]=h[217]; f[0]=h[216]; }

  f=(char *)&hdr->ealpha;
  if (f != h+212) { f[3]=h[215]; f[2]=h[214]; f[1]=h[213]; f[0]=h[212]; }

  f=(char *)&hdr->ezshift;
  if (f != h+208) { f[3]=h[211]; f[2]=h[210]; f[1]=h[209]; f[0]=h[208]; }

  f=(char *)&hdr->mident;
  if (f != h+204) { f[3]=h[207]; f[2]=h[206]; f[1]=h[205]; f[0]=h[204]; }

  f=(char *)&hdr->ref3d;
  if (f != h+200) { f[3]=h[203]; f[2]=h[202]; f[1]=h[201]; f[0]=h[200]; }

  f=(char *)&hdr->ccc3d;
  if (f != h+196) { f[3]=h[199]; f[2]=h[198]; f[1]=h[197]; f[0]=h[196]; }

  f=(char *)hdr->name;
  if (f != h+116) { size_t i=80; while (i) { --i; f[i]=h[i+116]; } }

  f=(char *)&hdr->sinoend;
  if (f != h+112) { f[3]=h[115]; f[2]=h[114]; f[1]=h[113]; f[0]=h[112]; }

  f=(char *)&hdr->sinostrt;
  if (f != h+108) { f[3]=h[111]; f[2]=h[110]; f[1]=h[109]; f[0]=h[108]; }

  f=(char *)&hdr->defangle;
  if (f != h+104) { f[3]=h[107]; f[2]=h[106]; f[1]=h[105]; f[0]=h[104]; }

  f=(char *)&hdr->defocus2;
  if (f != h+100) { f[3]=h[103]; f[2]=h[102]; f[1]=h[101]; f[0]=h[100]; }

  f=(char *)&hdr->defocus1;
  if (f != h+96) { f[3]=h[99]; f[2]=h[98]; f[1]=h[97]; f[0]=h[96]; }

  f=(char *)&hdr->cmplx;
  if (f != h+92) { f[3]=h[95]; f[2]=h[94]; f[1]=h[93]; f[0]=h[92]; }

  f=(char *)&hdr->densmin;
  if (f != h+88) { f[3]=h[91]; f[2]=h[90]; f[1]=h[89]; f[0]=h[88]; }

  f=(char *)&hdr->densmax;
  if (f != h+84) { f[3]=h[87]; f[2]=h[86]; f[1]=h[85]; f[0]=h[84]; }

  f=(char *)&hdr->user2;
  if (f != h+80) { f[3]=h[83]; f[2]=h[82]; f[1]=h[81]; f[0]=h[80]; }

  f=(char *)&hdr->user1;
  if (f != h+76) { f[3]=h[79]; f[2]=h[78]; f[1]=h[77]; f[0]=h[76]; }

  f=(char *)&hdr->sigma;
  if (f != h+72) { f[3]=h[75]; f[2]=h[74]; f[1]=h[73]; f[0]=h[72]; }

  f=(char *)&hdr->avdens;
  if (f != h+68) { f[3]=h[71]; f[2]=h[70]; f[1]=h[69]; f[0]=h[68]; }

  f=(char *)&hdr->iyold;
  if (f != h+64) { f[3]=h[67]; f[2]=h[66]; f[1]=h[65]; f[0]=h[64]; }

  f=(char *)&hdr->ixold;
  if (f != h+60) { f[3]=h[63]; f[2]=h[62]; f[1]=h[61]; f[0]=h[60]; }

  f=(char *)hdr->type;
  if (f != h+56) { f[3]=h[59]; f[2]=h[58]; f[1]=h[57]; f[0]=h[56]; }

  f=(char *)&hdr->iylp;
  if (f != h+52) { f[3]=h[55]; f[2]=h[54]; f[1]=h[53]; f[0]=h[52]; }

  f=(char *)&hdr->ixlp;
  if (f != h+48) { f[3]=h[51]; f[2]=h[50]; f[1]=h[49]; f[0]=h[48]; }

  f=(char *)&hdr->izold;
  if (f != h+44) { f[3]=h[47]; f[2]=h[46]; f[1]=h[45]; f[0]=h[44]; }

  f=(char *)&hdr->rsize;
  if (f != h+40) { f[3]=h[43]; f[2]=h[42]; f[1]=h[41]; f[0]=h[40]; }

  f=(char *)&hdr->nsec;
  if (f != h+36) { f[3]=h[39]; f[2]=h[38]; f[1]=h[37]; f[0]=h[36]; }

  f=(char *)&hdr->nminut;
  if (f != h+32) { f[3]=h[35]; f[2]=h[34]; f[1]=h[33]; f[0]=h[32]; }

  f=(char *)&hdr->nhour;
  if (f != h+28) { f[3]=h[31]; f[2]=h[30]; f[1]=h[29]; f[0]=h[28]; }

  f=(char *)&hdr->nyear;
  if (f != h+24) { f[3]=h[27]; f[2]=h[26]; f[1]=h[25]; f[0]=h[24]; }

  f=(char *)&hdr->nmonth;
  if (f != h+20) { f[3]=h[23]; f[2]=h[22]; f[1]=h[21]; f[0]=h[20]; }

  f=(char *)&hdr->nday;
  if (f != h+16) { f[3]=h[19]; f[2]=h[18]; f[1]=h[17]; f[0]=h[16]; }

  f=(char *)&hdr->nblocks;
  if (f != h+12) { f[3]=h[15]; f[2]=h[14]; f[1]=h[13]; f[0]=h[12]; }

  f=(char *)&hdr->ierror;
  if (f != h+8) { f[3]=h[11]; f[2]=h[10]; f[1]=h[9]; f[0]=h[8]; }

  f=(char *)&hdr->ifol;
  if (f != h+4) { f[3]=h[7]; f[2]=h[6]; f[1]=h[5]; f[0]=h[4]; }

  f=(char *)&hdr->imn;
  if (f != h+0) { f[3]=h[3]; f[2]=h[2]; f[1]=h[1]; f[0]=h[0]; }

}


static void ImagicHeaderSwap
            (ImagicHeader *hdr)

{
  char *h = (char *)hdr;

  Swap32( 14, h, h );
  Swap32( 14, h + 60, h + 60 );
  Swap32( 150, h + 196, h + 196 );

}


extern Status ImagicHeaderRead
              (Imageio *imageio,
               ImagicHeader *hdr)

{
  Fileio *hdrfile;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( hdr == NULL ) ) return pushexception( E_ARGVAL );

  /* use hdr file first, then switch to img file */
  ImagicMeta *meta = imageio->meta;
  if ( ( meta == NULL ) || ( meta->hdrfile == NULL ) ) {
    hdrfile = imageio->fileio;
  } else {
    hdrfile = meta->hdrfile;
  }

  /* read into buffer */
  status = FileioRead( hdrfile, 0, ImagicHeaderSize, hdr );
  if ( pushexception( status ) ) return status;

  /* swap if non-native byte order */
  if ( imageio->iostat & ImageioByteSwap ) {
    ImagicHeaderSwap( hdr );
  }

  /* unpack header, code may be removed by optimization */
  if ( sizeof(ImagicHeader) > ImagicHeaderSize ) {
    ImagicHeaderUnpack( hdr );
  }

  return E_NONE;

}


extern Status ImagicHeaderWrite
              (Imageio *imageio)

{
  Fileio *hdrfile;
  Offset offs = 0;
  ImagicHeader buf;
  int32_t *ibuf = (int32_t *)&buf;
  Size imn = 1;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  ImagicMeta *meta = imageio->meta;
  ImagicHeader *hdr = &meta->header;
  if ( meta->hdrfile == NULL ) {
    hdrfile = imageio->fileio;
  } else {
    Size len = sizeof( hdr->history );
    ImageioGetVersion( " modified by ", ImagicioVers, &len, hdr->history );
    hdrfile = meta->hdrfile;
  }

  /* temp copy of header */
  buf = *hdr;

  /* set open flag */
  if ( ~imageio->iostat & ImageioFinClose ) {
    buf.ierror = -1;
  }

  /* pack header, code may be removed by optimization */
  if ( sizeof(ImagicHeader) > ImagicHeaderSize ) {
    ImagicHeaderPack( &buf );
  }
  /* swap if non-native byte order */
  if ( imageio->iostat & ImageioByteSwap ) {
    ImagicHeaderSwap( &buf );
  }

  /* write to file */
  if ( imageio->iocap == ImageioCapStd ) {
    status = FileioWriteStd( hdrfile, 0, ImagicHeaderSize, &buf );
    if ( pushexception( status ) ) return status; 
  } else {
    status = FileioWrite( hdrfile, 0, ImagicHeaderSize, &buf );
    if ( pushexception( status ) ) return status; 
  }

  while ( meta->ifol && !status ) {
    ibuf[0] = ++imn;
    ibuf[1] = --meta->ifol;
    ibuf[2] = 0;
    if ( imageio->iostat & ImageioByteSwap ) {
      Swap32( 3, ibuf, ibuf );
    }
    offs += ImagicHeaderSize;
    if ( imageio->iocap == ImageioCapStd ) {
      status = FileioWriteStd( hdrfile, offs, ImagicHeaderSize, &buf );
      if ( pushexception( status ) ) return status; 
    } else {
      status = FileioWrite( hdrfile, offs, ImagicHeaderSize, &buf );
      if ( pushexception( status ) ) return status; 
    }
  }

  /* flush buffers */
  status = FileioFlush( hdrfile );
  if ( pushexception( status ) ) return status; 

  return E_NONE;

}
