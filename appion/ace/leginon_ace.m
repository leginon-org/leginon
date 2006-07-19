function leginon_ace(leginon1,ps,kv,expname,runname,parentdir,matfiledir,outimagedir,tempdir,typelist,display,stig,write2db,filefilters,fileindices)
% LEGINON_ACE : A wrapper around the core function ACE
% 
% The following variables need to be set
%
%
% 1) leginon1  : Set it to 1 if you are using leginon 1. Setting this
%                varibale would also mean that you have to manually 
%                give the values of Pixel Size(ps) and Kilovolts(kv). 
%                If leginon 1 is 0, the program assumes that the database 
%                type is leginon 2. ps and kv are automatically pulled 
%                out for leginon 2 database. 
%
% 2) expname   : Name of the experiment
% 
% 3) parentdir : Directory where you want the output. A directory 
%                with the experiment name would be created 
%                inside the parent directory. 
% 4) typelist  : A vector which tells the program to pull out files 
%                of specific file type.File type should be 1, 2 or 3 for 
%                focus, far from focus and near to focus respectively. 
%                for example: typelist =1 would process only focus images
%                typelist = [1,2] would process both focus and far from 
%                focus images. typelist = [1,2,3] would process all. 
% 5) display   : Set display to get images of different stages in 
%                opimages directory. For long experiments you should 
%                turn off the screen saver. display grabs images from 
%                the screen.      
% 6) stig      : Set it to 1 to turn on astigmatism calculation.
%
% 7) matfiledir: Directory for storing mat files 
%
% 8)outimagedir: Directory for storing output graphs. 
% 
% 9)tempdir    : Use two different tempdirs if two ace's are running
%                simultaenously from the same directory. 
%
% Note: The program assumes files are stored in leginon 1 or leginon 2 format 
%       For example in leginon 2 the focus images are of type *foc.mrc. 
%       However a user might have a file not conforming to leginon 1 or 
%       leginon 2. In that case the file filters should be changed to 
%       accomodate user's file. 

warning off all

if(parentdir(end)~='/')
  parentdir = strcat(parentdir,'/'); 
end 
if(outimagedir(end)~='/')
  outimagedir = strcat(outimagedir,'/'); 
end 
if(tempdir(end)~='/')
  tempdir = strcat(tempdir,'/'); 
end 
if(matfiledir(end)~='/')
  matfiledir = strcat(matfiledir,'/'); 
end 



outdir  = strcat(parentdir,expname,'/');
mkdir(parentdir); 
mkdir(parentdir,expname);
mkdir(outdir,matfiledir); 
mkdir(outdir,outimagedir); 
mkdir(tempdir); 
types = 0; 
while(types < length(typelist))
 types = types+1; 
 filetype = typelist(types); 

 switch filetype
  case 1  
    filelist = filefilters(1); 
    medium = 'carbon'; 
  case 2
    filelist = filefilters(2); 
    medium = 'ice'; 
  case 3
   filelist = filefilters(3); 
    medium = 'ice'; 
  otherwise 
    fprintf('File type should be 1, 2 or 3 for focus, fff and ntf respectively.'); 
    return; 
end 
filelist = cell2mat(filelist); 



if(leginon1) 
  conn = connect_db('leginon');
  query = strcat('select  Prefix as Experiment, ImagePath as Path, experimentId from ExperimentInfo where Prefix like "',expname,'"'); 
  curs = exec(conn, query);
  setdbprefs('DataReturnFormat','cellarray');
  result = fetch(curs);
  dirname = cell2mat(result.Data(2)); 
  expid = cell2mat(result.Data(3)); 
  dirname  = strcat(dirname,'/');
else 
  conn = connect_db('dbemdata');
  query = strcat('select  Name as Experiment, `image path` as Path, DEF_id as experimentId from SessionData where name like "',expname,'"');
  curs = exec(conn, query);
  setdbprefs('DataReturnFormat','cellarray');
  result = fetch(curs);
  dirname = cell2mat(result.Data(2)); 
  expid = cell2mat(result.Data(3));
  dirname  = strcat(dirname,'/');
end 

list = dir(strcat(dirname,filelist));

if(length(list)==0)
  fprintf('Invalid input directory\n'); 
  return
end 

for i= cell2mat(fileindices(typelist(types))); %449
  if(leginon1) 
    %Get Original Defocus
    query = strcat('select i.FilenameID as legimgId , i.filename, p.defocus from ImageInfo i natural left join Presets p where i.format="mrc" and  i.filename like "',list(i).name,'%";') ;
    curs = exec(conn, query);
    setdbprefs('DataReturnFormat','cellarray');
    result = fetch(curs);
    legimgId = cell2mat(result.Data(1));
    dforig = cell2mat(result.Data(3))*1e-9;  
  else 
    query = strcat('select pi.pixelsize from AcquisitionImageData a , PixelSizeCalibrationData pi left join ScopeEMData scope on (scope.`DEF_id`=a.`REF|ScopeEMData|scope`) left join SessionData s1 on (s1.`DEF_id`=a.`REF|SessionData|session`) where scope.`REF|InstrumentData|tem`=pi.`REF|InstrumentData|tem` and scope.magnification = pi.magnification and a.`MRC|image` = "',list(i).name,'"order by pi.`DEF_id` desc limit 1');
    
    %Get Pixel Size
    curs = exec(conn, query);
    setdbprefs('DataReturnFormat','numeric');
    result = fetch(curs);
    ps = result.Data*1e10;
   
    %Get KV 
    query = strcat('select a.`DEF_id` as legimgId, a.`REF|PresetData|preset` as legpresetId, `scope`.`defocus`, `scope`.`high tension` from AcquisitionImageData a left join ScopeEMData scope on (scope.`DEF_id`=a.`REF|ScopeEMData|scope`) left join SessionData s1 on (s1.`DEF_id`=a.`REF|SessionData|session`) where a.`MRC|image` = "',list(i).name,'"');
    curs = exec(conn, query);
    setdbprefs('DataReturnFormat','numeric');
    result = fetch(curs);
  
    legimgId = result.Data(1);
    legpresetId = result.Data(2);
    dforig = result.Data(3);
    kv = result.Data(4)/1e3;
  end 
 

  kv = kv(1); 
  ps = ps(1); 
  dforig = dforig(1); 
  
  setscopeparams(kv,2,ps,tempdir);  

  scopeparams = [kv,2,ps];
    
  imfinal = []; 
  ctfparams  = ace(strcat(dirname,list(i).name),strcat(outdir(1:end),expname,'.txt'),display,stig,medium,-dforig,tempdir);
  save(strcat(outdir,matfiledir,list(i).name,'.mat'),'ctfparams','scopeparams','dforig'); 
  if(display) 
  %  pause(1); 
  %  figflag(gcf,0);
    im1 = imread(strcat(tempdir,'im1.png')); 
    im2 = imread(strcat(tempdir,'im2.png')); 
    imwrite(im1,strcat(outdir,outimagedir,list(i).name,'1.png')); 
    imwrite(im2,strcat(outdir,outimagedir,list(i).name,'2.png')); 
  end 
 if(write2db) 
   dbctf( expid, runname, legimgId, legpresetId, list(i).name,abs(dforig),ctfparams,strcat(outdir,outimagedir,list(i).name,'1.png'),...
   strcat(outdir,outimagedir,list(i).name,'2.png'),strcat(outdir,matfiledir,list(i).name,'.mat')) 
 end 
end 
close(curs);
close(conn);
end 
