#include "Image.h"
#include <math.h>

void unionFindAB( u32 *roots, u32 *sizes, u32 a, u32 b );
void vecBin( f64 *src, f64 *dst, u32 bin, u32 dstsize );
void convolve1Ds( f32 *src, f32 *dst, u32 size, u32 cols, f32 *kernel, u32 ksize );
void rotateLong( f32 *src, f32 *dst, u32 size, u32 cols );

static int fftw_is_wise = 0;
static char fftw_wisdom_path[256] = "/tmp/.fftw_wisdom";

@implementation Array ( Image_Functions )

-(void) scaleFrom: (f64)newmin to: (f64)newmax {
	
	[self setTypeTo: TYPE_F64];
	SCALE_F64(data,size,newmin,newmax,data);
	
}

-(id) gaussianBlurWithSigma: (f64)sigma {
	
	[self setTypeTo: TYPE_F64];
	
	if ( sigma < 0.6 ) return self;
	
	s32 krad = sigma * 4;
	krad = MAX(krad,1);
	f64 *x1, *x2, *x3;	
	
	f64 * kernel = NEWV(f64,krad);
	f64 * xt = NEWV(f64,size);	
	f64 * xi = [self data];
	
	if ( kernel == NULL || xi == NULL || xt == NULL ) goto error;
	
	f64 two_s2  = 1.0 / ( sigma * sigma * 2 );
	f64 norm    = 1.0 / ( sigma * sqrt(2*PI) );
	s32 d, k, i, r;
	
	for (i=0;i<krad;i++) kernel[i] = norm * exp( -i*i*two_s2 );

	for(d=0;d<ndim;d++) {

		s32 cols = dim_size[d];
		s32 rots = size / cols;
		
		s32 minb = 0;
		s32 maxb = cols-1;

		x1 = xi;
		x2 = xt;
		x3 = xt;

		for(k=0;k<rots;k++) {
			for(r=0;r<cols;r++) {
				f64 sum = x1[r] * kernel[0];
				for(i=1;i<krad;i++) {
					s32 pos1 = r - i;
					s32 pos2 = r + i;
					//if ( pos1 < minb ) pos1 = cols + pos1%cols;
					//if ( pos2 > maxb ) pos2 = minb + pos2%cols;
					if ( pos1 < minb ) pos1 = minb;
					if ( pos2 > maxb ) pos2 = maxb;					
					sum += ( x1[pos1] + x1[pos2] ) * kernel[i];
				}
				*x2 = sum;
				x2 += rots;
			}
			x1 += cols;
			x2  = ++x3;
		}
		
		x3 = xi;
		xi = xt;
		xt = x3;
		
	}
	
	if ( xi == [self data] ) free(xt);
	else [self setDataTo: xi];
	
	error:
	
	free(kernel);
	return self;
	
}

-(void) gaussianBlurWithSigmaR:(f64)sigma {
	
	[self setTypeTo: TYPE_F64];

	int r, c, i, k;
	f64 * x1 = [self data];
	c64 * x3 = fftw_malloc(sizeof(c64)*size);

	for(i=0;i<size;i++) x3[i] = x1[i];
	
	int dim[ndim+1];

	for (i=0;i<ndim;i++) dim[i] = dim_size[i];
	
	fftw_plan plan1 = fftw_plan_dft(ndim, dim, x3, x3, FFTW_FORWARD, FFTW_ESTIMATE);
	fftw_execute(plan1);
	
	f64 x_rad = dim[0]/2.0;
	f64 y_rad = dim[1]/2.0;
		
	for(r=0,i=0;r<dim[0];r++) {
		for(c=0;c<dim[1];c++,i++) {
			f64 x = c;
			f64 y = r;
			if ( x > x_rad ) x = dim[0] - x;
			if ( y > y_rad ) y = dim[1] - y;
			x = x * ( 2.0 / dim[0] );
			y = y * ( 2.0 / dim[1] );
			f64 rad = x*x+y*y;
			x3[i] = exp(-rad*sigma*sigma*2.0)*x3[i];			
		}
	}
	
	fftw_plan plan2 = fftw_plan_dft(ndim, dim, x3, x3, FFTW_BACKWARD, FFTW_ESTIMATE);
	fftw_execute(plan2);
	
	for(i=0;i<size;i++) x1[i] = x3[i]/size;
	
	fftw_destroy_plan(plan1);
	fftw_destroy_plan(plan2);
	free(x3);
	
}

-(id) r2cfftc {
	
	if ( ![self isType:TYPE_F64] ) {
		fprintf(stderr,"r2cfftc only takes arrays of type %s\n",TYPE_STRINGS[TYPE_F64]);
		fprintf(stderr,"\tnot of type %s\n",TYPE_STRINGS[[self type]]);
		return self;
	}
	
	u64 i, k;
	
	int dim[ndim];
	for(i=0;i<ndim;i++) dim[i] = dim_size[ndim-1-i];
	
	u32 new_dims[ndim+1];
	for(i=0;i<ndim;i++) new_dims[i] = dim_size[i];
	new_dims[0] = floor(new_dims[0]/2)+1;
	new_dims[ndim] = 0;
	
	u32 new_size = 1;
	for(i=0;i<ndim;i++) new_size = new_size * new_dims[i];

	[self fftshift];
	
	f64 * xi = [self data];
	c64 * xt = NEWV(c64,new_size);

	if ( xi == NULL || xt == NULL ) {
		fprintf(stderr,"Function r2cfftc ran out of memory\n");
		free(xt);
		return self;
	}
	
	restoreFFTWisdom();
	
	fftw_plan plan = fftw_plan_dft_r2c(ndim, dim, xi, xt, FFTW_MEASURE|FFTW_WISDOM_ONLY);
	if ( plan == NULL ) {
		xi = NEWV(f64,size);
		plan = fftw_plan_dft_r2c(ndim, dim, xi, xt, FFTW_MEASURE);
		memcpy(xi,[self data],sizeof(f64)*size);
		[self setDataTo:xi];
	}
	
	if ( plan == NULL ) {
		fprintf(stderr,"Function r2cfftc could not create fftw plan\n");
		free(xt);
		return self;
	}
	
	fftw_execute(plan);
	
	fftw_destroy_plan(plan);
	
	saveFFTWisdom();
	
	[self setDataTo:NULL];
	[self setShapeTo:new_dims];
	[self setTypeTo:TYPE_C64];
	[self setDataTo:xt];
	
	return self;
	
}

-(id) c2rfftc {
	
	if ( ![self isType:TYPE_C64] ) {
		fprintf(stderr,"Function c2rfftc requires array of type: %s\n",TYPE_STRINGS[TYPE_C64]);
		fprintf(stderr,"\tbut got an array of type: %s\n",TYPE_STRINGS[[self type]]);
		return self;
	}

	u64 i, k;
		
	u32 new_dims[ndim+1];
	for(i=0;i<ndim;i++) new_dims[i] = dim_size[i];
	new_dims[0] = (new_dims[0]-1)*2;
	new_dims[ndim] = 0;
	
	int dims[ndim];
	for(i=0;i<ndim;i++) dims[i] = new_dims[ndim-1-i];
	
	u32 new_size = sizeFromDims(new_dims,ndim);

	c64 * xi = [self data];	
	f64 * xt = NEWV(f64,new_size);

	if ( xi == NULL || xt == NULL ) {
		fprintf(stderr,"Function c2rfftc ran out of memory\n");
		free(xt);
		return;
	}
	
	// Restore FFTW Wisdom from file, and if this is not possible create a new data array
	// for performing the FFTW_MEASURE, otherwise the input would be destroyed.
	
	restoreFFTWisdom();

	fftw_plan plan = fftw_plan_dft_c2r(ndim, dims, xi, xt, FFTW_MEASURE|FFTW_WISDOM_ONLY);
	if ( plan == NULL ) {
		xi = NEWV(c64,size);
		plan = fftw_plan_dft_c2r(ndim, dims, xi, xt, FFTW_MEASURE);
		memcpy(xi,[self data],sizeof(c64)*size);
		[self setDataTo:xi];
	}
	
	if ( plan == NULL ) {
		fprintf(stderr,"Function c2rfftc could not create fftw plan\n");
		free(xt);
		return self;
	}
	
	fftw_execute(plan);
	
	fftw_destroy_plan(plan);
	
	saveFFTWisdom();
	
	[self setDataTo:NULL];
	[self setShapeTo:new_dims];
	[self setTypeTo:TYPE_F64];
	[self setDataTo:xt];
	
	[self fftshift];
	
	return self;
	
}

-(id) fftc {
	
	if ( ![self isType:TYPE_F64] ) {
		fprintf(stderr,"Function fftc requires array of type: %s\n",TYPE_STRINGS[TYPE_F64]);
		fprintf(stderr,"\tbut got an array of type: %s\n",TYPE_STRINGS[[self type]]);
		return self;
	}
	
	[self fftshift];
	
	f64 * xi = [self data];
	c64 * xt = NEWV(c64,size);
	
	if ( xi == NULL || xt == NULL ) {
		fprintf(stderr,"Function fftc ran out of memory\n");
		free(xt);
		return self;
	}
	
	u64 i;
	
	int dims[ndim];
	for(i=0;i<ndim;i++) dims[i] = dim_size[ndim-1-i];
	
	// Restore any previously created FFTW Wisdom (cached)
	// In cases where appropriate wisdom does not already exist, FFTW_MEASURE destroys the input data
	// so we don't copy the data over until after the measurement has been done, just in case.
	// Then perform the transform, and clean-up
	
	restoreFFTWisdom();
	
	fftw_plan plan = fftw_plan_dft(ndim, dims, xt, xt, FFTW_FORWARD, FFTW_MEASURE);
	if ( plan == NULL ) {
		fprintf(stderr,"Could not create fftw plan in function fftc\n");
		return self;
	}
	
	for(i=0;i<size;i++) xt[i] = xi[i];
	
	fftw_execute(plan);
	
	fftw_destroy_plan(plan);
	
	saveFFTWisdom();
	
	// Delete the original array data, change the type, then set to the new data.
	// Doing things in this order means that we do not waste time trying to convert
	// the type on the current data.
	
	[self setDataTo:NULL];
	[self setTypeTo:TYPE_C64];
	[self setDataTo:xt];
	
	return self;
	
}

-(id) ifftc {
	
	if ( ![self isType:TYPE_F64] ) {
		fprintf(stderr,"Function ifftc requires array of type: %s",TYPE_STRINGS[TYPE_C64]);
		fprintf(stderr,"\tbut got an array of type: %s\n",TYPE_STRINGS[[self type]]);
		return self;
	}
	
	f64 * xt = NEWV(f64,size);
	c64 * xi = [self data];

	if ( xi == NULL || xt == NULL ) {
		fprintf(stderr,"Function fftc ran out of memory\n");
		free(xt);
		return self;
	}
	
	u64 i;
	
	int dims[ndim];
	for(i=0;i<ndim;i++) dims[i] = dim_size[ndim-1-i];
	
	restoreFFTWisdom();
	
	fftw_plan plan = fftw_plan_dft(ndim, dims, xi, xi, FFTW_BACKWARD, FFTW_MEASURE|FFTW_WISDOM_ONLY);
	if ( plan == NULL ) {
		xi = NEWV(c64,size);
		plan = fftw_plan_dft(ndim, dims, xi, xi, FFTW_BACKWARD, FFTW_MEASURE);
		memcpy(xi,[self data],sizeof(c64)*size);
		xi = [[self setDataTo:xi] data];
	}
	
	if ( plan == NULL ) {
		fprintf(stderr,"Could not create fftw plan in function ifftc\n");
		free(xt);
		return self;
	}
	
	for(i=0;i<size;i++) xt[i] = xi[i];
	
	fftw_execute(plan);

	fftw_destroy_plan(plan);
	
	saveFFTWisdom();
	
	[self setDataTo:NULL];
	[self setTypeTo:TYPE_F64];
	[self setDataTo:xt];
	[self fftshift];
	
	return self;
	
}

-(id) fftshift {
	
	if ( [self type] != TYPE_F64 ) {
		fprintf(stderr,"Function fftshift only takes arrays of type %s\n",TYPE_STRINGS[TYPE_F64]);
		fprintf(stderr,"\tnot of type %s\n",TYPE_STRINGS[[self type]]);
		return self;
	}
	
	u32 k, i;
	f64 * xi = [self data];
	
	if ( xi == NULL ) {
		fprintf(stderr,"Function fftshift had a memory problem\n");
		return self;
	}
	
	u32 flip_state = 0;
	u32 curpos[ndim];
	for(i=0;i<ndim;i++) curpos[i] = 0;

	for(i=0;i<size;i++) {
			
		for( k=0 ; k<ndim && curpos[k]==dim_size[k] ; k++ ) {
			curpos[k] = 0;
			curpos[k+1]++;
			flip_state = flip_state - dim_size[k] + 1;
		}
		
		if ( flip_state % 2 != 0 ) xi[i] = -xi[i];

		curpos[0]++; flip_state++;
		
	}
	
	return self;
	
}

-(id) generatePowerSpectrum {
	
	if ( [self type] != TYPE_F64 ) {
		fprintf(stderr,"generatePowerSpectrum only takes arrays of type %s\n",TYPE_STRINGS[TYPE_F64]);
		fprintf(stderr,"\tnot of type %s\n",TYPE_STRINGS[[self type]]);
		return self;
	}
	
	[self fftc];
	
	if ( ![self isType:TYPE_C64] ) {
		fprintf(stderr,"FFT function did not work\n");
		return self;
	}
	
	c64 * xi = [self data];
	f64 * xt = NEWV(f64,size);
	
	if ( xi == NULL || xt == NULL ) {
		fprintf(stderr,"generatePowerSpectrum has no memory\n");
		free(xt);
		return self;
	}
	
	u32 i;
	
	for(i=0;i<size;i++) xt[i] = sqrt(pow(creal(xi[i]),2.0)+pow(cimag(xi[i]),2.0));
	
	[self setDataTo:NULL];
	[self setTypeTo:TYPE_F64];
	[self setDataTo:xt];
	
}

-(void) binBy: (u32)bin {
		
	u32 i;
	
	if ( bin <= 1 ) return;
	
	[self setTypeTo: TYPE_F64];
	
	u32 n_size = 1;
	u32 newDim[ndim+1], newStp[ndim+1], curDim[ndim+1], newTrp[ndim+1];

	newStp[0] = dim_step[0];
	for(i=1;i<ndim;i++) newTrp[i] = ( dim_size[i] % bin ) * dim_step[i] - dim_step[i-1];
	for(i=0;i<ndim+1;i++) curDim[i] = 0;
	for(i=0;i<ndim;i++) newDim[i] = dim_size[i] / bin;
	for(i=0;i<ndim;i++) n_size = n_size * newDim[i];	
	for(i=0;i<ndim;i++) dim_size[i] = newDim[i] * bin;
	for(i=1;i<ndim;i++) newStp[i] = newStp[i-1] * newDim[i-1];
	
	f64 * xi = [self data];
	f64 * xt = NEWV(f64,n_size);
	
	size = 1;
	for(i=0;i<ndim;i++) size = size * dim_size[i];
	
	u32 vecs = dim_size[0];
	u32 vecn = size / dim_size[0];		// Number of 1d vectors in array
	
	for(i=0;i<vecn;i++) {
		
		u32 d, offset = 0;

		for(d=1;d<ndim;d++)	offset += curDim[d] / bin * newStp[d];

		vecBin(xi,xt+offset,bin,newDim[0]);
		
		curDim[1]++;
		xi+=dim_step[1];
		
		for(d=1;curDim[d]==dim_size[d];d++) {
			xi += newTrp[d];
			curDim[d] = 0;
			curDim[d+1]++;
		}
		
	}
	
	memcpy([self data],xt,sizeof(f64)*n_size);
	free(xt);
	
	u32 new_dimensions[ndim+1];
	for(i=0;i<ndim;i++) new_dimensions[i] = newDim[i];
	new_dimensions[ndim] = 0;
	[self setShapeTo: new_dimensions];

}

-(void) subtractImage: (id)image {
	
	if ( [self compareDimensions: image] ) return;
	
	[self  setTypeTo: TYPE_F64];
	[image setTypeTo: TYPE_F64];
	
	f64 *x1 = [self  data];
	f64 *x2 = [image data];
	
	u32 k;
	for(k=0;k<size;k++) x1[k] -= x2[k];

}

-(void) addImage: (id)image {
	
	if ( size != [image numberOfElements] ) return;
	
	[self  setTypeTo: TYPE_F64];
	[image setTypeTo: TYPE_F64];
	
	f64 *x1 = [self  data];
	f64 *x2 = [image data];
	
	u32 k;
	for(k=0;k<size;k++) x1[k] += x2[k];
	
}

-(void) divideImage: (id)image {
	
	if ( size != [image numberOfElements] ) return;
	
	[self  setTypeTo: TYPE_F64];
	[image setTypeTo: TYPE_F64];
	
	f64 * x1 = [self  data];
	f64 * x2 = [image data];
	
	u32 k;
	for(k=0;k<size;k++) x1[k] = x1[k] / ( x2[k] + 1 );
	
}

-(void) multiplyBy: (f64)scalar {
	
	[self  setTypeTo: TYPE_F64];
	
	f64 *x1 = [self  data];
	
	u32 k;
	for(k=0;k<size;k++) x1[k] = x1[k] * scalar;
	
}

-(void) divideBy: (f64)scalar {
	
	[self  multiplyBy: 1.0/scalar];
	
}

-(id) buildDoGFrom: (f64)fsigma to: (f64)tsigma sampled: (u32)samples {
	
	/* ----------------------------------------------------------------------------------
		The gaussian blurs between successive steps in DoG detection must be related
		by a constant multiplicative factor.  sigma_step is that factor and is calculated
		so that repeated multiplication with each previous sigma will end at the sigma 
		specified by max_range if the process begins at min_range.  One shortcut that 
		can be taken in DoG detection is to use a previously blurred image to achieve the 
		next desired blur with reduced computational cost.  The relationship between 
		a new gaussian blur and cascaded gaussian blurs is given by the formula:
	   
		actual_sigma = sqrt( last_sigma * last_sigma + next_sigma * next_sigma )
	   
		and remember that in DoG detection the actual_sigma wanted is related to the 
		last_sigma by the factor sigma_step, so:
	   
		actual_sigma = sigma_step * last_sigma
	   
		so solving for next_sigma:
	
		next_sigma = last_sigma * sqrt( sigma_step * sigma_step - 1 )
	   	
		provides us with the sigma blur needed to achieve the next image if we 
		base it off the previously blurred image;
		
		Another complication is that we want to center the search on the estimated size,
		which means we want the zero crossings for the DoG kernels to equal this
		size.  Unfortunately the zero crossing for a DoG created by subtracting 
		G(sigma1) - G(sigma1*sigma_step) does not equal sigma1.  Based on the sigma_step factor
		we can instead calculate:
		
		                 ___________________________________________ 
		               / ( (estimated_size^2)*(sigma_step^2-1) )
		 sigma =	 /	------------------------------------
				  \/	   2*(sigma_step^2)*ln(sigma_step)
		
		
		The DoG based on this calculated sigma, G(sigma) - G(sigma*sigma_step), 
		has zero crossings at the estimated_size.  We then just figure out the multiples 
		of this sigma that meet or exceed the desired search range, and we can proceed 
		with the cascaded DoG filtering as described before.
	--------------------------------------------------------------------------------------*/
	f64 sigma_step  = pow( tsigma / fsigma , 1.0 / samples );
	f64 sigma_interval = sqrt( sigma_step * sigma_step - 1.0 );
	
	u32 i, k, dogdims[32];
	for(k=0;k<ndim;k++) dogdims[k] = dim_size[k];
	
	dogdims[k] = samples;
	dogdims[k+1] = 1;
	
	[self setTypeTo: TYPE_F64];

	ArrayP dog_space = [Array newWithType: TYPE_F64 andDimensions: dim_size];
	f64 *x3 = [dog_space  data];
	
	ArrayP blurImage1 = [self copyArray];
	[blurImage1 gaussianBlurWithSigma: fsigma];

	for(k=0;k<samples;k++) {
	
		f32 next_sigma = fsigma * sigma_interval;
		fsigma = fsigma * sigma_step;
		
		fprintf(stderr,"Building sample %d with sigma %f (%f)\n",k,fsigma,next_sigma);
		
		ArrayP blurImage2 = [blurImage1 copyArray];
		[blurImage2 gaussianBlurWithSigma: next_sigma];
		
		f64 *x1 = [blurImage1 data];
		f64 *x2 = [blurImage2 data];
		
		for(i=0;i<size;i++) x3[i]  = x2[i] - x1[i];
		x3 += size;
		
		[blurImage1 release];
		blurImage1 = blurImage2;

	}
	
	[blurImage1 release];
	
	return dog_space;
	
}

-(void) absoluteValue {
	[self setTypeTo: TYPE_F64];
	f64 * xi = [self data];
	u32 k;
	for(k=0;k<size;k++) xi[k] = ABS(xi[k]);
}

-(void) edgeBlur:(u32)pixels {
	
	if ( pixels == 0 ) return;
	
	s32 k, d, i;

	s32 krad = pixels;	
	f64 sigma = (f64)pixels / 3.0;

	f64 kernel[krad];
	
	f64 two_s2  = 1.0 / ( sigma * sigma * 2 );
	
	for (i=0;i<krad;i++) kernel[krad-1-i] = exp( -(f64)i*(f64)i*two_s2 );	
	
	f64 max_value = kernel[0];
	for(i=0;i<krad;i++) max_value = MAX(max_value,kernel[i]);
	for(i=0;i<krad;i++) kernel[i] = kernel[i] / max_value;
	
	f64 * pix = [self data];
	if ( pix == NULL ) return;
	
	s32 pos = 0;
	s32 curpos[ndim+1];
	
	for(d=0;d<ndim+1;d++) curpos[d] = 0;
	
	for(i=0;i<size;i++) {
		
		for(d=0;d<ndim;d++) {
			if ( curpos[d] < krad ) pix[pos] *= kernel[curpos[d]];
			else if ( curpos[d] > dim_size[d]-1-krad ) pix[pos] *= kernel[dim_size[d]-1-curpos[d]];
		}
		
		curpos[0]++; pos++;
		for(d=0;curpos[d]==dim_size[d];d++) {
			curpos[d] = 0;
			curpos[d+1]++;
		}

	}
	
}

-(id) gradients {
	
	[self setTypeTo:TYPE_F64];
	if ( ndim != 2 ) return;
	
	u32 cols = [self sizeOfDimension:0];
	u32 rows = [self sizeOfDimension:1];
	
	u32 dims[4] = {cols, rows, 2, 0};
	ArrayP grad_image = [Array newWithType:TYPE_F64 andDimensions:dims];
	
	f64 * o_pixels = [self data];
	f64 * m_pixels = [grad_image getSlice:0];
	f64 * a_pixels = [grad_image getSlice:1];
	
	ArrayIteratorP iterator = createArrayIterator(ndim,dim_size,dim_step);
	BorderTesterP b_tester = createBorderTester(ndim,dim_size,dim_step);
	
	if ( iterator == NULL ) goto error;
	if ( b_tester == NULL ) goto error;
	
	u32 i, k = startArrayIterator(iterator,CV_ITERATOR_INCREASING);
	
	for(i=0;i<size;i++) {
		if ( testBorder(k,b_tester) ) {
			m_pixels[k] = 0.0;
			a_pixels[k] = 0.0;
		} else {
			f64 dx = o_pixels[k+dim_step[0]] - o_pixels[k-dim_step[0]];
			f64 dy = o_pixels[k-dim_step[1]] - o_pixels[k+dim_step[1]];
			m_pixels[k] = sqrt(dx*dx+dy*dy);
			a_pixels[k] = atan2(dy,dx);
		}
		k = incrementArrayIterator(iterator);
	}
	
	error:
	
	freeArrayIterator(iterator);
	freeBorderTester(b_tester);
	
	return grad_image;
	
}

-(void) cannyEdgesWithUpperTreshold:(f64)upper lowerTreshold:(f64)lower {
	
	[self setTypeTo:TYPE_F64];

	if ( ndim != 2 ) return;
	if ( lower > 1.0 ) return;
	if ( upper > 1.0 ) return;
	if ( lower > upper ) return;

	f64 * pixels = [self data];
	
	ArrayP gradients = [self gradients];
	f64 * mags = [gradients getSlice:0];
	f64 * angs = [gradients getSlice:1];
	
	if ( angs == NULL || mags == NULL || pixels == NULL ) goto error;

	s64 r, c;

	// Reset the values of the image to 0.0
	for(r=0;r<size;r++) pixels[r] = 0;

	// Perform non-maximum suppression.  That is, a pixel is only an edge if its gradient magnitude
	// along its direction is greater than than of neighboring pixels along that dimension.
	
	f64 minval = mags[2*dim_step[1]+2];
	f64 maxval = mags[2*dim_step[1]+2];
	
	for(r=2;r<dim_size[1]-2;r++) {
		for(c=2;c<dim_size[0]-2;c++) {
			u32 p = r*dim_size[0]+c;
			f64 cine = cos(angs[p]);
			f64 sine = sin(angs[p]);
			f64 p1 = interpolate(mags,r-sine,c+cine,dim_size[1],dim_size[0]);
			f64 p2 = interpolate(mags,r+sine,c-cine,dim_size[1],dim_size[0]); 
			if ( p1 < mags[p] && p2 < mags[p] ) {
				minval = MIN(mags[p],minval);
				maxval = MAX(mags[p],maxval);
				pixels[p] = mags[p];
			}	
		}
	}
	
	for(r=2;r<dim_size[1]-2;r++) {
		for(c=2;c<dim_size[0]-2;c++) {
			u32 p = r*dim_size[0]+c;
			pixels[p] = (pixels[p]-minval)/(maxval-minval);
		}
	}
	
	[self floodFillFrom:lower to:upper usingConnectivity:CV_CONNECT_ALL];
	
	error:
	
	[gradients release];

	return;

}

-(void) floodFillFrom:(f64)lower to:(f64)upper usingConnectivity:(u08)n_conn {
	
	// The hardest part about this function is lending it the generality to deal with n-dimensional
	// datasets, that may be sub-sliced from a larger array.  To handle this we must first determine
	// the appropriate offsets to reach the neighbors of each element along each dimension, which if
	// we include diagnals can be quite a few neighbors.

	if ( ndim < 1 ) return;
	[self setTypeTo:TYPE_F64];
	
	u32 * c_posi = NEWV(u32,ndim+1);
	s32 * n_stps = NEWV(s32,pow(3.0,ndim));
	u32 * stack  = NEWV(u32,size);
	
	s32 n, d, i, k;
	
	// First determine the number of neighbors we will have from the connectivity specified and the
	// number of dimensions.
	
	u32 n_size = 0;
	if ( n_conn == CV_CONNECT_ADJACENT ) n_size = 2 * ndim;
	else n_size = pow(3.0,ndim);

	if ( c_posi == NULL || n_stps == NULL || stack == NULL ) goto error;
	
	// Now we must determine the offsets for all the neighbors appropriately
	
	for(i=0;i<n_size;i++) n_stps[i] = 0;
	for(i=0;i<ndim;i++) c_posi[i] = 0;	
	
	if ( n_conn == CV_CONNECT_ADJACENT ) {
		for(i=0,k=0;i<ndim;i++) {
			n_stps[k++] =  dim_step[i];
			n_stps[k++] = -dim_step[i];
		}
	} else {
		for(i=0;i<n_size;i++) {
			for(d=0;d<ndim;d++) {
				if ( c_posi[d] == 0 ) n_stps[i] = n_stps[i] - dim_step[d];
				if ( c_posi[d] == 2 ) n_stps[i] = n_stps[i] + dim_step[d];
			}
			for( d=0 , c_posi[d]++ ; c_posi[d]==3 && d<ndim-1 ; c_posi[d]=0 , c_posi[++d]++ );
		}
	}
	
	// Add all the pixels to a stack that are above the first treshold, use the array iterator
	// construct to deal with subsliced arrays, etc.  Use the array l_map to keep track of
	// pixels that have already been added, in the end l_map is the returned result
	
	u32 stack_size = 0;
	
	f64 * pixels = [self data];
	if ( pixels == NULL ) goto error;
	
	ArrayIteratorP iterator = createArrayIterator(ndim,dim_size,dim_step);
	if ( iterator == NULL ) goto error;
	
	k = startArrayIterator(iterator,CV_ITERATOR_INCREASING);
	
	for(i=0;i<size;i++) {
		if ( pixels[k] >= upper ) {
			stack[stack_size++] = k;
			pixels[k] = -1.0;
		}
		k = incrementArrayIterator(iterator);
	}
	
	freeArrayIterator(iterator);
	
	// -------------------------------------------------------------------------------------------
	
	// Now we add pixels that are connected to the above pixels but remain above a second treshold
	// While doing this we must check to make sure the pixels being considered aren't on the border
	// of the array data, otherwise we risk seg_faults.  We use the border tester construct to verify
	// our currently considered position
	
	BorderTesterP b_tester = createBorderTester(ndim,dim_size,dim_step);
	if ( b_tester == NULL ) goto error;
	
	for(i=0;i<stack_size;i++) {
		u32 location = stack[i];
		if ( testBorder(location,b_tester) ) continue;
		for(n=0;n<n_size;n++) {
			u32 neighbor = location + n_stps[n];
			if ( pixels[neighbor] >= lower ) {
				stack[stack_size++] = neighbor;
				pixels[neighbor] = -1.0;
			}
		}
	}
	
	fprintf(stderr,"Found %d peaks\n");
	
	freeBorderTester(b_tester);
	
	for(i=0;i<size;i++) {
		if ( pixels[i] < 0.0 ) pixels[i] = 1.0;
		else pixels[i] = 0.0;  
	}
	
	error:
	
	if ( c_posi != NULL ) free(c_posi);
	if ( n_stps != NULL ) free(n_stps);
	if ( stack != NULL ) free(stack);
	
	return;
	
}

-(void) boxSum {
	if ( [self type] != TYPE_F64 ) return;
	boxSum([self data],ndim,dim_size,dim_step);
}

-(void) boxBlurSize:(u32)s {
	
	boxBlur([self data],ndim,dim_size,dim_step,s);
	
}

/*

-(void) map_reset {
	
	if ( !map ) map = NEWV(u32,size);
	if ( !map ) return;
	
	u32 k;
	mapsize = size;
	for(k=0;k<mapsize;k++) map[k] = k;  
	
}

-(void) label_reset {
	
	if ( !labels ) labels = NEWV(u32,size);
	if ( !sizes  ) sizes  = NEWV(u32,size);
	if ( !labels ) return;
	if ( !sizes  ) return;
	
	u32 k;
	for(k=0;k<size;k++) labels[k] = 0;
	for(k=0;k<size;k++) sizes[k] = 1;
	
}

-(void) map_removeBorderPixels {
	
	if ( !map ) [self map_reset];
	if ( !map ) return;
	
	u32 d, k, oldsize = mapsize;
	mapsize = 0;
	
	for(k=0;k<oldsize;k++) {

		u32 idx = map[k];
		u32 loc = idx;
		u32 border = FALSE;
		
		for( d=ndim-1 ; d>=0 ; d-- ) {
			if ( loc < stp[d] ) border = TRUE;
			if ( loc >= (dim[d]-1)*stp[d] ) border = TRUE;
			loc = loc % stp[d];
		}

		if ( !border ) map[mapsize++] = idx;
		
	}
	
}

-(void) map_tresholdFrom: (f64)min to: (f64)max {
	
	if ( !map ) [self map_reset];
	if ( !map ) return;
	
	[self setTypeTo: TYPE_F64];
	f64 *pixels = [self bufferWithSize: size atOffset: 0];
	if ( !pixels ) return;

	u32 k;
	u32 oldsize = mapsize;
	mapsize = 0;
	
	for(k=0;k<oldsize;k++) {
		u32 idx = map[k];
		if ( pixels[idx] < min ) continue;
		if ( pixels[idx] > max ) continue;
		map[mapsize++] = idx;
	}
	
	[self freeBuffer];
	
}

-(void) map_labelsWithSizesFrom: (u32)min to: (u32)max {
	
	if ( !labels || !sizes ) [self label_reset];
	if ( !labels || !sizes ) return;
	
	if ( !map ) [self map_reset];
	if ( !map ) return;
	
	u32 k, newsize = 0;
	for(k=0;k<mapsize;k++) {

		u32 idx = map[k];
		u32 label = labels[idx];

		if ( sizes[label] > max ) continue;
		if ( sizes[label] < min ) continue;
		
		map[newsize++] = idx;
		
	}
	
	mapsize = newsize;
	
}

-(void) label_connectedComponentsFromMap {
	
	if ( !labels || !sizes ) [self label_reset];
	if ( !labels || !sizes ) return;
	
	if ( !map ) [self map_reset];
	if ( !map ) return;
	
	[self map_removeBorderPixels];
	
	[self setTypeTo: TYPE_F64];
	f64 *pixels = [self bufferWithSize: size];
	if ( !pixels ) return;
	
	s32 k, d;

	for(k=0;k<mapsize;k++) {

		u32 idx = map[k];

		for(d=0;d<ndim;d++) {
			unionFindAB(labels,sizes,idx,idx-stp[d]);
			unionFindAB(labels,sizes,idx,idx+stp[d]);
		}

	}

	for(k=0;k<mapsize;k++) {

		u32 idx = map[k];
		u32 root = idx;
		while ( root != labels[root] ) root = labels[root];

		labels[idx] = root;
		
	}
	
}

-(void) map_findPeaks {
	
	if ( !map ) [self map_reset];
	if ( !map ) return;
	
	[self setTypeTo: TYPE_F64];
	f64 *pixels = [self bufferWithSize: size];
	if ( !pixels ) return;

	u32 k, d;
	u32 newsize = 0;

	for(k=0;k<mapsize;k++) {
		
		u32 idx = map[k];
		f64 val = pixels[idx];
		
		u32 ismin = TRUE, ismax = TRUE;
		for (d=0;d<ndim;d++) {
			if ( pixels[idx-stp[d]] <= val ) ismin = FALSE;
			else if ( pixels[idx+stp[d]] <= val ) ismin = FALSE;
			else if ( pixels[idx-stp[d]] >= val ) ismax = FALSE;
			else if ( pixels[idx+stp[d]] >= val ) ismax = FALSE;
		}

		if ( ismin || ismax ) map[newsize++] = idx;
		
	}
	
	mapsize = newsize;
	
	[self freeBuffer];
	
}

-(void) map_applyLabelsToImage {
	
	if ( !labels || !sizes ) [self label_reset];
	if ( !labels || !sizes ) return;
	
	if ( !map ) [self map_reset];
	if ( !map ) return;
	
	[self setTypeTo: TYPE_F64];
	f64 *pixels = [self bufferWithSize: size];
	if ( !pixels ) return;
	
	u32 k;
	for(k=0;k<mapsize;k++) {

		u32 idx = map[k];
		u32 label = labels[idx];

		pixels[idx] = sizes[label];
		
	}
	
	[self freeBuffer];
	
}

*/

-(void) lineDrawFromX:(f64)x0 Y:(f64)y0 toX:(f64)x1 Y:(f64)y1 {
	
	
	u32 maxcol = dim_size[0];
	u32 maxrow = dim_size[1];

//	fprintf(stderr,"Drawing Line from %f %f to %f %f\n",x0,y0,x1,y1);

	f64 * pixels = data;
	
	if ( x1 - x0 == 0 ) {
		if ( x0 < 0 || x0 >= maxcol ) return;
		if ( y0 < 0 ) y0 = 0;
		else if ( y0 >= maxrow ) y0 = maxrow-1;
	} else {
	
		f64 slope = (y1-y0)/(x1-x0);
		if ( slope == 0 && ( y0 < 0 || y0 >=maxrow ) ) return;
	
		f64 intercept = y0 - slope * x0;
	
		if ( x0 < 0 ) { x0 = 0; y0 = intercept; }
		if ( x0 >= maxcol ) { x0 = maxcol-1; y0 = slope*x0 + intercept; }
		if ( y0 < 0 ) { y0 = 0; x0 = -intercept/slope; }
		if ( y0 >= maxrow ) { y0 = maxrow-1; x0 = (y0-intercept)/slope; }
	
		if ( x1 < 0 ) { x1 = 0; y1 = intercept; }
		if ( x1 >= maxcol ) { x1 = maxcol-1; y1 = slope*x1 + intercept; }
		if ( y1 < 0 ) { y1 = 0; x1 = -intercept/slope; }
		if ( y1 >= maxrow ) { y1 = maxrow-1; x1 = (y1-intercept)/slope; }	
	
	}
	
	int ix0 = x0;
	int ix1 = x1;
	int iy0 = y0;
	int iy1 = y1;
	
	int dy = y1 - y0;
	int dx = x1 - x0;
	int stepx, stepy;
	
	if (dy < 0) { dy = -dy;  stepy = -maxcol; } else { stepy = maxcol; }
	if (dx < 0) { dx = -dx;  stepx = -1; } else { stepx = 1; }
	dy <<= 1;
	dx <<= 1;

	f64 v = 256;

	iy0 *= maxcol;
	iy1 *= maxcol;
	pixels[ix0+iy0] = v;
	if (dx > dy) {
		int fraction = dy - (dx >> 1);
		while (ix0 != ix1) {
			if (fraction >= 0) {
				iy0 += stepy;
				fraction -= dx;
			}
			ix0 += stepx;
			fraction += dy;
			pixels[ix0+iy0] = v;
		}
	} else {
		int fraction = dx - (dy >> 1);
		while (iy0 != iy1) {
			if (fraction >= 0) {
				ix0 += stepx;
				fraction -= dy;
			}
			iy0 += stepy;
			fraction += dx;
			pixels[ix0+iy0] = v;
		}
	}
}

@end

void vecBin( f64 * src, f64 * dst, u32 bin, u32 dstsize ) {
	u32 k, i;
	for(k=0;k<dstsize;k++,dst++) for(i=0;i<bin;i++,src++) *dst += *src;
}

void unionFindAB( u32 *roots, u32 *sizes, u32 a, u32 b ) {
	
	// Find path and compress
	for(;a!=roots[a];a=roots[a]) roots[a] = roots[roots[a]];
	for(;b!=roots[b];b=roots[b]) roots[b] = roots[roots[b]];
	
	// Same root aleady so return
	if ( a == b ) return;
	
	// Merge based on size, keeps union-find trees small!
	if ( sizes[a] < sizes[b] ) {
		roots[a] = b;
		sizes[b] += sizes[a];
		return;
	} else {
		roots[b] = a;
		sizes[a] += sizes[b];
		return;
	}
	
}

u08 * floodFill( f64 src[], u32 s_ndim, u32 s_dims[], u32 s_stps[], f64 lt, f64 ut, u08 n_conn ) {
	
	// The hardest part about this function is lending it the generality to deal with n-dimensional
	// datasets, that may be sub-sliced from a larger array.  To handle this we must first determine
	// the appropriate offsets to reach the neighbors of each element along each dimension, which if
	// we include diagnals can be quite a few neighbors.
	
	s32 * c_posi = NEWV(s32,s_ndim+1);
	s32 * n_stps = NULL;
	s32 * stack = NULL;
	u08 * l_map = NULL;
	
	if ( s_ndim < 1 ) goto error;
	if ( src == NULL || s_dims == NULL || s_stps == NULL ) goto error;
	
	s32 n, d, i, k;

	u32 s_size = sizeFromDims(s_dims,s_ndim);
	
	l_map = NEWV(u08,s_size);
	stack = NEWV(s64,s_size);
	
	// First determine the number of neighbors we will have from the connectivity specified and the
	// number of dimensions.
	
	s32 n_size = 0;
	if ( n_conn == CV_CONNECT_ADJACENT ) n_size = 2 * s_ndim;
	else n_size = pow(3.0,s_ndim);
	n_stps = NEWV(s64,n_size);
		
	if ( c_posi == NULL || n_stps == NULL || l_map == NULL || stack == NULL ) goto error;
	
	// Now we must determine the offsets for all the neighbors appropriately
	
	for(i=0;i<n_size;i++) n_stps[i] = 0;
	for(i=0;i<s_ndim;i++) c_posi[i] = 0;	
	
	if ( n_conn == CV_CONNECT_ADJACENT ) {
		for(i=0,k=0;i<s_ndim;i++) {
			n_stps[k++] =  s_stps[i];
			n_stps[k++] = -s_stps[i];
		}
	} else {
		for(i=0;i<n_size;i++) {
			for(d=0;d<s_ndim;d++) {
				if ( c_posi[d] == 0 ) n_stps[i] = n_stps[i] - s_stps[d];
				if ( c_posi[d] == 2 ) n_stps[i] = n_stps[i] + s_stps[d];
			}
			for( d=0 , c_posi[d]++ ; c_posi[d]==3 && d<s_ndim-1 ; c_posi[d]=0 , c_posi[++d]++ );
		}
	}
	
	// Add all the pixels to a stack that are above the first treshold, use the array iterator
	// construct to deal with subsliced arrays, etc.  Use the array l_map to keep track of
	// pixels that have already been added, in the end l_map is the returned result
	
	u32 stack_size = 0;
	for(i=0;i<s_size;i++) l_map[i] = 0;
	
	ArrayIteratorP iterator = createArrayIterator(s_ndim,s_dims,s_stps);
	k = startArrayIterator(iterator,CV_ITERATOR_INCREASING);
	
	for(i=0;i<s_size;i++) {
		if ( src[k] >= ut ) {
			stack[stack_size++] = k;
			l_map[k] = 1;
		}
		k = incrementArrayIterator(iterator);
	}
	
	freeArrayIterator(iterator);
	
	// -------------------------------------------------------------------------------------------
	
	// Now we add pixels that are connected to the above pixels but remain above a second treshold
	// While doing this we must check to make sure the pixels being considered aren't on the border
	// of the array data, otherwise we risk seg_faults.  We use the border tester construct to verify
	// our currently considered position
	
	BorderTesterP b_tester = createBorderTester(s_ndim,s_dims,s_stps);

	for(i=0;i<stack_size;i++) {
		s64 location = stack[i];
		if ( testBorder(location,b_tester) ) continue;
		for(n=0;n<n_size;n++) {
			s64 neighbor = location + n_stps[n];
			if ( l_map[neighbor] != 1 && src[neighbor] >= lt ) {
				stack[stack_size++] = neighbor;
				l_map[neighbor] = 1;
			}
		}
	}
	
	freeBorderTester(b_tester);
	
	free(c_posi);
	free(n_stps);
	free(stack);
	
	return l_map;
	
	error:
	
	if ( c_posi != NULL ) free(c_posi);
	if ( n_stps != NULL ) free(n_stps);
	if ( stack != NULL ) free(stack);
	if ( l_map != NULL ) free(l_map);
	
	return NULL;
	
}

void boxSum( f64 xi[], const u32 s_ndim, const u32 s_dims[], const u32 s_stps[] ) {
	
	u32 r, d, k;
	
	u32 size = s_dims[0];
	for (d=1;d<s_ndim;d++) size *= s_dims[d];
	
	f64 * xt = NEWV(f64,size);
	
	for (d=0;d<s_ndim;d++) {
		
		s32 cols = s_dims[d];
		s32 rots = size / cols;
		
		s32 minb = 0;
		s32 maxb = cols-1;

		f64 * x1 = xi;
		f64 * x2 = xt;
		f64 * x3 = xt;

		for(k=0;k<rots;k++) {
			for(r=1;r<cols;r++) {
				*x2 = x1[r]+x1[r-1];
				x2 += rots;
			}
			x1 += cols;
			x2  = ++x3;
		}
		
		x3 = xi;
		xi = xt;
		xt = x3;

	}
	
	if ( d % 2 != 0 ) memcpy(xi,xt,sizeof(f64)*size);
	free(xt);
	
}

void boxBlur( f64 xi[], const u32 s_ndim, const u32 s_dims[], const u32 s_stps[], u32 s ) {
	
	s32 d, k, r;
	
	u32 size = s_dims[0];
	for (d=1;d<s_ndim;d++) size *= s_dims[d];
	
	f64 * xt = NEWV(f64,size);
	
	for (d=0;d<s_ndim;d++) {
		
		s32 cols = s_dims[d];
		s32 rots = size / cols;
		
		s32 minb = 0;
		s32 maxb = cols-1;

		f64 * x1 = xi;
		f64 * x2 = xt;
		f64 * x3 = xt;

		for(k=0;k<rots;k++) {
			for(r=1;r<cols;r++) x1[r] = x1[r] + x1[r-1];
			for(r=0;r<cols;r++) {
				s32 p1 = r + (s32)s;
				s32 p2 = r - (s32)s;
				if ( p2 < minb ) p2 = minb;
				if ( p1 > maxb ) p1 = maxb;
				*x2 = (x1[p1]-x1[p2])/(p1-p2+1.0);
				x2 += rots;
			}
			x1 += cols;
			x2  = ++x3;
		}
		
		x3 = xi;
		xi = xt;
		xt = x3;

	}
	
	if ( d % 2 != 0 ) {
		memcpy(xt,xi,sizeof(f64)*size);
		free(xi);
	} else {
		memcpy(xi,xt,sizeof(f64)*size);
		free(xt);
	}
	
}

f64 interpolate( f64 *image, f64 row, f64 col, u32 rows, u32 cols ) {
	u32 maxrow = rows-1;
	u32 maxcol = cols-1;
	u32 irow = row;
	u32 icol = col;
	image = image+(irow*cols+icol);
	f64 a = *(image);
	f64 b = *(image+=1);
	f64 c = *(image+=maxcol);
	f64 d = *(image+=1);
	f64 rw2 = row - irow;
	f64 rw1 = 1.0 - rw2;
	f64 cw2 = col - icol;
	f64 cw1 = 1.0 - cw2;
	return a*rw1*cw1+b*rw1*cw2+c*rw2*cw1+d*rw2*cw2;
}

void gaussian1d( f64 * data, s32 minl, s32 maxl, f64 sigma ) {
		
	s32 krad = sigma * 6;
	krad = MAX(krad,1);	
	
	f64 *kernel = NEWV(f64,krad);
	f64 * xt = NEWV(f64,maxl-minl+1);
	if ( kernel == NULL || xt == NULL) return;
	f64 two_s2  = 1.0 / ( sigma * sigma * 2 );
	f64 norm    = 1.0 / ( sigma * sqrt(2*PI) );
	s32 i, r;
	
	xt = xt - minl;
	
	for (i=0;i<krad;i++) kernel[i] = norm * exp( -i*i*two_s2 );
	
	for(r=minl;r<=maxl;r++) {
		f64 sum = data[r] * kernel[0];
		for(i=1;i<krad;i++) {
			s32 pos1 = r - i;
			s32 pos2 = r + i;
			if ( pos1 < minl ) pos1 = minl;
			if ( pos2 > maxl ) pos2 = maxl;
			sum += ( data[pos1] + data[pos2] ) * kernel[i];
		}
		xt[r] = sum;
	}
	
	for(i=minl;i<=maxl;i++) data[i] = xt[i];
	
	free(kernel);
	free(xt+minl);
		
}

void restoreFFTWisdom() {

	if ( fftw_is_wise == TRUE ) return;

	FILE * fp = fopen(fftw_wisdom_path,"r");
	if ( fp == NULL ) return;

	if ( fftw_import_wisdom_from_file(fp) == TRUE ) fftw_is_wise = TRUE;
	else {
		fprintf(stderr,"FFTW wisdom file stored in '%s' is corrupted\n",fftw_wisdom_path);
		if ( remove(fftw_wisdom_path) == 0 ) fprintf(stderr,"File removed\n");
		else fprintf(stderr,"Tried to remove %s but could not... possibly a permissions error\n",fftw_wisdom_path);
	}
	
	fclose(fp);
	
}

void saveFFTWisdom() {
	
	FILE * fp = fopen(fftw_wisdom_path,"w");
	if ( fp == NULL ) {
		fprintf(stderr,"Could not open path %s to save fftw wisdom file.\n",fftw_wisdom_path);
		return;
	}
	
	fftw_export_wisdom_to_file(fp);
	
	fclose(fp);

}

