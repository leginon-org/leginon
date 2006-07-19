function varargout = leginon_ace_correct(varargin)
% For help use "doc leginon_ace_correct" 
%
% See also LEGINON_ACE_GUI.
%
% Copyright 2004 Satya P. Mallick 

% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
    'gui_Singleton',  gui_Singleton, ...
    'gui_OpeningFcn', @leginon_ace_correct_OpeningFcn, ...
    'gui_OutputFcn',  @leginon_ace_correct_OutputFcn, ...
    'gui_LayoutFcn',  [] , ...
    'gui_Callback',   []);
if nargin && ischar(varargin{1})
    gui_State.gui_Callback = str2func(varargin{1});
end

if nargout
    [varargout{1:nargout}] = gui_mainfcn(gui_State, varargin{:});
else
    gui_mainfcn(gui_State, varargin{:});
end
% End initialization code - DO NOT EDIT

% --- Executes just before leginon_ace_correct is made visible.
function leginon_ace_correct_OpeningFcn(hObject, eventdata, handles, varargin)

handles.output = hObject;

% Update handles structure
guidata(hObject, handles);

acecolor = [0.8 0.8 0.85];
set(handles.mainwindow,'Color',acecolor);
set(handles.title,'BackgroundColor',acecolor);
set(handles.expnamepanel,'BackgroundColor',acecolor);
set(handles.databasepanel,'BackgroundColor',acecolor);
set(handles.dirpanel,'BackgroundColor',acecolor);
set(handles.filetypepanel,'BackgroundColor',acecolor);
set(handles.leginon1,'BackgroundColor',acecolor);
set(handles.leginon2,'BackgroundColor',acecolor);
set(handles.otherfiletype,'BackgroundColor',acecolor);
set(handles.enr,'BackgroundColor',acecolor);
set(handles.msgboardpanel,'BackgroundColor',acecolor);
set(handles.msg,'BackgroundColor',acecolor);
set(handles.modes,'BackgroundColor',acecolor);
set(handles.mode1,'BackgroundColor',acecolor);
set(handles.mode2,'BackgroundColor',acecolor);
set(handles.correcttype,'BackgroundColor',acecolor);
set(handles.phamp,'BackgroundColor',acecolor);
set(handles.phonly,'BackgroundColor',acecolor);
set(handles.extpanel ,'BackgroundColor',acecolor);
set(handles.ext ,'BackgroundColor',acecolor);
set(handles.ext ,'Value',1);

axes(handles.logo1);
im = imread('ucsd_logo.bmp');
imshow(im);
axes(handles.logo2);
im = imread('tsri_logo.png');
imshow(im);

update_expdir(handles);


% --- Outputs from this function are returned to the command line.
function varargout = leginon_ace_correct_OutputFcn(hObject, eventdata, handles)
varargout{1} = handles.output;

function browse_Callback(hObject, eventdata, handles)
dirname = uigetdir;
set(handles.parentdir,'String',dirname);
update_text(handles);

% --- Executes on button press in Leginon1.
function leginon1_Callback(hObject, eventdata, handles)
update_filefilters(handles);
update_msg(handles);
load_listbox(handles);


function leginon1_CreateFcn(hObject, eventdata, handles)
set(hObject,'Value',0);

% --- Executes on button press in Leginon2.
function leginon2_Callback(hObject, eventdata, handles)
update_filefilters(handles);
update_msg(handles);
load_listbox(handles);

function leginon2_CreateFcn(hObject, eventdata, handles)
set(hObject,'Value',1);

function parentdir_Callback(hObject, eventdata, handles)
update_text(handles);

% --- Executes during object creation, after setting all properties.
function parentdir_CreateFcn(hObject, eventdata, handles)
set(hObject,'BackgroundColor','white');

function otherfiletype_Callback(hObject, eventdata, handles)
set(handles.enr,'Value',0);
set(handles.mode1,'Value',1);
set(handles.mode2,'Enable','off');
load_listbox(handles);
update_msg(handles);


% --- Executes on button press in enr.
function enr_Callback(hObject, eventdata, handles)
set(handles.otherfiletype,'Value',0);
set(handles.mode2,'Enable','on');
load_listbox(handles);
update_msg(handles);

function done_Callback(hObject, eventdata, handles)

set(handles.mainwindow,'Visible','off'); 
fprintf('Processing: Start\n'); 
pause(1); 
%%%%%%%%% User Setup
leginon1 = get(handles.leginon1,'Value');
expname =  get(handles.expname,'String');

indirname = get(handles.parentdir,'String');
if(indirname(end)~='/')
    indirname=strcat(indirname,'/'); 
end 
correctdir = get(handles.correctdir,'String');
if(correctdir(end)~='/')
    correctdir=strcat(correctdir,'/'); 
end 
enr_filter = get(handles.enr_filter,'String');
otherfiletype_filter = get(handles.otherfiletype_filter,'String');
expdir = get(handles.expdir,'String'); 
if(expdir(end)~='/')
    expdir=strcat(expdir,'/'); 
end 
phaseonly = get(handles.phonly,'Value');
outext = get(handles.ext,'Value');
if(outext==1)
    if(phaseonly)
        ext = get(handles.extph,'String');
    else
        ext = get(handles.extphamp,'String');
    end
end

if(get(handles.enr,'Value'))
    list = dir(strcat(expdir,enr_filter));
    if(get(handles.mode1,'Value'))
        md = 2; 
    elseif(get(handles.mode2,'Value'))
        md = 3; 
    else 
        md = 4;
    end 
else
    list = dir(strcat(expdir,otherfiletype_filter));
    md = 1; 
end
warning off all

mkdir(correctdir);


if(leginon1)
    
    conn = connect_db('leginon');
    query = strcat('select Prefix as Experiment, ImagePath as Path from ExperimentInfo where Prefix like "',expname,'"');
    curs = exec(conn, query);
    setdbprefs('DataReturnFormat','cellarray');
    result = fetch(curs);
    dirname = cell2mat(result.Data(2));
    dirname  = strcat(dirname,'/');

else
   
    conn = connect_db('dbemdata'); 
    query = strcat('select Name as Experiment, `image path` as Path from SessionData where name like "',expname,'"');
    curs = exec(conn, query);
    setdbprefs('DataReturnFormat','cellarray');
    result = fetch(curs);
    dirname = cell2mat(result.Data(2));
    dirname  = strcat(dirname,'/');
end

listindex = get(handles.filelistbox,'Value'); 
for i=listindex
    if(leginon1)
            query = strcat('select i.filename, p.defocus from ImageInfo i natural left join Presets p where i.format="mrc" and  i.filename like "',list(i).name,'%";') ;
            curs = exec(conn, query);
            setdbprefs('DataReturnFormat','cellarray');
            result = fetch(curs);
            dfenr = cell2mat(result.Data(2))*1e-9;
    else
            query = strcat('select scope.defocus from AcquisitionImageData a left join ScopeEMData scope on (scope.`DEF_id`=a.`REF|ScopeEMData|scope`) left join SessionData s1 on (s1.`DEF_id`=a.`REF|SessionData|session`) where a.`MRC|image` = "',list(i).name,'"');
            curs = exec(conn, query);
            setdbprefs('DataReturnFormat','numeric');
            result = fetch(curs);
            dfenr = result.Data;
    end

    if(md == 4)
        
        query = strcat('select children.`MRC|image` as focusimage from AcquisitionImageData a left join ScopeEMData scope on (scope.`DEF_id`=a.`REF|ScopeEMData|scope`) left join SessionData s1 on (s1.`DEF_id`=a.`REF|SessionData|session`) left join AcquisitionImageTargetData parent on (parent.`DEF_id`=a.`REF|AcquisitionImageTargetData|target`) left join AcquisitionImageTargetData targets on (targets.`REF|AcquisitionImageData|image`=parent.`REF|AcquisitionImageData|image`) left join AcquisitionImageData children on (targets.`DEF_id`=children.`REF|AcquisitionImageTargetData|target`) where children.`MRC|image` <> "NULL" and targets.type="focus" and a.`MRC|image` = "',list(i).name,'"');
        curs = exec(conn, query);
        setdbprefs('DataReturnFormat','cellarray');
        result = fetch(curs);
        focfile = cell2mat(result.Data);
        ldfile = strcat(indirname,focfile,'.mat');
        eval('load(ldfile)','err=1'); 
        err=0; 
        if(err==1)
            fprintf(strcat(ldfile,'Focus mat file corresponding to the near to focus file not found!\n')); 
            continue; 
        else 
            fprintf(strcat('Using shift defocus from Focus file:', ldfile,'\n'));  
        end 
        
    elseif(md == 3)
        
        ldfile = strcat(indirname,list(i).name(1:end-length(enr_filter)+1),otherfiletype_filter(2:end),'.mat'); 
        eval('load(ldfile)','err=1'); 
        err=0; 
        if(err==1)
            fprintf(strcat(ldfile,'Far from focus mat file corresponding to the near to focus file not found!\n')); 
            continue; 
        else
            fprintf(strcat('Using shift FFF defocus from file:', ldfile,'\n'));  
        end 

    else
        
        ldfile = strcat(indirname,list(i).name,'.mat'); 
        err=0; 
        eval('load(ldfile)','err=1;'); 
        if(err==1)
            fprintf(strcat(ldfile,': Mat file not found!\n')); 
            continue; 
        end 
    end

    
    if(ctfparams~=-1)
        if((abs(dforig)-mean(ctfparams(1:2)))>1e-6)
            ctfparams(1) = abs(dforig);
            ctfparams(2) = abs(dforig);
        end
        if(md==3 | md==4)
            ctfparams(1) = ctfparams(1) - abs(dforig-dfenr);
            ctfparams(2) = ctfparams(2) - abs(dforig-dfenr);
            
        end

        im = readmrc(strcat(dirname,list(i).name));
        tic
        im_correct = ctfcorrect(im,ctfparams,scopeparams,phaseonly);
        if(outext)
            writemrc(im_correct,strcat(correctdir,list(i).name,ext),'float');
        else
            writemrc(im_correct,strcat(correctdir,list(i).name),'float');
        end
        if(md==3)
            if(outext)
                fprintf('%s %f %f %f %f %f\n',strcat(list(i).name,ext),abs(dfenr)*1e6, abs(dforig)*1e6,ctfparams(1)*1e6,ctfparams(2)*1e6,toc);
            else
                fprintf('%s %f %f %f %f %f\n',list(i).name,abs(dfenr)*1e6, abs(dforig)*1e6,ctfparams(1)*1e6,ctfparams(2)*1e6,toc);
            end

        else
           
            if(outext)
                fprintf('%s %f %f %f %f %f\n',strcat(list(i).name,ext),abs(dfenr)*1e6,abs(dforig)*1e6,ctfparams(1)*1e6,ctfparams(2)*1e6,toc);
            else
                fprintf('%s %f %f %f %f %f\n',list(i).name,abs(dfenr)*1e6,abs(dforig)*1e6,ctfparams(1)*1e6,ctfparams(2)*1e6,toc);
            end
        end
    else 
        fprintf(strcat(list(i).name,': Mat files indicates unreliable CTF estimation')); 
    end
end


close(curs);
set(handles.mainwindow,'Visible','on'); 
fprintf('Processing: End\n'); 

function expname_Callback(hObject, eventdata, handles)
update_expdir(handles);
update_text(handles);
update_msg(handles);
%update_perlviewer(handles);
load_listbox(handles);

% --- Executes during object creation, after setting all properties.
function expname_CreateFcn(hObject, eventdata, handles)

function update_text(handles)
s1 = get(handles.expname,'String');


function update_msg(handles)
dirname = get(handles.expdir,'String');
if(length(dirname)>0)
    list_otherfiletype = dir(strcat(dirname,get(handles.otherfiletype_filter,'String')));
    list_enr = dir(strcat(dirname,get(handles.enr_filter,'String')));
    num_files = get(handles.otherfiletype,'Value')*length(list_otherfiletype) + get(handles.enr,'Value')*length(list_enr)  ;
    sel_files = get(handles.filelistbox,'Value');
    set(handles.msg,'String',{strcat(num2str(num_files),' files found.'); strcat(num2str(length(sel_files)),' files selected.')});
else
    set(handles.msg,'String','Invalid experiment name ');
end


% --- Executes on selection change in filelistbox.
function filelistbox_Callback(hObject, eventdata, handles)
update_msg(handles);

% --- Executes during object creation, after setting all properties.
function filelistbox_CreateFcn(hObject, eventdata, handles)
set(hObject,'BackgroundColor','white');
set(hObject,'Max',2,'Min',0);


function load_listbox(handles)
list = '' ;
dirname = get(handles.expdir,'String');
if(get(handles.otherfiletype,'Value'))
    filefilter = get(handles.otherfiletype_filter,'String');
    dir_struct = dir(strcat(dirname,filefilter));
    list = [list; {dir_struct.name}'];
else
    filefilter = get(handles.enr_filter,'String');
    dir_struct = dir(strcat(dirname,filefilter));
    list = [list; {dir_struct.name}'];
end

set(handles.filelistbox,'String',list,'Value',[])

function update_expdir(handles)
if(get(handles.leginon1,'Value'))
    
    conn = connect_db('leginon');
    query = strcat('select Prefix as Experiment, ImagePath as Path from ExperimentInfo where Prefix like "',get(handles.expname,'String'),'"');
    curs = exec(conn, query);
    setdbprefs('DataReturnFormat','cellarray');
    result = fetch(curs);
    if(length(result.Data)>1)
        dirname = cell2mat(result.Data(2));
        dirname  = strcat(dirname,'/');
        set(handles.expdir,'String',dirname);
    else
        set(handles.expdir,'String','');
    end
else
    conn = connect_db('dbemdata');
    query = strcat('select Name as Experiment, `image path` as Path from SessionData where name like "',get(handles.expname,'String'),'"');
    curs = exec(conn, query);
    
    setdbprefs('DataReturnFormat','cellarray');
    result = fetch(curs);
    if(length(result.Data)>1)
        dirname = cell2mat(result.Data(2));
        dirname  = strcat(dirname,'/');
        set(handles.expdir,'String',dirname);
    else
        set(handles.expdir,'String','');
    end

end

function otherfiletype_filter_Callback(hObject, eventdata, handles)
load_listbox(handles);
update_msg(handles);

% --- Executes during object creation, after setting all properties.
function otherfiletype_filter_CreateFcn(hObject, eventdata, handles)
set(hObject,'BackgroundColor','white');
set(hObject,'String','*efar.mrc');

function enr_filter_Callback(hObject, eventdata, handles)
load_listbox(handles);
update_msg(handles);

% --- Executes during object creation, after setting all properties.
function enr_filter_CreateFcn(hObject, eventdata, handles)
set(hObject,'BackgroundColor','white');
set(hObject,'String','*enr.mrc');


function update_filefilters(handles)
if(get(handles.leginon1,'Value') )
    set(handles.otherfiletype_filter,'String','*.*.*.002.mrc');
    set(handles.enr_filter,'String','*.*.*.001.mrc');
else
    set(handles.otherfiletype_filter,'String','*efar.mrc');
    set(handles.enr_filter,'String','*enr.mrc');
end


% --- Executes on button press in help.
function help_Callback(hObject, eventdata, handles)
doc leginon_ace_correct



function extph_Callback(hObject, eventdata, handles)

% --- Executes during object creation, after setting all properties.
function extph_CreateFcn(hObject, eventdata, handles)
set(hObject,'BackgroundColor','white');




function extphamp_Callback(hObject, eventdata, handles)

% --- Executes during object creation, after setting all properties.
function extphamp_CreateFcn(hObject, eventdata, handles)
set(hObject,'BackgroundColor','white');



% --- Executes on button press in ext.
function ext_Callback(hObject, eventdata, handles)
if(get(hObject,'Value'))
    set(handles.extph,'Enable','on');
    set(handles.extph ,'BackgroundColor','white');
    set(handles.extphamp,'Enable','on');
    set(handles.extphamp ,'BackgroundColor','white');
else
    set(handles.extph,'Enable','off');
    set(handles.extph ,'BackgroundColor',get(0,'defaultUicontrolBackgroundColor'));
    set(handles.extphamp,'Enable','off');
    set(handles.extphamp ,'BackgroundColor',get(0,'defaultUicontrolBackgroundColor'));
end



function correctdir_Callback(hObject, eventdata, handles)

% --- Executes during object creation, after setting all properties.
function correctdir_CreateFcn(hObject, eventdata, handles)
set(hObject,'BackgroundColor','white');


