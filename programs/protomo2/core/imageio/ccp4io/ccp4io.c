/*----------------------------------------------------------------------------*
*
*  ccp4io.c  -  imageio: CCP4 files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "ccp4io.h"
#include "imageiocommon.h"
#include "exception.h"
#include "baselib.h"


/* header layout

  nr offs size  type name
   0    0    4  uint32_t nx
   1    4    4  uint32_t ny
   2    8    4  uint32_t nz
   3   12    4  uint32_t mode
   4   16    4  int32_t nxstart
   5   20    4  int32_t nystart
   6   24    4  int32_t nzstart
   7   28    4  uint32_t mx
   8   32    4  uint32_t my
   9   36    4  uint32_t mz
  10   40    4  Real32 a
  11   44    4  Real32 b
  12   48    4  Real32 c
  13   52    4  Real32 alpha
  14   56    4  Real32 beta
  15   60    4  Real32 gamma
  16   64    4  uint32_t mapc
  17   68    4  uint32_t mapr
  18   72    4  uint32_t maps
  19   76    4  Real32 amin
  20   80    4  Real32 amax
  21   84    4  Real32 amean
  22   88    4  uint32_t ispg
  23   92    4  uint32_t nsymbt
  24   96    4  uint32_t lskflg
  25  100   36  Real32 skwmat[3][3]
  26  136   12  Real32 skwtrn[3]
  27  148   60  uint32_t unused[15]
  28  208    4  char map[4]
  29  212    4  uint32_t machst
  30  216    4  Real32 arms
  31  220    4  uint32_t nlab
  32  224  800  char label[10][80]
  33      1024  CCP4Hdr
*/


static void CCP4HeaderPack
            (CCP4Header *hdr)

{
  char *f,*h=(char *)hdr;

  f=(char *)&hdr->nx;
  if (f != h+0) { h[0]=f[0]; h[1]=f[1]; h[2]=f[2]; h[3]=f[3]; }

  f=(char *)&hdr->ny;
  if (f != h+4) { h[4]=f[0]; h[5]=f[1]; h[6]=f[2]; h[7]=f[3]; }

  f=(char *)&hdr->nz;
  if (f != h+8) { h[8]=f[0]; h[9]=f[1]; h[10]=f[2]; h[11]=f[3]; }

  f=(char *)&hdr->mode;
  if (f != h+12) { h[12]=f[0]; h[13]=f[1]; h[14]=f[2]; h[15]=f[3]; }

  f=(char *)&hdr->nxstart;
  if (f != h+16) { h[16]=f[0]; h[17]=f[1]; h[18]=f[2]; h[19]=f[3]; }

  f=(char *)&hdr->nystart;
  if (f != h+20) { h[20]=f[0]; h[21]=f[1]; h[22]=f[2]; h[23]=f[3]; }

  f=(char *)&hdr->nzstart;
  if (f != h+24) { h[24]=f[0]; h[25]=f[1]; h[26]=f[2]; h[27]=f[3]; }

  f=(char *)&hdr->mx;
  if (f != h+28) { h[28]=f[0]; h[29]=f[1]; h[30]=f[2]; h[31]=f[3]; }

  f=(char *)&hdr->my;
  if (f != h+32) { h[32]=f[0]; h[33]=f[1]; h[34]=f[2]; h[35]=f[3]; }

  f=(char *)&hdr->mz;
  if (f != h+36) { h[36]=f[0]; h[37]=f[1]; h[38]=f[2]; h[39]=f[3]; }

  f=(char *)&hdr->a;
  if (f != h+40) { h[40]=f[0]; h[41]=f[1]; h[42]=f[2]; h[43]=f[3]; }

  f=(char *)&hdr->b;
  if (f != h+44) { h[44]=f[0]; h[45]=f[1]; h[46]=f[2]; h[47]=f[3]; }

  f=(char *)&hdr->c;
  if (f != h+48) { h[48]=f[0]; h[49]=f[1]; h[50]=f[2]; h[51]=f[3]; }

  f=(char *)&hdr->alpha;
  if (f != h+52) { h[52]=f[0]; h[53]=f[1]; h[54]=f[2]; h[55]=f[3]; }

  f=(char *)&hdr->beta;
  if (f != h+56) { h[56]=f[0]; h[57]=f[1]; h[58]=f[2]; h[59]=f[3]; }

  f=(char *)&hdr->gamma;
  if (f != h+60) { h[60]=f[0]; h[61]=f[1]; h[62]=f[2]; h[63]=f[3]; }

  f=(char *)&hdr->mapc;
  if (f != h+64) { h[64]=f[0]; h[65]=f[1]; h[66]=f[2]; h[67]=f[3]; }

  f=(char *)&hdr->mapr;
  if (f != h+68) { h[68]=f[0]; h[69]=f[1]; h[70]=f[2]; h[71]=f[3]; }

  f=(char *)&hdr->maps;
  if (f != h+72) { h[72]=f[0]; h[73]=f[1]; h[74]=f[2]; h[75]=f[3]; }

  f=(char *)&hdr->amin;
  if (f != h+76) { h[76]=f[0]; h[77]=f[1]; h[78]=f[2]; h[79]=f[3]; }

  f=(char *)&hdr->amax;
  if (f != h+80) { h[80]=f[0]; h[81]=f[1]; h[82]=f[2]; h[83]=f[3]; }

  f=(char *)&hdr->amean;
  if (f != h+84) { h[84]=f[0]; h[85]=f[1]; h[86]=f[2]; h[87]=f[3]; }

  f=(char *)&hdr->ispg;
  if (f != h+88) { h[88]=f[0]; h[89]=f[1]; h[90]=f[2]; h[91]=f[3]; }

  f=(char *)&hdr->nsymbt;
  if (f != h+92) { h[92]=f[0]; h[93]=f[1]; h[94]=f[2]; h[95]=f[3]; }

  f=(char *)&hdr->lskflg;
  if (f != h+96) { h[96]=f[0]; h[97]=f[1]; h[98]=f[2]; h[99]=f[3]; }

  f=(char *)hdr->skwmat;
  if (f != h+100) { size_t i=0; while (i < 36) { h[i+100]=f[i]; i++; } }

  f=(char *)hdr->skwtrn;
  if (f != h+136) { size_t i=0; while (i < 12) { h[i+136]=f[i]; i++; } }

  f=(char *)hdr->unused;
  if (f != h+148) { size_t i=0; while (i < 60) { h[i+148]=f[i]; i++; } }

  f=(char *)hdr->map;
  if (f != h+208) { h[208]=f[0]; h[209]=f[1]; h[210]=f[2]; h[211]=f[3]; }

  f=(char *)&hdr->machst;
  if (f != h+212) { h[212]=f[0]; h[213]=f[1]; h[214]=f[2]; h[215]=f[3]; }

  f=(char *)&hdr->arms;
  if (f != h+216) { h[216]=f[0]; h[217]=f[1]; h[218]=f[2]; h[219]=f[3]; }

  f=(char *)&hdr->nlab;
  if (f != h+220) { h[220]=f[0]; h[221]=f[1]; h[222]=f[2]; h[223]=f[3]; }

  f=(char *)hdr->label;
  if (f != h+224) { size_t i=0; while (i < 800) { h[i+224]=f[i]; i++; } }

}


static void CCP4HeaderUnpack
            (CCP4Header *hdr)

{
  char *f,*h=(char *)hdr;

  f=(char *)hdr->label;
  if (f != h+224) { size_t i=800; while (i) { --i; f[i]=h[i+224]; } }

  f=(char *)&hdr->nlab;
  if (f != h+220) { f[3]=h[223]; f[2]=h[222]; f[1]=h[221]; f[0]=h[220]; }

  f=(char *)&hdr->arms;
  if (f != h+216) { f[3]=h[219]; f[2]=h[218]; f[1]=h[217]; f[0]=h[216]; }

  f=(char *)&hdr->machst;
  if (f != h+212) { f[3]=h[215]; f[2]=h[214]; f[1]=h[213]; f[0]=h[212]; }

  f=(char *)hdr->map;
  if (f != h+208) { f[3]=h[211]; f[2]=h[210]; f[1]=h[209]; f[0]=h[208]; }

  f=(char *)hdr->unused;
  if (f != h+148) { size_t i=60; while (i) { --i; f[i]=h[i+148]; } }

  f=(char *)hdr->skwtrn;
  if (f != h+136) { size_t i=12; while (i) { --i; f[i]=h[i+136]; } }

  f=(char *)hdr->skwmat;
  if (f != h+100) { size_t i=36; while (i) { --i; f[i]=h[i+100]; } }

  f=(char *)&hdr->lskflg;
  if (f != h+96) { f[3]=h[99]; f[2]=h[98]; f[1]=h[97]; f[0]=h[96]; }

  f=(char *)&hdr->nsymbt;
  if (f != h+92) { f[3]=h[95]; f[2]=h[94]; f[1]=h[93]; f[0]=h[92]; }

  f=(char *)&hdr->ispg;
  if (f != h+88) { f[3]=h[91]; f[2]=h[90]; f[1]=h[89]; f[0]=h[88]; }

  f=(char *)&hdr->amean;
  if (f != h+84) { f[3]=h[87]; f[2]=h[86]; f[1]=h[85]; f[0]=h[84]; }

  f=(char *)&hdr->amax;
  if (f != h+80) { f[3]=h[83]; f[2]=h[82]; f[1]=h[81]; f[0]=h[80]; }

  f=(char *)&hdr->amin;
  if (f != h+76) { f[3]=h[79]; f[2]=h[78]; f[1]=h[77]; f[0]=h[76]; }

  f=(char *)&hdr->maps;
  if (f != h+72) { f[3]=h[75]; f[2]=h[74]; f[1]=h[73]; f[0]=h[72]; }

  f=(char *)&hdr->mapr;
  if (f != h+68) { f[3]=h[71]; f[2]=h[70]; f[1]=h[69]; f[0]=h[68]; }

  f=(char *)&hdr->mapc;
  if (f != h+64) { f[3]=h[67]; f[2]=h[66]; f[1]=h[65]; f[0]=h[64]; }

  f=(char *)&hdr->gamma;
  if (f != h+60) { f[3]=h[63]; f[2]=h[62]; f[1]=h[61]; f[0]=h[60]; }

  f=(char *)&hdr->beta;
  if (f != h+56) { f[3]=h[59]; f[2]=h[58]; f[1]=h[57]; f[0]=h[56]; }

  f=(char *)&hdr->alpha;
  if (f != h+52) { f[3]=h[55]; f[2]=h[54]; f[1]=h[53]; f[0]=h[52]; }

  f=(char *)&hdr->c;
  if (f != h+48) { f[3]=h[51]; f[2]=h[50]; f[1]=h[49]; f[0]=h[48]; }

  f=(char *)&hdr->b;
  if (f != h+44) { f[3]=h[47]; f[2]=h[46]; f[1]=h[45]; f[0]=h[44]; }

  f=(char *)&hdr->a;
  if (f != h+40) { f[3]=h[43]; f[2]=h[42]; f[1]=h[41]; f[0]=h[40]; }

  f=(char *)&hdr->mz;
  if (f != h+36) { f[3]=h[39]; f[2]=h[38]; f[1]=h[37]; f[0]=h[36]; }

  f=(char *)&hdr->my;
  if (f != h+32) { f[3]=h[35]; f[2]=h[34]; f[1]=h[33]; f[0]=h[32]; }

  f=(char *)&hdr->mx;
  if (f != h+28) { f[3]=h[31]; f[2]=h[30]; f[1]=h[29]; f[0]=h[28]; }

  f=(char *)&hdr->nzstart;
  if (f != h+24) { f[3]=h[27]; f[2]=h[26]; f[1]=h[25]; f[0]=h[24]; }

  f=(char *)&hdr->nystart;
  if (f != h+20) { f[3]=h[23]; f[2]=h[22]; f[1]=h[21]; f[0]=h[20]; }

  f=(char *)&hdr->nxstart;
  if (f != h+16) { f[3]=h[19]; f[2]=h[18]; f[1]=h[17]; f[0]=h[16]; }

  f=(char *)&hdr->mode;
  if (f != h+12) { f[3]=h[15]; f[2]=h[14]; f[1]=h[13]; f[0]=h[12]; }

  f=(char *)&hdr->nz;
  if (f != h+8) { f[3]=h[11]; f[2]=h[10]; f[1]=h[9]; f[0]=h[8]; }

  f=(char *)&hdr->ny;
  if (f != h+4) { f[3]=h[7]; f[2]=h[6]; f[1]=h[5]; f[0]=h[4]; }

  f=(char *)&hdr->nx;
  if (f != h+0) { f[3]=h[3]; f[2]=h[2]; f[1]=h[1]; f[0]=h[0]; }

}


static void CCP4HeaderSwap
            (CCP4Header *hdr)

{
  char *h = (char *)hdr;

  Swap32( 52, h, h );
  /* do not swap map */
  Swap32( 3, h+212, h+212 );

}


static void MRCHeaderSwap
            (CCP4Header *hdr)

{
  char *h = (char *)hdr;

  Swap32( 56, h, h );

}


extern Status CCP4HeaderRead
              (Imageio *imageio,
               CCP4Header *hdr)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( hdr == NULL ) ) return pushexception( E_ARGVAL );

  /* read into buffer */
  status = FileioRead( imageio->fileio, 0, CCP4HeaderSize, hdr );
  if ( pushexception( status ) ) return status;

  /* swap if non-native byte order */
  if ( imageio->iostat & ImageioByteSwap ) {
    if ( *imageio->format->version.ident == 'C' ) {
      CCP4HeaderSwap( hdr );
    } else {
      MRCHeaderSwap( hdr );
    }
  }

  /* unpack header, code may be removed by optimization */
  if ( sizeof(CCP4Header) > CCP4HeaderSize ) {
    CCP4HeaderUnpack( hdr );
  }

  return E_NONE;

}


extern Status CCP4HeaderWrite
              (Imageio *imageio)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  CCP4Meta *meta = imageio->meta;
  CCP4Header *hdr = &meta->header;

  /* set label */
  if ( meta->ilab < 10 ) {
    Size len = sizeof( hdr->label[meta->ilab] );
    ImageioGetVersion( " modified by ", CCP4ioVers, &len, hdr->label[meta->ilab] );
    hdr->nlab = meta->ilab + 1;
  }

  /* temp copy of header */
  CCP4Header buf = *hdr;

  /* set open flag */
  if ( ~imageio->iostat & ImageioFinClose ) {
    buf.mode = CCP4_OPENFLAG;
  }

  /* pack header, code may be removed by optimization */
  if ( sizeof(CCP4Header) > CCP4HeaderSize ) {
    CCP4HeaderPack( &buf );
  }
  /* swap if non-native byte order */
  if ( imageio->iostat & ImageioByteSwap ) {
    if ( *imageio->format->version.ident == 'C' ) {
      CCP4HeaderSwap( &buf );
    } else {
      MRCHeaderSwap( &buf );
    }
  }

  /* write to file */
  if ( imageio->iocap == ImageioCapStd ) {
    status = FileioWriteStd( imageio->fileio, 0, CCP4HeaderSize, &buf );
    if ( pushexception( status ) ) return status; 
  } else {
    status = FileioWrite( imageio->fileio, 0, CCP4HeaderSize, &buf );
    if ( pushexception( status ) ) return status; 
  }

  /* flush buffers */
  status = FileioFlush( imageio->fileio );
  if ( pushexception( status ) ) return status; 

  return E_NONE;

}
