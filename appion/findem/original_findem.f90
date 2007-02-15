!C*   FindEM programs  ***************************************************
!C                                                                       *
!C    Programs for automatic particle finding in electron micrographs.   *
!C                                                                       *
!C                                                                       *
!C************************************************************************
!C   Copyright (c) Medical Research Council, Laboratory of Molecular 	 *
!C    Biology.    All rights reserved.					 *
!C									 *
!C  All files within this package, unless otherwise stated, are Copyright*
!C  (c) Medical Research Council 2002. Redistribution is forbidden.	 *
!C   This program was written by Alan Roseman at the MRC Laboratory of	 *
!C   Molecular Biology, Hills Road, Cambridge, CB2 2QH, United Kingdom.	 *
!C									 *	
!C   MRC disclaims all warranties with regard to this software. 	 *
!C									 *
!C************************************************************************


! Projection matching program, findem
! uses local real space correlations
! AMR 4/2000
! assume downsizing and filtering already done 
!  amr 8/5/00
! added FLCF , amr 29/10/01

!IN: image, stack of projections, resolution range, threshold of projections,
!3D mask file , exent to search 

!OUT: cross-correlation map.

      Module image_arrays
      Real, dimension (:,:,:), allocatable :: map1,image,image2,map2, projections,maxmap2,pmap,wmap,smap,proj
      Real, dimension (:,:,:), allocatable :: search_object,search_object2
      Real, dimension (:,:), allocatable :: cccmap,current_image,image_object,pvectors,maxmap,LCF
      Real, dimension (:), allocatable :: array,products
      End Module image_arrays  
      
      Module image_arrays2
      real,  dimension (:,:,:), allocatable :: AA,T,maskimage,m,map2
      real,  dimension (:,:,:), allocatable :: a,b,c,cnv1,cnv2,corr1,v,f,w
      End Module image_arrays2          
                
        Module mrc_image
                DIMENSION ALINE(32768),NXYZ(3),MXYZ(3),NXYZST(3),NXYZ2(3)
                DIMENSION IXYZMIN(3),IXYZMAX(3),OUT(32768)
                DIMENSION LABELS(20,10),CELL(6)
                COMPLEX CLINE(16384),COUT(16384)
                CHARACTER*40 INFILE,OUTFILE 
                CHARACTER*80 TITLE, AA 
                INTEGER NX,NY,NZ,NXM1,NYM1,NZM1,NXP1,NXP2                 
                COMMON //NX,NY,NZ,IXMIN,IYMIN,IZMIN,IXMAX,IYMAX,IZMAX
                EQUIVALENCE (NX,NXYZ), (ALINE,CLINE), (OUT,COUT)
                EQUIVALENCE (IXYZMIN, IXMIN), (IXYZMAX, IXMAX)
                DATA NXYZST/3*0/, CNV/57.29578/  
                REAL DMIN,DMAX,DMEAN
                integer ntflag
        End Module  mrc_image



      Program MAIN
      Use  image_arrays
      use mrc_image
      Real  stepsize,wstepsize,wlimit,wstart
      Parameter (stepsize=1)
      real scale1,scale2,scalestep
      parameter (scale1=1.0, scale2=1.15,scalestep=1.0)
      Character*80 imagefilename,projfilename,relaxfile,pmapname,wmapname,cccmaxmap,smapname,blank
      Real threshold,sampling,real_sampling,resmin,resmax,defocus,downsize
      real diameter, rot_matrix(2,2)
      Integer iteration, search_radius

      Integer px,py,pz,err,x,y,z,p,np,pxp2,ival
      Real w,ccc,val
      Real ccc_max,w_max,p_max,x_max,y_max,radius
	character*3 num
	integer runcode
  	integer nxft,nyft,pxft,pyft
! 	integer next_ft_size
	integer siyp1,sixp1,i,j
        integer border_width            !sans_border change here. 1    


       Write (6,*) 'FindEM program:'
       Write (6,*) ' '
       Write (6,*) ' - local real space correlation'
       Write (6,*) '_______________________________'


! 1. Read in filenames and parameters 
      Write (6,*) 'Enter filename of the image file :'
      Read (5,*) imagefilename
      
      Write (6,*) 'Enter filename of the search template :'
      Read (5,*) projfilename
      
      Write (6,*) 'Enter a threshold for values to use from the search template: '
      Read (5,*) threshold
      Write (6,*) threshold
      
      Write (6,*) 'Enter sampling of the images in angstroms/pixel : '
      Read (5,*)   Sampling
      Write (6,*) Sampling
      
      Write (6,*) 'Enter a diameter of particles (A) ' 
      Read (5,*)   diameter
      Write (6,*) diameter
      
      Write (6,*) 'Enter a runcode '
      Read(5,*)  runcode
      Write (6,*) runcode
      
      Write (6,*) 'Enter  omega start, limit, stepsize '
      Read(5,*) wstart,wlimit,wstepsize
      Write(6,*) wstart,wlimit,wstepsize
     
      border_width=0 !sans_border change here. 2   
      Write (6,*) 'Enter a border_width in pixels for the ccc map (default=0) '!sans_border change here. 3
      Read*, border_width               !sans_border change here. 4
      Write (6,*) border_width 		!sans_border change here. 5

      	radius=diameter/2
	ntflag=-1
100    format (A50)
110    format (A80)
120    format (G12.5)
130    format (3G12.5)
140    format (2G12.5)
    

! 2 initialise other variables
	    blank='                                                 '            
            wmapname='wmap.mrc '//blank
            pmapname='pmap.mrc'//blank
            cccmaxmap='cccmaxmap'//num(runcode)//'.mrc'//blank
	    smapname='smap.mrc '//blank
!3 MAIN loop

  	call IMOPEN(1,imagefilename,'old')
	
	CALL IRDHDR(1,NXYZ,MXYZ,MODE,DMIN,DMAX,DMEAN)
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
 	
 	
        call read_mrcimage(1, image2, nx,ny,nz,err)
        val = minval(image2)
        if (val.lt.0) image2=image2-val
        !min of image must be gt 0
        image(1:nx,1:ny,1)=image2(1:nx,1:ny,1)

       call readmrcheader(2,projfilename,px,py,pz,err)
       if (err.gt.0) goto 9000
    
        ival=px
      	pxft=next_ft_size(ival)
      	ival=py
        pyft=next_ft_size(ival)
        
        
        pxp2=px+2
	allocate(projections(px,py,pz),pvectors(pz,px*py),proj(px,py,1))
	allocate(search_object(pxft,pyft,1),search_object2(px,py,1))
	
	search_object=0
	search_object2=5
	projections=0

        call read_mrcimage(2,projections,px,py,pz,err)
  


 	

! loop over projections
      do p = 1, pz
      	print*,'p=',p
! loop over orientations
            do w = wstart,wlimit,wstepsize
		print*,'w=',w	,'p=',p	
			!loop over scale
			do s=scale1,scale2,scalestep
                  call make_sobj(projections(:,:,p),px,py,w,search_object2,threshold,np,s)
                  search_object(1:px,1:py,1)=search_object2(1:px,1:py,1)
 
		

!      search_st = int(diameter/2/sampling) 	!sans_border change here. 6
      
 	search_st = border_width+1		 !sans_border change here. 7
      
      search_endx = nxft-search_st+1		!sans_border change here. 8
      search_endy = nyft-search_st+1		!sans_border change here. 9



	
	call FLCF(image,nxft,nyft,nz,search_object,pxft,pyft,pz,cccmap,radius,sampling)
	
	     do x= search_st,search_endx,stepsize
	       do y =  search_st,search_endy,stepsize
	     		if (cccmap(x,y).gt.maxmap(x,y)) then
	     		
	     					maxmap(x,y)=cccmap(x,y)
	     					pmap(x,y,1)=p
	     					wmap(x,y,1)=w
	     					smap(x,y,1)=s
	     		endif
	     
	      enddo

	    enddo

	  enddo
	     

        enddo  




        enddo 
	print*,' write file now'

   


	print*,'end',nx,ny,nz,nxft,nyft
	
	PRINT*,'minval=',minval(maxmap)
	PRINT*,'maxval=',maxval(maxmap)
	 maxmap2(1:nx,1:ny,1)=maxmap(1:nx,1:ny)
	 
	call IMOPEN(2,cccmaxmap,'NEW')
        call ITRHDR(2,1)
        call IWRHDR(2,title,ntflag,dmin,dmax,dmean)  
      
	call write_mrcimage2(2,maxmap2,nx,ny,nz,err,sampling)
	call imclose(9)
	
!	call    copyaheader(imagefilename,pmapname,3)
!	call    write_mrcimage(3,pmap,nx,ny,nz,err)
	
!	call    copyaheader(imagefilename,wmapname,3)
!	call    write_mrcimage(3,wmap,nx,ny,nz,err)

!	call    copyaheader(imagefilename,smapname,3)
!	call    write_mrcimage(3,smap,nx,ny,nz,err)

! normal exit
	close(1)
      print*,'Program finished O.K.'
  
      Print*,'Correlation map output to file: ',cccmaxmap
      goto 9998

! Errors
9000   continue
	print*, 'Image read error.'
9998   continue
         
         
      end
      
      subroutine make_sobj(projection,px,py,w,search_object,threshold,np,s)
     
	integer px,py,np
        real projection(px,py,1),search_object(px,py,1)
	real w,threshold,s
	
        search_object =projection
  
        
        call rot_image(search_object,w,px,py,s)
 
	
        return
      end subroutine make_sobj





      subroutine rot_image(image,w,nx,ny,s)

    
      real image(nx,ny,1),new_image(nx,ny,1)
      real coords(2),new_coords(2),s
      real x,y,val,w,originx,originy,rot_matrix(2,2)
      integer nx,ny,ix,iy

      equivalence (coords(1),x)
      equivalence (coords(2),y)
      
 
      originx=int(nx/2)+1
      originy=int(ny/2)+1
      
	
	call matrix(w,rot_matrix)
	
      new_image=0
      do ix=1,nx
           do iy=1,ny
	
           x=ix-originx
           y=iy-originy
                val = image(ix,iy,1)
		new_coords=(matmul(rot_matrix,coords)*s)+originx
		call interpo2D(new_image,new_coords(1),new_coords(2),nx,ny,val)
		
	   enddo
      enddo
      image=new_image

      return
      end subroutine rot_image



      subroutine matrix(w,rot_matrix)
	real w
	real r
	real rot_matrix(2,2)
	
	call rad(w,r)

	rot_matrix(1,1)=  cos(r)
	rot_matrix(1,2)=  sin(r)
	rot_matrix(2,1)= -sin(r)
	rot_matrix(2,2)=   cos(r)

       return
       
       
       
       end subroutine matrix

      subroutine rad(deg,r)
      real deg,pi,r
      parameter (pi=3.1415927)

      r = deg/180.*pi

      return
      end subroutine rad




      subroutine interpo2D(map,sx,sy,nx,ny,val)
!C bilinear ip of coords
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
             
        
        
        
        
        ! wraparound , should not be more than one 'cell' away.
	if (ix.le.0) ix=ix+nx
	if (ix.gt.nx) ix=ix-nx	
	if (iy.le.0) iy=iy+ny
	if (iy.gt.ny) iy=iy-ny
        
        
      	sixp1 = ix+1
	siyp1  =iy+1
	
	if (sixp1.gt.nx) sixp1=sixp1-nx
	if (siyp1.gt.ny) siyp1=siyp1-nx	  
        
!        	print*,sx,sy,ix,iy
  
        map(ix,iy,1) =  map(ix,iy,1)+   nwx*nwy*val
           
       	map(ix,siyp1,1)=  map(ix,siyp1,1)+  nwx* wy*val
 	
        map(sixp1,iy,1) =   map(sixp1,iy,1)+    wx*nwy*val
   
        map(sixp1,siyp1,1)=  map(sixp1,siyp1,1)+  wx* wy*val
     
777     continue        
        return
        end subroutine interpo2D


!C ************************************************

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
!C       print *,hun,ten,units


        num=digit(hun)//digit(ten)//digit(units)  
        return
        end function

!Fast local correlation function.
! AM Roseman 2001

 
     

 

        subroutine FLCF(map,nx,ny,nz,template,tx,ty,tz,lcf,radius,sampling)
        !use mrc_image
        use  image_arrays2
      
        
        integer nx,ny,nz,TX,TY,TZ
       

        real sampling,lp,hp
        logical odd
	CHARACTER*40 TEMPLATEFILE
        INTEGER TXYZ(3),TXP1,TYM1,TZM1,TXM1
	integer IXYZ(3)

	INTEGER NM,NI,x,y

        DATA IFOR/0/,IBAK/1/,ZERO/0.0/
 
 	real r,val,v2,v1
 	integer s(3)
 	real array(1000000)
 	   Real, dimension (:,:,:), allocatable :: lcf2
 	
 	real map(0:NX-1,0:NY-1,0:NZ-1),template(0:tx-1,0:ty-1,0:tz-1),LCF(0:NX-1,0:NY-1,0:NZ-1)
        allocate(AA(0:NX+1,0:NY-1,0:NZ-1),T(0:NX+1,0:NY-1,0:NZ-1),lcf2(0:NX+1,0:NY-1,0:NZ-1))
        allocate  (A(0:NX+1,0:NY-1,0:NZ-1),B(0:NX+1,0:NY-1,0:NZ-1),C(0:NX+1,0:NY-1,0:NZ-1),w(0:NX-1,0:NY-1,0:NZ-1))
        allocate (cnv1(0:NX+1,0:NY-1,0:NZ-1),cnv2(0:NX+1,0:NY-1,0:NZ-1),corr1(0:NX+1,0:NY-1,0:NZ-1))
        allocate (m(0:NX+1,0:NY-1,0:NZ-1),V(0:NX+1,0:NY-1,0:NZ-1),F(0:NX+1,0:NY-1,0:NZ-1),map2(0:NX+1,0:NY-1,0:NZ-1))
 	allocate (maskimage(0:tx-1,0:ty-1,0:tz-1))
 	
1     format(A45)      
!      write(*,1) 'Fast Local correlation Program'
!      write(*,1) '------------------------------'
    


        nxp2=nx+2
        nxp1=nx+1
        nym1=ny-1
        nzm1=nz-1
	nxm1=nx-1
	
	
       
         s1=size(map,1)
       
        MapX=nx
 	MapY=ny
        MapZ=nz
        
 	NI=NX*NY

       
       txm1=tx-1
       txp1=tx+1
       tym1=ty-1
       tzm1=tz-1
        
      
	IXYZ=NXYZ


! 4. calculate mask
	r=radius/sampling
	
	call mask(template,tx,r,NM)
	
	
	   
	call msd_set(template,tx,ty,nm,val,err)
 	 
	 call mask(template,tx,r,NM)
	 
	
 
	val=0
	call pad2(template,tx,ty,t,mapx,mapy,val)

	maskimage=1
	call mask(maskimage,tx,r,NM)
		
	
          val=0
	call pad2(maskimage,tx,ty,m,mapx,mapy,val)
	
         val=0
	call pad(map,mapx,mapy,map2,mapx+2,mapy,val)

	
! 5. do FFTs


      
	  AA = map2 * map2

	  

          CALL TODFFT(MAP2,mapx,mapY,IFOR)
        
        
          CALL TODFFT(AA,mapX,mapY,IFOR)  
      
          CALL TODFFT(T,mapX,mapY,IFOR)
          
          CALL TODFFT(M,mapX,mapY,IFOR)    
           
 
          call CONVOLUTION(map2,m,cnv1,mapx,mapy)
      
  
          call CONVOLUTION(aa,m,cnv2,mapx,mapy)       
      
          call CORRELATION(t,map2,corr1,mapx,mapy,hp,lp,sampling)
          
         


! 8. Calculate LCF map.

		
               V=((nm*cnv2)-(cnv1*cnv1))/(nm*nm)

			
		where (v.gt.0)
                      v=sqrt(v)
                      elsewhere
                      v=0
		endwhere 
	
		F=CORR1/NM
		

		lcf2=0
		where (v.ne.0)
				LCF=F /v
		endwhere 
!		

! 9. Write FLCF map.

      deallocate (aa,t,a,b,c,w,cnv1,cnv2,corr1,m,v,f,map2,maskimage)     
      return
      
997   STOP 'Error on file read.'
      end subroutine FLCF

	

        subroutine read_mrcimage(stream,map,X,Y,Z,err)
 
	Use mrc_image
!        Use  image_arrays
	INTEGER  X,Y,Z,err
	 INTEGER  stream, IX,IY,IZ,xm1
	 real, DIMENSION (0:X-1,0:Y-1,0:Z-1) :: map  
	 INTEGER S(3),S1
	    
	    PRINT*,'xyz ',X,Y,Z
	    
  	   s1=size(map,1)
  	
 	    
   	   s1=size(map,2)
  	
 	       s1=size(map,3)
  	
      	
      
!     read in file 

      DO 350 IZ = 0,z-1
          DO 350 IY = 0,y-1
            CALL IRDLIN(stream,ALINE,*998)
            DO 300 IX = 0,x-1       
       !     print*,ix
                map(ix,iy,iz) = ALINE(IX+1)
300         CONTINUE   
          !  map(X+0,iy,iz)=0
           ! map(X+1,iy,iz)=0
!           print*,ix,iy,iz
350   CONTINUE
		
      return
998   STOP 'Error on file read1.'
      end subroutine 
      
      
      
      
      subroutine write_mrcimage(stream,map,x,y,z,err)
      Use  mrc_image
      REAL val,sampling
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

      print*,NX,NY,NZ  
!     write file 

      DMIN =  1.E10
      DMAX = -1.E10
      DOUBLMEAN = 0.0

      DO 450 IZ = 0,NZM1
      DO 450 IY = 0,NYM1
            
            DO 400 IX = 0,NXM1
     
                val = map(IX,IY,IZ)
                ALINE(IX+1) = val
                
                DOUBLMEAN = DOUBLMEAN + val         
                IF (val .LT. DMIN) DMIN = val
                IF (val .GT. DMAX) DMAX = val

400         CONTINUE   

      CALL IWRLIN(stream,ALINE)
450   CONTINUE
      DMEAN = DOUBLMEAN/(NX*NY*NZ)
      
      cell(1) = sampling *NXM1
      cell(2) = sampling *NYM1
      cell(3) = sampling *NZM1
      cell(4) = 90
      cell(5) = 90
      cell(6) = 90

      CALL IALCEL(STREAM,CELL)  
      CALL IWRHDR(stream,TITLE,-1,DMIN,DMAX,DMEAN)
      CALL IMCLOSE(stream)
      
      return
999   STOP 'Error on file write.'
      end subroutine 

	
     
      subroutine write_mrcimage2(stream,map,x,y,z,err,sampling)
      Use  mrc_image
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

      DMIN =  1.E10
      DMAX = -1.E10
      DOUBLMEAN = 0.0

      DO 450 IZ = 0,NZM1
      DO 450 IY = 0,NYM1
    
            DO 400 IX = 0,NXM1
                val = map(IX,IY,IZ)
                ALINE(IX+1) = val
                
                DOUBLEMEAN = DOUBLEMEAN + val         
                IF (val .LT. DMIN) DMIN = val
                IF (val .GT. DMAX) DMAX = val

400         CONTINUE   

      CALL IWRLIN(stream,ALINE)
450   CONTINUE
	
      DMEAN = DOUBLEMEAN/(NX*NY*NZ)


      CALL IALCEL(STREAM,CELL)  
    
      CALL IWRHDR(stream,TITLE,1,DMIN,DMAX,DMEAN)
      
      CALL IMCLOSE(stream)
     
      
      return
999   STOP 'Error on file write.'
      end subroutine 

	


        real function radiusXY(x,y,xc,yc)
      
        integer x,y,xc,yc,xx,yy
        real r2


        xx=x-xc
        yy=y-yc


	r2=float(xx**2 +  yy**2)

        radiusXY=sqrt(r2)

        return
        end function

        subroutine mask(template,nx,radius,msum)
!	use image_arrays 
 	integer nx ,ty,tx
 	dimension template(0:nx-1,0:nx-1,0:0)
        real x,y,radius    
        integer msum,i,j,cx,cy 
        real radiusXY
        
	tx=size(template,1)
        ty=size(template,2)

	cx=int(float(tx)/2.)
	cy=int(float(ty)/2.)
	
 
        maskimage = 0
        msum=0

        do i=0,nx-1
         do j=0,nx-1
!       	print*,i,j
                if (radiusXY(i,j,cx,cy).gt.radius) then
                        	template(i,j,0) = 0.0
                        else
                        	msum=msum+1
                end if

          enddo
        enddo
       
        return
        end subroutine

!C***************************************************************************

	subroutine pad(a,sx,sy,b,nx2,ny2,val)
	
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
	
	do i=0,sy-1
		do j=0,sx-1
	
			bx=j
			by=i		
			b(bx,by,0)=a(j,i,0)
	!		print*,i,j,a(j,i,0),bx,by,b(bx,by,0)
		enddo
	enddo
		
		
	end subroutine pad
	
	       
	subroutine pad2(a,sx,sy,b,nx2,ny2,val)
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
	
	do i=0,sy-1
		do j=0,sx-1
		
			bx=wrap(j-cx,nx2)
			by=wrap(i-cy,ny2)
					
			b(bx,by,0)=a(j,i,0)
	!		print*,i,j,a(j,i,0),bx,by,b(bx,by,0)
		enddo
	enddo
		
		
	end subroutine pad2
	
	integer function wrap(a,b)
	integer a,b
		
	wrap = a	
	if (a.lt.0) wrap = b+a
		
	end function wrap


	subroutine CONVOLUTION(a,b,c,nx2,ny2)
	!use image_arrays
	integer nx2,ny2
	real a(0:nx2+1,0:ny2-1,0:0),b(0:nx2+1,0:ny2-1,0:0),c(0:nx2+1,0:ny2-1,0:0)
	real n
	
	DATA IFOR/0/,IBAK/1/,ZERO/0.0/
	
	c=0
	do j=0,ny2-1
		do i=0,nx2,2					
			c(i,j,0)=a(i,j,0)*b(i,j,0)-a(i+1,j,0)*b(i+1,j,0)
			c(i+1,j,0)=a(i,j,0)*b(i+1,j,0)+a(i+1,j,0)*b(i,j,0)
		!	print*,i,j,nx2,ny2
		enddo
	enddo
	CALL TODFFT(C,NX2,NY2,IBAK)
	n=nx2*ny2
	n=sqrt(n)
	C=C*N
	
	end subroutine CONVOLUTION
	
	
	

	
	
	
	subroutine CORRELATION(a,b,c,nx,ny,hp,lp,sampling)
!	use image_arrays
	integer nx,ny
	real a(0:nx+1,0:ny-1,0:0),b(0:nx+1,0:ny-1,0:0),c(0:nx+1,0:ny-1,0:0)
	
	real r1,r2,hp,lp,sampling,n
	real*8 dd
	DATA IFOR/0/,IBAK/1/,ZERO/0.0/
	
	r1=hp/sampling
	r2=lp/sampling

	c=0
	do j=0,ny-1
		do i=0,nx+1,2
			!r=radft(i,j,ny)
			!if ((r.gt.r1).and.(r.lt.r2)) then
			c(i,j,0)=a(i,j,0)*b(i,j,0)+a(i+1,j,0)*b(i+1,j,0)
			c(i+1,j,0)=a(i,j,0)*b(i+1,j,0)-a(i+1,j,0)*b(i,j,0)
			!endif
		enddo
	enddo
	dd=(nx*ny)
	
	CALL TODFFT(C,NX,NY,IBAK)
	n=nx*ny
	n=sqrt(n)
	
	C=C*n
	
	end subroutine CORRELATION
	
	
	real function radft(a,b,ny)
	integer a,b
	real r
	
	a=a/2
	b=b-(ny/2)
	r=(a*a + b*b) 	
		
	radft = sqrt(r)
	
		
	end function radft
	
	

	
      subroutine msd_set(map,nx,ny,n,val,err)
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
       end subroutine msd_set

       
!C***************************************************************************

        integer function next_ft_size(x)
        logical ftsize
        integer x
	

        if (int(x/2).ne.(x/2)) x=x+1
        
        do while (.not.ftsize(x))
               
                x=x+2
        enddo
        next_ft_size=x
        return

        end function next_ft_size

!C***************************************************************************
        logical function ftsize(x)
        integer x,n,a

        real b
        real primes(8)
        primes=(/2,3,5,7,11,13,17,19/)

        ftsize = .false.
        
        a=x
        do n=1,8
100     continue
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

        end function ftsize

!C***************************************************************************

      Subroutine readmrcheader(stream,filename,nx,ny,nz,err)
      Integer stream,err
      Character*80 filename



! mrc file stuff
        INTEGER NX,NY,NZ
        DIMENSION ALINE(8192),NXYZ(3),MXYZ(3),NXYZST(3)
        DIMENSION IXYZMIN(3),IXYZMAX(3),OUT(8192)
        DIMENSION LABELS(20,10),CELL(6)
        COMPLEX CLINE(4096),COUT(4096)
        CHARACTER*80 TITLE
        EQUIVALENCE  (ALINE,CLINE), (OUT,COUT)
        EQUIVALENCE (IXYZMIN, IXMIN), (IXYZMAX, IXMAX) 
        DATA NXYZST/3*0/, CNV/57.29578/


   
       Call imopen(stream,filename,'RO')
       CALL IRDHDR(stream,NXYZ,MXYZ,MODE,DMIN,DMAX,DMEAN)
       If (mode.lt.0 .or.mode.gt.2) err=1
 
        nx=nxyz(1)
        ny=nxyz(2)
        nz=nxyz(3)      

      Return
      End subroutine readmrcheader





      
