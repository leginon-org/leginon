#include "Array.h"

int compare_f64( const void * a, const void * b );

@implementation Array

+(id) newWithType:(u32)totype andDimensions:(u32 *)dimensions {

	ArrayP new_array = [[Array alloc] init];

	[new_array setTypeTo:totype];
	[new_array setShapeTo:dimensions];

	return new_array;

}

+(id) newWithType:(u32)totype andSize:(u32)tosize {

	u32 new_dims[2] = {tosize, 0};
	return [self newWithType:totype andDimensions:new_dims];

}

-(id) readFromFile:(FILE *)fp {
	
	/* Reads the Array object from a file stream in binary format.  Note that pointer data is also read */
	
	/* Free any extra data already belonging to the Array to prevent memory leaks */
	if (data) free(data);
	if (dim_size) free(dim_size);
	if (dim_step) free(dim_step); 	
	
	/* Read in the object */
	fread(self,sizeof(Array),1,fp);
	
	
	/* Check the object pointers, if they are not NULL, then the data for the pointers should exist in the
	file stream and need to be read in */
	
	if ( dim_size != NULL ) {
		dim_size = NEWV(u32,ndim);
		fread(dim_size,sizeof(u32),ndim,fp);
	}
	
	if ( dim_step != NULL ) {
		dim_step = NEWV(u32,ndim);
		fread(dim_step,sizeof(u32),ndim,fp);
	}
	
	if ( data != NULL ) {
		data = malloc(memory);
		fread(data,esize,size,fp);
	}
	
	return self;
	
}

-(void) writeToFile:(FILE *)fp {
	
	/* Writes the Array object to a file stream in binary format.  Note that pointer data is also written, as well
	as the data the pointers point to.  This additional data is written in the order given in the object declaration */
	
	fwrite(self,sizeof(Array),1,fp);
	
	if ( dim_size != NULL ) fwrite(dim_size,sizeof(u32),ndim,fp);
	if ( dim_step != NULL ) fwrite(dim_step,sizeof(u32),ndim,fp);
	if ( data != NULL ) fwrite(data,esize,size,fp);
	
	return;

}

-(id) copy {
	
	ArrayP new = [[Array alloc] init];
	
	if ( new == nil ) return new;
	
	new->dim_size = COPYV(dim_size,sizeof(u32)*(ndim+1));
	new->dim_step = COPYV(dim_step,sizeof(u32)*(ndim+1));
	
	sprintf(new->name,"%s",name);
	
	new->ndim = ndim;
	new->type = type;
	new->size = size;
	new->esize = esize;
	new->memory = memory;
	
	new->ref_count = 1;
	
	new->flags = flags;
	[new setFlag:CV_ARRAY_REFERS_DATA to:TRUE];
	
	new->data = data;
	new->original = self;
	
	[self retain];
	
	return new;
	
}

-(id) deepCopy {
	
	ArrayP new = [self copy];
	
	if ( new == nil ) return new;
	
	[new setFlag:CV_ARRAY_REFERS_DATA to:FALSE];
	void * temp = malloc(memory);	
	memcpy(temp,data,memory);
	new->data = temp;
	new->original = nil;
	
	return new;
	
}

-(void *)getRow:(u64)row {
	
	if ( ndim < 2 ) return NULL;
	
	void * off = [self data];
	if ( off == NULL ) return NULL;
	else return off + [self sizeOfDimension:0]*[self elementSize]*row; 

}

-(void *)getSlice:(u64)slice {
	
	if ( ndim < 3 ) return NULL;
	
	void * off = [self data];
	if ( off == NULL ) return NULL;
	else return off + [self strideAlong:2]*[self elementSize]*slice; 

}

-(id) sliceArrayFrom:(u32 *)origin to:(u32 *)new_dims {
	
	if ( origin == NULL || new_dims == NULL ) return nil;
	
	/* Note: origin is inclusive, but new_dims is not!! So an array that starts at 5,5 with dims 10,10*/
	/* has ten spaces in each dimension and goes from 5 to 14 (inclusive) */
	
	u32 i;
	u32 memory_offset = 0;
	
	for (i=0;i<ndim;i++) {
		origin[i] = MIN(origin[i],dim_size[i]-1);
		new_dims[i] = MIN(new_dims[i],dim_size[i]-1);
	}
	
	/* Find the memory offset for the starting point based on origin */
	
	for (i=0;i<ndim;i++) memory_offset += origin[i] * dim_step[i];
	

	/* For speed reasons there is no reason why the sliced Array should take into account degenerate dimensions, that is dimensions
	where the bounds have been set so as to take only a single slice along that dimension.  For example in a 3D array with bounds 
	0-10,0-10,0-10 and a slice with bounds 5-5,3-8,7-7 then the first and last dimensions are degenerate and what we really have 
	is a 1D vector along the second dimension */
	
	u32 new_ndim = 0;
	u32 * new_step = NEWV(u32,ndim+1);
	
	for (i=0;i<ndim;i++) {
		if ( new_dims[i] == 1 ) continue; // Degenerate dimension
		new_step[new_ndim] = dim_step[i];
		new_dims[new_ndim] = new_dims[i];
		new_ndim++;
	}
	
	// Remember to mark the end of the arrays!
	new_dims[new_ndim] = 0;
	new_step[new_ndim] = 0;
	
	ArrayP slice = [[Array alloc] init];
	
	[slice setTypeTo: type];
	[slice setShapeTo:new_dims];
	[slice setStridesTo:new_step];
	[slice setDataTo:[self data]+memory_offset];
	[slice setOriginal:self];
	
	return slice;

}

-(id) init {
	
	self = [super init];
	
	type		= TYPE_NULL;
	ndim		= 0;
	ref_count	= 1;
	size		= 0;
	esize		= 0;
	memory		= 0;
	flags		= 0;
	
	maxv        = 0.0;
	minv        = 0.0;
	mean        = 0.0;
	stdv        = 0.0;
	
	data        = NULL;
	dim_size	= NULL;
	dim_step 	= NULL;
	
	original	= nil;
	
	sprintf(name,"New Array");
	
	return self;
	
}

-(void) getIndex:(u64 *)index forPosition:(u64 *)position {
	
	u64 d;
	for(d=0;d<ndim;d++) index[0] += position[d] * dim_step[d];
	
}

-(void) getPosition:(u64 *)position forIndex:(u64 *)index {
	
	s64 d;
	for(d=ndim-1;d>=0;d--) {
		position[d] = index[0] / dim_step[d];
		index[0] = index[0] % dim_step[d];
	}

}

-(void *) dataAsType:(u32)totype withFlags:(u32)dataFlags {
	return TO_TYPE(data,size,type,totype,dataFlags);
}

-(void)	rotate {
	
	if ( ndim < 2 ) return;
	
	u32 k, i = 1;
	
	u32 *rotDim = NEWV(u32,ndim);
	u32 *rotIdx = NEWV(u32,ndim);
	u32 *rotStp = NEWV(u32,ndim);
	
	for(k=0;k<ndim;k++) rotIdx[k] = 0;
	
	for(k=1;k<=ndim;k++) rotDim[k%ndim] = dim_size[k-1];
	for(k=1;k<=ndim;k++) rotStp[k%ndim] = dim_step[k-1];
		
	void *copy = malloc(memory);
	if ( !copy ) return;
	
	u32 fromIdx = 0;
	for(k=0;k<size;k++) {
		
		rotIdx[0]++;
		
		for(i=0;i<ndim;i++) {
			if ( rotIdx[i] == rotDim[i] ) {
				rotIdx[i]    = 0;
				rotIdx[i+1] += 1;
			}
		}
		
		u32 toIdx = 0;
		for(i=0;i<ndim;i++) toIdx += rotIdx[i] * rotStp[i];

		toIdx   *= esize;
		fromIdx += esize;
		
		if ( toIdx   >= memory ) continue;
		if ( fromIdx >= memory ) continue;
		
		memcpy(copy+toIdx,data+fromIdx,esize);
		
	}
	
	i = 1;
	for(k=0;k<ndim;k++) dim_size[k] = rotDim[k];
	for(k=0;k<ndim;k++) {
		dim_step[k] = i;
		i *= dim_size[k];
	}
	
	free(rotDim);
	free(rotIdx);
	free(rotStp);
	
	free(data);
	data = copy;
	
}

-(void)	printInfoTo:(FILE *)fp {
	
	u32 k;
	
	fprintf(fp,"--------Array Info---------\n");
	fprintf(fp,"Name: %s\n",name);
	fprintf(fp,"Type:  %s\n",TYPE_STRINGS[type]);
	fprintf(fp,"Element Size: %u Bytes\n",(u32)esize);
	fprintf(fp,"Number of Elements: %d\n",(u32)size);
	fprintf(fp,"Memory: %2.2f MB\n",(f32)memory/MB);
	fprintf(fp,"Dimensions: %u\n",ndim);
	fprintf(fp,"Mean: %.1e +- %.1e\n",[self meanValue],[self standardDeviation]);	
	fprintf(fp,"Extremes: %.1e <> %.1e\n",[self minValue],[self maxValue]);	

	fprintf(fp,"Bounds:  ");
	for(k=0;k<ndim;k++) fprintf(fp,"%u ",dim_size[k]);
	fprintf(fp,"\n");
	
	fprintf(fp,"Strides: ");
	for(k=0;k<ndim;k++) fprintf(fp,"%u ",dim_step[k]);
	fprintf(fp,"\n");
	
	if ( !data ) fprintf(stderr,"Data is null\n");
	
}

-(void) printContentsTo:(FILE *)fp {
	
	u32 k;
	f64 * t = data;
	
	for(k=0;k<size;k++) fprintf(fp,"%f\n",t[k]); 
	
}

-(void)	release {
	ref_count--;
	if ( ref_count == 0 ) {
		if ( dim_step != NULL ) free(dim_step);
		if ( dim_size != NULL ) free(dim_size);
		if ( original != nil ) [original release];
		else if ( data != NULL ) free(data);
		[super free];
	}
}

-(void) retain {
	ref_count++;
}

-(u32)	getFlag:(u32)flag {
	return flags & flag;
}

-(void)	setFlag:(u32)flag to:(bool)value {
	flags |= (value*flag);
}

-(void)	calculateStats {
	if ( [self getFlag:CV_ARRAY_STATS_ARE_VALID] ) return;
	f64 * copy = [self dataAsType:TYPE_F64 withFlags:CV_COPY_DATA];
	[self setMinValue:MIN_F64(copy,size)];
	[self setMaxValue:MAX_F64(copy,size)];
	[self setMeanValue:MEAN_F64(copy,size)];
	[self setStandardDeviation:STDV_F64(copy,size,mean)];
	[self setFlag:CV_ARRAY_STATS_ARE_VALID to:TRUE];
	free(copy);
}

-(u32)	compareDimensions:(id)a {
	
	u32 k;
	if ( [self numberOfDimensions] != [a numberOfDimensions] ) return FALSE;
	for(k=0;k<ndim;k++) if ( [self sizeOfDimension:k] != [a sizeOfDimension:k] ) return FALSE;
	return TRUE;
	
}

/* Getters */

-(u08) isType:(u08)istype {
	if ( [self type] == istype ) return TRUE;
	else return FALSE;
}

-(char *)name {
	return name;
}

-(u08) type {
	return type;
}

-(void *) data {
	
	if ( data == NULL ) {
		data = calloc(size,esize);
		if ( data == NULL ) fprintf(stderr,"Error while allocating memory for array %s data\n",[self name]);
	}
	
	[self setFlag:CV_ARRAY_STATS_ARE_VALID to:FALSE];
	return data;
	
}

-(u32)	numberOfElements {
	return size;
}

-(u32)	elementType {
	return type;
}

-(u32)	numberOfDimensions {
	return ndim;
}

-(u32)	elementSize {
	return esize;
}

-(u32 *) dimensions {
	return memcpy(NEWV(u32,ndim+1),dim_size,sizeof(u32)*(ndim+1));
}

-(u32 *) strides {
	return memcpy(NEWV(u32,ndim+1),dim_step,sizeof(u32)*(ndim+1));
}

-(f32)	maxValue {
	[self calculateStats];
	return maxv;
}

-(f32)	minValue {
	[self calculateStats];
	return minv;
}

-(f32)	meanValue {
	[self calculateStats];
	return mean;
}

-(f32)	standardDeviation {
	[self calculateStats];
	return stdv;
}

-(u32)	sizeOfDimension: (u32)n {
	if ( n >= ndim ) return 0;
	else return dim_size[n];
} 

-(u32)	strideAlong: (u32)n {
	if ( n >= ndim ) return 0;
	return dim_step[n];
}

-(id) original {
	return original;
}

/* Setters */

-(void) setMinValue: (f32)tominv {
	minv = tominv;
}

-(void) setMaxValue: (f32)tomaxv {
	maxv = tomaxv;
}

-(void) setMeanValue: (f32)tomean {
	mean = tomean;
}

-(void) setStandardDeviation: (f32)tostdv {
	stdv = tostdv;
}

-(void) setNameTo: (char *)toname {
	sprintf(name,"%s",toname);
}

-(id) setDataTo: (void *)todata {
	if ( data == todata ) return self;
	free(data);
	data = todata;
	return self;
}

-(void) setShapeTo: (const u32 *)dimensions {

	u32 k, total_size = 1;
	
	for(ndim=0;dimensions[ndim]!=0;ndim++);
	
	dim_size = realloc(dim_size,sizeof(u32)*(ndim+1));
	dim_step = realloc(dim_step,sizeof(u32)*(ndim+1));
	
	if ( dim_size == NULL ) goto error;
	if ( dim_step == NULL ) goto error;
	
	for(k=0;k<ndim;k++) {
		dim_size[k] = dimensions[k];
		dim_step[k] = total_size;
		total_size *= dim_size[k];
	}
	
	dim_size[ndim] = 0;
	dim_step[ndim] = 0;
	
	size = total_size;
	memory = esize * size;
	
	if ( data != NULL && memory != 0 ) {
		data = realloc(data,memory);
		if ( data == NULL ) goto error;
	}
	
	return;
	
	error:
	fprintf(stderr,"Ran out of memory during shape change of array: %s\n",[self name]);
	[self release];
	
}

-(void) setTypeTo: (u32)totype {
	
	if ( type == totype ) return;

	esize  = sizeFromType(totype);
	memory = esize * size;	
		
	if ( data != NULL && memory != 0 ) {
		u32 scale_flag = [self getFlag: CV_ARRAY_DATA_SCALES];
		u32 complex_flag = [self getFlag: CV_ARRAY_PREFERS_IMAGINARY];
		data = TO_TYPE(data,size,type,totype,scale_flag|complex_flag);
	}

	type = totype;
		
}

-(void) setStridesTo:(u32 *)strides {
	
	u32 k, total_size = 1;
	
	dim_step = realloc(dim_step,sizeof(u32)*(ndim+1));
	if ( dim_step == NULL ) goto error;
	
	for(k=0;k<ndim;k++) dim_step[k] = strides[k];
	
	return;
	
	error:
	fprintf(stderr,"Ran out of memory assigning new stride to array %s\n",[self name]);
	return;

}

-(void) setOriginal:(id)object {
	[object retain];
	original = object;
}

-(ArrayIteratorP) arrayIterator {
	return createArrayIterator(ndim,dim_size,dim_step);
}

-(BorderTesterP) borderTester {
	return createBorderTester(ndim,dim_size,dim_step);	
}

-(u64) countByComparingTo:(f64)value using:(bool(*)(f64, f64))f_comp {
	
	if ( type != TYPE_F64 ) return 0;
	if ( size == 0 ) return 0;
	
	u64 i, count = 0;
	
	f64 * values = [self data];
	if ( values == NULL ) return 0;
	
	if ( original == nil ) {
		for(i=0;i<size;i++) if ( (*f_comp)(values[i],value) ) count++;
	} else {
		ArrayIteratorP it = [self arrayIterator];
		u64 idx = startArrayIterator(it,CV_ITERATOR_INCREASING);
		for(i=0;i<size;i++) {
			if ( (*f_comp)(values[idx],value) ) count++;
			idx = incrementArrayIterator(it);
		}
		freeArrayIterator(it);
	}
	
	return count;
	
}

-(id) findByComparingTo:(f64)value using:(bool(*)(f64, f64))f_comp inFormat:(u08)format {
	
	ArrayP found = nil;
	u64 * indexes = NULL;
	u64 * points = NULL;
	
	if ( type != TYPE_F64 ) goto error;
	if ( size == 0 ) goto error;
	
	u64 i, count = 0;
	indexes = NEWV(u64,size);
		
	f64 * values = [self data];
	if ( values == NULL ) goto error;
	
	if ( original == nil ) {
		for(i=0;i<size;i++) if ( (*f_comp)(values[i],value) ) indexes[count++] = i;
	} else {
		ArrayIteratorP it = [self arrayIterator];
		u64 idx = startArrayIterator(it,CV_ITERATOR_INCREASING);
		for(i=0;i<size;i++) {
			if ( (*f_comp)(values[idx],value) ) indexes[count++] = idx;
			idx = incrementArrayIterator(it);
		}
		freeArrayIterator(it);
	}
	
	u32 f_dims[3];
	
	switch (format) {
		case CV_INDEX_FORMAT:
			f_dims[0] = count;
			f_dims[1] = 0;
			points = NEWV(u64,count);
			if ( points == NULL ) goto error;
			for(i=0;i<count;i++) points[i] = indexes[i];
			break;
		case CV_POSITION_FORMAT:
			f_dims[0] = ndim;
			f_dims[1] = count;
			f_dims[2] = 0;
			u64 * points = NEWV(u64,ndim*count);
			if ( points == NULL ) goto error;
			for(i=0;i<count;i++) [self getPosition:points+i*ndim forIndex:indexes+i];
			break;
		default:
			goto error;
	}
	
	if ( indexes != NULL ) free(indexes);
	
	found = [Array newWithType:TYPE_U64 andDimensions:f_dims];
	if ( found == nil ) goto error;
	
	[found setDataTo:points];
	
	return found;
	
	error:
	
	if ( points != NULL ) free(points);
	if ( found != nil ) [found release];
	if ( indexes != NULL ) free(indexes);
	
	return nil;
	
}

-(void) sqrt {
	
	if ( type != TYPE_F64 ) return;
	
	u32 i;
	f64 * pix = [self data];
	if ( pix == NULL || size == 0 ) return;
	
	for(i=0;i<size;i++) pix[i] = sqrt(pix[i]);
	
}

-(id) ln {
	
	if ( type != TYPE_F64 ) return;
	
	u32 i;
	f64 * values = [self data];
	if ( values == NULL || size == 0 ) return;
	
	for(i=0;i<size;i++) values[i] = log(values[i]);
	
	return self;
	
}

-(void) exp {
	
	if ( type != TYPE_F64 ) return;
	
	u32 i;
	f64 * values = [self data];
	if ( values == NULL || size == 0 ) return;
	
	for(i=0;i<size;i++) values[i] = exp(values[i]);
	
}

-(void) qsort {
	
	if ( type != TYPE_F64 ) return;
	
	u32 a_size = [self numberOfElements];
	u32 e_size = [self elementSize];
	
	f64 * values = [self data];
	
	if ( values == NULL || a_size == 0 || e_size == 0 ) return;
	
	qsort(values,a_size,e_size,&compare_f64);
	
}

-(void) add:(id) a {
	
	if ( [self type] != TYPE_F64 ) goto error;
	if ( [a type] != TYPE_F64 ) goto error;
	
	s64 i;
	s64 size1 = [self numberOfElements];
	s64 size2 = [a numberOfElements];
	f64 * v1 = [self data], * v2 = [a data];
	
	if ( size2 == 1 ) {
		for(i=0;i<size;i++) v1[i] += v2[0];
	} else if ( size2 == size1 ) {
		for(i=0;i<size1;i++) v1[i] += v2[i];
	}
	return;
	
	error:
	fprintf(stderr,"Attempt to add arrays %s, %s with size %d %d and types %s %s failed\n",
			[self name],[a name],size1,size2,TYPE_STRINGS[[self type]],TYPE_STRINGS[[a type]]);
	return;
	
}

-(void) subtract:(id) a {
	
	if ( [self type] != TYPE_F64 ) goto error;
	if ( [a type] != TYPE_F64 ) goto error;
	
	s64 i;
	s64 size1 = [self numberOfElements];
	s64 size2 = [a numberOfElements];
	f64 * v1 = [self data], * v2 = [a data];
	
	if ( size2 == 1 ) {
		for(i=0;i<size;i++) v1[i] -= v2[0];
	} else if ( size2 == size1 ) {
		for(i=0;i<size1;i++) v1[i] -= v2[i];
	}
	return;
	
	error:
	fprintf(stderr,"Attempt to add arrays %s, %s with size %d %d and types %s %s failed\n",
			[self name],[a name],size1,size2,TYPE_STRINGS[[self type]],TYPE_STRINGS[[a type]]);
	return;
	
}

-(void) multiply:(id) a {
	
	if ( [self type] != TYPE_F64 ) goto error;
	if ( [a type] != TYPE_F64 ) goto error;
	
	s64 i;
	s64 size1 = [self numberOfElements];
	s64 size2 = [a numberOfElements];
	f64 * v1 = [self data], * v2 = [a data];
	
	if ( size2 == 1 ) {
		for(i=0;i<size;i++) v1[i] *= v2[0];
	} else if ( size2 == size1 ) {
		for(i=0;i<size1;i++) v1[i] *= v2[i];
	}
	return;
	
	error:
	fprintf(stderr,"Attempt to add arrays %s, %s with size %d %d and types %s %s failed\n",
			[self name],[a name],size1,size2,TYPE_STRINGS[[self type]],TYPE_STRINGS[[a type]]);
	return;
	
}

-(void) divide:(id) a {
	
	if ( [self type] != TYPE_F64 ) goto error;
	if ( [a type] != TYPE_F64 ) goto error;
	
	s64 i;
	s64 size1 = [self numberOfElements];
	s64 size2 = [a numberOfElements];
	f64 * v1 = [self data], * v2 = [a data];
	
	if ( size2 == 1 ) {
		for(i=0;i<size;i++) v1[i] /= v2[0];
	} else if ( size2 == size1 ) {
		for(i=0;i<size1;i++) v1[i] /= v2[i];
	}
	return;
	
	error:
	fprintf(stderr,"Attempt to add arrays %s, %s with size %d %d and types %s %s failed\n",
			[self name],[a name],size1,size2,TYPE_STRINGS[[self type]],TYPE_STRINGS[[a type]]);
	return;
	
}

-(id) removeNonFiniteUsing:(char [])filt_string {
	
	if ( ![self isType:TYPE_F64] ) {
		fprintf(stderr,"Type Error in function %s in file %s at line %d\n",__FUNCTION__,__FILE__,__LINE__);
		return self;
	}
	 
	f64 * s_data = [self data];

	if ( s_data == NULL ) {
		fprintf(stderr,"Memory Error in function %s in file %s at line %d\n",__FUNCTION__,__FILE__,__LINE__);
		return self;
	}
	
	
	u08 filt_type = 0;
	f64 filt_value = 0;
	if ( strcmp(filt_string,"array average") == 0 ) {
		filt_type = 0;
	} else if ( strncmp(filt_string,"set to:",7) == 0 ) {
		filt_type = 1;
		sscanf(filt_string,"set to: %le",&filt_value);
	} else {
		fprintf(stderr,"%s is not a valid parameter for function %s in file %s at line %d\n",filt_string,__FUNCTION__,__FILE__,__LINE__);
		return self;
	}
	
	u32 i;
	for(i=0;i<size;i++) {
		if ( !ISFINITE(s_data[i]) ) {
			switch (filt_type) {
				case 0:
					s_data[i] = [self meanValue];
					break;
				case 1:
					s_data[i] = filt_value;
					break;
			}
		}
	}
	
	return self;
	
}
	

@end

int compare_f64( const void * a, const void * b ) {
	
	f64 x1 = *(f64*)a;
	f64 x2 = *(f64*)b;
	
	if ( x1 < x2 ) return -1;
	else if ( x1 == x2 ) return 0;
	else return 1;
	
}

ArrayIteratorP createArrayIterator( u32 ndim, u32 * dims, u32 * steps ) {
	
	ArrayIteratorP iterator = malloc(sizeof(ArrayIterator));
	if ( iterator == NULL ) return NULL;
	
	/* Allocating data for iterator as a single solid block with the idea of forcing more efficient memory use and/or
	increasing cacheability of the iterator data.  Not sure if this actually helps or not. */
	
	void * iterator_data = NEWV(u32,(ndim+1)*6);
	size_t iterator_data_offset = sizeof(u32)*(ndim+1);

	iterator->dim_step		= iterator_data + iterator_data_offset * 0;
	iterator->dim_size 		= iterator_data + iterator_data_offset * 1;
	iterator->dim_jump		= iterator_data + iterator_data_offset * 2;
	iterator->min_bounds	= iterator_data + iterator_data_offset * 3;
	iterator->max_bounds	= iterator_data + iterator_data_offset * 4;
	iterator->cur_position	= iterator_data + iterator_data_offset * 5;
	
	iterator->min_offset = 0;
	iterator->max_offset = 1;
	
	u32 i;
	for (i=0;i<ndim;i++) {
		iterator->dim_step[i] = steps[i];
		iterator->dim_size[i] = dims[i];
		iterator->dim_jump[i] = steps[i+1] - dims[i];
		iterator->max_offset += (dims[i]-1)*steps[i];
		iterator->cur_position[i] = 0;
	}
	
	iterator->cur_offset = 0;
	
	return iterator;
	
}

inline u32 startArrayIterator( ArrayIteratorP iterator, bool direction ) {
	if ( direction == CV_ITERATOR_INCREASING ) {
		iterator->cur_offset = iterator->min_offset;
		return iterator->cur_offset;
	} else {
		iterator->cur_offset = iterator->max_offset;
		return iterator->cur_offset;
	}
}

inline u32 incrementArrayIterator( ArrayIteratorP ite ) {
	
	u32 k = 0;
	ite->cur_position[0]++;

	while ( ite->cur_position[k] == ite->dim_size[k]  ) {
		ite->cur_position[k] = 0;
		ite->cur_offset += ite->dim_jump[k];
		ite->cur_position[++k]++;
		if ( k == ite->ndim ) ite->cur_offset = ite->min_offset;
	}
	
	return ite->cur_offset += ite->dim_step[0];
	
}

inline u32 decrementArrayIterator( ArrayIteratorP ite ) {
	
	u32 k = 0;
	ite->cur_position[0]++;

	while ( ite->cur_position[k] == ite->dim_size[k]  ) {
		ite->cur_position[k] = 0;
		ite->cur_offset -= ite->dim_jump[k];
		ite->cur_position[++k]++;
		if ( k == ite->ndim-1 ) ite->cur_offset = ite->max_offset;
	}
	
	return ite->cur_offset -= ite->dim_step[0];
	
}

void freeArrayIterator( ArrayIteratorP ite ) {
	
	if ( ite == NULL ) return;
	if ( ite->dim_step != NULL ) free(ite->dim_step);
	free(ite);
	
}

BorderTesterP createBorderTester( const u32 ndim, const u32 dims[], const u32 stps[] ) {
	
	BorderTesterP tester = malloc(sizeof(BorderTester));
	if ( tester == NULL ) return NULL;
	
	tester->ndim = ndim;
	tester->f_steps = NEWV(u32,ndim);
	tester->b_steps = NEWV(u32,ndim);
	
	if ( tester->f_steps == NULL || tester->b_steps == NULL ) {
		freeBorderTester(tester);
		return NULL;
	} 
	
	u32 d;
	for(d=0;d<ndim;d++) tester->f_steps[d] = stps[d];
	for(d=0;d<ndim;d++) tester->b_steps[d] = (dims[d]-1)*stps[d];
	
	return tester;
	
} 

void freeBorderTester( BorderTesterP tester ) {
	if ( tester == NULL ) return;
	if ( tester->f_steps != NULL ) free(tester->f_steps);
	if ( tester->b_steps != NULL ) free(tester->b_steps);
	free(tester);
}

inline u08 testBorder( s64 loc, BorderTesterP tester ) {

	s64 d;
	u08 border = FALSE;
	
	for( d=tester->ndim-1 ; d>=0 ; d-- ) {
		if ( loc < tester->f_steps[d] ) border = TRUE;
		if ( loc >= tester->b_steps[d] ) border = TRUE;
		loc = loc % tester->f_steps[d];
	}

	return border;
}

bool lessThanOrEqualTo( f64 v1, f64 v2 ) {
	if ( v1 <= v2 ) return TRUE;
	else return FALSE;
}

bool greaterThanOrEqualTo( f64 v1, f64 v2 ) {
	if ( v1 >= v2 ) return TRUE;
	else return FALSE;
}

bool equalTo( f64 v1, f64 v2 ) {
	if ( v1 == v2 ) return TRUE;
	else return FALSE;
}

u64 sizeFromDims( u32 dims[], u32 ndim ) {
	u64 k, size = 1;
	for(k=0;dims[k]!=0 && k<ndim;k++) size = size * dims[k];
	return size;
} 

void flipDims( u32 dims[], u32 ndim ) {
	u64 k, d;
	for(k=0;k<ndim;k++,ndim--) { d=dims[ndim]; dims[ndim] = dims[k]; dims[k] = d; } 
}

