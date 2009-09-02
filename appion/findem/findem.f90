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
	real, dimension (:,:,:), allocatable :: map1,image,image2,map2, template,maxmap2,angmap,proj
	real, dimension (:,:,:), allocatable :: search_object,search_object2
	real, dimension (:,:), allocatable :: cccmap,normconvmap,current_image,image_object,pvectors,maxmap,lcf
	real, dimension (:), allocatable :: array,products
END MODULE image_arrays

MODULE image_arrays2
	real,  dimension (:,:,:), allocatable :: imsq,tmplpad,tmplmask,tmplmaskpad,impad
	real,  dimension (:,:,:), allocatable :: a,b,c,cnv1,cnv2,corr1,v,f,w
END MODULE image_arrays2

MODULE mrc_image
	dimension aline(32768),nxyz(3),mxyz(3),nxyzst(3),nxyz2(3)
	dimension ixyzmin(3),ixyzmax(3),out(32768)
	dimension labels(20,10),cell(6)
	complex cline(16384),cout(16384)
	character*40 infile,outfile
	character*80 title, imsq
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

	real stepsize,angstepsize,anglimit,angstart
	parameter (stepsize=1)
	real scale1,scale2,scalestep
	parameter (scale1=1.0, scale2=1.15,scalestep=1.0)
	character*80 imagefile,templatefile,relaxfile,angmapname,cccmaxmap,blank
	real sampling,real_sampling,resmin,resmax,defocus,downsize,thresh
	real diameter, rot_matrix(2,2)
	integer iteration, search_radius, numrot

	integer px,py,pz,err,x,y,z,p,np,ival
	real ang,ccc,min1,max1
	real ccc_max,w_max,p_max,x_max,y_max,radius
	character*3 num
	integer runcode,pixrad,bord
	integer nxft,nyft,pxft,pyft,nxyft
! 	integer next_ft_size
	real avg,stdev

	write (6,*) 'X Fast FindEM Program:'
	!write (6,*) ' - local real space correlation'

	! 1. read in filenames and parameters
	write (6,*) '>>> enter filename of the image file :'
	read (5,*) imagefile
	!write (6,*) imagefile
	PRINT*,"X ... image:    ",imagefile

	write (6,*) '>>> enter filename of the search template :'
	read (5,*) templatefile
	PRINT*,"X ... template: ",templatefile
	!write (6,*) templatefile

	write (6,*) '>>> (for backward compat) enter any random float 0,1 :'
	read (5,*) thresh

	write (6,*) '>>> enter pixelsize of the images in angstroms/pixel : '
	read (5,*)   sampling
	!write (6,*) sampling
	PRINT*,"X ... A/pix:    ",sampling

	write (6,*) '>>> enter a diameter of particles (a) '
	read (5,*)   diameter
	!write (6,*) diameter
	PRINT*,"X ... part diam:",diameter

	write (6,*) '>>> enter a runcode '
	read (5,*)  runcode
	!write (6,*) runcode
	PRINT*,"X ... runcode:  ",runcode

	write (6,*) '>>> enter angle start, limit, stepsize '
	read (5,*) angstart,anglimit,angstepsize
	!write(6,*) angstart,anglimit,angstepsize
	PRINT*,"X ... angles:   ",angstart,anglimit,angstepsize

	write (6,*) '>>> enter border size '
	read (5,*), bord
	PRINT*,"X ... border:   ",bord

	radius=diameter/2

! 2 initialise other variables
	    blank='                                                 '            
            angmapname='angmap.mrc '//blank
            cccmaxmap='cccmaxmap'//num(runcode)//'.mrc'//blank

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
	allocate (cccmap(nxft,nyft),maxmap2(nx,ny,1),maxmap(nxft,nyft),normconvmap(nxft,nyft))
	allocate (angmap(nxft,nyft,1))
	maxmap=-1.2;angmap=0

	CALL read_mrcimage(1, image2, nx,ny,nz,err)

	!image2 = (image2-6990.0)/316.0+8.0
	!image = normRange(image)+0.000001
	min1 = minval(image2)
	max1 = maxval(image2)
	image2 = 5.0*(image2 - min1)/(max1 - min1) + 0.000001
	!PRINT*,"IMAGE"
	!CALL imageinfo(image2,nx,ny)
	!PRINT*,""
	!IF (val.lt.0) image2=image2-val
!	min of image must be gt 0
	image(1:nx,1:ny,1)=image2(1:nx,1:ny,1)

	CALL readmrcheader(2,templatefile,px,py,pz,err)

	ival=px
	pxft=next_ft_size(ival)
	ival=py
	pyft=next_ft_size(ival)

	allocate(template(px,py,pz),pvectors(pz,px*py),proj(px,py,1))
	allocate(search_object(pxft,pyft,1),search_object2(px,py,1))

	search_object=0
	search_object2=5
	template=0

	CALL read_mrcimage(2,template,px,py,pz,err)

	! SANS BORDER
	search_st = 1
        search_endx = nxft-search_st+1
        search_endy = nyft-search_st+1
	! WITH BORDER
	!search_st = int(diameter/2.0/sampling)
	!search_endx = nxft-search_st-1
	!search_endy = nyft-search_st-1


	CALL normconvfunc(image,nxft,nyft,pxft,pyft,normconvmap,radius,sampling)

	numrot = (anglimit-0.1-angstart)/angstepsize

	PRINT*,"X DOING",numrot,"ROTATIONS..."
	! LOOP OVER ANGLES
	DO ang = angstart, anglimit-0.1, angstepsize
		!PRINT*,'angle=',ang

		! GET ROTATED TEMPLATE
		CALL make_sobj(template(:,:,1),px,py,ang,search_object2,np,1.0)
		search_object(1:px,1:py,1) = search_object2(1:px,1:py,1)

		!CALL flcf(image,nxft,nyft,search_object,pxft,pyft,cccmap,radius,sampling)
		!PRINT*,"CCMAP"
		CALL getccmap(image,nxft,nyft,search_object,pxft,pyft,cccmap,radius,sampling)
		!CALL imageinfo(cccmap,nxft,nyft)
		! GET MAXIMUM VALUES
		DO x= search_st,search_endx,stepsize
			DO y =  search_st, search_endy, stepsize
				IF (cccmap(x,y) .gt. maxmap(x,y)) then
					maxmap(x,y)=cccmap(x,y)
					!angmap(x,y,1)=ang
				ENDIF
			ENDDO
		ENDDO
	ENDDO
	PRINT*,"X DONE"

	!PRINT*,"NORMCONVMAP"
	!CALL imageinfo(normconvmap,nxft,nyft)
	!PRINT*,normconvmap(511,511),normconvmap(512,512),normconvmap(513,513)

	!PRINT*,"CCMAXMAP"
	!CALL imageinfo(maxmap,nxft,nyft)
	!PRINT*,maxmap(511,511),maxmap(512,512),maxmap(513,513)

	WHERE (normconvmap .ne. 0)
		maxmap = maxmap / normconvmap
	ENDWHERE

	PRINT*,"X NORMCCMAXMAP info:"
	CALL imageinfo(maxmap,nxft,nyft)
	!PRINT*,maxmap(511,511),maxmap(512,512),maxmap(513,513)

	!pixrad = int(diameter/2.0/sampling)+1
	!pixrad = px/2
	!CALL removeborder(maxmap,nx,ny,pixrad)
	CALL removeborder(maxmap,nx,ny,bord)

	!PRINT*,""
	!PRINT*,'writing file now...  ',cccmaxmap
	maxmap2(1:nx,1:ny,1) = maxmap(1:nx,1:ny)
	CALL imopen(2,cccmaxmap,'new')
	CALL itrhdr(2,1)
	CALL iwrhdr(2,title,ntflag,dmin,dmax,dmean)
	CALL write_mrcimage2(2,maxmap2,nx,ny,nz,err,sampling)
	CALL imclose(9)
	!close(1)

	!PRINT*,'program finished o.k.'
	PRINT*,'correlation map output to file: ',cccmaxmap

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

SUBROUTINE removeborder(image,nx,ny,pixrad)
	integer nx,ny,pixrad
	real image(nx,ny)
	real black1
	integer ix,iy,ix2,iy2

	black1 = 0.0

	!PRINT*,"filling border by",pixrad,"pixels"

	DO ix=1,pixrad,1
		ix2 = nx - ix + 1
		DO iy=1,ny,1
			image(ix,iy) = black1
			image(ix2,iy) = black1
		ENDDO
	ENDDO
	DO iy=1,pixrad,1
		iy2 = ny - iy + 1
		DO ix=1,nx,1
			image(ix,iy) = black1
			image(ix,iy2) = black1
		ENDDO
	ENDDO

	RETURN
END SUBROUTINE removeborder

SUBROUTINE imageinfo(image,nx,ny)
	integer nx,ny
	real image(nx,ny,1)
	real avg,stdev,n

	n = nx*ny
!	PRINT*,"IMAGE INFO:"
!	PRINT*,'  size= ',nx,' x ',ny
!	PRINT*,'  sum=  ',sum(image)
	avg = sum(image)/n
	stdev = sqrt((n*sum(image*image)-sum(image)**2)/(n*(n-1)))
	PRINT*,'X ... avg=  ',avg,' +- ',stdev
	PRINT*,'X ... range=',minval(image),' <> ',maxval(image)

	return
END SUBROUTINE imageinfo

!c ************************************************

SUBROUTINE make_sobj(projection,px,py,w,search_object,np,s)
	integer px,py,np
	real projection(px,py,1),search_object(px,py,1)
	real w,s

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

SUBROUTINE normconvfunc(image,nx,ny,tx,ty,normconvmap,radius,sampling)
	!use mrc_image
	use  image_arrays2
	integer nx,ny,tx,ty
	real sampling
	integer nmask
	data ifor/0/,ibak/1/,zero/0.0/
	real pixrad,val
	real image(0:nx-1,0:ny-1,0:0),normconvmap(0:nx-1,0:ny-1,0:0)
	allocate (imsq(0:nx+1,0:ny-1,0:0))
	allocate (cnv1(0:nx+1,0:ny-1,0:0),cnv2(0:nx+1,0:ny-1,0:0))
	allocate (tmplmaskpad(0:nx+1,0:ny-1,0:0),impad(0:nx+1,0:ny-1,0:0))
	allocate (tmplmask(0:tx-1,0:ty-1,0:0))

! 4. calculate mask
	pixrad=radius/sampling

	! CREATE REGULAR MASK
	tmplmask=1
	CALL mask(tmplmask,tx,pixrad,nmask)
	!PRINT*,"nmask=",nmask

	val=0
	!PRINT*,"IMAGE"
	!CALL imageinfo(image,nx,ny)
	CALL pad(image,nx,ny,impad,nx+2,ny,val)

	val=0
	!PRINT*,"MASK"
	!CALL imageinfo(tmplmask,tx,ty)
	CALL pad2(tmplmask,tx,ty,tmplmaskpad,nx,ny,val)

! 5. do ffts
	!imsq = image squared
	imsq = impad * impad
	!PRINT*,"IMAGESQ"
	!CALL imageinfo(imsq,nx,ny)

	!impad= FT(image)
	CALL todfft(impad,nx,ny,ifor) 

	!imsq = FT(image squared)
	CALL todfft(imsq,nx,ny,ifor) 

	!tmplmaskpad = FT(mask)
	CALL todfft(tmplmaskpad,nx,ny,ifor)

	!cnv1 = convolution(image,mask)
	CALL convolutionfft(impad,tmplmaskpad,cnv1,nx,ny)
	!PRINT*,"CNV1"
	!CALL imageinfo(cnv1,nx,ny)
	!PRINT*,cnv1(499,499,0),cnv1(500,500,0),cnv1(501,501,0)

	!cnv2 = convolution(image squared,mask)
	CALL convolutionfft(imsq,tmplmaskpad,cnv2,nx,ny)
	!PRINT*,"CNV2"
	!CALL imageinfo(cnv2,nx,ny)
	!PRINT*,cnv2(499,499,0),cnv2(500,500,0),cnv2(501,501,0)

! 8. calculate lcf map.
	!PRINT*,"nmask=",nmask
	normconvmap=((nmask*cnv2)-(cnv1*cnv1))/(nmask*nmask)
	!PRINT*,"normconvfunc**2"
	!CALL imageinfo(normconvmap,nx,ny)
	!PRINT*,normconvmap(499,499,0),normconvmap(500,500,0),normconvmap(501,501,0)

	WHERE (normconvmap.gt.0)
		normconvmap=sqrt(normconvmap)
	ELSEWHERE
		normconvmap=0
	ENDWHERE
	!PRINT*,"NORMCONV"
	!CALL imageinfo(normconvmap,nx,ny)
	!PRINT*,normconvmap(499,499,0),normconvmap(500,500,0),normconvmap(501,501,0)

! 9. write flcf map.
	
	deallocate (imsq,cnv1,cnv2,tmplmaskpad,impad,tmplmask)
! NEIL ENTERED STOP
!	STOP

	RETURN

END SUBROUTINE normconvfunc

!fast local correlation function.
! am roseman 2001

SUBROUTINE getccmap(image,nx,ny,template,tx,ty,ccmap,radius,sampling)
	!use mrc_image
	use  image_arrays2
	integer nx,ny,tx,ty
	real sampling
	integer nmask
	data ifor/0/,ibak/1/,zero/0.0/
	real pixrad,val
	real image(0:nx-1,0:ny-1,0:0),template(0:tx-1,0:ty-1,0:0),ccmap(0:nx-1,0:ny-1,0:0)
	allocate (tmplpad(0:nx+1,0:ny-1,0:0))
	allocate (corr1(0:nx+1,0:ny-1,0:0))
	allocate (impad(0:nx+1,0:ny-1,0:0))

! 4. calculate mask
	pixrad=radius/sampling

	!masks template and returns nm=# of points inside mask
	CALL mask(template,tx,pixrad,nmask)
	! NORMALIZE
	CALL normStdev(template,tx,ty,nmask,val,err)
	! REMASK
	CALL mask(template,tx,pixrad,nmask)

	val=0
	CALL pad2(template,tx,ty,tmplpad,nx,ny,val)

	val=0
	!PRINT*,"IMAGE"
	!CALL imageinfo(image,nx,ny)
	CALL pad(image,nx,ny,impad,nx+2,ny,val)

! 5. do ffts

	!map2= FT(image)
	CALL todfft(impad,nx,ny,ifor) 

	!t = FT(template)
	CALL todfft(tmplpad,nx,ny,ifor)

	!corr1 = crosscorrelation(template,image)
	CALL correlationfft(tmplpad,impad,corr1,nx,ny)
	!corr1 = 1.0

	corr1=corr1/nmask

	!PRINT*,"CORR"
	!CALL imageinfo(corr1,nx,ny)

	ccmap = corr1

! 9. write flcf map.
	
	deallocate (tmplpad,corr1,impad)
! NEIL ENTERED STOP
!	STOP

	RETURN

END SUBROUTINE getccmap


!fast local correlation function.
! am roseman 2001

SUBROUTINE flcf(image,nx,ny,template,tx,ty,lcf,radius,sampling)
	!use mrc_image
	use  image_arrays2
	integer nx,ny,tx,ty
	real sampling
	integer nmask
	data ifor/0/,ibak/1/,zero/0.0/
	real pixrad,val
	real image(0:nx-1,0:ny-1,0:0),template(0:tx-1,0:ty-1,0:0),lcf(0:nx-1,0:ny-1,0:0)
	allocate (imsq(0:nx+1,0:ny-1,0:0),tmplpad(0:nx+1,0:ny-1,0:0))
	allocate (cnv1(0:nx+1,0:ny-1,0:0),cnv2(0:nx+1,0:ny-1,0:0),corr1(0:nx+1,0:ny-1,0:0))
	allocate (tmplmaskpad(0:nx+1,0:ny-1,0:0),v(0:nx+1,0:ny-1,0:0),impad(0:nx+1,0:ny-1,0:0))
	allocate (tmplmask(0:tx-1,0:ty-1,0:0))

! 4. calculate mask
	pixrad=radius/sampling

	!masks template and returns nm=# of points inside mask
	CALL mask(template,tx,pixrad,nmask)
	! NORMALIZE
	CALL normStdev(template,tx,ty,nmask,val,err)
	! REMASK
	CALL mask(template,tx,pixrad,nmask)

	val=0
	CALL pad2(template,tx,ty,tmplpad,nx,ny,val)

	! CREATE REGULAR MASK
	tmplmask=1
	CALL mask(tmplmask,tx,pixrad,nmask)
	PRINT*,"nmask=",nmask

	val=0
	PRINT*,"IMAGE"
	CALL imageinfo(image,nx,ny)
	CALL pad(image,nx,ny,impad,nx+2,ny,val)

	val=0
	PRINT*,"MASK"
	CALL imageinfo(tmplmask,tx,ty)
	CALL pad2(tmplmask,tx,ty,tmplmaskpad,nx,ny,val)

! 5. do ffts
	!imsq = image squared
	imsq = impad * impad
	PRINT*,"IMAGESQ"
	CALL imageinfo(imsq,nx,ny)

	!map2= FT(image)
	CALL todfft(impad,nx,ny,ifor) 

	!imsq = FT(image squared)
	CALL todfft(imsq,nx,ny,ifor) 

	!t = FT(template)
	CALL todfft(tmplpad,nx,ny,ifor)

	!m = FT(mask)
	CALL todfft(tmplmaskpad,nx,ny,ifor)

	!cnv1 = convolution(image,mask)
	CALL convolutionfft(impad,tmplmaskpad,cnv1,nx,ny)
	PRINT*,"CNV1"
	CALL imageinfo(cnv1,nx,ny)
	PRINT*,cnv1(499,499,0),cnv1(500,500,0),cnv1(501,501,0)

	!cnv2 = convolution(image squared,mask)
	CALL convolutionfft(imsq,tmplmaskpad,cnv2,nx,ny)
	PRINT*,"CNV2"
	CALL imageinfo(cnv2,nx,ny)
	PRINT*,cnv2(499,499,0),cnv2(500,500,0),cnv2(501,501,0)

	!corr1 = crosscorrelation(template,image)
	CALL correlationfft(tmplpad,impad,corr1,nx,ny)
	!corr1 = 1.0

! 8. calculate lcf map.
	PRINT*,"nmask=",nmask
	v=((nmask*cnv2)-(cnv1*cnv1))/(nmask*nmask)
	PRINT*,"V2"
	CALL imageinfo(v,nx,ny)
	PRINT*,v(499,499,0),v(500,500,0),v(501,501,0)

	WHERE (v.gt.0)
		v=sqrt(v)
	ELSEWHERE
		v=0
	ENDWHERE
	PRINT*,"NORMCONV"
	CALL imageinfo(v,nx,ny)
	PRINT*,v(499,499,0),v(500,500,0),v(501,501,0)

	corr1=corr1/nmask

	PRINT*,"CORR"
	CALL imageinfo(corr1,nx,ny)

	WHERE (v.ne.0)
		lcf = corr1/v
	ENDWHERE

! 9. write flcf map.
	
	deallocate (imsq,tmplpad,cnv1,cnv2,corr1,tmplmaskpad,v,impad,tmplmask)
! NEIL ENTERED STOP
	STOP

	RETURN

END SUBROUTINE flcf

!c***************************************************************************

SUBROUTINE read_mrcimage(stream,map,x,y,z,err)
	use mrc_image
!	use  image_arrays
	integer  x,y,z,err
	integer  stream, ix,iy,iz,xm1
	real, dimension (0:x-1,0:y-1,0:z-1) :: map
	integer s(3),s1

!	print*,'xyz ',x,y,z

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

SUBROUTINE convolutionfft(afft,bfft,c,nx2,ny2)
	! c = iFT(afft * bfft)
	integer nx2,ny2
	real afft(0:nx2+1,0:ny2-1,0:0),bfft(0:nx2+1,0:ny2-1,0:0),c(0:nx2+1,0:ny2-1,0:0)
	real n
	data ifor/0/,ibak/1/,zero/0.0/
	c=0
	! THIS IS JUST ELEMENT BY ELEMENT MULTIPLICATION FOR COMPLEX NUMBERS
	DO j=0,ny2-1
		DO i=0,nx2,2
			c(i,j,0)=afft(i,j,0)*bfft(i,j,0) - afft(i+1,j,0)*bfft(i+1,j,0)
			c(i+1,j,0)=afft(i,j,0)*bfft(i+1,j,0) + afft(i+1,j,0)*bfft(i,j,0)
		ENDDO
	ENDDO
	! INVERSE TRANSFORM
	CALL todfft(c,nx2,ny2,ibak)
	n=nx2*ny2
	n=sqrt(n)
	c=c*n
END SUBROUTINE convolutionfft

!c***************************************************************************

SUBROUTINE correlationfft(afft,bfft,c,nx,ny)
	! c = iFT( afft * conj(bfft) )
	integer nx,ny
	real afft(0:nx+1,0:ny-1,0:0),bfft(0:nx+1,0:ny-1,0:0),c(0:nx+1,0:ny-1,0:0)

	real n
	real*8 dd
	data ifor/0/,ibak/1/,zero/0.0/

	c=0
	DO j=0,ny-1
		DO i=0,nx+1,2
			c(i,j,0)   = afft(i,j,0)*bfft(i,j,0)   + afft(i+1,j,0)*bfft(i+1,j,0)
			c(i+1,j,0) = afft(i,j,0)*bfft(i+1,j,0) - afft(i+1,j,0)*bfft(i,j,0)
		ENDDO
	ENDDO

	CALL todfft(c,nx,ny,ibak)
	n=nx*ny
	n=sqrt(n)

	c=c*n
END SUBROUTINE correlationfft

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

SUBROUTINE normStdev(map,nx,ny,n,val,err)
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
END SUBROUTINE normStdev


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
	IF (mode.lt.0 .or. mode.gt.2) then
		PRINT*,"IMAGE READ ERROR, MODE =",mode
!		STOP
	ENDIF
	nx=nxyz(1)
	ny=nxyz(2)
	nz=nxyz(3)

	return
END SUBROUTINE readmrcheader


