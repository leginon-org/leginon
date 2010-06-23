#include "util.h"

f32  randomNumber( f32 min, f32 max) {
//	if ( rand_seeded == 0 ) srand(time(NULL));
	f32 random = (f32)rand() / RAND_MAX;
	random = random*(max-min) + min;
	return random;
}

void byteSwap2( u08 *data ) {
	u08 temp = data[0];
	data[0]  = data[1];
	data[1]  = temp;
}

void byteSwap4( u08 *data ) {
	u08 temp1 = data[0];
	u08 temp2 = data[1];
	data[0]   = data[3];
	data[1]   = data[2];
	data[2]   = temp2;
	data[3]   = temp1;
}

u32  byteSwapRead( FILE *fp, void *data, u32 number_of_elements, u32 element_size ) {
	if ( !fp || !data ) return 0;
	u32 count = fread(data,element_size,number_of_elements,fp);
	if ( count != number_of_elements ) return 0;
	if ( IS_BIG_ENDIAN ) byteSwapBuffer(data,number_of_elements,element_size);
	return count;	
}

u32  byteSwapWrite( FILE *fp, void *data, u32 number_of_elements, u32 element_size ) {
	if ( !fp || !data ) return 0;
	char *copy = NEWV(char,element_size*number_of_elements);
	if ( !copy ) return 0;
	memcpy(copy,data,element_size*number_of_elements);
	if ( IS_BIG_ENDIAN ) byteSwapBuffer(copy,number_of_elements,element_size);
	u32 count = fwrite(copy,element_size,number_of_elements,fp);
	free(copy);
	return count;
} 

u32  byteSwapBuffer( void *data, u32 number_of_elements, u32 element_size ) {
	u32 k = 0;
	if ( !data  ) return k;
	for(k=0;k<number_of_elements;k++) {
		if (element_size == 2) byteSwap2(data);
		if (element_size == 4) byteSwap4(data);
		data += element_size;
	}
	return k;
}
