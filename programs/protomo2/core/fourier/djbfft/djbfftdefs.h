/*----------------------------------------------------------------------------*
*
*  djbfftdefs.h  -  djbfft: fast Fourier transforms
*
*----------------------------------------------------------------------------*/

#ifndef djbfftdefs_h_
#define djbfftdefs_h_

#include "fourierdefs.h"


/* external functions */

extern void fftfreq_rtable( unsigned int *, unsigned int );
extern void fftfreq_ctable( unsigned int *, unsigned int );

extern void fftr4_2( Real32 * );
extern void fftr4_4( Real32 * );
extern void fftr4_8( Real32 * );
extern void fftr4_16( Real32 * );
extern void fftr4_32( Real32 * );
extern void fftr4_64( Real32 * );
extern void fftr4_128( Real32 * );
extern void fftr4_256( Real32 * );
extern void fftr4_512( Real32 * );
extern void fftr4_1024( Real32 * );
extern void fftr4_2048( Real32 * );
extern void fftr4_4096( Real32 * );
extern void fftr4_8192( Real32 * );

#define fftr4_un2 fftr4_2
extern void fftr4_un4( Real32 * );
extern void fftr4_un8( Real32 * );
extern void fftr4_un16( Real32 * );
extern void fftr4_un32( Real32 * );
extern void fftr4_un64( Real32 * );
extern void fftr4_un128( Real32 * );
extern void fftr4_un256( Real32 * );
extern void fftr4_un512( Real32 * );
extern void fftr4_un1024( Real32 * );
extern void fftr4_un2048( Real32 * );
extern void fftr4_un4096( Real32 * );
extern void fftr4_un8192( Real32 * );

extern void fftc4_2( Cmplx32 * );
extern void fftc4_4( Cmplx32 * );
extern void fftc4_8( Cmplx32 * );
extern void fftc4_16( Cmplx32 * );
extern void fftc4_32( Cmplx32 * );
extern void fftc4_64( Cmplx32 * );
extern void fftc4_128( Cmplx32 * );
extern void fftc4_256( Cmplx32 * );
extern void fftc4_512( Cmplx32 * );
extern void fftc4_1024( Cmplx32 * );
extern void fftc4_2048( Cmplx32 * );
extern void fftc4_4096( Cmplx32 * );
extern void fftc4_8192( Cmplx32 * );

#define fftc4_un2 fftc4_2
extern void fftc4_un4( Cmplx32 * );
extern void fftc4_un8( Cmplx32 * );
extern void fftc4_un16( Cmplx32 * );
extern void fftc4_un32( Cmplx32 * );
extern void fftc4_un64( Cmplx32 * );
extern void fftc4_un128( Cmplx32 * );
extern void fftc4_un256( Cmplx32 * );
extern void fftc4_un512( Cmplx32 * );
extern void fftc4_un1024( Cmplx32 * );
extern void fftc4_un2048( Cmplx32 * );
extern void fftc4_un4096( Cmplx32 * );
extern void fftc4_un8192( Cmplx32 * );


#endif
