!c*   findem programs  ***************************************************
!c									*
!c    programs for automatic particle finding in electron micrographs.   *
!c									*
!c									*
!c************************************************************************
!c   copyright (c) medical research council, laboratory of molecular 	*
!c    biology.    all rights reserved.					*
!c									*
!c  all files within this package, unless otherwise stated, are copyright*
!c  (c) medical research council 2002. redistribution is forbidden.	*
!c   this program was written by alan roseman at the mrc laboratory of	*
!c   molecular biology, hills road, cambridge, cb2 2qh, united kingdom.	*
!c									*
!c   mrc disclaims all warranties with regard to this software. 	*
!c									*
!c************************************************************************


! projection matching program, findem
! uses local real space correlations
! amr 4/2000
! assume downsizing and filtering already done
!  amr 8/5/00
! added flcf , amr 29/10/01

!in: image, stack of template, resolution range, threshold of template,
!3d mask file , exent to search

!out: cross-correlation map.

MODULE image_arrays
	real, dimension (:,:,:), allocatable :: map1,image,image2,map2, template,maxmap2,pmap,wmap,smap,proj
	real, dimension (:,:,:), allocatable :: search_object,search_object2
	real, dimension (:,:), allocatable :: cccmap,current_image,image_object,pvectors,maxmap,lcf
	real, dimension (:), allocatable :: array,products
END MODULE image_arrays

MODULE image_arrays2
	real,  dimension (:,:,:), allocatable :: aa,t,maskimage,m,map2
	real,  dimension (:,:,:), allocatable :: a,b,c,cnv1,cnv2,corr1,v,f,w
END MODULE image_arrays2

MODULE mrc_image
	dimension aline(32768),nxyz(3),mxyz(3),nxyzst(3),nxyz2(3)
	dimension ixyzmin(3),ixyzmax(3),out(32768)
	dimension labels(20,10),cell(6)
	complex cline(16384),cout(16384)
	character*40 infile,outfile
	character*80 title, aa
	integer nx,ny,nz,nxm1,nym1,nzm1,nxp1,nxp2
	common //nx,ny,nz,ixmin,iymin,izmin,ixmax,iymax,izmax
	equivalence (nx,nxyz), (aline,cline), (out,cout)
	equivalence (ixyzmin, ixmin), (ixyzmax, ixmax)
	data nxyzst/3*0/, cnv/57.29578/
	real dmin,dmax,dmean
	integer ntflag
END MODULE  mrc_image

program main
	use image_arrays
	use mrc_image

	real stepsize,wstepsize,wlimit,wstart
	parameter (stepsize=1)
	real scale1,scale2,scalestep
	parameter (scale1=1.0, scale2=1.15,scalestep=1.0)
	character*80 imagefile,templatefile,relaxfile,pmapname,wmapname,cccmaxmap,smapname,blank
	real threshold,sampling,real_sampling,resmin,resmax,defocus,downsize
	real diameter, rot_matrix(2,2)
	integer iteration, search_radius

	integer px,py,pz,err,x,y,z,p,np,pxp2,ival
	real w,ccc,val
	real ccc_max,w_max,p_max,x_max,y_max,radius
	character*3 num
	integer runcode2
	integer nxft,nyft,pxft,pyft
	! 	integer next_ft_size
	integer siyp1,sixp1,i,j


	write (6,*) 'findem program:'
	write (6,*) ' '
	write (6,*) ' - local real space correlation'
	write (6,*) '_______________________________'


	! 1. read in filenames and parameters
	write (6,*) 'enter filename of the image file :'
	read (5,*) imagefile

	write (6,*) 'enter filename of the search template :'
	read (5,*) templatefile

	write (6,*) 'enter a threshold for values to use from the search template: '
	read (5,*) threshold
	write (6,*) threshold

	write (6,*) 'enter sampling of the images in angstroms/pixel : '
	read (5,*)   sampling
	write (6,*) sampling

	write (6,*) 'enter a diameter of particles (a) '
	read (5,*)   diameter
	write (6,*) diameter

	write (6,*) 'enter a runcode '
	read(5,*)  runcode
	write (6,*) runcode

	write (6,*) 'enter  omega start, limit, stepsize '
	read(5,*) wstart,wlimit,wstepsize
	write(6,*) wstart,wlimit,wstepsize

	radius=diameter/2
	ntflag=-1
	100    format (a50)
	110    format (a80)
	120    format (g12.5)
	130    format (3g12.5)
	140    format (2g12.5)


! 2 initialise other variables
	blank=' '
	wmapname='wmap.mrc '//blank
	pmapname='pmap.mrc'//blank
	cccmaxmap='cccmaxmap'//num(runcode)//'.mrc'//blank
	smapname='smap.mrc '//blank

!3 main loop
	CALL imopen(1,imagefile,'old')

	CALL irdhdr(1,nxyz,mxyz,mode,dmin,dmax,dmean)
	nxp2=nx+2
	ival=nx
	nxft=next_ft_size(ival)
	ival=ny
	nyft=next_ft_size(ival)

	allocate(image(nxft,nyft,nz))
	allocate(image2(nx,ny,nz))
	image=0
	image2=5
	allocate (cccmap(nxft,nyft),maxmap2(nx,ny,1),maxmap(nxft,nyft), pmap(nxft,nyft,1))
	allocate (wmap(nxft,nyft,1) ,smap(nxft,nyft,1))
	maxmap=-1.2;pmap=0;wmap=0;smap=0


	CALL read_mrcimage(1, image2, nx,ny,nz,err)
	val = minval(image2)
	IF (val.lt.0) image2=image2-val
!	min of image must be gt 0
	image(1:nx,1:ny,1)=image2(1:nx,1:ny,1)

	CALL readmrcheader(2,templatefile,px,py,pz,err)
	IF (err.gt.0) goto 9000

	ival=px
	pxft=next_ft_size(ival)
	ival=py
	pyft=next_ft_size(ival)


	pxp2=px+2
	allocate(template(px,py,pz),pvectors(pz,px*py),proj(px,py,1))
	allocate(search_object(pxft,pyft,1),search_object2(px,py,1))

	search_object=0
	search_object2=5
	template=0

	CALL read_mrcimage(2,template,px,py,pz,err)

	! loop over template

		! loop over orientations
	DO w = wstart, wlimit, wstepsize
		PRINT*,'w=',w
		!loop over scale
		CALL make_sobj(template(:,:,p),px,py,w,search_object2,threshold,np,1.0)
		search_object(1:px,1:py,1)=search_object2(1:px,1:py,1)
		search_st = int(diameter/2/sampling)
		search_endx = nxft-search_st-1
		search_endy = nyft-search_st-1
		CALL flcf(image,nxft,nyft,nz,search_object,pxft,pyft,pz,cccmap,radius,sampling)
		DO x= search_st,search_endx,stepsize
			DO y =  search_st,search_endy,stepsize
				IF (cccmap(x,y).gt.maxmap(x,y)) then
					maxmap(x,y)=cccmap(x,y)
					pmap(x,y,1)=p
					wmap(x,y,1)=w
					smap(x,y,1)=s
				ENDIF
			ENDDO
		ENDDO
	ENDDO
	PRINT*,' write file now'

	PRINT*,'end',nx,ny,nz,nxft,nyft

	maxmap2(1:nx,1:ny,1)=maxmap(1:nx,1:ny)

	CALL imopen(2,cccmaxmap,'new')
	CALL itrhdr(2,1)
	CALL iwrhdr(2,title,ntflag,dmin,dmax,dmean)

	CALL write_mrcimage2(2,maxmap2,nx,ny,nz,err,sampling)
	CALL imclose(9)

	!	CALL    copyaheader(imagefile,pmapname,3)
	!	CALL    write_mrcimage(3,pmap,nx,ny,nz,err)

	!	CALL    copyaheader(imagefile,wmapname,3)
	!	CALL    write_mrcimage(3,wmap,nx,ny,nz,err)

	!	CALL    copyaheader(imagefile,smapname,3)
	!	CALL    write_mrcimage(3,smap,nx,ny,nz,err)

	! normal exit
	close(1)
	PRINT*,'program finished o.k.'

	PRINT*,'correlation map output to file: ',cccmaxmap
	goto 9998

	! errors
	9000   continue
	PRINT*, 'image read error.'
	9998   continue

END program

!c ************************************************
! END MAIN PROGRAM
! END MAIN PROGRAM
! END MAIN PROGRAM
! END MAIN PROGRAM
! END MAIN PROGRAM
! END MAIN PROGRAM
! END MAIN PROGRAM
! END MAIN PROGRAM
! END MAIN PROGRAM
! END MAIN PROGRAM
!c ************************************************

SUBROUTINE make_sobj(projection,px,py,w,search_object,threshold,np,s)
	integer px,py,np
	real projection(px,py,1),search_object(px,py,1)
	real w,threshold,s

	search_object =projection

	CALL rot_image(search_object,w,px,py,s)

	return
END SUBROUTINE make_sobj

!c ************************************************

SUBROUTINE rot_image(image,w,nx,ny,s)
	real image(nx,ny,1),new_image(nx,ny,1)
	real coords(2),new_coords(2),s
	real x,y,val,w,originx,originy,rot_matrix(2,2)
	integer nx,ny,ix,iy

	equivalence (coords(1),x)
	equivalence (coords(2),y)


	originx=int(nx/2)+1
	originy=int(ny/2)+1

	CALL matrix(w,rot_matrix)

	new_image=0
	do ix=1,nx
		do iy=1,ny
			x=ix-originx
			y=iy-originy
			val = image(ix,iy,1)
			new_coords=(matmul(rot_matrix,coords)*s)+originx
			CALL interpo2d(new_image,new_coords(1),new_coords(2),nx,ny,val)
		enddo
	enddo
	image=new_image

	return
END SUBROUTINE rot_image

!c ************************************************

SUBROUTINE matrix(w,rot_matrix)
	real w
	real r
	real rot_matrix(2,2)

	CALL rad(w,r)

	rot_matrix(1,1)=  cos(r)
	rot_matrix(1,2)=  sin(r)
	rot_matrix(2,1)= -sin(r)
	rot_matrix(2,2)=  cos(r)

	return
END SUBROUTINE matrix

!c ************************************************

SUBROUTINE rad(deg,r)
	real deg,pi,r
	parameter (pi=3.1415927)

	r = deg/180.*pi

	return
END SUBROUTINE rad

!c ************************************************

SUBROUTINE interpo2d(map,sx,sy,nx,ny,val)
!c 	bilinear ip of coords
	real map(nx,ny,1)
	real sx,sy,sz,val,sampling,tx
	integer x,y,z,ix,iy,iz,nx,ny
	real wx,wy,wz,nwx,nwy,nwz
	integer sixp1,siyp1

	ix = int(sx)
	iy = int(sy)

	wx = sx - float(ix)
	wy = sy - float(iy)

	nwx = 1.0-wx
	nwy = 1.0-wy

!	wraparound , should not be more than one 'cell' away.
	IF (ix.le.0)	ix=ix+nx
	IF (ix.gt.nx)	ix=ix-nx
	IF (iy.le.0)	iy=iy+ny
	IF (iy.gt.ny)	iy=iy-ny

	sixp1 = ix+1
	siyp1  =iy+1

	IF (sixp1.gt.nx) sixp1=sixp1-nx
	IF (siyp1.gt.ny) siyp1=siyp1-nx

!	PRINT*,sx,sy,ix,iy

	map(ix,iy,1)       = map(ix,iy,1)       + nwx * nwy * val
	map(ix,siyp1,1)    = map(ix,siyp1,1)    + nwx *  wy * val
	map(sixp1,iy,1)    = map(sixp1,iy,1)    +  wx * nwy * val
	map(sixp1,siyp1,1) = map(sixp1,siyp1,1) +  wx *  wy * val

	777     continue
	return
END SUBROUTINE interpo2d


!c ************************************************

function num(number)
	character(len=3) num

	integer number,order
	real fnum,a
	integer hun,ten,units
	character*1 digit(0:9)

	digit(0)='0'
	digit(1)='1'
	digit(2)='2'
	digit(3)='3'
	digit(4)='4'
	digit(5)='5'
	digit(6)='6'
	digit(7)='7'
	digit(8)='8'
	digit(9)='9'

	fnum=float(number)
	fnum=mod(fnum,1000.)
	hun=int(fnum/100.)
	a=mod(fnum,100.)
	ten=int(a/10.)
	units=mod(fnum,10.)
!c	print *,hun,ten,units

	num=digit(hun)//digit(ten)//digit(units)
	return
END function

!fast local correlation function.
! am roseman 2001

SUBROUTINE flcf(map,nx,ny,nz,template,tx,ty,tz,lcf,radius,sampling)
	!use mrc_image
	use  image_arrays2
	integer nx,ny,nz,tx,ty,tz
	real sampling,lp,hp
	logical odd
	character*40 templatefile
	integer txyz(3),txp1,tym1,tzm1,txm1
	integer ixyz(3)
	integer nm,ni,x,y
	data ifor/0/,ibak/1/,zero/0.0/
	real r,val,v2,v1
	integer s(3)
	real array(1000000)
	real, dimension (:,:,:), allocatable :: lcf2
	real map(0:nx-1,0:ny-1,0:nz-1),template(0:tx-1,0:ty-1,0:tz-1),lcf(0:nx-1,0:ny-1,0:nz-1)
	allocate (aa(0:nx+1,0:ny-1,0:nz-1),t(0:nx+1,0:ny-1,0:nz-1),lcf2(0:nx+1,0:ny-1,0:nz-1))
	allocate (a(0:nx+1,0:ny-1,0:nz-1),b(0:nx+1,0:ny-1,0:nz-1),c(0:nx+1,0:ny-1,0:nz-1),w(0:nx-1,0:ny-1,0:nz-1))
	allocate (cnv1(0:nx+1,0:ny-1,0:nz-1),cnv2(0:nx+1,0:ny-1,0:nz-1),corr1(0:nx+1,0:ny-1,0:nz-1))
	allocate (m(0:nx+1,0:ny-1,0:nz-1),v(0:nx+1,0:ny-1,0:nz-1),f(0:nx+1,0:ny-1,0:nz-1),map2(0:nx+1,0:ny-1,0:nz-1))
	allocate (maskimage(0:tx-1,0:ty-1,0:tz-1))

	1	format(a45)
	!	write(*,1) 'fast local correlation program'
	!	write(*,1) '------------------------------'

	nxp2=nx+2
	nxp1=nx+1
	nym1=ny-1
	nzm1=nz-1
	nxm1=nx-1

	s1=size(map,1)

	mapx=nx
	mapy=ny
	mapz=nz

	ni=nx*ny

	txm1=tx-1
	txp1=tx+1
	tym1=ty-1
	tzm1=tz-1

	ixyz=nxyz

! 4. calculate mask
	r=radius/sampling

	!masks template and returns nm=# of points inside mask
	CALL mask(template,tx,r,nm)

	CALL msd_set(template,tx,ty,nm,val,err)

	CALL mask(template,tx,r,nm)

	val=0
	CALL pad2(template,tx,ty,t,mapx,mapy,val)

	maskimage=1
	CALL mask(maskimage,tx,r,nm)

	val=0
	CALL pad2(maskimage,tx,ty,m,mapx,mapy,val)

	val=0
	CALL pad(map,mapx,mapy,map2,mapx+2,mapy,val)

! 5. do ffts
	!aa = image squared
	aa = map2 * map2

	!map2= FT(image)
	CALL todfft(map2,mapx,mapy,ifor) 

	!aa = FT(image squared)
	CALL todfft(aa,mapx,mapy,ifor) 

	!t = FT(template)
	CALL todfft(t,mapx,mapy,ifor)

	!m = FT(mask)
	CALL todfft(m,mapx,mapy,ifor)

	!cnv1 = convolution(image,mask)
	CALL convolution(map2,m,cnv1,mapx,mapy)

	!cnv2 = convolution(image squared,mask)
	CALL convolution(aa,m,cnv2,mapx,mapy)

	!corr1 = crosscorrelation(template,image)
	CALL correlation(t,map2,corr1,mapx,mapy,hp,lp,sampling)

! 8. calculate lcf map.
	v=((nm*cnv2)-(cnv1*cnv1))/(nm*nm)

	WHERE (v.gt.0)
		v=sqrt(v)
	ELSEWHERE
		v=0
	ENDWHERE

	f=corr1/nm
	lcf2=0

	WHERE (v.ne.0)
		lcf = f/v
	ENDWHERE

! 9. write flcf map.

	deallocate (aa,t,a,b,c,w,cnv1,cnv2,corr1,m,v,f,map2,maskimage)
	RETURN

	997   stop 'error on file read.'
END SUBROUTINE flcf

!c***************************************************************************

SUBROUTINE read_mrcimage(stream,map,x,y,z,err)
	use mrc_image
!	use  image_arrays
	integer  x,y,z,err
	integer  stream, ix,iy,iz,xm1
	real, dimension (0:x-1,0:y-1,0:z-1) :: map
	integer s(3),s1

	print*,'xyz ',x,y,z

	s1=size(map,1)
	s1=size(map,2)
	s1=size(map,3)

!	read in file

	do 350 iz = 0,z-1
	do 350 iy = 0,y-1
	CALL irdlin(stream,aline,*998)
	do 300 ix = 0,x-1
!	print*,ix
	map(ix,iy,iz) = aline(ix+1)
	300 continue
	! map(x+0,iy,iz)=0
	! map(x+1,iy,iz)=0
!	print*,ix,iy,iz
	350 continue

	return
	998   stop 'error on file read1.'
END SUBROUTINE

!c***************************************************************************

SUBROUTINE write_mrcimage(stream,map,x,y,z,err)
	use  mrc_image
	real val,sampling
	real*8 doublemean
	integer x,y,z,err,stream
	real map(0:x+1,0:y-1,0:0)
	sampling=1

	nx=x
	ny=y
	nz=1

	nxm1=nx-1
	nym1=ny-1
	nzm1=nz-1

	print*,'write_mrcimage'

	print*,nx,ny,nz
	!     write file

	dmin =  1.e10
	dmax = -1.e10
	doublmean = 0.0

	do 450 iz = 0,nzm1
		do 450 iy = 0,nym1
			do 400 ix = 0,nxm1
				val = map(ix,iy,iz)
				aline(ix+1) = val
				doublmean = doublmean + val
				if (val .lt. dmin) dmin = val
				if (val .gt. dmax) dmax = val
			400 continue
		CALL iwrlin(stream,aline)
		450 continue
	dmean = doublmean/(nx*ny*nz)

	cell(1) = sampling *nxm1
	cell(2) = sampling *nym1
	cell(3) = sampling *nzm1
	cell(4) = 90
	cell(5) = 90
	cell(6) = 90

	CALL ialcel(stream,cell)
	CALL iwrhdr(stream,title,-1,dmin,dmax,dmean)
	CALL imclose(stream)

	return
	999   stop 'error on file write.'
END SUBROUTINE

!c***************************************************************************

SUBROUTINE write_mrcimage2(stream,map,x,y,z,err,sampling)
	use  mrc_image
	integer x,y,z,err,stream
	real map(0:x-1,0:y-1,0:0)
	real val
	real sampling
	real*8 doublemean

	nx=x
	ny=y
	nz=1

	nxm1=x-1
	nym1=y-1
	nzm1=z-1

	!     write file

	dmin =  1.e10
	dmax = -1.e10
	doublmean = 0.0

	do 450 iz = 0,nzm1
		do 450 iy = 0,nym1
			do 400 ix = 0,nxm1
				val = map(ix,iy,iz)
				aline(ix+1) = val
				doublemean = doublemean + val
				if (val .lt. dmin) dmin = val
				if (val .gt. dmax) dmax = val
			400	continue
		CALL iwrlin(stream,aline)
	450   continue

	dmean = doublemean/(nx*ny*nz)

	CALL ialcel(stream,cell)
	CALL iwrhdr(stream,title,1,dmin,dmax,dmean)
	CALL imclose(stream)

	return
	999   stop 'error on file write.'
END SUBROUTINE

!c***************************************************************************

real function radiusxy(x,y,xc,yc)

	integer x,y,xc,yc,xx,yy
	real r2

	xx=x-xc
	yy=y-yc

	r2=float(xx**2 +  yy**2)

	radiusxy=sqrt(r2)

	return
END function

!c***************************************************************************

SUBROUTINE mask(template,nx,radius,msum)
	!	use image_arrays
	integer nx,ty,tx
	dimension template(0:nx-1,0:nx-1,0:0)
	real x,y,radius
	integer msum,i,j,cx,cy
	real radiusxy

	tx=size(template,1)
	ty=size(template,2)

	cx=int(float(tx)/2.)
	cy=int(float(ty)/2.)

	maskimage = 0
	msum=0

	do i=0,nx-1
		do j=0,nx-1
!			PRINT*,i,j
			if (radiusxy(i,j,cx,cy).gt.radius) then
				template(i,j,0) = 0.0
			else
				msum=msum+1
			END if
		enddo
	enddo

	RETURN
END SUBROUTINE

!c***************************************************************************

SUBROUTINE pad(a,sx,sy,b,nx2,ny2,val)
	integer sx,sy,nx2,ny2
	dimension a(0:sx-1,0:sy-1,0:0),b(0:nx2-1,0:ny2-1,0:0)
	integer wrap
!pads a into b, and puts the origin at 0,0
!	use image_arrays
	integer cx,cy,bx,by,i,j
	real val

	cx=int(sx/2)
	cy=int(sy/2)

	b=val

	DO i=0,sy-1
		DO j=0,sx-1
			bx=j
			by=i
			b(bx,by,0)=a(j,i,0)
!			PRINT*,i,j,a(j,i,0),bx,by,b(bx,by,0)
		ENDDO
	ENDDO
END SUBROUTINE pad

!c***************************************************************************

SUBROUTINE pad2(a,sx,sy,b,nx2,ny2,val)
	integer sx,sy,nx2,ny2
	dimension a(0:sx-1,0:sy-1,0:0),b(0:nx2+1,0:ny2-1,0:0)
	integer wrap
!pads a into b, and puts the origin at 0,0
!	use image_arrays
	integer cx,cy,bx,by
	integer i,j
	real val

	cx=int(sx/2)
	cy=int(sy/2)

	b=val

	DO i=0,sy-1
		DO j=0,sx-1
			bx=wrap(j-cx,nx2)
			by=wrap(i-cy,ny2)
			b(bx,by,0)=a(j,i,0)
!			PRINT*,i,j,a(j,i,0),bx,by,b(bx,by,0)
		ENDDO
	ENDDO
END SUBROUTINE pad2

!c***************************************************************************

integer function wrap(a,b)
	integer a,b
	wrap = a
	IF (a.lt.0) wrap = b+a
END FUNCTION wrap

!c***************************************************************************

SUBROUTINE convolution(a,b,c,nx2,ny2)
	!use image_arrays
	integer nx2,ny2
	real a(0:nx2+1,0:ny2-1,0:0),b(0:nx2+1,0:ny2-1,0:0),c(0:nx2+1,0:ny2-1,0:0)
	real n
	data ifor/0/,ibak/1/,zero/0.0/
	c=0
	DO j=0,ny2-1
		DO i=0,nx2,2
			c(i,j,0)=a(i,j,0)*b(i,j,0) - a(i+1,j,0)*b(i+1,j,0)
			c(i+1,j,0)=a(i,j,0)*b(i+1,j,0) + a(i+1,j,0)*b(i,j,0)
!			PRINT*,i,j,nx2,ny2
		ENDDO
	ENDDO
	CALL todfft(c,nx2,ny2,ibak)
	n=nx2*ny2
	n=sqrt(n)
	c=c*n
END SUBROUTINE convolution

!c***************************************************************************

SUBROUTINE correlation(a,b,c,nx,ny,hp,lp,sampling)
!	use image_arrays
	integer nx,ny
	real a(0:nx+1,0:ny-1,0:0),b(0:nx+1,0:ny-1,0:0),c(0:nx+1,0:ny-1,0:0)

	real r1,r2,hp,lp,sampling,n
	real*8 dd
	data ifor/0/,ibak/1/,zero/0.0/

	r1=hp/sampling
	r2=lp/sampling

	c=0
	DO j=0,ny-1
		DO i=0,nx+1,2
			!r=radft(i,j,ny)
			!if ((r.gt.r1).and.(r.lt.r2)) then
			c(i,j,0)=a(i,j,0)*b(i,j,0) + a(i+1,j,0)*b(i+1,j,0)
			c(i+1,j,0)=a(i,j,0)*b(i+1,j,0) - a(i+1,j,0)*b(i,j,0)
			!endif
		ENDDO
	ENDDO
	dd=(nx*ny)

	CALL todfft(c,nx,ny,ibak)
	n=nx*ny
	n=sqrt(n)

	c=c*n
END SUBROUTINE correlation

!c***************************************************************************

real function radft(a,b,ny)
	integer a,b
	real r

	a=a/2
	b=b-(ny/2)
	r=(a*a + b*b)

	radft = sqrt(r)


END FUNCTION radft

!c***************************************************************************

SUBROUTINE msd_set(map,nx,ny,n,val,err)
	real map(0:nx-1,0:ny-1,0:0)

	integer z,err,nxp1,nym1,nx,ny,nxm1
	real*8 mean,sd,lsum,sum_sqs,sq
	real val,th
	integer n

	! treats as if all vals not in the masked n, are zero.
	nxp1=nx+1
	nym1=ny-1
	nxm1=nx-1

	err=0

	lsum = sum(map(0:nxm1,0:nym1,0))

	mean=lsum/n

	sum_sqs=sum(map(0:nxm1,0:nym1,0)*map(0:nxm1,0:nym1,0))

	sq = ((n*sum_sqs-lsum*lsum)/(n*n))

	if (sq.lt.0) stop 'sd lt zero in msd set.'

	th=0.00001
	if (sq.gt.th) then
		sd = sqrt(sq)
		map=(map-mean)/sd
		val= -mean/sd
		err=0
	elseif (sq.le.0) then
		err=1
		print*,'le0'
	elseif (sq.le.th) then
		map=(map-mean)
		eval= -mean/sd
		err=0
	endif

	return
END SUBROUTINE msd_set


!c***************************************************************************

integer function next_ft_size(x)
	logical ftsize
	integer x
	if (int(x/2).ne.(x/2)) x=x+1
	do while (.not.ftsize(x))
		x=x+2
	enddo
	next_ft_size=x
	return
END function next_ft_size

!c***************************************************************************

logical function ftsize(x)
	integer x,n,a
	real b
	real primes(8)

	primes=(/2,3,5,7,11,13,17,19/)

	ftsize = .false.

	a=x
	do n=1,8
		100 continue
		b=float(a)/primes(n)
		if (a.eq.0) stop 'error in primes'
		if (b.eq.int(b)) then
			a=int(b)
			goto 100
		endif
	enddo

	if (a.eq.1) then
		ftsize=.true.
	else
		ftsize=.false.
	endif
	return
END function ftsize

!c***************************************************************************

SUBROUTINE readmrcheader(stream,filename,nx,ny,nz,err)
	integer stream,err
	character*80 filename

	! mrc file stuff
	integer nx,ny,nz
	dimension aline(8192),nxyz(3),mxyz(3),nxyzst(3)
	dimension ixyzmin(3),ixyzmax(3),out(8192)
	dimension labels(20,10),cell(6)
	complex cline(4096),cout(4096)
	character*80 title
	equivalence (aline,cline), (out,cout)
	equivalence (ixyzmin, ixmin), (ixyzmax, ixmax)
	data nxyzst/3*0/, cnv/57.29578/

	CALL imopen(stream,filename,'ro')
	CALL irdhdr(stream,nxyz,mxyz,mode,dmin,dmax,dmean)
	if (mode.lt.0 .or.mode.gt.2) err=1

	nx=nxyz(1)
	ny=nxyz(2)
	nz=nxyz(3)

	return
END SUBROUTINE readmrcheader


