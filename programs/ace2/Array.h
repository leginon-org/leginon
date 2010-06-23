#ifndef libCV_array
#define libCV_array

#include <objc/Object.h>
#include "cvtypes.h"
#include "util.h"

#define NAME_LENGTH 1024

// Array *FLAGS*, note there is some overlap for compatibility with cvtypes data flags, these are left as comments
#define CV_ARRAY_THREAD_LOCKED		( 1 << 0 )		// Set if the Array data is being manipulated using threaded processes
#define CV_ARRAY_PREFERS_IMAGINARY	( 1 << 1 )		// Set to what type of complex data the array should prefer if a type conversion occurs
#define CV_ARRAY_DATA_SCALES		( 1 << 2 )		// Set if the data in the array is meant to maintain precision
#define CV_ARRAY_REFERS_DATA		( 1 << 3 )		// Set if the Array does not own it's own data pointer
#define CV_ARRAY_STATS_ARE_VALID    ( 1 << 4 )		// Set if the statistics for the array data are valid ( if not, stats are invalid )

#define CV_ITERATOR_INCREASING		1
#define CV_ITERATOR_DECREASING		0

#define CV_POSITION_FORMAT	0
#define CV_INDEX_FORMAT		1

/* Array Iterator functions  -----------------------------------------------*/

typedef struct ArrayIterator {
	u32 ndim;
	u32 min_offset;
	u32 max_offset;
	u32 cur_offset;
	u32 * dim_step;
	u32 * dim_size;
	u32 * dim_jump;
	s32 * min_bounds;
	s32 * max_bounds;
	s32 * cur_position;
	u08 direction;
} ArrayIterator;

typedef ArrayIterator * ArrayIteratorP;

typedef struct u32v {
	u32   size;
	u32 * data;
} u32v;


ArrayIteratorP createArrayIterator( u32 ndim, u32 * dims, u32 * steps );
inline u32 startArrayIterator( ArrayIteratorP iterator, bool direction );
inline u32 incrementArrayIterator( ArrayIteratorP ite );
inline u32 decrementArrayIterator( ArrayIteratorP ite );
void freeArrayIterator( ArrayIteratorP ite );

/*-------------------------------------------------------------------------*/

/* Structure and functions for testing if array location is on a border */

typedef struct BorderTesterSt {
	u32 ndim;
	u32 * f_steps;
	u32 * b_steps;
} BorderTester;

typedef BorderTester * BorderTesterP;	

BorderTesterP createBorderTester( const u32 ndim, const u32 dims[], const u32 stps[] );
void freeBorderTester( BorderTesterP tester );
u08 testBorder( s64 loc, BorderTesterP tester );

/*----------------------------------------------------------------------*/

@interface Array : Object {

	u32			type;
	u32			size;
	size_t		esize;
	size_t		memory;
	u32			ref_count;
	
	u32			ndim;				// Number of dimensions
	char		name[NAME_LENGTH];	// A string name for this array
	u32			flags;				// Set of flags for this array ( see *FLAGS* section above )
	
	f64			maxv;				// Maximum value of data
	f64			minv;				// Minimum value of data
	f64			mean;				// Mean value of data
	f64			stdv;				// Standard Deviation of data

	u32		*	dim_size;			// # of elements along each dimension
	u32		*	dim_step;			// Steps in memory required to advance one element along each dimension

	void    *   data;				// Pointer to the beginning of memory allocated to hold the data
	id			original;
	
}

+(id) newWithType:(u32)totype andDimensions:(u32 *)dimensions;
+(id) newWithType:(u32)totype andSize:(u32)tosize;
-(void)  writeToFile:(FILE *)fp;
-(id) copy;
-(id) deepCopy;
-(id) init;

-(void *)getRow:(u64)row;
-(void *)getSlice:(u64)slice;
-(void) getIndex:(u64 *)index forPosition:(u64 *)position;
-(void) getPosition:(u64 *)position forIndex:(u64 *)index;

-(void *)	dataAsType:(u32)totype withFlags:(u32)flags;
-(void)	rotate;
-(void)	printInfoTo:(FILE *)fp;
-(void)	release;
-(void) retain;

-(void)	calculateStats;
-(u32)	compareDimensions:(id)array;

/* Getters */

-(char *) name;
-(u08)	type;
-(u08) isType:(u08)istype;
-(void *) data;
-(u32)	numberOfElements;
-(u32)	elementType;
-(u32)	numberOfDimensions;
-(u32)	elementSize;
-(u32 *) dimensions;
-(u32 *) strides;
-(f32)	maxValue;
-(f32)	minValue;
-(f32)	meanValue;
-(f32)	standardDeviation;
-(u32)	sizeOfDimension: (u32)n;
-(u32)	strideAlong: (u32)n;
-(u32)	getFlag:(u32)flag;

/* Setters */

-(void) setMinValue: (f32)tominv;
-(void) setMaxValue: (f32)tomaxv;
-(void) setMeanValue: (f32)tomean;
-(void) setStandardDeviation: (f32)tostdv;
-(void) setNameTo: (char *)toname;
-(id) setDataTo: (void *)todata;
-(void) setShapeTo: (const u32 *)dimensions;
-(void) setTypeTo: (u32)totype;
-(void)	setFlag:(u32)flag to:(bool)value;
-(void) setStridesTo:(u32 *)strides;
-(void) setOriginal:(id)object;

-(u64) countByComparingTo:(f64)value using:(bool(*)(f64, f64))f_comp;

-(id) findByComparingTo:(f64)value using:(bool(*)(f64, f64))f_comp inFormat:(u08)format;

-(ArrayIteratorP) arrayIterator;
-(BorderTesterP) borderTester;


-(void) sqrt;
-(id) ln;
-(void) exp;
-(void) qsort;
-(void) add:(id)a;
-(void) subtract:(id)a;
-(void) multiply:(id)a;
-(void) divide:(id)a;

@end

typedef Array * ArrayP;

bool lessThanOrEqualTo( f64 v1, f64 v2 );
bool greaterThanOrEqualTo( f64 v1, f64 v2 );
bool equalTo( f64 v1, f64 v2 );

u64 sizeFromDims( u32 dims[], u32 ndim );
void flipDims( u32 dims[], u32 ndim );

#endif
