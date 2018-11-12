/*----------------------------------------------------------------------------*
*
*  emio.c  -  imageio: em files
*
*-----------------------------------------------------------------------------*
*
*  Copyright © 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "emio.h"
#include "imageiocommon.h"
#include "exception.h"
#include "baselib.h"


/* header layout

  nr offs size  type name
   0    0    1  uint8_t machine
   1    1    1  uint8_t general
   2    2    1  uint8_t unused
   3    3    1  uint8_t datatype
   4    4    4  int32_t nx
   5    8    4  int32_t ny
   6   12    4  int32_t nz
   7   16   80  char label[80]
   8   96    4  int32_t voltage
   9  100    4  int32_t Cs
  10  104    4  int32_t aperture
  11  108    4  int32_t mag
  12  112    4  int32_t postmag
  13  116    4  int32_t exposure
  14  120    4  int32_t objpixel
  15  124    4  int32_t emcode
  16  128    4  int32_t ccdpixel
  17  132    4  int32_t ccdlength
  18  136    4  int32_t defocus
  19  140    4  int32_t astig
  20  144    4  int32_t astigdir
  21  148    4  int32_t defocusinc
  22  152    4  int32_t counts
  23  156    4  int32_t c2
  24  160    4  int32_t slit
  25  164    4  int32_t offs
  26  168    4  int32_t tiltangle
  27  172    4  int32_t tiltdir
  28  176    4  int32_t internal21
  29  180    4  int32_t internal22
  30  184    4  int32_t internal23
  31  188    4  int32_t subframex0
  32  192    4  int32_t subframey0
  33  196    4  int32_t resolution
  34  200    4  int32_t density
  35  204    4  int32_t contrast
  36  208    4  int32_t unknown
  37  212    4  int32_t cmx
  38  216    4  int32_t cmy
  39  220    4  int32_t cmz
  40  224    4  int32_t cmh
  41  228    4  int32_t reserved34
  42  232    4  int32_t d1
  43  236    4  int32_t d2
  44  240    4  int32_t lambda
  45  244    4  int32_t dtheta
  46  248    4  int32_t reserved39
  47  252    4  int32_t reserved40
  48  256   20  char username[20]
  49  276    8  char date[8]
  50  284  228  char extra[228]
  51       512  EMHdr
*/


static void EMHeaderPack
            (EMHeader *hdr)

{
  char *f,*h=(char *)hdr;

  f=(char *)&hdr->machine;
  if (f != h+0) { h[0]=f[0]; }

  f=(char *)&hdr->general;
  if (f != h+1) { h[1]=f[0]; }

  f=(char *)&hdr->unused;
  if (f != h+2) { h[2]=f[0]; }

  f=(char *)&hdr->datatype;
  if (f != h+3) { h[3]=f[0]; }

  f=(char *)&hdr->nx;
  if (f != h+4) { h[4]=f[0]; h[5]=f[1]; h[6]=f[2]; h[7]=f[3]; }

  f=(char *)&hdr->ny;
  if (f != h+8) { h[8]=f[0]; h[9]=f[1]; h[10]=f[2]; h[11]=f[3]; }

  f=(char *)&hdr->nz;
  if (f != h+12) { h[12]=f[0]; h[13]=f[1]; h[14]=f[2]; h[15]=f[3]; }

  f=(char *)hdr->label;
  if (f != h+16) { size_t i=0; while (i < 80) { h[i+16]=f[i]; i++; } }

  f=(char *)&hdr->voltage;
  if (f != h+96) { h[96]=f[0]; h[97]=f[1]; h[98]=f[2]; h[99]=f[3]; }

  f=(char *)&hdr->Cs;
  if (f != h+100) { h[100]=f[0]; h[101]=f[1]; h[102]=f[2]; h[103]=f[3]; }

  f=(char *)&hdr->aperture;
  if (f != h+104) { h[104]=f[0]; h[105]=f[1]; h[106]=f[2]; h[107]=f[3]; }

  f=(char *)&hdr->mag;
  if (f != h+108) { h[108]=f[0]; h[109]=f[1]; h[110]=f[2]; h[111]=f[3]; }

  f=(char *)&hdr->postmag;
  if (f != h+112) { h[112]=f[0]; h[113]=f[1]; h[114]=f[2]; h[115]=f[3]; }

  f=(char *)&hdr->exposure;
  if (f != h+116) { h[116]=f[0]; h[117]=f[1]; h[118]=f[2]; h[119]=f[3]; }

  f=(char *)&hdr->objpixel;
  if (f != h+120) { h[120]=f[0]; h[121]=f[1]; h[122]=f[2]; h[123]=f[3]; }

  f=(char *)&hdr->emcode;
  if (f != h+124) { h[124]=f[0]; h[125]=f[1]; h[126]=f[2]; h[127]=f[3]; }

  f=(char *)&hdr->ccdpixel;
  if (f != h+128) { h[128]=f[0]; h[129]=f[1]; h[130]=f[2]; h[131]=f[3]; }

  f=(char *)&hdr->ccdlength;
  if (f != h+132) { h[132]=f[0]; h[133]=f[1]; h[134]=f[2]; h[135]=f[3]; }

  f=(char *)&hdr->defocus;
  if (f != h+136) { h[136]=f[0]; h[137]=f[1]; h[138]=f[2]; h[139]=f[3]; }

  f=(char *)&hdr->astig;
  if (f != h+140) { h[140]=f[0]; h[141]=f[1]; h[142]=f[2]; h[143]=f[3]; }

  f=(char *)&hdr->astigdir;
  if (f != h+144) { h[144]=f[0]; h[145]=f[1]; h[146]=f[2]; h[147]=f[3]; }

  f=(char *)&hdr->defocusinc;
  if (f != h+148) { h[148]=f[0]; h[149]=f[1]; h[150]=f[2]; h[151]=f[3]; }

  f=(char *)&hdr->counts;
  if (f != h+152) { h[152]=f[0]; h[153]=f[1]; h[154]=f[2]; h[155]=f[3]; }

  f=(char *)&hdr->c2;
  if (f != h+156) { h[156]=f[0]; h[157]=f[1]; h[158]=f[2]; h[159]=f[3]; }

  f=(char *)&hdr->slit;
  if (f != h+160) { h[160]=f[0]; h[161]=f[1]; h[162]=f[2]; h[163]=f[3]; }

  f=(char *)&hdr->offs;
  if (f != h+164) { h[164]=f[0]; h[165]=f[1]; h[166]=f[2]; h[167]=f[3]; }

  f=(char *)&hdr->tiltangle;
  if (f != h+168) { h[168]=f[0]; h[169]=f[1]; h[170]=f[2]; h[171]=f[3]; }

  f=(char *)&hdr->tiltdir;
  if (f != h+172) { h[172]=f[0]; h[173]=f[1]; h[174]=f[2]; h[175]=f[3]; }

  f=(char *)&hdr->internal21;
  if (f != h+176) { h[176]=f[0]; h[177]=f[1]; h[178]=f[2]; h[179]=f[3]; }

  f=(char *)&hdr->internal22;
  if (f != h+180) { h[180]=f[0]; h[181]=f[1]; h[182]=f[2]; h[183]=f[3]; }

  f=(char *)&hdr->internal23;
  if (f != h+184) { h[184]=f[0]; h[185]=f[1]; h[186]=f[2]; h[187]=f[3]; }

  f=(char *)&hdr->subframex0;
  if (f != h+188) { h[188]=f[0]; h[189]=f[1]; h[190]=f[2]; h[191]=f[3]; }

  f=(char *)&hdr->subframey0;
  if (f != h+192) { h[192]=f[0]; h[193]=f[1]; h[194]=f[2]; h[195]=f[3]; }

  f=(char *)&hdr->resolution;
  if (f != h+196) { h[196]=f[0]; h[197]=f[1]; h[198]=f[2]; h[199]=f[3]; }

  f=(char *)&hdr->density;
  if (f != h+200) { h[200]=f[0]; h[201]=f[1]; h[202]=f[2]; h[203]=f[3]; }

  f=(char *)&hdr->contrast;
  if (f != h+204) { h[204]=f[0]; h[205]=f[1]; h[206]=f[2]; h[207]=f[3]; }

  f=(char *)&hdr->unknown;
  if (f != h+208) { h[208]=f[0]; h[209]=f[1]; h[210]=f[2]; h[211]=f[3]; }

  f=(char *)&hdr->cmx;
  if (f != h+212) { h[212]=f[0]; h[213]=f[1]; h[214]=f[2]; h[215]=f[3]; }

  f=(char *)&hdr->cmy;
  if (f != h+216) { h[216]=f[0]; h[217]=f[1]; h[218]=f[2]; h[219]=f[3]; }

  f=(char *)&hdr->cmz;
  if (f != h+220) { h[220]=f[0]; h[221]=f[1]; h[222]=f[2]; h[223]=f[3]; }

  f=(char *)&hdr->cmh;
  if (f != h+224) { h[224]=f[0]; h[225]=f[1]; h[226]=f[2]; h[227]=f[3]; }

  f=(char *)&hdr->reserved34;
  if (f != h+228) { h[228]=f[0]; h[229]=f[1]; h[230]=f[2]; h[231]=f[3]; }

  f=(char *)&hdr->d1;
  if (f != h+232) { h[232]=f[0]; h[233]=f[1]; h[234]=f[2]; h[235]=f[3]; }

  f=(char *)&hdr->d2;
  if (f != h+236) { h[236]=f[0]; h[237]=f[1]; h[238]=f[2]; h[239]=f[3]; }

  f=(char *)&hdr->lambda;
  if (f != h+240) { h[240]=f[0]; h[241]=f[1]; h[242]=f[2]; h[243]=f[3]; }

  f=(char *)&hdr->dtheta;
  if (f != h+244) { h[244]=f[0]; h[245]=f[1]; h[246]=f[2]; h[247]=f[3]; }

  f=(char *)&hdr->reserved39;
  if (f != h+248) { h[248]=f[0]; h[249]=f[1]; h[250]=f[2]; h[251]=f[3]; }

  f=(char *)&hdr->reserved40;
  if (f != h+252) { h[252]=f[0]; h[253]=f[1]; h[254]=f[2]; h[255]=f[3]; }

  f=(char *)hdr->username;
  if (f != h+256) { size_t i=0; while (i < 20) { h[i+256]=f[i]; i++; } }

  f=(char *)hdr->date;
  if (f != h+276) { size_t i=0; while (i < 8) { h[i+276]=f[i]; i++; } }

  f=(char *)hdr->extra;
  if (f != h+284) { size_t i=0; while (i < 228) { h[i+284]=f[i]; i++; } }

}


static void EMHeaderUnpack
            (EMHeader *hdr)

{
  char *f,*h=(char *)hdr;

  f=(char *)hdr->extra;
  if (f != h+284) { size_t i=228; while (i) { --i; f[i]=h[i+284]; } }

  f=(char *)hdr->date;
  if (f != h+276) { size_t i=8; while (i) { --i; f[i]=h[i+276]; } }

  f=(char *)hdr->username;
  if (f != h+256) { size_t i=20; while (i) { --i; f[i]=h[i+256]; } }

  f=(char *)&hdr->reserved40;
  if (f != h+252) { f[3]=h[255]; f[2]=h[254]; f[1]=h[253]; f[0]=h[252]; }

  f=(char *)&hdr->reserved39;
  if (f != h+248) { f[3]=h[251]; f[2]=h[250]; f[1]=h[249]; f[0]=h[248]; }

  f=(char *)&hdr->dtheta;
  if (f != h+244) { f[3]=h[247]; f[2]=h[246]; f[1]=h[245]; f[0]=h[244]; }

  f=(char *)&hdr->lambda;
  if (f != h+240) { f[3]=h[243]; f[2]=h[242]; f[1]=h[241]; f[0]=h[240]; }

  f=(char *)&hdr->d2;
  if (f != h+236) { f[3]=h[239]; f[2]=h[238]; f[1]=h[237]; f[0]=h[236]; }

  f=(char *)&hdr->d1;
  if (f != h+232) { f[3]=h[235]; f[2]=h[234]; f[1]=h[233]; f[0]=h[232]; }

  f=(char *)&hdr->reserved34;
  if (f != h+228) { f[3]=h[231]; f[2]=h[230]; f[1]=h[229]; f[0]=h[228]; }

  f=(char *)&hdr->cmh;
  if (f != h+224) { f[3]=h[227]; f[2]=h[226]; f[1]=h[225]; f[0]=h[224]; }

  f=(char *)&hdr->cmz;
  if (f != h+220) { f[3]=h[223]; f[2]=h[222]; f[1]=h[221]; f[0]=h[220]; }

  f=(char *)&hdr->cmy;
  if (f != h+216) { f[3]=h[219]; f[2]=h[218]; f[1]=h[217]; f[0]=h[216]; }

  f=(char *)&hdr->cmx;
  if (f != h+212) { f[3]=h[215]; f[2]=h[214]; f[1]=h[213]; f[0]=h[212]; }

  f=(char *)&hdr->unknown;
  if (f != h+208) { f[3]=h[211]; f[2]=h[210]; f[1]=h[209]; f[0]=h[208]; }

  f=(char *)&hdr->contrast;
  if (f != h+204) { f[3]=h[207]; f[2]=h[206]; f[1]=h[205]; f[0]=h[204]; }

  f=(char *)&hdr->density;
  if (f != h+200) { f[3]=h[203]; f[2]=h[202]; f[1]=h[201]; f[0]=h[200]; }

  f=(char *)&hdr->resolution;
  if (f != h+196) { f[3]=h[199]; f[2]=h[198]; f[1]=h[197]; f[0]=h[196]; }

  f=(char *)&hdr->subframey0;
  if (f != h+192) { f[3]=h[195]; f[2]=h[194]; f[1]=h[193]; f[0]=h[192]; }

  f=(char *)&hdr->subframex0;
  if (f != h+188) { f[3]=h[191]; f[2]=h[190]; f[1]=h[189]; f[0]=h[188]; }

  f=(char *)&hdr->internal23;
  if (f != h+184) { f[3]=h[187]; f[2]=h[186]; f[1]=h[185]; f[0]=h[184]; }

  f=(char *)&hdr->internal22;
  if (f != h+180) { f[3]=h[183]; f[2]=h[182]; f[1]=h[181]; f[0]=h[180]; }

  f=(char *)&hdr->internal21;
  if (f != h+176) { f[3]=h[179]; f[2]=h[178]; f[1]=h[177]; f[0]=h[176]; }

  f=(char *)&hdr->tiltdir;
  if (f != h+172) { f[3]=h[175]; f[2]=h[174]; f[1]=h[173]; f[0]=h[172]; }

  f=(char *)&hdr->tiltangle;
  if (f != h+168) { f[3]=h[171]; f[2]=h[170]; f[1]=h[169]; f[0]=h[168]; }

  f=(char *)&hdr->offs;
  if (f != h+164) { f[3]=h[167]; f[2]=h[166]; f[1]=h[165]; f[0]=h[164]; }

  f=(char *)&hdr->slit;
  if (f != h+160) { f[3]=h[163]; f[2]=h[162]; f[1]=h[161]; f[0]=h[160]; }

  f=(char *)&hdr->c2;
  if (f != h+156) { f[3]=h[159]; f[2]=h[158]; f[1]=h[157]; f[0]=h[156]; }

  f=(char *)&hdr->counts;
  if (f != h+152) { f[3]=h[155]; f[2]=h[154]; f[1]=h[153]; f[0]=h[152]; }

  f=(char *)&hdr->defocusinc;
  if (f != h+148) { f[3]=h[151]; f[2]=h[150]; f[1]=h[149]; f[0]=h[148]; }

  f=(char *)&hdr->astigdir;
  if (f != h+144) { f[3]=h[147]; f[2]=h[146]; f[1]=h[145]; f[0]=h[144]; }

  f=(char *)&hdr->astig;
  if (f != h+140) { f[3]=h[143]; f[2]=h[142]; f[1]=h[141]; f[0]=h[140]; }

  f=(char *)&hdr->defocus;
  if (f != h+136) { f[3]=h[139]; f[2]=h[138]; f[1]=h[137]; f[0]=h[136]; }

  f=(char *)&hdr->ccdlength;
  if (f != h+132) { f[3]=h[135]; f[2]=h[134]; f[1]=h[133]; f[0]=h[132]; }

  f=(char *)&hdr->ccdpixel;
  if (f != h+128) { f[3]=h[131]; f[2]=h[130]; f[1]=h[129]; f[0]=h[128]; }

  f=(char *)&hdr->emcode;
  if (f != h+124) { f[3]=h[127]; f[2]=h[126]; f[1]=h[125]; f[0]=h[124]; }

  f=(char *)&hdr->objpixel;
  if (f != h+120) { f[3]=h[123]; f[2]=h[122]; f[1]=h[121]; f[0]=h[120]; }

  f=(char *)&hdr->exposure;
  if (f != h+116) { f[3]=h[119]; f[2]=h[118]; f[1]=h[117]; f[0]=h[116]; }

  f=(char *)&hdr->postmag;
  if (f != h+112) { f[3]=h[115]; f[2]=h[114]; f[1]=h[113]; f[0]=h[112]; }

  f=(char *)&hdr->mag;
  if (f != h+108) { f[3]=h[111]; f[2]=h[110]; f[1]=h[109]; f[0]=h[108]; }

  f=(char *)&hdr->aperture;
  if (f != h+104) { f[3]=h[107]; f[2]=h[106]; f[1]=h[105]; f[0]=h[104]; }

  f=(char *)&hdr->Cs;
  if (f != h+100) { f[3]=h[103]; f[2]=h[102]; f[1]=h[101]; f[0]=h[100]; }

  f=(char *)&hdr->voltage;
  if (f != h+96) { f[3]=h[99]; f[2]=h[98]; f[1]=h[97]; f[0]=h[96]; }

  f=(char *)hdr->label;
  if (f != h+16) { size_t i=80; while (i) { --i; f[i]=h[i+16]; } }

  f=(char *)&hdr->nz;
  if (f != h+12) { f[3]=h[15]; f[2]=h[14]; f[1]=h[13]; f[0]=h[12]; }

  f=(char *)&hdr->ny;
  if (f != h+8) { f[3]=h[11]; f[2]=h[10]; f[1]=h[9]; f[0]=h[8]; }

  f=(char *)&hdr->nx;
  if (f != h+4) { f[3]=h[7]; f[2]=h[6]; f[1]=h[5]; f[0]=h[4]; }

  f=(char *)&hdr->datatype;
  if (f != h+3) { f[0]=h[3]; }

  f=(char *)&hdr->unused;
  if (f != h+2) { f[0]=h[2]; }

  f=(char *)&hdr->general;
  if (f != h+1) { f[0]=h[1]; }

  f=(char *)&hdr->machine;
  if (f != h+0) { f[0]=h[0]; }

}


static void EMHeaderSwap
            (EMHeader *hdr)

{
  char *h = (char *)hdr;

  Swap32( 3, h+4, h+4 );
  Swap32( 40, h+96, h+96 );

}


extern Status EMHeaderRead
              (Imageio *imageio,
               EMHeader *hdr)

{
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );
  if ( argcheck( hdr == NULL ) ) return pushexception( E_ARGVAL );

  /* read into buffer */
  status = FileioRead( imageio->fileio, 0, EMHeaderSize, hdr );
  if ( pushexception( status ) ) return status;

  /* swap if non-native byte order */
  if ( imageio->iostat & ImageioByteSwap ) {
    EMHeaderSwap( hdr );
  }

  /* unpack header, code may be removed by optimization */
  if ( sizeof(EMHeader) > EMHeaderSize ) {
    EMHeaderUnpack( hdr );
  }

  return E_NONE;

}


extern Status EMHeaderWrite
              (Imageio *imageio)

{
  EMMeta *meta;
  EMHeader *hdr;
  EMHeader buf;
  Status status;

  if ( argcheck( imageio == NULL ) ) return pushexception( E_ARGVAL );

  /* temp copy of header */
  meta = imageio->meta;
  hdr = &meta->header;
  buf = *hdr;

  /* set open flag */
  if ( ~imageio->iostat & ImageioFinClose ) {
    buf.datatype = EMundef;
  }

  /* pack header, code may be removed by optimization */
  if ( sizeof(EMHeader) > EMHeaderSize ) {
    EMHeaderPack( &buf );
  }
  /* swap if non-native byte order */
  if ( imageio->iostat & ImageioByteSwap ) {
      EMHeaderSwap( &buf );
  }

  /* write to file */
  if ( imageio->iocap == ImageioCapStd ) {
    status = FileioWriteStd( imageio->fileio, 0, EMHeaderSize, &buf );
    if ( pushexception( status ) ) return status; 
  } else {
    status = FileioWrite( imageio->fileio, 0, EMHeaderSize, &buf );
    if ( pushexception( status ) ) return status;
  }

  /* flush buffers */
  status = FileioFlush( imageio->fileio );
  if ( pushexception( status ) ) return status;

  return E_NONE;

}
