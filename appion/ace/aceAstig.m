function   [ctfparams sx]= aceAstig(filename,outfile,display,stig,medium,dforig,tempdir, startOrientn, sectorAngle);
%
% DESCRIPTION:
%
% Returns the parameters of the Contrast Transfer Function. This function
% is at the heart of Automated CTF Estimation and is called by both
% leginon_ace_gui and acedemo.
%
% USAGE  :
%        ctfparams = ace(filename,outfile,display,stig,medium,dforig,tempdir);
%
%        filename : Name of the input mrc file.
%        outfile  : The name of output file.
%        display  : Boolean input to control the graphical display.
%        stig     : Boolean switch to turn on astigmatism estiamtion.
%        medium   :  'carbon' or 'ice'.
%        dforig   : The defocus set by the microscope. It is used only
%                   when the edge detection fails. It defaults to -2um.
%        tempdir  : Optional string argument to specify directory for
%                   temporary files.
%
%        ctfparams: Vector of ctf parameters. First two element give
%                   the defoci, the third value is Amplitude contrast,
%                   the fourth value is the angle of astigmatism, elements
%                   5-8 are the noise parameters and 9-12 are the envelope
%                   parameters. 17 & 18 are the confidence values.
%
%
% See also leginon_ace_gui and acedemo.
%
% Copyright 2004-2005 Satya P. Mallick.




singlefigure=1;
if nargin<4
    display = 1;
    stig = 1;
    medium = 'carbon';
    dforig = 2e-6;
    tempdir = './';
elseif nargin<5
    stig = 1;
    medium = 'carbon';
    dforig = 2e-6;
    tempdir = './';
elseif nargin<6
    medium = 'carbon';
    dforig = 2e-6;
    tempdir = './';
elseif nargin<7
    tempdir = './';
end


%START: File I/O
outid  = fopen(outfile,'a');

warning off all
%if(dirname(end) ~='/')
%  dirname = strcat(dirname,'/');
%end
%End: File I/O

trial = 1;


while (trial <3)
    % Load Microscope Parameters

    load(strcat(tempdir,'scopeparams.mat'));
    V = V*1e3;
    Cs = Cs*1e-3;
    Ca = Ca;
    lambda = getlambda(V);

    % End Load Microscope Parameters

    %START: Initialization

    conf = 0;


    %End: Initialization


    if startOrientn==0
        % get filename extension
        fileType=filename((max(findstr(filename,'.'))+1):length(filename));

        % read mrc or tiff formatted files
        switch fileType
            case {'mrc','MRC'}
                file = readmrc(filename);
            case {'tif','TIF','tiff','TIFF'}
                file=imread(filename);
        end

        filesz = size(file);
        file = file - mean(file(:));

        if(strcmp(medium,'ice'))
            trial = 3;
            confth = 0.1;
            load(strcat(tempdir,'aceconfig.mat'),'pfice');
            powerfactor = pfice;
            if(filesz(1)<512)
                fprintf('Field too small for ice medium\n');
                return;
            end

            load(strcat(tempdir,'aceconfig.mat'),'resamplefr');
            if(resamplefr~=1.0)
                file = imresize(file,1/resamplefr,'bilinear');
                Ca = resamplefr*Ca;
            end

            %     if(Ca<1.7 && abs(dforig)>3.3e-6)
            %      file = imresize(file,0.5,'bilinear');
            %      Ca = 2*Ca;
            %
            %     end
            %   elseif(Ca<1.7 && trial==2)
            %     file = file(1:512,1:512);
            %  elseif(Ca>1.7 & trial ==1)
            %    file = file(1:1024,1:1024);
            %  else

        elseif(strcmp(medium,'carbon'))
            confth = 0.1;
            load(strcat(tempdir,'aceconfig.mat'),'pfcarbon');
            powerfactor = pfcarbon;


            %START: Choose field size based on pixel size
            %if(Ca<1.7 & abs(dforig)>3.3e-6)
            load(strcat(tempdir,'aceconfig.mat'),'resamplefr');
            if(resamplefr~=1.0)
                file = imresize(file,1/resamplefr,'bilinear');
                Ca = resamplefr*Ca;
            end
            %end

            %END: Choose field size based on pixel size

        else
            fprintf('Medium should be ice or carbon\n');
            return;
        end

        save(strcat(tempdir,'file.mat'));
        clear file;
    else
        load(strcat(tempdir,'file.mat'), 'Ca', 'resamplefr', 'powerfactor', 'confth');
    end
    %START: Get 1D profile

    [val, pg, rat, ang] = getprofile_ang(stig,medium,tempdir, startOrientn, sectorAngle);
    %  [val, pg, imfftabs, rat, ang] = getprofile(file,stig,medium,tempdir);

    if(isempty(val))
        fprintf(outid,'\n%s %s', filename, 'Could not process micrograph: Problem with ellipse fit');
        fprintf('\n%s %s', filename, 'Could not process micrograph : Problem with ellipse fit');
        fclose(outid);
        ctfparams(1:18) = -1;
        return
    end
    clear val;
    %END: Get 1D profile
    
    load(strcat(tempdir,'imfftabs.mat'),'imfftabs');
    [imheight, imwidth] = size(imfftabs);
    freqfactor = (imwidth*Ca)/1e10;
    save(strcat(tempdir,'freqfactor'),'freqfactor');

    %START: Check for hyperbolic or parabolic distortion

    if(rat==-1)
        fprintf(outid,'\n%s %s',filename, 'Could not process micrograph: Hyperbolic distortion');
        fprintf('\n%s %s',filename, 'Could not process micrograph: Hyperbolic distortion');
        fclose(outid);
        ctfparams(1:18) = -1;
        return;
    end

    %END: Check for hyperbolic or parabolic distortion


    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    pg1 = smooth(pg,round(5*imwidth/512));
    dpg1 = diff(pg1);
    ddpg1 = diff(dpg1);


    %START:  Determining the lower cuttoff

    %   load(strcat(tempdir,'k1'));
    %   load(strcat(tempdir,'k2'));
    %   x = round(max(sqrt([1/k1 1/k2])));


    lambda = getlambda(V);

    xtemp = sqrt((-abs(dforig)*lambda+sqrt(dforig^2*lambda^2+2*Cs*lambda^3))...
        /(Cs*lambda^3));
    xtemp = round(xtemp*freqfactor);


    %  if(abs(xtemp-x)>imwidth/20)
    x = xtemp-round(imwidth/50);
    %  end
    x1 = x;

    % if(~strcmp(medium,'ice'))
    %   while(1.1*pg1(x)<pg1(x-1) && x>1)
    %     x = x-1;
    %   end
    %
    %   while(pg1(x1)>pg1(x1+1) && x1 < imwidth/2 )
    %     x1 = x1+1;
    %   end
    % end

    if(~isreal(x) | x>0.35*imwidth)

        fprintf(outid,'\n%s %s', filename,...
            'Could not process micrograph:Low SNR');
        fprintf('\n%s %s', filename,...
            'Could not process micrograph:Low SNR ');
        fclose(outid);
        ctfparams(1:18) = -1;
        return;
    end

    %  else
    %     while(abs(ddpg1(x1))/abs(dpg1(x1))<0.3)
    %       abs(ddpg1(x1))/abs(dpg1(x1));
    %       x1 = x1+1;
    %     end


    %END:  Determining the lower cuttoff

    %x = 10;
    %x1=11;

    %START: Removing lower frequencies.

    pgram = pg1(x:end);
    pgram1 = pg1(x1:end);

    %END: Removing lower frequencies.

    %START: Calculation of the noise function

    s = [x:length(pg1)]';
    pixeloff = 1;
    s = s - pixeloff;

    snoise = [x1:length(pg1)]';
    snoise = snoise - pixeloff;

    A1 = [ones(length(snoise),1) sqrt(snoise) snoise snoise.^2];
    b1 = log(pgram1);

    options1 = optimset('TolFun',1e-4,'MaxFunEvals', 30,'MaxIter',1000,'Display','off');
    [optparams1,fun1,eflag1,out1] = fmincon(@objnoise,[0 0 0 0]', A1,b1,[],[],[],[1e6 0 0 0],[],options1,A1,b1);

    if(eflag1<0)
        fprintf(outid,'\n%s %s', filename, 'Could not process micrograph,:Unreliable noise fit');
        fprintf('\n%s %s', filename, 'Could not process micrograph:Unreliable noise fit');
        fclose(outid);
        ctfparams(1:18) = -1;
        return
    end
    A1 = [ones(length(s),1) sqrt(s) s s.^2];
    b_calc1 = 2*A1*optparams1;

    noiseparams = 2*[optparams1(1) optparams1(2)*sqrt(freqfactor) optparams1(3)*(freqfactor) optparams1(4)*(freqfactor).^2];

    %END: Calculation of the noise function

    %START: Calculation of the ctf + env  function

    ctfenv = pgram.^2 - exp(b_calc1);

    %END: Calculation of the ctf + env  function

    %START: Calculation of higher cutoff frequency

    ctfenvcum = cumsum(ctfenv(x1-x+1:end));
    upcut = find(ctfenvcum> powerfactor*ctfenvcum(end));

    %upcut = upcut(1);
    upcut = 60;
    if(strcmp(medium,'ice'))
        upcut=60;
    end
    %while(ctfenv(x+upcut)<ctfenv(x+upcut-1))
    %  upcut = upcut-1;
    %end

    %END: Calculation of higher cutoff frequency

    ctfenv = ctfenv(1:upcut);
    s = s(1: upcut);
    pg = pg(x:end);
    pgram = pg1(x:x+upcut-1);
    A1 = [ones(length(s),1) sqrt(s) s s.^2];
    b_calc1 = 2*A1*optparams1;

    %START: Calculation of the envelope  function

    A2 = [ones(upcut,1) sqrt(s(1:upcut)) s(1:upcut) s(1:upcut).^2 ];
    b2 = log(ctfenv(1:upcut) -min(ctfenv(1:upcut))+1);
    options2 = optimset('TolFun',1e-4,'MaxFunEvals',30,...
        'MaxIter',1000,'Display','off');
    [optparams2,fun2,eflag2,out2] = fmincon(@objenv,[max(b2)   0  0 0]',...
        -A2, -b2,[],[],[],[1e6 0 0 0],[],options2,A2,b2);

    envparams = [optparams2(1) optparams2(2)*sqrt(freqfactor) ...
        optparams2(3)*(freqfactor) optparams2(4)*(freqfactor).^2];

    if(eflag2<0)
        fprintf(outid,'\n%s %s', filename,...
            'Could not process micrograph:Unreliable envelope fit');
        fprintf('\n%s %s', filename,...
            'Could not process micrograph :Unreliable envelope fit');
        fclose(outid);
        h1=figure('Visible','off');
        load(strcat(tempdir,'k1'))
        load(strcat(tempdir,'k2'))
        imshow(log(imfftabs),[])

        hold on;
        quiver('v6',imwidth/2,imwidth/2,-sqrt(1/k1)*sin(pi*ang/180),-sqrt(1/k1)*cos(pi*ang/180));
        quiver('v6',imwidth/2,imwidth/2,sqrt(1/k1)*sin(pi*ang/180),sqrt(1/k1)*cos(pi*ang/180));
        quiver('v6',imwidth/2,imwidth/2,sqrt(1/k2)*sin(pi*(ang+90)/180),sqrt(1/k2)*cos(pi*(ang+90)/180));
        quiver('v6',imwidth/2,imwidth/2, -sqrt(1/k2)*sin(pi*(ang+90)/180),-sqrt(1/k2)*cos(pi*(ang+90)/180));

        print(strcat('-f',num2str(h1)),'-dpng','-r75',strcat(tempdir,'im1.png'));
        print(strcat('-f',num2str(h1)),'-dpng','-r75',strcat(tempdir,'im2.png'));

        ctfparams(1:18) = -1;
        return
    end
    A2 = [ones(length(s),1) sqrt(s) s s.^2 ];
    b_calc2 = A2*optparams2;
    env = exp(b_calc2);
    % END: Calculation of the envelope  function

    % START: Calculation of the ctf function
    ctf = ctfenv./env;

    %Dont user fir filters. Not every user will have the signal processing
    %toolbox.
    %h = fir1(round(8*imwidth/512),[0.0001 0.1]);
    %ctffilt = conv(ctf,h);
    %ctffilt = ctffilt(1+(length(h)-1)/2:end-(length(h)-1)/2);

    ctffilt = smooth(ctf,round(5*imwidth/512));
    %  figure; plot(ctffilt, '-');

    %ctffilt = reshape(ctffilt,length(ctffilt),1);
    % END: Calculation of the ctf function

    % START:Calculating the location of zeros of ctf
    ind= [];
    ctfsign = sign(diff(ctffilt));
    for i=1:length(ctfsign)-1;
        if(ctfsign(i)==-1 & ctfsign(i+1)== 1)
            ind = [ind' i+1]';
        end
    end
    if(length(ind)==0)
        ind = 1;
    end
    % End:Calculating the location zeros of ctf


    % Start: Robust initial estimate of defocus

    soffset = x-1;
    snew = (s)/freqfactor;
    sind = ind + soffset - pixeloff;
    sind = sind/freqfactor;

    flag = 1;
    n=1 ;
    nzero = [];

    i = [1:length(ind)]';
    imat = repmat(i,1,length(ind));
    sindmat = repmat(sind,1,length(ind));
    nzero = [];
    nzero  = (imat -Cs*lambda^3*sindmat.^4/2)./(lambda*sindmat.^2);

    err = [];
    for i=1:length(ind)
        for j=1:length(ind)
            gmma = getgamma(snew,nzero(i,j),Cs,lambda);
            ctf_temp = getctf(gmma,0.0);
            err(i,j) =  norm(ctf-ctf_temp,2);
        end
    end

    if(sum(isnan(err(:)))==0 &&  sum(isinf(err(:)))==0 && length(err(:))>0)
        [score_final maxscoreind] = min(err(:));
        if(strcmp(medium,'carbon'))
            zinit = nzero(maxscoreind); % initial estimate of defocus
        else
            zinit = nzero(1);
        end

        zinit = nzero(maxscoreind);


        %keyboard
        %scut = sqrt(2.0/(zinit*lambda));
        %indcut = find(snew>scut);
        %snew1 = snew(1:indcut(1));
        Ainit = 0.0; % Setting the initial Amplitude contrast to 0.
        gmmainit = getgamma(snew,zinit,Cs,lambda);
        ctfinit = getctf(gmmainit,Ainit);
        % End : Robust initial estimate of defocus

        % Start: Refined estimate of defocus
        ctffiltnew =ctffilt;
        ctffiltnew(ind)=0;

        %ctffiltnew1 = ctffiltnew(1:indcut(1));
        %ctffilt1 = ctffilt(1:indcut(1));
        defocusoptions = optimset('TolX',1e-10,'MaxIter',30,'MaxFunEvals',1000,'Display','off');

        if strcmp(medium,'carbon')

            [param,fun3,eflag3,out3] = fmincon(@defocusobj,[zinit Ainit],[],[],...
                [],[],[0.0 0.0],[10e-6 0.2],[],...
                defocusoptions,ctffiltnew,snew,V,Cs);
        else

            [param,fun3,eflag3,out3] = fmincon(@defocusobj,[zinit Ainit],[],[],...
                [],[],[zinit- 0.1*1e-6 0.0],[zinit+0.1*1e-6 0.2],[],...
                defocusoptions,ctffiltnew,snew,V,Cs);
        end


        if(eflag3<0)

            fprintf(outid ,'\n%s %s', filename,...
                'Could not process micrograph:Unreliable defocus fit');

            fprintf('\n%s %s', filename,...
                'Could not process micrograph:Unreliable defocus fit');
            fclose(outid);
            h1=figure('Visible','off');
            load(strcat(tempdir,'k1'))
            load(strcat(tempdir,'k2'))
            imshow(log(imfftabs),[])

            hold on;
            quiver('v6',imwidth/2,imwidth/2,-sqrt(1/k1)*sin(pi*ang/180),...
                -sqrt(1/k1)*cos(pi*ang/180));
            quiver('v6',imwidth/2,imwidth/2,sqrt(1/k1)*sin(pi*ang/180),...
                sqrt(1/k1)*cos(pi*ang/180));
            quiver('v6',imwidth/2,imwidth/2,sqrt(1/k2)*sin(pi*(ang+90)/180),...
                sqrt(1/k2)*cos(pi*(ang+90)/180));
            quiver('v6',imwidth/2,imwidth/2, -sqrt(1/k2)*sin(pi*(ang+90)/180),...
                -sqrt(1/k2)*cos(pi*(ang+90)/180));

            print(strcat('-f',num2str(h1)),'-dpng','-r75',strcat(tempdir,'im1.png'));
            print(strcat('-f',num2str(h1)),'-dpng','-r75',strcat(tempdir,'im2.png'));

            ctfparams(1:18) = -1;
            return

        end

        zfinal = param(1);
        Afinal = param(2);
        gmmafinal = getgamma(snew,zfinal,Cs,lambda);
        ctffinal = getctf(gmmafinal,Afinal);

        if startOrientn==0
            ctffiltArr = ctffilt;
            ctffinalArr = ctffinal;
            save(strcat(tempdir, 'ctfMatchPlotData.mat'), 'ctffiltArr', 'ctffinalArr');
        else
            load(strcat(tempdir, 'ctfMatchPlotData.mat'), 'ctffiltArr', 'ctffinalArr');
            ctffiltArr = [ctffiltArr ctffilt];
            ctffinalArr = [ctffinalArr ctffinal];
            save(strcat(tempdir, 'ctfMatchPlotData.mat'), 'ctffiltArr', 'ctffinalArr');            
        end
        
%         h1=figure('Visible','off'); plot(ctffilt, '-'); hold on; plot(ctffinal, 'r-'); title(sprintf('%f degrees - CTFFilt, CTFFinal - 1st iter', startOrientn*180/pi));
%         saveas(h1,strcat(tempdir, 'im1.png'));
%         close(h1);

        % Start: Calculating the confidence of estimation
        meanctffinal = mean(ctffinal);
        meanctf_filt = mean(ctffilt);

        conf = mean((ctffinal - meanctffinal).*(ctffilt -meanctf_filt));
        conf = conf/(std(ctffinal)*std(ctffilt));

        % Start: Calculating the confidence of estimation based on the slopes
        ctffinal_d=diff(ctffinal);
        ctffilt_d=diff(ctffilt);

        meanctffinal = mean(ctffinal_d);
        meanctf_filt = mean(ctffilt_d);

        conf_d = mean((ctffinal_d - meanctffinal).*(ctffilt_d -meanctf_filt));
        conf_d = conf_d/(std(ctffinal_d)*std(ctffilt_d));

        if(conf<confth)
            trial=trial+1;
        else
            trial = 3;
        end
    else
        trial = trial+1;
    end
end
% End: Calculating the confidence of estimation



if(~isnan(conf) & conf ~= 0 & ~isnan(conf_d) & conf_d ~=0)
    slarge =sqrt((-zfinal*lambda+sqrt(zfinal^2*lambda^2+2*Cs*lambda^3))...
        /(Cs*lambda^3));
    ssmall = slarge*rat;
    zsmall = (1-Cs*lambda^3*ssmall^4/2)/(lambda*ssmall^2);
    defoci = [zfinal zsmall];   Ampconst = Afinal;

    %   sx = sqrt((-abs(defoci(1))*lambda+sqrt(defoci(1)^2*lambda^2+2*Cs*lambda^3))...
    %       /(Cs*lambda^3));
    %  sx = round(sx*freqfactor);
    sx = round(slarge*freqfactor);

    fprintf(outid,'\n %s %f %f %f %f %f %f  %f %f %f %f %d %s',filename,...
        abs(dforig)*1e6, zinit*1e6, zfinal*1e6,zsmall*1e6,Afinal, rat, ang,conf,conf_d, sx, sprintf('R%.1f', resamplefr));
    %  fprintf('%s %f %f %f %f %f %f %f %d\n', filename, abs(dforig)*1e6, ...
    %     zinit*1e6, zfinal*1e6, zsmall*1e6, Afinal, conf, conf_d, sx);
    fclose(outid);
    lowercutoff = (x-pixeloff)/freqfactor;
    uppercutoff = (x+upcut-pixeloff)/freqfactor;

    ssnr = [round(imwidth/20):round(imwidth/4)]';
    ssnr = ssnr*1e10/(imwidth*Ca);
    Asnr = [ones(length(ssnr),1) sqrt(ssnr) ssnr ssnr.^2];
    noise_snr = exp(Asnr*noiseparams');
    env_snr   = exp(Asnr*envparams');
    snr= sum((env_snr./noise_snr));

    ctfparams = [defoci(1), defoci(2) zinit Ampconst -ang*pi/180, noiseparams/2,...
        envparams/2 lowercutoff uppercutoff snr conf conf_d];



else
    fprintf(outid,'\n%s %s', filename,'Could not process micrograph');
    fprintf('\n%s %s', filename,'Could not process micrograph');
    fclose(outid);
    h1=figure('Visible','off');
    load(strcat(tempdir,'k1'))
    load(strcat(tempdir,'k2'))
    imshow(log(imfftabs),[])

    hold on;
    quiver('v6',imwidth/2,imwidth/2,-sqrt(1/k1)*sin(pi*ang/180),-sqrt(1/k1)*cos(pi*ang/180));
    quiver('v6',imwidth/2,imwidth/2,sqrt(1/k1)*sin(pi*ang/180),sqrt(1/k1)*cos(pi*ang/180));
    quiver('v6',imwidth/2,imwidth/2,sqrt(1/k2)*sin(pi*(ang+90)/180),sqrt(1/k2)*cos(pi*(ang+90)/180));
    quiver('v6',imwidth/2,imwidth/2, -sqrt(1/k2)*sin(pi*(ang+90)/180),-sqrt(1/k2)*cos(pi*(ang+90)/180));

    print(strcat('-f',num2str(h1)),'-dpng','-r75',strcat(tempdir,'im1.png'));
    print(strcat('-f',num2str(h1)),'-dpng','-r75',strcat(tempdir,'im2.png'));

    ctfparams(1:18) = -1;
    return
end


clear imfftabs;