/*----------------------------------------------------------------------------*
*
*  spiderio.c  -  imageio: spider files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "spiderio.h"
#include "imageiocommon.h"
#include "exception.h"
#include "baselib.h"


/* header layout

  nr offs size  type name
   0    0    4  Real32 nslice
   1    4    4  Real32 nrow
   2    8    4  Real32 irec
   3   12    4  Real32 nhistrec
   4   16    4  Real32 iform
   5   20    4  Real32 imami
   6   24    4  Real32 fmax
   7   28    4  Real32 fmin
   8   32    4  Real32 av
   9   36    4  Real32 sig
  10   40    4  Real32 ihist
  11   44    4  Real32 nsam
  12   48    4  Real32 labrec
  13   52    4  Real32 iangle
  14   56    4  Real32 phi
  15   60    4  Real32 theta
  16   64    4  Real32 gamma
  17   68    4  Real32 xoff
  18   72    4  Real32 yoff
  19   76    4  Real32 zoff
  20   80    4  Real32 scale
  21   84    4  Real32 labbyt
  22   88    4  Real32 lenbyt
  23   92    4  Real32 istack
  24   96    4  Real32 unused25
  25  100    4  Real32 maxim
  26  104    4  Real32 imgnum
  27  108    4  Real32 lastindx
  28  112    4  Real32 unused29
  29  116    4  Real32 unused30
  30  120    4  Real32 kangle
  31  124    4  Real32 phi1
  32  128    4  Real32 theta1
  33  132    4  Real32 psi1
  34  136    4  Real32 phi2
  35  140    4  Real32 theta2
  36  144    4  Real32 psi2
  37  148    8  Real32 unused38[2]
  38  156   40  Real32 unused40[10]
  39  196  108  Real32 jose[27]
  40  304   12  Real32 unused77[3]
  41  316   80  Real32 unused80[20]
  42  396  400  Real32 unused100[100]
  43  796   48  Real32 unused200[12]
  44  844   12  char cdat[12]
  45  856    8  char ctim[8]
  46  864  160  char ctit[160]
  47      1024  SpiderHdr
*/


static void SpiderHeaderPack
            (SpiderHeader *hdr)

{
  char *f,*h=(char *)hdr;

  f=(char *)&hdr->nslice;
  if (f != h+0) { h[0]=f[0]; h[1]=f[1]; h[2]=f[2]; h[3]=f[3]; }

  f=(char *)&hdr->nrow;
  if (f != h+4) { h[4]=f[0]; h[5]=f[1]; h[6]=f[2]; h[7]=f[3]; }

  f=(char *)&hdr->irec;
  if (f != h+8) { h[8]=f[0]; h[9]=f[1]; h[10]=f[2]; h[11]=f[3]; }

  f=(char *)&hdr->nhistrec;
  if (f != h+12) { h[12]=f[0]; h[13]=f[1]; h[14]=f[2]; h[15]=f[3]; }

  f=(char *)&hdr->iform;
  if (f != h+16) { h[16]=f[0]; h[17]=f[1]; h[18]=f[2]; h[19]=f[3]; }

  f=(char *)&hdr->imami;
  if (f != h+20) { h[20]=f[0]; h[21]=f[1]; h[22]=f[2]; h[23]=f[3]; }

  f=(char *)&hdr->fmax;
  if (f != h+24) { h[24]=f[0]; h[25]=f[1]; h[26]=f[2]; h[27]=f[3]; }

  f=(char *)&hdr->fmin;
  if (f != h+28) { h[28]=f[0]; h[29]=f[1]; h[30]=f[2]; h[31]=f[3]; }

  f=(char *)&hdr->av;
  if (f != h+32) { h[32]=f[0]; h[33]=f[1]; h[34]=f[2]; h[35]=f[3]; }

  f=(char *)&hdr->sig;
  if (f != h+36) { h[36]=f[0]; h[37]=f[1]; h[38]=f[2]; h[39]=f[3]; }

  f=(char *)&hdr->ihist;
  if (f != h+40) { h[40]=f[0]; h[41]=f[1]; h[42]=f[2]; h[43]=f[3]; }

  f=(char *)&hdr->nsam;
  if (f != h+44) { h[44]=f[0]; h[45]=f[1]; h[46]=f[2]; h[47]=f[3]; }

  f=(char *)&hdr->labrec;
  if (f != h+48) { h[48]=f[0]; h[49]=f[1]; h[50]=f[2]; h[51]=f[3]; }

  f=(char *)&hdr->iangle;
  if (f != h+52) { h[52]=f[0]; h[53]=f[1]; h[54]=f[2]; h[55]=f[3]; }

  f=(char *)&hdr->phi;
  if (f != h+56) { h[56]=f[0]; h[57]=f[1]; h[58]=f[2]; h[59]=f[3]; }

  f=(char *)&hdr->theta;
  if (f != h+60) { h[60]=f[0]; h[61]=f[1]; h[62]=f[2]; h[63]=f[3]; }

  f=(char *)&hdr->gamma;
  if (f != h+64) { h[64]=f[0]; h[65]=f[1]; h[66]=f[2]; h[67]=f[3]; }

  f=(char *)&hdr->xoff;
  if (f != h+68) { h[68]=f[0]; h[69]=f[1]; h[70]=f[2]; h[71]=f[3]; }

  f=(char *)&hdr->yoff;
  if (f != h+72) { h[72]=f[0]; h[73]=f[1]; h[74]=f[2]; h[75]=f[3]; }

  f=(char *)&hdr->zoff;
  if (f != h+76) { h[76]=f[0]; h[77]=f[1]; h[78]=f[2]; h[79]=f[3]; }

  f=(char *)&hdr->scale;
  if (f != h+80) { h[80]=f[0]; h[81]=f[1]; h[82]=f[2]; h[83]=f[3]; }

  f=(char *)&hdr->labbyt;
  if (f != h+84) { h[84]=f[0]; h[85]=f[1]; h[86]=f[2]; h[87]=f[3]; }

  f=(char *)&hdr->lenbyt;
  if (f != h+88) { h[88]=f[0]; h[89]=f[1]; h[90]=f[2]; h[91]=f[3]; }

  f=(char *)&hdr->istack;
  if (f != h+92) { h[92]=f[0]; h[93]=f[1]; h[94]=f[2]; h[95]=f[3]; }

  f=(char *)&hdr->unused25;
  if (f != h+96) { h[96]=f[0]; h[97]=f[1]; h[98]=f[2]; h[99]=f[3]; }

  f=(char *)&hdr->maxim;
  if (f != h+100) { h[100]=f[0]; h[101]=f[1]; h[102]=f[2]; h[103]=f[3]; }

  f=(char *)&hdr->imgnum;
  if (f != h+104) { h[104]=f[0]; h[105]=f[1]; h[106]=f[2]; h[107]=f[3]; }

  f=(char *)&hdr->lastindx;
  if (f != h+108) { h[108]=f[0]; h[109]=f[1]; h[110]=f[2]; h[111]=f[3]; }

  f=(char *)&hdr->unused29;
  if (f != h+112) { h[112]=f[0]; h[113]=f[1]; h[114]=f[2]; h[115]=f[3]; }

  f=(char *)&hdr->unused30;
  if (f != h+116) { h[116]=f[0]; h[117]=f[1]; h[118]=f[2]; h[119]=f[3]; }

  f=(char *)&hdr->kangle;
  if (f != h+120) { h[120]=f[0]; h[121]=f[1]; h[122]=f[2]; h[123]=f[3]; }

  f=(char *)&hdr->phi1;
  if (f != h+124) { h[124]=f[0]; h[125]=f[1]; h[126]=f[2]; h[127]=f[3]; }

  f=(char *)&hdr->theta1;
  if (f != h+128) { h[128]=f[0]; h[129]=f[1]; h[130]=f[2]; h[131]=f[3]; }

  f=(char *)&hdr->psi1;
  if (f != h+132) { h[132]=f[0]; h[133]=f[1]; h[134]=f[2]; h[135]=f[3]; }

  f=(char *)&hdr->phi2;
  if (f != h+136) { h[136]=f[0]; h[137]=f[1]; h[138]=f[2]; h[139]=f[3]; }

  f=(char *)&hdr->theta2;
  if (f != h+140) { h[140]=f[0]; h[141]=f[1]; h[142]=f[2]; h[143]=f[3]; }

  f=(char *)&hdr->psi2;
  if (f != h+144) { h[144]=f[0]; h[145]=f[1]; h[146]=f[2]; h[147]=f[3]; }

  f=(char *)hdr->unused38;
  if (f != h+148) { size_t i=0; while (i < 8) { h[i+148]=f[i]; i++; } }

  f=(char *)hdr->unused40;
  if (f != h+156) { size_t i=0; while (i < 40) { h[i+156]=f[i]; i++; } }

  f=(char *)hdr->jose;
  if (f != h+196) { size_t i=0; while (i < 108) { h[i+196]=f[i]; i++; } }

  f=(char *)hdr->unused77;
  if (f != h+304) { size_t i=0; while (i < 12) { h[i+304]=f[i]; i++; } }

  f=(char *)hdr->unused80;
  if (f != h+316) { size_t i=0; while (i < 80) { h[i+316]=f[i]; i++; } }

  f=(char *)hdr->unused100;
  if (f != h+396) { size_t i=0; while (i < 400) { h[i+396]=f[i]; i++; } }

  f=(char *)hdr->unused200;
  if (f != h+796) { size_t i=0; while (i < 48) { h[i+796]=f[i]; i++; } }

  f=(char *)hdr->cdat;
  if (f != h+844) { size_t i=0; while (i < 12) { h[i+844]=f[i]; i++; } }

  f=(char *)hdr->ctim;
  if (f != h+856) { size_t i=0; while (i < 8) { h[i+856]=f[i]; i++; } }

  f=(char *)hdr->ctit;
  if (f != h+864) { size_t i=0; while (i < 160) { h[i+864]=f[i]; i++; } }

}


static void SpiderHeaderUnpack
            (SpiderHeader *hdr)

{
  char *f,*h=(char *)hdr;

  f=(char *)hdr->ctit;
  if (f != h+864) { size_t i=160; while (i) { --i; f[i]=h[i+864]; } }

  f=(char *)hdr->ctim;
  if (f != h+856) { size_t i=8; while (i) { --i; f[i]=h[i+856]; } }

  f=(char *)hdr->cdat;
  if (f != h+844) { size_t i=12; while (i) { --i; f[i]=h[i+844]; } }

  f=(char *)hdr->unused200;
  if (f != h+796) { size_t i=48; while (i) { --i; f[i]=h[i+796]; } }

  f=(char *)hdr->unused100;
  if (f != h+396) { size_t i=400; while (i) { --i; f[i]=h[i+396]; } }

  f=(char *)hdr->unused80;
  if (f != h+316) { size_t i=80; while (i) { --i; f[i]=h[i+316]; } }

  f=(char *)hdr->unused77;
  if (f != h+304) { size_t i=12; while (i) { --i; f[i]=h[i+304]; } }

  f=(char *)hdr->jose;
  if (f != h+196) { size_t i=108; while (i) { --i; f[i]=h[i+196]; } }

  f=(char *)hdr->unused40;
  if (f != h+156) { size_t i=40; while (i) { --i; f[i]=h[i+156]; } }

  f=(char *)hdr->unused38;
  if (f != h+148) { size_t i=8; while (i) { --i; f[i]=h[i+148]; } }

  f=(char *)&hdr->psi2;
  if (f != h+144) { f[3]=h[147]; f[2]=h[146]; f[1]=h[145]; f[0]=h[144]; }

  f=(char *)&hdr->theta2;
  if (f != h+140) { f[3]=h[143]; f[2]=h[142]; f[1]=h[141]; f[0]=h[140]; }

  f=(char *)&hdr->phi2;
  if (f != h+136) { f[3]=h[139]; f[2]=h[138]; f[1]=h[137]; f[0]=h[136]; }

  f=(char *)&hdr->psi1;
  if (f != h+132) { f[3]=h[135]; f[2]=h[134]; f[1]=h[133]; f[0]=h[132]; }

  f=(char *)&hdr->theta1;
  if (f != h+128) { f[3]=h[131]; f[2]=h[130]; f[1]=h[129]; f[0]=h[128]; }

  f=(char *)&hdr->phi1;
  if (f != h+124) { f[3]=h[127]; f[2]=h[126]; f[1]=h[125]; f[0]=h[124]; }

  f=(char *)&hdr->kangle;
  if (f != h+120) { f[3]=h[123]; f[2]=h[122]; f[1]=h[121]; f[0]=h[120]; }

  f=(char *)&hdr->unused30;
  if (f != h+116) { f[3]=h[119]; f[2]=h[118]; f[1]=h[117]; f[0]=h[116]; }

  f=(char *)&hdr->unused29;
  if (f != h+112) { f[3]=h[115]; f[2]=h[114]; f[1]=h[113]; f[0]=h[112]; }

  f=(char *)&hdr->lastindx;
  if (f != h+108) { f[3]=h[111]; f[2]=h[110]; f[1]=h[109]; f[0]=h[108]; }

  f=(char *)&hdr->imgnum;
  if (f != h+104) { f[3]=h[107]; f[2]=h[106]; f[1]=h[105]; f[0]=h[104]; }

  f=(char *)&hdr->maxim;
  if (f != h+100) { f[3]=h[103]; f[2]=h[102]; f[1]=h[101]; f[0]=h[100]; }

  f=(char *)&hdr->unused25;
  if (f != h+96) { f[3]=h[99]; f[2]=h[98]; f[1]=h[97]; f[0]=h[96]; }

  f=(char *)&hdr->istack;
  if (f != h+92) { f[3]=h[95]; f[2]=h[94]; f[1]=h[93]; f[0]=h[92]; }

  f=(char *)&hdr->lenbyt;
  if (f != h+88) { f[3]=h[91]; f[2]=h[90]; f[1]=h[89]; f[0]=h[88]; }

  f=(char *)&hdr->labbyt;
  if (f != h+84) { f[3]=h[87]; f[2]=h[86]; f[1]=h[85]; f[0]=h[84]; }

  f=(char *)&hdr->scale;
  if (f != h+80) { f[3]=h[83]; f[2]=h[82]; f[1]=h[81]; f[0]=h[80]; }

  f=(char *)&hdr->zoff;
  if (f != h+76) { f[3]=h[79]; f[2]=h[78]; f[1]=h[77]; f[0]=h[76]; }

  f=(char *)&hdr->yoff;
  if (f != h+72) { f[3]=h[75]; f[2]=h[74]; f[1]=h[73]; f[0]=h[72]; }

  f=(char *)&hdr->xoff;
  if (f != h+68) { f[3]=h[71]; f[2]=h[70]; f[1]=h[69]; f[0]=h[68]; }

  f=(char *)&hdr->gamma;
  if (f != h+64) { f[3]=h[67]; f[2]=h[66]; f[1]=h[65]; f[0]=h[64]; }

  f=(char *)&hdr->theta;
  if (f != h+60) { f[3]=h[63]; f[2]=h[62]; f[1]=h[61]; f[0]=h[60]; }

  f=(char *)&hdr->phi;
  if (f != h+56) { f[3]=h[59]; f[2]=h[58]; f[1]=h[57]; f[0]=h[56]; }

  f=(char *)&hdr->iangle;
  if (f != h+52) { f[3]=h[55]; f[2]=h[54]; f[1]=h[53]; f[0]=h[52]; }

  f=(char *)&hdr->labrec;
  if (f != h+48) { f[3]=h[51]; f[2]=h[50]; f[1]=h[49]; f[0]=h[48]; }

  f=(char *)&hdr->nsam;
  if (f != h+44) { f[3]=h[47]; f[2]=h[46]; f[1]=h[45]; f[0]=h[44]; }

  f=(char *)&hdr->ihist;
  if (f != h+40) { f[3]=h[43]; f[2]=h[42]; f[1]=h[41]; f[0]=h[40]; }

  f=(char *)&hdr->sig;
  if (f != h+36) { f[3]=h[39]; f[2]=h[38]; f[1]=h[37]; f[0]=h[36]; }

  f=(char *)&hdr->av;
  if (f != h+32) { f[3]=h[35]; f[2]=h[34]; f[1]=h[33]; f[0]=h[32]; }

  f=(char *)&hdr->fmin;
  if (f != h+28) { f[3]=h[31]; f[2]=h[30]; f[1]=h[29]; f[0]=h[28]; }

  f=(char *)&hdr->fmax;
  if (f != h+24) { f[3]=h[27]; f[2]=h[26]; f[1]=h[25]; f[0]=h[24]; }

  f=(char *)&hdr->imami;
  if (f != h+20) { f[3]=h[23]; f[2]=h[22]; f[1]=h[21]; f[0]=h[20]; }

  f=(char *)&hdr->iform;
  if (f != h+16) { f[3]=h[19]; f[2]=h[18]; f[1]=h[17]; f[0]=h[16]; }

  f=(char *)&hdr->nhistrec;
  if (f != h+12) { f[3]=h[15]; f[2]=h[14]; f[1]=h[13]; f[0]=h[12]; }

  f=(char *)&hdr->irec;
  if (f != h+8) { f[3]=h[11]; f[2]=h[10]; f[1]=h[9]; f[0]=h[8]; }

  f=(char *)&hdr->nrow;
  if (f != h+4) { f[3]=h[7]; f[2]=h[6]; f[1]=h[5]; f[0]=h[4]; }

  f=(char *)&hdr->nslice;
  if (f != h+0) { f[3]=h[3]; f[2]=h[2]; f[1]=h[1]; f[0]=h[0]; }

}


static void SpiderHeaderSwap
            (SpiderHeader *hdr)

{
  char *h = (char *)hdr;

  Swap32( 211, h, h );

}


extern Status SpiderHeaderRead
              (Imageio *imageio,
               SpiderHeader *hdr)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( hdr == NULL ) ) return pushexception( E_ARGVAL );

  /* read into buffer */
  status = FileioRead( imageio->fileio, 0, SpiderHeaderSize, hdr );
  if ( pushexception( status ) ) return status;

  /* swap if non-native byte order */
  if ( imageio->iostat & ImageioByteSwap ) {
    SpiderHeaderSwap( hdr );
  }

  /* unpack header, code may be removed by optimization */
  if ( sizeof(SpiderHeader) > SpiderHeaderSize ) {
    SpiderHeaderUnpack( hdr );
  }

  return E_NONE;

}


extern Status SpiderHeaderWrite
              (Imageio *imageio)

{
  SpiderMeta *meta;
  SpiderHeader *hdr, buf;
  Size len;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  meta = imageio->meta;
  hdr = &meta->header;
  len = sizeof( hdr->ctit );

  /* set label */
  ImageioGetVersion( " modified by ", SpiderioVers, &len, hdr->ctit );

  /* temp copy of header */
  buf = *hdr;

  /* set open flag */
  if ( ~imageio->iostat & ImageioFinClose ) {
    buf.iform = SPIDER_OPENFLAG;
  }

  /* pack header, code may be removed by optimization, unless check is set */
  if ( sizeof(SpiderHeader) > SpiderHeaderSize ) {
    SpiderHeaderPack( &buf );
  }
  /* swap if non-native byte order */
  if ( imageio->iostat & ImageioByteSwap ) {
    SpiderHeaderSwap( &buf );
  }

  /* write to file */
  if ( imageio->iocap == ImageioCapStd ) {
    status = FileioWriteStd( imageio->fileio, 0, SpiderHeaderSize, &buf );
    if ( pushexception( status ) ) return status; 
  } else {
    status = FileioWrite( imageio->fileio, 0, SpiderHeaderSize, &buf );
    if ( pushexception( status ) ) return status; 
  }

  /* flush buffers */
  status = FileioFlush( imageio->fileio );
  if ( pushexception( status ) ) return status; 

  return E_NONE;

}
