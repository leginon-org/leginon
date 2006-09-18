#include "lautil.h"
#include "util.h"
#include "mutil.h"

char GaussJordanElimination( double **matrix, double **result, int size ) {
	
	double **TEMP = CopyDMatrix(matrix,NULL,0,0,size-1,size-1);
	
	if ( TEMP == NULL ) {
		Debug(1,"GaussJordanElimination: Out of memory.\n");
		return FALSE;
	}
	
	if ( !InvertMatrix(TEMP,size) ) {
		Debug(1,"GaussJordanElimination: Matrix could not be inverted.\n");
		FreeDMatrix(TEMP,0,0);
		return FALSE;
	}
	
	MATMULT( TEMP, result, 0,0, size-1,size-1 );
	FreeDMatrix(TEMP,0,0);
	
	return TRUE;
		
}

void MATMULT( double **A, double **B, int r1, int c1, int r2, int c2 ) {
	int r, c, i;
	double **TEMP = CopyDMatrix(B,NULL,r1,c1,r2,c2);
	for (r=r1;r<=r2;r++) {
		for (c=c1;c<=c2;c++) {
			B[r][c] = 0;
			for (i=c1;i<=c2;i++) B[r][c] += A[r][i] * TEMP[i][c];
	}}
	FreeDMatrix(TEMP,0,0);
}	

char InvertMatrix( double **A, int size ) {
	
	int i, icol = 0, irow = 0, j, k ,l ,ll;
	double big, dum, pivinv, temp;
	
	int indxc[size];
	int indxr[size];
	int ipiv[size];
	
	for(j=0;j<size;j++) ipiv[j] = 0;
	
	for(i=0;i<size;i++) {
		big = 0;
		for(j=0;j<size;j++) {
			if (ipiv[j] != 1) {
				for(k=0;k<size;k++) {
					if (ipiv[k] == 0) {
						if (ABS(A[j][k]) >= big) {
							big = ABS(A[j][k]);
							irow = j;
							icol = k;
						}
					} else if ( ipiv[k] > 1) {
						Debug(1,"InvertMatrix: Matrix could not be inverted (Singular)\n");
						return FALSE;
					}
				}
			}
		}
		
		++(ipiv[icol]);
		
		if (irow != icol) for (l=0;l<size;l++) SWAP(A[irow][l],A[icol][l]);

		indxr[i] = irow;
		indxc[i] = icol;
		
		if (A[icol][icol] == 0) {
			Debug(1,"InvertMatrix: Matrix could not be inverted (Singular)\n");
			return FALSE;
		}
		
		pivinv = 1.0 / A[icol][icol];
		A[icol][icol] = 1;
		
		for(l=0;l<size;l++) A[icol][l] *= pivinv;
		
		for (ll=0;ll<size;ll++) {
			if	( ll != icol ) {
				dum = A[ll][icol];
				A[ll][icol] = 0;
				for (l=0;l<size;l++) A[ll][l] -= A[icol][l]*dum;
			}
		}
		
	}
	
	for (l=size-1; l >=0; l--) if (indxr[l] != indxc[l]) for (k=0;k<size;k++) SWAP(A[k][indxr[l]],A[k][indxc[l]]);
	
	return TRUE;
		
}

char LUDecomp( double **A, int n, int *index ) {
		
	if ( A == NULL || index == NULL ) return FALSE;
	
	int i, imax=0, j, k;
	double big, dum, sum, temp, vv[n], d;
	
	d = 1.0;

	for (i=0;i<n;i++) {
		big = 0.0;
		for (j=0;j<n;j++) if ((temp=ABS(A[i][j])) > big) big = temp;
		if (big == 0.0 ) return FALSE;
		vv[i] = 1.0/big;
	}
	
	for (j=0;j<n;j++) {
		for (i=0;i<j;i++) {
			sum = A[i][j];
			for (k=0;k<i;k++) sum -=A[i][k]*A[k][j];
			A[i][j] = sum;
		}
		big = 0.0;
		for (i=j;i<n;i++) {
			sum=A[i][j];
			for(k=0;k<j;k++) sum -= A[i][k]*A[k][j];
			A[i][j] = sum;
			if ( (dum=vv[i]*ABS(sum)) >=big ) {
				big=dum;
				imax=i;
			}
		}
		if (j!=imax) {
			for (k=0;k<n;k++) {
				dum=A[imax][k];
				A[imax][k]=A[j][k];
				A[j][k]=dum;
			}
			d=-d;
			vv[imax]=vv[j];
		}
		index[j]=imax;
		if (A[j][j] == 0.0) A[j][j]=TINY;
		if ( j != n ) {
			dum=1.0/(A[j][j]);
			for (i=j+1;i<n;i++) A[i][j] *= dum;
		}
	}
	
	return TRUE;
	
}

char LUSolveMatrix( double **A, double **B, int m ) {
	
	double vec[m];
	double **LU = AllocDMatrix(m,m,0,0);
	int  index[m];
	int col;
	
	CopyDMatrix(A,LU,0,0,m-1,m-1);
	if ( !LUDecomp(LU,m,index) ) return FALSE;

	for (col=0;col<m;col++) {
		GETCOL(B,col,vec,0,m-1);
		LUSolveVec(LU,m,index,vec);
		SETCOL(B,col,vec,0,m-1);
	}
	
	FreeDMatrix(LU,0,0);
	
	return TRUE;
	
}

void LUSolveVec( double **LU, int m, int *index, double *b ) {

	int i, ii=-1, ip, j;
	double sum;

	for (i=0;i<m;i++) {
		ip=index[i];
		sum=b[ip];
		b[ip]=b[i];
		if (ii<0) for (j=ii;j<=i-1;j++) sum -= LU[i][j]*b[j];
		else if (sum) ii=i;
		b[i] = sum;
	}
	for (i=m-1;i>=0;i--) {
		sum=b[i];
		for (j=i+1;j<m;j++) sum -= LU[i][j]*b[j];
		b[i]=sum/LU[i][i];
	}

}

char SchurEigenVectors( double **T, double **Q, double **X_re, double **X_im, int m ) {

	int	i, j, limit;
	double t11_re, t11_im, t12, t21, t22_re, t22_im;
	double l_re, l_im, det_re, det_im, invdet_re, invdet_im;
	double val1_re, val1_im, val2_re, val2_im;
	double tmp_val1_re, tmp_val1_im, tmp_val2_re, tmp_val2_im;
	double sum, diff, discrim, magdet, norm, scale;

	if ( T == NULL || X_re == NULL ) return FALSE;

	double *tmp1_re = malloc(sizeof(double)*m);
	double *tmp1_im = malloc(sizeof(double)*m);
	double *tmp2_re = malloc(sizeof(double)*m);
	double *tmp2_im = malloc(sizeof(double)*m);

	i = 0;
	while ( i < m ) {
	    if ( i+1 < m && T[i+1][i] != 0.0 ) {
			sum  = 0.5*(T[i][i]+T[i+1][i+1]);
			diff = 0.5*(T[i][i]-T[i+1][i+1]);
			discrim = diff*diff + T[i][i+1]*T[i+1][i];
			l_re = l_im = 0.0;
			if ( discrim < 0.0 ) {
				l_re = sum;
				l_im = sqrt(-discrim);
			} else {
				free(tmp1_re);free(tmp1_im);free(tmp2_re);free(tmp2_im);
				return FALSE;
			}
	    } else {
			l_re = T[i][i];
			l_im = 0.0;
	    }

	    VZERO(tmp1_im,0,m-1);
	    VRAND(tmp1_re,0,m-1);
	    SVMLT(MACHEPS,tmp1_re,0,m-1);

	    limit = ( l_im != 0.0 ) ? i+1 : i;
		VZERO(tmp1_re,limit+1,m-1);
	    j = limit;
	    while ( j >= 0 ) {
			if ( j > 0 && T[j][j-1] != 0.0 ) {   
		    	val1_re = tmp1_re[j-1] - IP(tmp1_re,T[j-1],j+1,limit);
		    	val1_im = tmp1_im[j-1] - IP(tmp1_im,T[j-1],j+1,limit);
		    	val2_re = tmp1_re[j]   - IP(tmp1_re,T[j],j+1,limit);
		    	val2_im = tmp1_im[j]   - IP(tmp1_im,T[j],j+1,limit);
		    
		    	t11_re = T[j-1][j-1] - l_re;
		    	t11_im = - l_im;
		    	t22_re = T[j][j] - l_re;
		    	t22_im = - l_im;
		    	t12 = T[j-1][j];
		    	t21 = T[j][j-1];

		    	scale =  fabs(T[j-1][j-1]) + fabs(T[j][j]) + fabs(t12) + fabs(t21) + fabs(l_re) + fabs(l_im);

			    det_re = t11_re*t22_re - t11_im*t22_im - t12*t21;
			    det_im = t11_re*t22_im + t11_im*t22_re;
			    magdet = det_re*det_re+det_im*det_im;
			    if ( sqrt(magdet) < MACHEPS*scale ) {
			        det_re = MACHEPS*scale;
					magdet = det_re*det_re+det_im*det_im;
			    }
			    invdet_re =   det_re/magdet;
			    invdet_im = - det_im/magdet;
				tmp_val1_re = t22_re*val1_re-t22_im*val1_im-t12*val2_re;
			    tmp_val1_im = t22_im*val1_re+t22_re*val1_im-t12*val2_im;
			    tmp_val2_re = t11_re*val2_re-t11_im*val2_im-t21*val1_re;
			    tmp_val2_im = t11_im*val2_re+t11_re*val2_im-t21*val1_im;
			    tmp1_re[j-1] = invdet_re*tmp_val1_re - invdet_im*tmp_val1_im;
			    tmp1_im[j-1] = invdet_im*tmp_val1_re + invdet_re*tmp_val1_im;
				tmp1_re[j]   = invdet_re*tmp_val2_re - invdet_im*tmp_val2_im;
				tmp1_im[j]   = invdet_im*tmp_val2_re + invdet_re*tmp_val2_im;
				j -= 2;
		} else {
		    t11_re = T[j][j] - l_re;
		    t11_im = - l_im;
		    magdet = t11_re*t11_re + t11_im*t11_im;
		    scale = fabs(T[j][j]) + fabs(l_re);
		    if ( sqrt(magdet) < MACHEPS*scale ) {
		        t11_re = MACHEPS*scale;
				magdet = t11_re*t11_re + t11_im*t11_im;
		    }
		    invdet_re =   t11_re/magdet;
		    invdet_im = - t11_im/magdet;
		    val1_re = tmp1_re[j] - IP(tmp1_re,T[j],j+1,limit);
		    val1_im = tmp1_im[j] - IP(tmp1_im,T[j],j+1,limit);
		    tmp1_re[j] = invdet_re*val1_re - invdet_im*val1_im;
		    tmp1_im[j] = invdet_im*val1_re + invdet_re*val1_im;
		    j -= 1;
		}
	}

	norm = VNORMINF(tmp1_re,0,m-1) + VNORMINF(tmp1_im,0,m-1);
	SVMLT(1/norm,tmp1_re,0,m-1);
	if ( l_im != 0.0 ) SVMLT(1/norm,tmp1_im,0,m-1);
	MVMLT(Q,tmp1_re,tmp2_re,m);
	if ( l_im != 0.0 ) MVMLT(Q,tmp1_im,tmp2_im,m);
	if ( l_im != 0.0 ) norm = sqrt(IP(tmp2_re,tmp2_re,0,m-1)+IP(tmp2_im,tmp2_im,0,m-1));
	else norm = VNORM2(tmp2_re,0,m-1);
	SVMLT(1/norm,tmp2_re,0,m-1);
	if ( l_im != 0.0 ) SVMLT(1/norm,tmp2_im,0,m-1);

	if ( l_im != 0.0 ) {
		if ( X_im == NULL ) {
			free(tmp1_re);free(tmp1_im);free(tmp2_re);free(tmp2_im);
			return FALSE;
		}
		SETCOL(X_re,i,tmp2_re,0,m-1);
		SETCOL(X_im,i,tmp2_im,0,m-1);
		SVMLT(-1.0,tmp2_im,0,m-1);
		SETCOL(X_re,i+1,tmp2_re,0,m-1);
		SETCOL(X_im,i+1,tmp2_im,0,m-1);
		i += 2;
	}
	else {
		SETCOL(X_re,i,tmp2_re,0,m-1);
		if ( X_im != NULL ) SETCOL(X_im,i,tmp1_im,0,m-1);
		i += 1;
	}
	}
	free(tmp1_im);free(tmp1_re);free(tmp2_re);free(tmp2_im);
	
	return TRUE;
}

void GETCOL( double **mat, int col, double *vec, int l, int r ) {
	while (l<=r) {vec[l]=mat[l][col];++l;}
}

void SETCOL( double **mat, int col, double *vec, int l, int r ) {
	while (l<=r) {mat[l][col]=vec[l];++l;}
}

double VNORM2( double *x, int l, int r ) {
	double sum = 0.0;
	while (l<=r) {sum+=x[l]*x[l];++l;}
	return sqrt(sum);
}

void SVMLT( double scalar, double *vector, int l, int r ) {
	while(l<=r) vector[l++] *= scalar;
}

void SVADD( double scalar, double *v, int l, int r ) {
	while(l<=r) v[l++] += scalar;
}

void VZERO( double *vector, int l, int r ) {
	while(l<=r) {vector[l] = 0.0;++l;}
}

void VRAND( double *vector, int l, int r ) {
	while(l<=r) vector[l++] = RandomNumber(0,1);
}

double IP( double *dp1, double *dp2, int l, int r ) {
    double sum = 0.0;
	while (l<=r) {sum+=dp1[l]*dp2[l];l++;}
    return sum;
}

double VNORMINF( double *x, int l, int r ) {
	double maxval, tmp;
	maxval = 0.0;
	while (l<=r) {	
		tmp = fabs(x[l++]);
		maxval = MAX(maxval,tmp);
	}
	return maxval;
}

void VLIMIT( double *v, int l, int r, double max, double min ) {
	while (l<=r) { v[l] = MAX(min,MIN(v[l],max)); l++; }
}

void MVMLT( double **A, double *b, double *out, int m) {
	int	i;
	for(i=0;i<m;i++) out[i] = IP(A[i],b,0,m-1);
}

float VDISTSQ( float *d1, float *d2, int l, int r) {
	float distsq = 0;
	int i;
    for (i=l;i<=r;i++) distsq += (d1[i]-d2[i])*(d1[i]-d2[i]);
    return distsq;
}

void InitIMatrix( int **array, int minr, int minc, int maxr, int maxc, int val ) {
	int row, col;
	for (row=minr;row<=maxr;++row) {
		for (col=minc;col<=maxc;++col) {
			array[row][col] = val;
	}}
}

double *HHVEC(double *vec, int i0, double *beta, double *out, double *newval, int m) {
	if ( vec!=out ) VCOPY(vec,out,0,m-1);
	double norm = sqrt(IP(out,out,i0,m-1));
	if ( norm <= 0.0 ) {
		*beta = 0.0;
		return (out);
	}
	*beta = 1.0/(norm*(norm+fabs(out[i0])));
	if (out[i0]>0.0) *newval = -norm;
	else *newval = norm;
	out[i0] -= *newval;
	return (out);
}



double	**HHTRCOLS( double **M, int i0, int j0, double *hh, double beta, int m ) {
	if ( beta == 0.0 )	return (M);	
	int	i;
	double *w = malloc(sizeof(double)*m);
	for(i=0;i<m;w[i++]=0.0);
	for (i=i0;i<m;i++) if ( hh[i] != 0.0 ) MLTADD(w,M[i],hh[i],j0,m-1);
	for (i=i0;i<m;i++) if ( hh[i] != 0.0 ) MLTADD(M[i],w,-beta*hh[i],j0,m-1);
	free(w);
	return (M);
}

double	**HHTRROWS( double **M, int i0, int j0, double *hh, double beta, int m) {
	double	ip, scale;
	int	i;
	if ( beta == 0.0 )	return (M);
	for (i=i0;i<m;i++) {	
		ip = IP(M[i],hh,j0,m-1);
		scale = beta*ip;
		if ( scale == 0.0 ) continue;
		MLTADD(M[i],hh,-scale,j0,m-1);
	}
	return (M);
}

double **HFACTOR( double **A, double *diag, double *beta, int m) {
	double *tmp1 = malloc(sizeof(double)*m);
	int	k;
	for (k=0;k<m-1;k++) {
		GETCOL(A,k,tmp1,0,m-1);
		HHVEC(tmp1,k+1,&(beta[k]),tmp1,&(A[k+1][k]),m);
		diag[k]=tmp1[k+1];
		HHTRCOLS(A,k+1,k+1,tmp1,beta[k],m);
		HHTRROWS(A,0  ,k+1,tmp1,beta[k],m);
	}
	free(tmp1);
	return (A);
}

double *VCOPY( double *in, double *out, int l, int r ) {
	while (l<=r) {out[l]=in[l];++l;}
	return out;
}

double *MLTADD( double *v1, double *v2, double s, int l, int r ) {
	while (l<=r) {v1[l]+=v2[l]*s;++l;}
	return v1;
}

void HHTRVEC( double *hh, double beta, int i0, double *in, double *out, int m ) {
	double scale;
	scale = beta*IP(hh,in,i0,m-1);
	if (in!=out) VCOPY(in,out,0,m-1);
	MLTADD(out,hh,-scale,i0,m-1);
}


void MAKEHQ( double **H, double *diag, double *beta, double **Qout, int m ) {
	int	i, j, limit;
	double *tmp1 = malloc(sizeof(double)*m);
	double *tmp2 = malloc(sizeof(double)*m);
	limit = m-1;
	for (i=0;i<m;i++) {
		for (j=0;j<m;j++) tmp1[j] = 0.0;
		tmp1[i] = 1.0;
		for (j=limit-1;j>= 0;j--) {
			GETCOL(H,j,tmp2,0,m-1);
			tmp2[j+1] = diag[j];
			HHTRVEC(tmp2,beta[j],j+1,tmp1,tmp1,m);
		}
		SETCOL(Qout,i,tmp1,0,m-1);
	}
	free(tmp1);free(tmp2);
}

void MAKEH( double **H, double **Hout, int m) {
	int	i, j;
	if ( H != Hout ) CopyDMatrix(H,Hout,0,0,m-1,m-1);
	for (i=1;i<m;i++) for (j=0;j<i-1;j++) Hout[i][j]=0.0;
}

void ROTROWS( double **mat, int i, int k, double c, double s, double **out, int m, int n) {
	int	j;
	CopyDMatrix(mat,out,0,0,m-1,n-1);
	for (j=0;j<n;j++) {
		double temp = c*(out[i][j]) + s*(out[k][j]);
		out[k][j] = -s*(out[i][j]) + c*(out[k][j]);
		out[i][j] = temp;
	}
}

void HHLDR3(double x, double y, double z, double *nu1, double *beta, double *newval) {
	double alpha;
	if (x>=0.0)	alpha=sqrt(x*x+y*y+z*z);
	else alpha=-sqrt(x*x+y*y+z*z);
	*nu1 = x+alpha;
	*beta = 1.0/(alpha*(*nu1));
	*newval = alpha;
}

void HHLDR3COLS(double **A, int k, int j0, double beta, double nu1, double nu2, double nu3, int m, int n) {
	double ip, prod;
	int	j;
	if ( k < 0 || k+3 > m || j0 < 0 ) FatalError("hhldr3cols: bounds\n");
	for (j=j0;j<n;j++) {
	    ip = nu1*(A[k][j])+nu2*(A[k+1][j])+nu3*(A[k+2][j]);
	    prod = ip*beta;
		A[k  ][j] -= prod*nu1;
		A[k+1][j] -= prod*nu2;
		A[k+2][j] -= prod*nu3;
	}
}

void HHLDR3ROWS(double **A, int k, int i0, double beta, double nu1, double nu2, double nu3, int m, int n) {
	double ip, prod;
	int	i;
	if ( k < 0 || k+3 > n ) FatalError("hhldr3rows: bounds\n");
	i0 = MIN(i0,m-1);
	for (i=0;i<=i0;i++) {
	    ip = nu1*(A[i][k])+nu2*(A[i][k+1])+nu3*(A[i][k+2]);
	    prod = ip*beta;
		A[i][k  ] -= prod*nu1;
		A[i][k+1] -= prod*nu2;
		A[i][k+2] -= prod*nu3;
	}
}

void GIVENS( double x, double y, double *c, double *s) {
	double norm = sqrt(x*x+y*y);
	if ( norm == 0.0 ) {*c=1.0;*s=0.0;}
	else {*c=x/norm;*s=y/norm;}
}

void ROTCOLS( double **mat, int i, int k, double c, double s, double **out, int m, int n) {
	int	j;
	if ( mat != out ) CopyDMatrix(mat,out,0,0,m-1,n-1);
	for (j=0;j<m;j++) {
		double temp = c*(out[j][i])+s*(out[j][k]);
		out[j][k] =  -s*(out[j][i])+c*(out[j][k]);
		out[j][i] = temp;
	}
}	

char SchurDecomposition( double **A, double **Q, int m) {
    int		i, j, iter, k, k_min, k_max, k_tmp, split;
    double	beta2, c, discrim, dummy, nu1, s, tmp, x, y, z;
    double	sqrt_macheps;
    double *diag=malloc(sizeof(double)*m);
	double *beta=malloc(sizeof(double)*m);

    HFACTOR(A,diag,beta,m);
    if ( Q != NULL ) MAKEHQ(A,diag,beta,Q,m);
    MAKEH(A,A,m);

    sqrt_macheps = sqrt(MACHEPS);

    k_min = 0;

    while ( k_min < m ) {
		double	a00, a01, a10, a11;
		double	scale, t, numer, denom;

		k_max = m-1;
		for (k=k_min;k<k_max;k++) if (A[k+1][k]==0.0) {k_max=k;break;}
		if (k_max<=k_min) {k_min=k_max+1;continue;}
		if (k_max==k_min+1) {
	    	a00 = A[k_min][k_min];
	    	a01 = A[k_min][k_max];
	   		a10 = A[k_max][k_min];
	    	a11 = A[k_max][k_max];
	    	tmp = a00 - a11;
	    	discrim = tmp*tmp + 4*a01*a10;
	    	if ( discrim < 0.0 ) {	
				numer = - tmp;
				denom = ( a01+a10 >= 0.0 ) ? (a01+a10) + sqrt((a01+a10)*(a01+a10)+tmp*tmp) : (a01+a10) - sqrt((a01+a10)*(a01+a10)+tmp*tmp);
				if ( denom != 0.0 ) {
		    		t = numer/denom;
		    		scale = c = 1.0/sqrt(1+t*t);
		    		s = c*t;
				} else {
		    		c = 1.0;
		    		s = 0.0;
				}
				ROTCOLS(A,k_min,k_max,c,s,A,m,m);
				ROTROWS(A,k_min,k_max,c,s,A,m,m);
				if ( Q != NULL ) ROTCOLS(Q,k_min,k_max,c,s,Q,m,m);
				k_min = k_max + 1;
				continue;
	    	} else {
				numer = ( tmp >= 0.0 ) ? - tmp - sqrt(discrim) : - tmp + sqrt(discrim);
				denom = 2*a01;
				if ( fabs(numer) < fabs(denom) ) {
		    		t = numer/denom;
		    		scale = c = 1.0/sqrt(1+t*t);
		    		s = c*t;
				} else if ( numer != 0.0 ) {
		    		t = denom/numer;
		    		scale = 1.0/sqrt(1+t*t);
		    		c = fabs(t)*scale;
		    		s = ( t >= 0.0 ) ? scale : -scale;
				} else {
		    		c = 0.0;
		  			s = 1.0;
				}
				ROTCOLS(A,k_min,k_max,c,s,A,m,m);
				ROTROWS(A,k_min,k_max,c,s,A,m,m);
				if ( Q != NULL ) ROTCOLS(Q,k_min,k_max,c,s,Q,m,m);
				k_min = k_max + 1;
				continue;
	    	}
		}

		split = FALSE; iter = 0;
		while ( ! split ) {
	    	iter++;
	    	k_tmp = k_max - 1;
	    	a00 = A[k_tmp][k_tmp];
	    	a01 = A[k_tmp][k_max];
	    	a10 = A[k_max][k_tmp];
	    	a11 = A[k_max][k_max];
	    	if ( iter >= 5 && fabs(a00-a11) < sqrt_macheps*(fabs(a00)+fabs(a11)) && (fabs(a01) < sqrt_macheps*(fabs(a00)+fabs(a11)) || fabs(a10) <
				sqrt_macheps*(fabs(a00)+fabs(a11))) ) {
	    		if ( fabs(a01) < sqrt_macheps*(fabs(a00)+fabs(a11)) ) A[k_tmp][k_max] = 0.0;
	    		if ( fabs(a10) < sqrt_macheps*(fabs(a00)+fabs(a11)) ) {
					A[k_max][k_tmp] = 0.0;
		  			split = TRUE;
		  			continue;
				}
	    	}

	    	s = a00 + a11;
	    	t = a00*a11 - a01*a10;

	    	if ( k_max == k_min + 1 && s*s < 4.0*t ) {
				split = TRUE;
				continue;
	    	}

	    	if ( (iter % 10) == 0 ) {
				s += iter*0.02;
				t += iter*0.02;
	    	}
	    	k_tmp = k_min + 1;
	    	a00 = A[k_min][k_min];
	    	a01 = A[k_min][k_tmp];
	    	a10 = A[k_tmp][k_min];
	    	a11 = A[k_tmp][k_tmp];
	    	x = a00*a00 + a01*a10 - s*a00 + t;
	    	y = a10*(a00+a11-s);
	    	if ( k_min + 2 <= k_max ) z = a10*A[k_min+2][k_tmp];
	    	else z = 0.0;
			for ( k = k_min; k <= k_max-1; k++ ) {
				if ( k < k_max - 1 ) {
		    		HHLDR3(x,y,z,&nu1,&beta2,&dummy);
		    		HHLDR3COLS(A,k,MAX(k-1,0),beta2,nu1,y,z,m,m);
		    		HHLDR3ROWS(A,k,MIN(m-1,k+3),beta2,nu1,y,z,m,m);
		    		if ( Q != NULL ) HHLDR3ROWS(Q,k,m-1,beta2,nu1,y,z,m,m);
				} else {
		    		GIVENS(x,y,&c,&s);
		    		ROTCOLS(A,k,k+1,c,s,A,m,m);
		    		ROTROWS(A,k,k+1,c,s,A,m,m);
		    		if ( Q != NULL ) ROTCOLS(Q,k,k+1,c,s,Q,m,m);
				}
				x = A[k+1][k];
				if ( k <= k_max - 2 ) y = A[k+2][k];
				else y = 0.0;
				if ( k <= k_max - 3 ) z = A[k+3][k];
				else z = 0.0;
	    	}
	    	for ( k = k_min; k <= k_max-2; k++ ) {
				A[k+2][k] = 0.0;
				if ( k < k_max-2 ) A[k+3][k] = 0.0;
	    	}
	    	for (k=k_min;k<k_max;k++) if (fabs(A[k+1][k])<MACHEPS*(fabs(A[k][k])+fabs(A[k+1][k+1]))) {
				A[k+1][k] = 0.0;
				split = TRUE;
			}
		}
    }
    
    for (i=0;i<m;i++) for (j=0;j<i-1;j++) A[i][j] = 0.0;
    for (i=0;i<m-1;i++) if (fabs(A[i+1][i]) < MACHEPS*(fabs(A[i][i])+fabs(A[i+1][i+1]))) A[i+1][i] = 0.0;
	free(diag);free(beta);
    return TRUE;
}

void SVDSOLVEVEC( double **U, double *W, double **V, int m, int n, double *b, double *x ) {
	int jj, j, i;
	double s, *tmp=malloc(sizeof(double)*n);
	
	for(j=0;j<n;j++) {
		s=0.0;
		if ( W[j] ) {
			for (i=0;i<m;i++) s+=U[i][j]*b[i];
			s /= W[j];
		}
		tmp[j]=s;
	}
	
	for (j=0;j<n;j++) {
		s=0.0;
		for (jj=0;jj<n;jj++) s+=V[j][jj]*tmp[jj];
		x[j]=s;
	}
	
	free(tmp);
	
}

char SVDCMP( double **A, int m, int n, double *W, double **V ) {
	
	int flag, i, its, j, jj, k, l, nm;
	double anorm, c, f, g, h, s, scale, x, y, z, rv1[n];

	x=g=scale=anorm=0.0;
	
	for (i=0;i<n;i++) {
		l=i+1;
		rv1[i]=scale*g;
		g=s=scale=0.0;
		if (i<m) {
			for (k=i;k<m;k++) scale += ABS(A[k][i]);
			if (scale) {
				for (k=i;k<m;k++) {
					A[k][i] /= scale;
					s += A[k][i]*A[k][i];
				}
				f = A[i][i];
				g = -SIGN(sqrt(s),f);
				h=f*g-s;
				A[i][i] = f-g;
				for (j=l;j<n;j++) {
					for (s=0.0,k=i;k<m;k++) s+= A[k][i]*A[k][j];
					f = s/h;
					for (k=i;k<m;k++) A[k][j] += f*A[k][i];
				}
				for (k=i;k<m;k++) A[k][i] *= scale;
			}
		}
		W[i]=scale*g;
		g=s=scale=0.0;
		if ( i < m && i < n-1 ) {
			for (k=l;k<n;k++) scale += ABS(A[i][k]);
			if (scale) {
				for (k=l;k<n;k++) {
					A[i][k] /= scale;
					s += A[i][k]*A[i][k];
				}
				f=A[i][l];
				g = -SIGN(sqrt(s),f);
				h = f*g-s;
				A[i][l] = f-g;
				for (k=l;k<n;k++) rv1[k]=A[i][k]/h;
				for (j=l;j<m;j++) {
					for (s=0.0,k=l;k<n;k++) s += A[j][k]*A[i][k];
					for (k=l;k<n;k++) A[j][k] += s*rv1[k];
				}
				for (k=l;k<n;k++) A[i][k] *= scale;
			}
		}
		anorm=MAX(anorm,(ABS(W[i])+ABS(rv1[i])));
	}
	
	for (i=n-1;i>=0;i--) {
		if ( i < n-1 ) {
			if (g) {
				for (j=l;j<n;j++) V[j][i] = (A[i][j]/A[i][l])/g;
				for (j=l;j<n;j++) {
					for (s=0.0,k=l;k<n;k++) s += A[i][k]*V[k][j];
					for (k=l;k<n;k++) V[k][j] += s*V[k][i];
				}
			}
			for (j=l;j<n;j++) V[i][j] = V[j][i] = 0.0;
		}
		V[i][i]=1.0;
		g=rv1[i];
		l=i;
	}
	
	for (i=MIN(m-1,n-1);i>=0;i--) {
		l = i+1;
		g=W[i];
		for (j=l;j<n;j++) {
			for (s=0.0,k=l;k<m;k++) s += A[k][i]*A[k][j];
			f = (s/A[i][i])*g;
			for (k=i;k<m;k++) A[k][j] += f*A[k][i];
		}
		for (j=i;j<=m;j++) A[j][i]=0.0;
		++A[i][i];
	}
	
	for (k=n-1;k>=0;k--) {
		for (its=1;its<=30;its++) {
			flag=1;
			for (l=k;l>=0;l--) {
				nm=l-1;
				if ( ABS(rv1[l])+anorm == anorm ) {
					flag = 0;
					break;
				}
				if ( ABS(W[nm])+anorm == anorm ) break;
			}
			if ( flag ) {
				c=0.0;
				s=1.0;
				for (i=l;i<=k;i++) {
					f=s*rv1[i];
					rv1[i]=c*rv1[i];
					if ( ABS(f)+anorm == anorm ) break;
					g=W[i];
					h=pythag(f,g);
					W[i]=h;
					h=1.0/h;
					c=g*h;
					s= -f*h;
					for (j=0;j<m;j++) {
						y=A[j][nm];
						z=A[j][i];
						A[j][nm] = y*c+z*s;
						A[j][i]  = z*c-y*s;
					}
				}
			}
			z=W[k];
			if (l == k ) {
				if ( x < 0.0 ) {
					W[k] = -z;
					for (j=0;j<n;j++) V[j][k] = -V[j][k];
				}
				break;
			}
			if (its==30) return FALSE;
			x=W[l];
			nm=k-1;
			y=W[nm];
			g=rv1[nm];
			h=rv1[k];
			f=((y-z)*(y+z)+(g-h)*(g+h))/(2.0*h*y);
			g=pythag(f,1.0);
			f=((x-z)*(x+z)+h*((y/(f+SIGN(g,f)))-h))/x;
			c=s=1.0;
			for (j=l;j<nm;j++) {
				i=j+1;
				g=rv1[i];
				y=W[i];
				h=s*g;
				g=c*g;
				z=pythag(f,h);
				rv1[j]=z;
				c=f/z;
				s=h/z;
				f=x*c+g*s;
				g=g*c-x*s;
				h=y*s;
				y *= c;
				for (jj=0;jj<n;jj++) {
					x=V[jj][j];
					z=V[jj][i];
					V[jj][j]=x*c+z*s;
					V[jj][i]=z*c-x*s;
				}
				z=pythag(f,h);
				W[j]=z;
				if (z) {
					z=1.0/z;
					c=f*z;
					s=h*z;
				}
				f=c*g+s*y;
				x=c*y-s*g;
				for (jj=0;jj<m;jj++) {
					y=A[jj][j];
					z=A[jj][i];
					A[jj][j]=y*c+z*s;
					A[jj][i]=z*c-y*s;
				}
			}
			rv1[l]=0.0;
			rv1[k]=f;
			W[k]=x;
		}
	}
	return TRUE;
}

char CholeskyDecomposition( double **A, int size ) {
	
	int	i, j, k;
	double	sum;
	double p[size];
	
	for ( i = 0; i < size; i++ ) {	
		for ( j = i; j < size; j++ ) {
			for ( sum=A[i][j],k=i-1;k>=0;k-- ) sum -= A[i][k]*A[j][k];
			if ( i == j ) p[i] = sqrt(sum);
			else A[j][i] = sum / p[i];
		}
	}

	for ( i = 0; i < size; i++) {
		for ( j = 0; j < i; j++) {
			A[j][i] = A[i][j];
			A[i][j] = 0.0;
	}}

	for( i = 0; i < size; i++ ) A[i][i] = p[i];
	
	return TRUE;
	
}
