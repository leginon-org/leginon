#include "ctf.h"

ArrayP findCTFMinima( ArrayP radialavg, s32 nsize );
ArrayP findCTFMaxima( ArrayP radialavg, s32 nsize );
f64 gen_n( f64 p[], f64 x );
double n_cost( const gsl_vector * variables, void * fit_data );
u32 run_minimizer( gsl_multimin_fminimizer * minimizer, u64 max_iter, f64 treshold );
f64 ctf_calc( f64 c[], f64 x );
double ctf_cost( const gsl_vector * variables, void * params );
f64 gen_e( f64 p[], f64 x );
double e_cost( const gsl_vector * variables, void * fit_data );
f64 calculate_score(f64 c1[], f64 c2[], u32 lcut, u32 rcut );
f64 calculate_cost(f64 c1[], f64 c2[], u32 lcut, u32 rcut );
void put_split( f64 data[], u32 size, f64 pos, f64 val );
void ctf_norm2( f64 fit_data[], f64 ctf_p[], f64 ctf[], f64 norm[], u32 size );

@implementation Array ( CTF_Functions )
		
-(id) ellipse1DAvg:(EllipseP)ellipse {
	
	if ( [self numberOfDimensions] != 2 ) return nil;

	f64 x_axis = 1.0;
	f64 y_axis = 1.0;
	f64 xaxis_angle = 0.0;
	
	if ( ellipse != nil ) {
		x_axis = [ellipse x_axis] / MIN([ellipse x_axis],[ellipse y_axis]);
		y_axis = [ellipse y_axis] / MIN([ellipse x_axis],[ellipse y_axis]);
		xaxis_angle = [ellipse rotation];
	}
	
	u32 r, rows = [self sizeOfDimension:1];
	u32 c, cols = [self sizeOfDimension:0];

	// This is because the center of an FFT is at pixel n/2+1,n/2 rather than n/2,n/2
	f64 x_rad = cols/2.0; 
	f64 y_rad = rows/2.0;
	
	f64 cs = cos(xaxis_angle);
	f64 ss = sin(xaxis_angle);
	
	u32 i, a_rad = MIN(x_rad,y_rad);

	// Create transform to origin-centered unit circle
	f64 TR[3][3], IT[3][3];
	f64 x1 = x_axis*cs+x_rad, y1 = y_rad+x_axis*ss;
	f64 x2 = x_rad-y_axis*ss, y2 = y_axis*cs+y_rad;
	createDirectAffineTransform(x_rad,y_rad,x1,y1,x2,y2,0.0,0.0,1.0,0.0,0.0,1.0,TR,IT);
	
	// Allocate array for average, and stdv data
	u32 dims[3] = { a_rad, 2, 0 };
	ArrayP radial_avg = [Array newWithType:TYPE_F64 andDimensions:dims];
	[radial_avg setNameTo:[self name]];
	
	f64 * ori_data = [self data];
	f64 * avg_mean = [radial_avg getRow:0];
	f64 * avg_cont = [radial_avg getRow:1];
//	f64 * avg_cont = [radial_avg getRow:2];
//	f64 * avg_quon = [radial_avg getRow:3];
	
	if ( ori_data == NULL ) goto error;
	if ( avg_mean == NULL ) goto error;
	if ( avg_cont == NULL ) goto error;
//	if ( avg_cont == NULL ) goto error;
	
	for(r=0;r<a_rad;r++) avg_mean[r] = 0.0;
	for(r=0;r<a_rad;r++) avg_cont[r] = 0.0;
//	for(r=0;r<a_rad;r++) avg_cont[r] = 0.0;
//	for(r=0;r<a_rad;r++) avg_quon[r] = 0.0;
	
	for(i=0,r=0;r<rows;r++) {
		for(c=0;c<cols;c++,i++) {
			
			f64 val = ori_data[i];
			
			f64 x = c*TR[0][0] + r*TR[1][0] + TR[2][0];
			f64 y = c*TR[0][1] + r*TR[1][1] + TR[2][1];
			
			f64 rad = sqrt(x*x+y*y);
			u32 irad = floor(rad);
			
			if ( irad >= a_rad ) continue;
		
			f64 rw1 = rad - irad;
			f64 rw2 = 1.0 - rw1;
			
			avg_cont[irad] = avg_cont[irad] + rw2;
			avg_mean[irad] = avg_mean[irad] + val*rw2;
//			avg_stdv[irad] = avg_stdv[irad] + (val-avg_stdv[irad])*(rw2/avg_cont[irad]);
//			avg_quon[irad] = avg_quon[irad] + (rw2*(avg_cont[irad]-rw2)/avg_cont[irad])*pow(val-avg_stdv[irad],2.0);
			
			if ( ++irad >= a_rad ) continue;
			
			avg_cont[irad] = avg_cont[irad] + rw1;
			avg_mean[irad] = avg_mean[irad] + val*rw1;
//			avg_stdv[irad] = avg_stdv[irad] + (val-avg_stdv[irad])*(rw1/avg_cont[irad]);
//			avg_quon[irad] = avg_quon[irad] + (rw1*(avg_cont[irad]-rw1)/avg_cont[irad])*pow(val-avg_stdv[irad],2.0);
	
		}
	}
	
	// Calculate mean
	// Compute RMSD
	// Compute RMSD use ABS, because occasionally the sum is off slightly
	for(r=0;r<a_rad;r++) avg_mean[r] = avg_mean[r] / avg_cont[r]; 
//	for(r=0;r<a_rad;r++) avg_stdv[r] = avg_quon[r] / avg_cont[r];
//	for(r=0;r<a_rad;r++) if ( isinf(avg_stdv[r]) ) fprintf(stderr,"INF Error\n"); 
//	for(r=0;r<a_rad;r++) if ( avg_stdv[r] < 0.0 ) fprintf(stderr,"RMSD Error\n"); 
//	for(r=0;r<a_rad;r++) avg_stdv[r] = sqrt(ABS(avg_stdv[r])); 
	
	return radial_avg;
	
	error:
	[radial_avg release];
	return nil;
	
}

@end

void put_split( f64 data[], u32 size, f64 pos, f64 val ) {
	
	u32 ipos = pos;
	f64 rw1 = pos - ipos;
	f64 rw2 = 1.0 - rw1;
	if ( ipos >= size ) return;
	data[ipos++] += val*rw2;
	if ( ipos >= size ) return;
	data[ipos]   += val*rw1;
	
}

u32 run_minimizer( gsl_multimin_fminimizer * minimizer, u64 max_iter, f64 treshold ) {
		
	u32 k;
	u32 status = 0;
	
	for(k=0;k<max_iter;k++) {
		
		status = gsl_multimin_fminimizer_iterate(minimizer);
		
		if (status) break;

		f64 score = gsl_multimin_fminimizer_size(minimizer);
		status = gsl_multimin_test_size(score,treshold);
		
		if (status == GSL_SUCCESS) break;
		
	}

	return k;
	
}

f64 gen_n( f64 p[], f64 x ) {
	return p[0] + p[1]*exp(-p[2]*(x-p[3])*(x-p[3])) + p[4]*exp(-p[5]*x) + p[6]*exp(-p[7]*(x-p[8])*(x-p[8]));
}

double n_cost( const gsl_vector * variables, void * fit_data ) {
	
	u32 k, size = [(id)fit_data sizeOfDimension:0];
	f64 * values = [(id)fit_data getRow:0];
	f64 * p = gsl_vector_ptr((gsl_vector *)variables,0);
	
	p[1] = sqrt(p[1]*p[1]);
	if ( p[2] > 1e-5 ) p[2] = 1e-4;
	if ( p[2] < 1e-10 ) p[2] = 1e-10;
	p[4] = sqrt(p[4]*p[4]);
	p[5] = sqrt(p[5]*p[5]);
	p[6] = sqrt(p[6]*p[6]);
	if ( p[7] > 1e-5 ) p[7] = 1e-4;
	if ( p[7] < 1e-10 ) p[7] = 1e-10;

	f64 cost = 0.0;

	for(k=0;k<size;k++) {
		f64 y_calc = gen_n(p,k);
		f64 y_diff = values[k]-y_calc;
		if ( y_diff >= 0.0 ) cost += pow(y_diff,2.0);
		else cost += pow(0.5-y_diff,2.0);
	}
	
	return cost;
	
}

ArrayP fitNoise( ArrayP fit_data ) {
	
	u32 i;
	
	u32 size = [fit_data sizeOfDimension:0];
	f64 * data = [fit_data getRow:0];
	
	u32 n_ndim = 9;

	gsl_multimin_fminimizer * n_min = gsl_multimin_fminimizer_alloc(gsl_multimin_fminimizer_nmsimplex, n_ndim);
	gsl_vector * n_start = gsl_vector_alloc(n_ndim);
	gsl_vector * n_steps = gsl_vector_alloc(n_ndim);
	
	// Start values for background model where chosen empirically through a lot of experimentation
	// Nonetheless, they will (hopefully) still work through a wide range of magnifications and microscopes
	
	gsl_vector_set(n_steps,0,5e-1);
	gsl_vector_set(n_steps,1,1e-1);
	gsl_vector_set(n_steps,2,1e-6);
	gsl_vector_set(n_steps,3,10.0);
	gsl_vector_set(n_steps,4,1e-1);
	gsl_vector_set(n_steps,5,1e-1);
	gsl_vector_set(n_steps,6,1e-1);
	gsl_vector_set(n_steps,7,1e-6);
	gsl_vector_set(n_steps,8,10.0);
	
	gsl_vector_set(n_start,0,0.0);
	gsl_vector_set(n_start,1,2e-1);
	gsl_vector_set(n_start,2,2e-6);
	gsl_vector_set(n_start,3,0.0);
	gsl_vector_set(n_start,4,9e-1);
	gsl_vector_set(n_start,5,5e-1);
	gsl_vector_set(n_start,6,1e-1);
	gsl_vector_set(n_start,7,1e-6);
	gsl_vector_set(n_start,8,size);
	
	gsl_multimin_function n_function;

	n_function.n = n_ndim;
	n_function.f = &n_cost;
	n_function.params = fit_data;
	
	gsl_multimin_fminimizer_set (n_min, &n_function, n_start, n_steps);
	u32 status = run_minimizer(n_min,10000,1e-10);

	u32 dims[2] = { n_ndim, 0 };
	ArrayP noise_params = [Array newWithType:TYPE_F64 andDimensions:dims];
	f64 * p = [noise_params data];
	
	for(i=0;i<n_ndim;i++) p[i] = gsl_vector_get(n_min->x,i);
	
	fprintf(stderr,"\n\tIterations: %d\n",status);
	fprintf(stderr,"\tNoise: %.2e %.2e %.2e %.2e %.2e %.2e %.2e %.2e %.2e\n",p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7],p[8]);
			
	gsl_multimin_fminimizer_free(n_min);	
	gsl_vector_free(n_start);
	gsl_vector_free(n_steps);
		
	return noise_params;

}

f64 gen_e( f64 p[], f64 x ) {
	return p[0] + p[1]*exp(-p[2]*x*x) + p[3]*exp(-p[4]*x);
}

double e_cost( const gsl_vector * variables, void * fit_data ) {
		
	u32 k, size = [(id)fit_data sizeOfDimension:0];
	f64 * values = [(id)fit_data data];
	f64 * p = gsl_vector_ptr((gsl_vector *)variables,0);
	
	p[1] = sqrt(p[1]*p[1]);
	p[2] = sqrt(p[2]*p[2]);
	p[3] = sqrt(p[3]*p[3]);
	p[4] = sqrt(p[4]*p[4]);

	f64 cost = 0.0;

	for(k=0;k<size;k++) {
		f64 y_calc = gen_e(p,k);
		f64 y_diff = y_calc-values[k];
		if ( y_diff >= 0.0 ) cost += pow(y_diff,2.0);
		else cost += pow(1.0-y_diff,10.0);
	}
	
	return cost;
	
}

ArrayP fitEnvelope( ArrayP fit_data ) {
	
	if ( [fit_data numberOfDimensions] != 1 ) return;
	
	u32 i, size = [fit_data sizeOfDimension:0];
	f64 * data = [fit_data data];
	
	u32 e_ndim = 5;
	
	gsl_multimin_fminimizer * e_min = gsl_multimin_fminimizer_alloc (gsl_multimin_fminimizer_nmsimplex, e_ndim);
	gsl_vector * e_start = gsl_vector_alloc(e_ndim);
	gsl_vector * e_steps = gsl_vector_alloc(e_ndim);
	
	f64 start1 = data[0];
	f64 start2 = 1.0/pow(size,2.0);
		
	gsl_vector_set(e_steps,0,1e-2);
	gsl_vector_set(e_steps,1,1e-2);
	gsl_vector_set(e_steps,2,1e-8);
	gsl_vector_set(e_steps,3,1e-3);
	gsl_vector_set(e_steps,4,0.999);
	
	gsl_vector_set(e_start,0,0.0);
	gsl_vector_set(e_start,1,1.0);
	gsl_vector_set(e_start,2,0.0);
	gsl_vector_set(e_start,3,1.0);
	gsl_vector_set(e_start,4,1.0);
			
	gsl_multimin_function e_function;
	
	e_function.n      = e_ndim;
	e_function.f      = &e_cost;
	e_function.params = fit_data;
	
	gsl_multimin_fminimizer_set (e_min, &e_function, e_start, e_steps);
	run_minimizer(e_min,10000,1e-20);
	
	u32 dims[2] = {e_ndim,0};
	ArrayP e_params = [Array newWithType:TYPE_F64 andDimensions:dims];
	f64 * b = [e_params data];
	
	for(i=0;i<e_ndim;i++) b[i] = gsl_vector_get(e_min->x,i);
	
    gsl_multimin_fminimizer_free(e_min);	
	gsl_vector_free(e_start);
    gsl_vector_free(e_steps);
	
	return e_params;
	
}

f64 ctf_calc( f64 c[], f64 x ) {
	
	x *= c[4];
	x = x * x;
		
	f64 chi = M_PI*c[2]*x*(c[0]+0.5*c[2]*c[2]*c[3]*x)-asin(c[1]);
	return sin(chi);
	
}

f64 ctf2_calc( f64 c[], f64 x ) {
	
	return pow(ctf_calc(c,x),2.0);
	
}

void ctf_calcv( f64 c[], f64 ctf[], u64 size ) {
	
	while ( size-- ) ctf[size] = ctf_calc(c,size);
	
}

void ctf2_calcv( f64 c[], f64 ctf[], u64 size ) {
	
	while ( size-- ) ctf[size] = ctf2_calc(c,size);
	
}

double ctf_cost( const gsl_vector * variables, void * params ) {
	
	static int iter = 0;
	f64 * p = gsl_vector_ptr((gsl_vector *)variables,0);

	if ( p[1] < 0.05 ) p[1] = randomNumber(0.05,0.50);
	if ( p[1] > 0.50 ) p[1] = randomNumber(0.05,0.50);
	
	u32 k, size = [(ArrayP)params sizeOfDimension:0];
	f64 * values = [(ArrayP)params data];

	f64 ctf[size], norm[size];
	ctf2_calcv(p,ctf,size);
	
	return calculate_cost(ctf,values,90,size-1);
	
}

void fitCTF( ArrayP fit_data, ArrayP ctf_p ) {
	
	if ( fit_data == nil ) return;	
	if ( ctf_p == nil ) return;
		
	if ( [fit_data sizeOfDimension:0] == 0 ) return;
	if ( [ctf_p sizeOfDimension:0] != 5 ) return;	
	
	u32 size = [fit_data sizeOfDimension:0];
	
	ArrayP normalized = [fit_data deepCopy];
	
	f64 * ctf_params = [ctf_p data];
	f64 * fit_norm = [normalized data];	

	fprintf(stderr,"Normalized....");

	peakNormalize(fit_norm,size);
	
	if ( ctf_params == NULL || fit_norm == NULL ) return;
		
	u32 c_ndim = 5;

	gsl_multimin_fminimizer * e_min = gsl_multimin_fminimizer_alloc(gsl_multimin_fminimizer_nmsimplex,c_ndim);
	gsl_vector * e_start = gsl_vector_alloc(c_ndim);
	gsl_vector * e_steps = gsl_vector_alloc(c_ndim);

	gsl_vector_set(e_steps,0,3e-7);
	gsl_vector_set(e_steps,1,3e-1);
	gsl_vector_set(e_steps,2,0.0);
	gsl_vector_set(e_steps,3,0.0);
	gsl_vector_set(e_steps,4,0.0);

	gsl_vector_set(e_start,0,ctf_params[0]);
	gsl_vector_set(e_start,1,ctf_params[1]);
	gsl_vector_set(e_start,2,ctf_params[2]);
	gsl_vector_set(e_start,3,ctf_params[3]);
	gsl_vector_set(e_start,4,ctf_params[4]);
				
	gsl_multimin_function e_function;
	
	e_function.n      = c_ndim;
	e_function.f      = &ctf_cost;
	e_function.params = normalized;
	
	u32 i, k, status1 = 0;
	
	for(i=0;i<c_ndim;i++) ctf_params[i] = 0.0;
	
	u32 trials = 20;
	f64 tolerance = 1e-10;
	
	for(i=0;i<trials;i++) {
		gsl_multimin_fminimizer_set(e_min, &e_function, e_start, e_steps);
		status1 += run_minimizer(e_min,10000,tolerance);
		gsl_vector * minimum = gsl_multimin_fminimizer_x(e_min);
		for(k=0;k<c_ndim;k++) ctf_params[k] += gsl_vector_get(minimum,k);
		gsl_vector_memcpy(e_start,minimum);
	}
	
	for(i=0;i<c_ndim;i++) ctf_params[i] /= trials;
	
	fprintf(stderr,"\n\tMinimizer used %d iterations (%.2lf%%)\n",status1,status1/(trials*10000.0));

    gsl_multimin_fminimizer_free(e_min);	
	gsl_vector_free(e_start);
    gsl_vector_free(e_steps);
	
	f64 * original_values = [fit_data data];
	f64 * c_ctf = NEWV(f64,size);
	
	for(i=0;i<size;i++) c_ctf[i] = ctf_calc(ctf_params,i);

	char name[256];
	sprintf(name,"%s.norm.txt",basename([fit_data name]));
	fprintf(stderr,"\tWriting CTF Fitting results to: %s\n\n",name);
	FILE * fp  = fopen(name,"w");	
	for(i=0;i<size;i++)	fprintf(fp,"%d\t%e\t%e\t%e\t%e\n",i,original_values[i],fit_norm[i],c_ctf[i],c_ctf[i]*c_ctf[i]);
	fclose(fp);

	[normalized release];
	free(c_ctf);
	
	return;
	
}

void peakNormalize( f64 values[], u32 size ) {
	
	s32 r, i;
	
	s32 nsize = 3;
	s32 min_n = 0;
	s32 max_n = size-1;
	
	u32 stack_size = 0;
	u32 * stack = NEWV(u32,size);
	f64 * norm = NEWV(f64,size);
	
	stack[stack_size++] = 0;
	for(r=0;r<size;r++) {
		u08 isminima = TRUE;
		u08 ismaxima = TRUE;
		for(i=1;i<=nsize;i++) {
			s32 p1 = r - i;
			s32 p2 = r + i;
			if ( p1 < min_n ) p1 = min_n;
			if ( p2 > max_n ) p2 = max_n;
			if ( values[r] >= values[p1] ) isminima = FALSE;
			if ( values[r] >= values[p2] ) isminima = FALSE;
			if ( values[r] <= values[p1] ) ismaxima = FALSE;
			if ( values[r] <= values[p2] ) ismaxima = FALSE;
		}
		if ( isminima == TRUE ) stack[stack_size++] = r;
		if ( ismaxima == TRUE ) stack[stack_size++] = r;
	}
	stack[stack_size++] = size-1;
	
	for(r=0;r<stack_size-1;r++) {
		u32 p1 = stack[r];
		u32 p2 = stack[r+1];
		f64 l_min_value = values[p1];
		f64 l_max_value = values[p1];
		for(i=p1;i<=p2;i++) l_min_value = MIN(l_min_value,values[i]);
		for(i=p1;i<=p2;i++) l_max_value = MAX(l_max_value,values[i]);
		for(i=p1;i<=p2;i++) norm[i] = ( values[i] - l_min_value ) / ( l_max_value - l_min_value );
	}
	
	for(i=0;i<size;i++) values[i] = norm[i];
	
	free(stack);
	free(norm);
	
}

f64 calculate_score(f64 c1[], f64 c2[], u32 lcut, u32 rcut ) {
	
	u32 i;
	
	if ( c1 == NULL || c2 == NULL ) return 0.0;
	if ( lcut > rcut ) return 0.0;
	
	f64 size = rcut - lcut + 1.0;
	
	f64 c1_mean = 0.0;
	f64 c2_mean = 0.0;
	
	for(i=lcut;i<=rcut;i++) c1_mean += c1[i];
	for(i=lcut;i<=rcut;i++) c2_mean += c2[i];
	
	c1_mean = c1_mean / size;
	c2_mean = c2_mean / size;
	
	f64 c1_stdv = 0.0;
	f64 c2_stdv = 0.0;
	
	for(i=lcut;i<=rcut;i++) c1_stdv += pow(c1[i]-c1_mean,2.0);
	for(i=lcut;i<=rcut;i++) c2_stdv += pow(c2[i]-c2_mean,2.0);
	
	c1_stdv = sqrt(c1_stdv / size);
	c2_stdv = sqrt(c2_stdv / size);
	
	f64 mean_conf = 0.0;
	for(i=lcut;i<=rcut;i++) mean_conf += ABS(c2[i]-c2_mean)*ABS(c1[i]-c1_mean);
	mean_conf = sqrt(mean_conf / size);
	
	mean_conf = (mean_conf*mean_conf)/(c1_stdv*c2_stdv);
	
	return (mean_conf-0.5)*2.0;
	
}

f64 calculate_cost(f64 c1[], f64 c2[], u32 lcut, u32 rcut ) {
	
	u32 i;
	
	if ( c1 == NULL || c2 == NULL ) return 0.0;
	if ( lcut > rcut ) return 0.0;
	
	f64 cost = 0.0;
	
	for(i=lcut;i<=rcut;i++) {
		f64 diff = c1[i]-c2[i];
		if ( isnan(diff) || isinf(diff) ) continue;
		else cost += pow(diff,2.0);
	}
	
	return cost;
	
}

f64 getTEMLambda( f64 volts ) {
	
//	f64 planck = 6.6260709544e-34;
//	f64 e_mass = 9.10938188e-31;
//	f64 e_charge = 1.60217646e-19;
//	f64 c_speed = 299792458.0;
	
	f64 t1 = 1.2265191e-9;  // This is planck/sqrt(2*e_masss*e_charge)
	f64 t2 = 9.7840893e-7;  // This is e_charge/(2*e_mass*c_speed*c_speed)
	
	f64 lambda = t1/sqrt(volts+t2*volts*volts);
	
	return lambda;
	
}

f64 getTEMVoltage( f64 lambda ) {
	
	f64 t1 = 1.2265191e-9;  // This is planck/sqrt(2*e_masss*e_charge)
	f64 t2 = 9.7840893e-7;  // This is e_charge/(2*e_mass*c_speed*c_speed)

	f64 a = t2;
	f64 b = 1.0;
	f64 c = -(t1*t1)/(lambda*lambda);
	
	f64 s1 = (-1.0+sqrt(1.0-4.0*a*c))/(2.0*a);
	f64 s2 = (-1.0-sqrt(1.0-4.0*a*c))/(2.0*a);
	
	if ( s1 > s2 ) return s1;
	else return s2;
	
}

void estimateDefocus( ArrayP fit_data, ArrayP ctf_params ) {
	
	if ( fit_data == nil ) return;
	if ( ctf_params == nil ) return;
	
	fit_data = [fit_data deepCopy];
	f64 * values = [fit_data data];
		
	u32 i, j, size = [fit_data sizeOfDimension:0];
	
	ArrayP minima = findCTFMinima(fit_data,1);
	ArrayP maxima = findCTFMaxima(fit_data,1);
	
	u32 min_num = [minima sizeOfDimension:0];
	u32 max_num = [maxima sizeOfDimension:0];
	
	fprintf(stderr,"\n\tFound %d %d extrema for estimate",min_num,max_num);
	
	f64 d_wide = MAX(max_num,min_num);
	u32 d_size = (max_num+min_num)*d_wide;
	
	u32 dims[2] = { d_size, 0 };
	ArrayP defocus_values = [Array newWithType:TYPE_F64 andDimensions:dims];

	f64 * defoci = [defocus_values data];		
	f64 * min_locations = [minima data];
	f64 * max_locations = [maxima data];
	f64 * ctf_p = [ctf_params data];

	d_size = 0;
	for(i=0;i<min_num;i++) {
		for(j=0;j<d_wide;j++) {
			f64 df = defocusForPeak(ctf_p,max_locations[i],j*2+1);
			if ( isnan(df) || isinf(df) ) continue;
			if ( df > -4e-7 ) continue;
			if ( df < -5e-5 ) continue;
			defoci[d_size++] = df;
		}
	}
	
	for(i=0;i<max_num;i++) {
		for(j=1;j<d_wide;j++) {
			f64 df = defocusForPeak(ctf_p,min_locations[i],j*2);
			if ( isnan(df) || isinf(df) ) continue;
			if ( df > -4e-7 ) continue;
			if ( df < -5e-5 ) continue;
			defoci[d_size++] = df;
		}
	}
	
	dims[0] = d_size;
	[defocus_values setShapeTo:dims];
	
	[defocus_values qsort];

	defoci = [defocus_values data];
	
	f64 * ctf = NEWV(f64,size);
	f64 * scores = NEWV(f64,d_size);
	
	if ( ctf == NULL || scores == NULL ) {
		fprintf(stderr,"Memory error in defocus estimation\n");
		return;
	}
	
	peakNormalize(values,size);
	
	f64 lcut = 50e-10;
	f64 rcut = 10e-10;
	
	lcut = MAX(0,(1.0/lcut)*(1.0/ctf_p[4]));
	rcut = MIN(size-1,(1.0/rcut)*(1.0/ctf_p[4]));
	
	fprintf(stderr,"\n\tUsing limits %f %f for estimation",lcut,rcut);
	
	for(i=0;i<d_size;i++) {
		ctf_p[0] = defoci[i];
		ctf2_calcv(ctf_p,ctf,size);
		scores[i] = calculate_cost(ctf,values,lcut,rcut);
	}

	gaussian1d(scores,0,d_size-1,1.0);
		
	f64 min_score = scores[0];
	for(i=0;i<d_size;i++) {
		if ( scores[i] < min_score ) {
			min_score = scores[i];
			ctf_p[0] = defoci[i];
		}
	}
	
	ctf2_calcv(ctf_p,ctf,size);

	char * name = NEWV(char,1000);
	sprintf(name,"%s.ctfinit.txt",basename([fit_data name]));
	FILE * fp = fopen(name,"w");
	if ( fp != NULL ) for(i=0;i<d_size;i++) fprintf(fp,"%le\t%le\n",-defoci[i],scores[i]);
	fclose(fp);
	sprintf(name,"%s.ctfinit-best.txt",basename([fit_data name]));
	fp = fopen(name,"w");
	if ( fp != NULL ) for(i=0;i<size;i++) fprintf(fp,"%le\t%le\n",ctf[i],values[i]);
	fclose(fp);
	free(name);
	
	[defocus_values release];
	[fit_data release];
	[minima release];
	[maxima release];
	
	free(scores);
	free(ctf);
	
	fprintf(stderr,"\n\tEstimated Defocus is: %e\n",ctf_p[0]);
	
}

ArrayP findCTFMinima( ArrayP radialavg, s32 nsize ) {
	
	s32 i, k, size = [radialavg sizeOfDimension:0];
	f64 * values = [radialavg getRow:0];
	
	s32 min_n = 0;
	s32 max_n = size - 1;
	
	u32 stacksize = 0;
	u32 * stack = NEWV(u32,size);

	for(k=0;k<size;k++) {
		u08 isminima = TRUE;
		for(i=1;i<=nsize;i++) {
			s32 p1 = k - i;
			s32 p2 = k + i;
			if ( p1 < min_n ) p1 = min_n;
			if ( p2 > max_n ) p2 = max_n;
			if ( values[k] >= values[p1] ) isminima = FALSE;
			if ( values[k] >= values[p2] ) isminima = FALSE;
		}
		if ( isminima == TRUE ) stack[stacksize++] = k;
	}
	
	u32 dims[3] = { stacksize, 2, 0 };
	ArrayP peak_array = [Array newWithType:TYPE_F64 andDimensions:dims];
	
	f64 * peak_positions = [peak_array getRow:0];
	f64 * peak_values = [peak_array getRow:1];
	
	for(k=0;k<stacksize;k++) {
		peak_positions[k] = stack[k];
		peak_values[k] = values[stack[k]];
	}
	
	free(stack);

	return peak_array;
	
}

ArrayP findCTFMaxima( ArrayP radialavg, s32 nsize ) {
	
	s32 i, k, size = [radialavg sizeOfDimension:0];
	f64 * values = [radialavg getRow:0];
	
	s32 min_n = 0;
	s32 max_n = size - 1;
	
	u32 stacksize = 0;
	u32 * stack = NEWV(u32,size);

	for(k=0;k<size;k++) {
		u08 ismaxima = TRUE;
		for(i=1;i<=nsize;i++) {
			s32 p1 = k - i;
			s32 p2 = k + i;
			if ( p1 < min_n ) p1 = min_n;
			if ( p2 > max_n ) p2 = max_n;
			if ( values[k] <= values[p1] ) ismaxima = FALSE;
			if ( values[k] <= values[p2] ) ismaxima = FALSE;
		}
		if ( ismaxima == TRUE ) stack[stacksize++] = k;
	}
	
	u32 dims[3] = { stacksize, 2, 0 };
	ArrayP peak_array = [Array newWithType:TYPE_F64 andDimensions:dims];
	
	f64 * peak_positions = [peak_array getRow:0];
	f64 * peak_values = [peak_array getRow:1];
	
	for(k=0;k<stacksize;k++) {
		peak_positions[k] = stack[k];
		peak_values[k] = values[stack[k]];
	}
	
	free(stack);

	return peak_array;
	
}

ArrayP ctfNormalize( ArrayP fit_data, ArrayP ctf_params ) {
	
	// Find CTF Min and Maxima
	
	s32 i, size = [fit_data sizeOfDimension:0];
	
	fit_data = [fit_data deepCopy];
	
	f64 * ctf_p = [ctf_params getRow:0];
	f64 * ctf_v = [fit_data getRow:0];
	
	for(i=0;i<size;i++) ctf_v[i] = log(ctf_v[i]);
	
	f64 minv = ctf_v[0];
	f64 maxv = ctf_v[0];

	for(i=0;i<size;i++) minv = MIN(ctf_v[i],minv);
	for(i=0;i<size;i++) maxv = MAX(ctf_v[i],maxv);
	
	for(i=0;i<size;i++) ctf_v[i] = (ctf_v[i]-minv)/(maxv-minv);
	
	f64 t1 = CPUTIME;
	fprintf(stderr,"\tFitting noise and envelope...");
	
	ArrayP n_params = fitNoise(fit_data);

	f64 * n_values = [n_params data];
	
	char name[1024];
	sprintf(name,"%s.back.txt",basename([fit_data name]));
	FILE * fp = fopen(name,"w");
	for(i=0;i<size;i++) fprintf(fp,"%e\t%e\t%e\n",ctf_v[i],gen_n(n_values,i),ctf_v[i]-gen_n(n_values,i));
	fclose(fp);
	
	for(i=0;i<size;i++) ctf_v[i] = (ctf_v[i]-gen_n(n_values,i));
		
	[n_params release];

	return fit_data;
	
}

f64 defocusForPeak( f64 c[], f64 peak_pos, u32 peak_num ) {
	
	// Super awesome function.  Returns the plausible defocus value for the given peak
	// Peak numbers are given as:
	// 0 is first zero-crossing (likely masked by the amplitude contrast)
	// 1 is the first peak (after the origin)
	// 2 is the second zero-crossing
	// 3 is the second peak (after the second zero-crossing)
	// 4 is the third zero crossing
	// 5 is the second positive peak (after the first zero-crossing)
	// ...
	
	// Unfortunately peak numbering in this manner leads to complications when underfocus becomes
	// too close to focus and the false minima moves in closer to the origin.  All peaks past
	// this false minima must be subtracted from twice the max peak number, which is not known since
	// we do not know the defocus.  Our only possible hint that we have moved past the false minima
	// is when the minimum being examined is moved past the maxima (zero-crossing in the derivative)
	// in the defocus function.  This point is given by setting the derivative to 0 and solving for x:
	
	//		   	   __________________
	// 	     4   /  n*pi-2asin(ac)
	// x = _   /   ----------------
	//	    \/     pi*lm^3*ap^4*cs
	
	// There are two possible ways to deal with this problem:
	// 1. Return NaN when asking for the defocus of a point past the above limit
	// 2. Keep a running tally of the peak numbers that have been requested, the last closest
	//    peak number that does not violate the above condition can be used as the false minima peak
	//    t, any peak number n past t can then be converted as 2t-n.
	
	// Unfortunately the second solution is harder to implement, makes the function non-thread safe
	// and harder to use correctly.  We therefore use solution one.
	
	// Function works by determining the chi factor required to get CTF^2 to be either 0 or 1
	// Two potential focus values are determined, one for overfocus(df1), and one for underfocus(df2)
	
	f64 ac = c[1];
	f64 lm = c[2];
	f64 cs = c[3];
	f64 ap = c[4];
	
	f64 x_limit = pow((peak_num*M_PI-2.0*asin(ac))/(M_PI*lm*lm*lm*ap*ap*ap*ap*cs),0.25);
	
	if ( peak_pos > x_limit ) return 0.0;
	
	f64 chi = asin(ac) - 0.5*peak_num*M_PI;;
	
	f64 x = pow(peak_pos*ap,2.0);
	
	f64 df = chi/(M_PI*lm*x) - 0.5*lm*lm*x*cs;

	return df;
	
}

f64 positionForPeak( f64 c[], u32 peak_num ) {
	
	// Super awesome function.  Returns the position in pixels for a given peak
	// Peak numbers are given as:
	// 0 is first zero-crossing (likely masked by the amplitude contrast)
	// 1 is the first peak (after the origin)
	// 2 is the second zero-crossing
	// 3 is the second peak (after the second zero-crossing)
	// 4 is the third zero crossing
	// 5 is the second positive peak (after the first zero-crossing)
	// ...
	
	f64 df = c[0];
	f64 ac = c[1];
	f64 lm = c[2];
	f64 cs = c[3];
	f64 ap = c[4];
	
	// First determine the positive root for the derivative of the chi function
	// This finds the local minima/maxima in chi which results in a "false" extrema
	// in the CTF function.  Note that for overfocus, chi does not cross zero
	// so there is no need to determine peak_switch.
	// For peak numbers below peak_switch the lesser of the roots
	// for the equation chi(x)-asin(ac) = peak_num*pi/2 must be used.  Any peak number 
	// desired past peak_switch must be inverted around peak_switch and the second root used.
	// The 0.8 is a rounding function, basically if the false peak isn't big enough 
	// we don't count it as a peak
	
	f64 aq = 0.5*M_PI*lm*lm*lm*cs;
	f64 bq = lm*df*M_PI;
	f64 cq = -asin(ac);
	
	if ( df >= 0.0 ) {
		
		cq = cq - 0.5*peak_num*M_PI;
		
		f64 dq = sqrt((bq*bq-4.0*aq*cq));
		f64 r1 = (-bq+dq) / (2.0*aq);
		f64 r2 = (-bq-dq) / (2.0*aq);
		
		// One of these roots is crappola
		
		f64 x1 = sqrt(ABS(r1))/ap;
		f64 x2 = sqrt(ABS(r2))/ap;
		
		u08 test_case1 = isnan(x1) || isinf(x1);
		u08 test_case2 = isnan(x2) || isinf(x2);
		
		if ( test_case1 && test_case2 ) return 0.0;
		
		if ( test_case1 ) return x2;
		if ( test_case2 ) return x1;
		
		return MIN(x1,x2);
		
	} else {
		
		u32 peak_switch = (2*sqrt(-df/(lm*lm*cs)))/M_PI + 0.9;
		if ( peak_num == peak_switch ) return sqrt(-df/(lm*lm*cs))/ap;
				
		if ( peak_num < peak_switch ) cq = cq + 0.5*peak_num*M_PI;
		else cq = cq + 0.5*(2*peak_switch-peak_num)*M_PI;

		f64 dq = sqrt((bq*bq-4.0*aq*cq));
		f64 r1 = (-bq+dq) / (2.0*aq);
		f64 r2 = (-bq-dq) / (2.0*aq);

		f64 x1 = sqrt(ABS(r1))/ap;
		f64 x2 = sqrt(ABS(r2))/ap;
		
		u08 test_case1 = isnan(x1) || isinf(x1);
		u08 test_case2 = isnan(x2) || isinf(x2);
		
		if ( test_case1 && test_case2 ) return 0.0;
		
		if ( test_case1 ) return x2;
		if ( test_case2 ) return x1;
		
		if ( peak_num < peak_switch ) return MIN(x1,x2);
		else return MAX(x1,x2);
		
	}
	
}

ArrayP g2DCTF( f64 df1, f64 df2, f64 theta, u32 rows, u32 cols, f64 apix, f64 cs, f64 kv, f64 ac ) {
	
	apix = apix * 1.0e-10;
	
	f64 lm = getTEMLambda(kv*1.0e3);
	
	f64 x_freq = 1.0/((cols-1)*2*apix);
	f64 y_freq = 1.0/(rows*apix);
	
	u32 dims[3] = {cols,rows,0};
	ArrayP ctf = [Array newWithType:TYPE_F64 andDimensions:dims];
	
	f64 * data = [ctf data];
	
	u32 r, c;
	f64 x_ori = cols-0.5;
	f64 y_ori = rows/2.0-0.5;
	
	f64 mdf = (df1+df2)/2.0;
	f64 ddf = (df1-df2)/2.0;
	
	f64 t1 = M_PI*lm;
	f64 t2 = 0.5*lm*lm*cs;
	f64 t3 = asin(ac);
	
	for(r=0;r<rows;r++) {
		for(c=0;c<cols;c++) {
			f64 x = (c-x_ori)*x_freq;
			f64 y = (y_ori-r)*y_freq;
			f64 t = atan2(y,x);
			f64 f = x*x+y*y;
			f64 d = mdf+ddf*cos(2.0*(t-theta));
			f64 chi = t1*f*(d+t2*f)-t3;
			data[r*cols+c] = sin(chi);
		}
	}
	
	return ctf;
	
}

