function varargout = acedemo_correct(varargin)
%
% DESCRIPTION: 
%      A GUI for CTF correction. 
%
% USAGE: 
%     Use "doc acedemo_correct" for help in detail. 
%
% Copyright 2004-2005 Satya P. Mallick. 


% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
    'gui_Singleton',  gui_Singleton, ...
    'gui_OpeningFcn', @acedemo_correct_OpeningFcn, ...
    'gui_OutputFcn',  @acedemo_correct_OutputFcn, ...
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
function acedemo_correct_OpeningFcn(hObject, eventdata, handles, varargin)

handles.output = hObject;

% Update handles structure
guidata(hObject, handles);

acecolor = [0.8 0.8 0.85];
set(handles.mainwindow,'Color',acecolor);
set(handles.title,'BackgroundColor',acecolor);
set(handles.dirpanel,'BackgroundColor',acecolor);
set(handles.filepanel,'BackgroundColor',acecolor);
set(handles.mat_file_ext_str,'BackgroundColor',acecolor);
set(handles.input_file_ext_str,'BackgroundColor',acecolor);
set(handles.msgboardpanel,'BackgroundColor',acecolor);
set(handles.msg,'BackgroundColor',acecolor);
set(handles.correcttype,'BackgroundColor',acecolor);
set(handles.phamp,'BackgroundColor',acecolor);
set(handles.phonly,'BackgroundColor',acecolor);
set(handles.extpanel ,'BackgroundColor',acecolor);
set(handles.ext ,'BackgroundColor',acecolor);
set(handles.ext ,'Value',1);
set(handles.offsetpanel ,'BackgroundColor',acecolor);

% axes(handles.logo1);
% im = imread('ucsd_logo.bmp');
% imshow(im);
% axes(handles.logo2);
% im = imread('tsri_logo.png');
% imshow(im);

% --- Outputs from this function are returned to the command line.
function varargout = acedemo_correct_OutputFcn(hObject, eventdata, handles)
varargout{1} = handles.output;

function browse_Callback(hObject, eventdata, handles)
dirname = uigetdir;
if(dirname(end)~='/')
    dirname = strcat(dirname,'/'); 
end 

set(handles.matfile_dir,'String',dirname);



function mat_file_ext_Callback(hObject, eventdata, handles)
set(handles.input_file_ext_str,'Value',0);
set(handles.mode1,'Value',1);
set(handles.mode2,'Enable','off');
load_listbox(handles);
update_msg(handles);


% --- Executes on button press in input_file_ext_str.
function input_file_ext_str_Callback(hObject, eventdata, handles)
set(handles.mat_file_ext,'Value',0);
set(handles.mode2,'Enable','on');
load_listbox(handles);
update_msg(handles);

function done_Callback(hObject, eventdata, handles)

set(handles.mainwindow,'Visible','off'); 
fprintf('Processing: Start\n'); 
pause(1); 

phaseonly = get(handles.phonly,'Value');
outext = get(handles.ext,'Value');
if(outext==1)
    if(phaseonly)
        ext = get(handles.extph,'String');
    else
        ext = get(handles.extphamp,'String');
    end
else ext='';
end

% Directory names
inputdir = get(handles.inputdir,'String'); 
matfile_dir = get(handles.matfile_dir,'String'); 
correctdir = get(handles.correctdir,'String'); 
% Make the directory to store corrected images. 
mkdir(correctdir); 

% File Filters
input_file_filter = get(handles.input_file_filter,'String'); 
mat_file_filter = get(handles.mat_file_filter,'String'); 

% File list and indices
listindex = get(handles.filelistbox,'Value'); 
list = dir(strcat(inputdir,input_file_filter));

% Defocus offset 
dfoffset = str2num(get(handles.offset,'String'))*1e-6;

for i=1:length(listindex) 
    % Load the corresponding mat file 
    filename = list(listindex(i)).name;
    filename = filename(1:end-length(input_file_filter)+1);
    filename = strcat(filename,mat_file_filter(2:end));
    ldfile = strcat(matfile_dir,filename);
    % Check if the corresponding mat file exists. 
    err=0; 
    eval('load(ldfile)','err=1;');
    
    if(err==1)
        fprintf(strcat(ldfile,': Matfile not found!\n'));
        continue;
    end
    
    load(ldfile);

    if(ctfparams~=-1) % Check if the estimation was successful
        ctfparams(1:2) = ctfparams(1:2) + dfoffset; % Account for defocus offset
        im = readmrc(strcat(inputdir,list(listindex(i)).name)); % Read the file to correct
        im_correct = ctfcorrect(im,ctfparams,scopeparams,phaseonly);
         fprintf('%s %f %f \n',strcat(list(listindex(i)).name,ext), ... 
             ctfparams(1)*1e6,ctfparams(2)*1e6);
         if(outext) % Write corrected file
             writemrc(im_correct,strcat(correctdir,list(listindex(i)).name,ext),'float');
         else
             writemrc(im_correct,strcat(correctdir,list(listindex(i)).name),'float');
         end
     end
     
     
end 

set(handles.mainwindow,'Visible','on'); 
fprintf('Processing: End\n'); 


function update_msg(handles)
dirname = get(handles.expdir,'String');
if(length(dirname)>0)
    list_otherfiletype = dir(strcat(dirname,get(handles.mat_file_ext_filter,'String')));
    list_enr = dir(strcat(dirname,get(handles.input_file_ext_str_filter,'String')));
    num_files = get(handles.mat_file_ext,'Value')*length(list_otherfiletype) + get(handles.input_file_ext_str,'Value')*length(list_enr)  ;
    sel_files = get(handles.filelistbox,'Value');
    set(handles.msg,'String',{strcat(num2str(num_files),' files found.'); strcat(num2str(length(sel_files)),' files selected.')});
else
    set(handles.msg,'String','Invalid experiment name ');
end


% --- Executes on selection change in filelistbox.
function filelistbox_Callback(hObject, eventdata, handles)


% --- Executes during object creation, after setting all properties.
function filelistbox_CreateFcn(hObject, eventdata, handles)
set(hObject,'BackgroundColor','white');
set(hObject,'Max',2,'Min',0);


function load_listbox(handles)
list = '' ;
dirname = get(handles.inputdir,'String');
filefilter = get(handles.input_file_filter,'String');
dir_struct = dir(strcat(dirname,filefilter));
list = [{dir_struct.name}'];
set(handles.filelistbox,'String',list,'Value',[])


% --- Executes during object creation, after setting all properties.
function mat_file_ext_filter_CreateFcn(hObject, eventdata, handles)
set(hObject,'BackgroundColor','white');
set(hObject,'String','*efar.mrc');

function input_file_ext_str_filter_Callback(hObject, eventdata, handles)
load_listbox(handles);
update_msg(handles);

% --- Executes during object creation, after setting all properties.
function input_file_ext_str_filter_CreateFcn(hObject, eventdata, handles)
set(hObject,'BackgroundColor','white');
set(hObject,'String','*enr.mrc');




% --- Executes on button press in help.
function help_Callback(hObject, eventdata, handles)
doc acedemo_correct



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
correctdir = get(handles.correctdir,'String'); 
if(correctdir(end)~='/')
    correctdir = strcat(correctdir,'/'); 
end 
set(handles.correctdir,'String',correctdir);

% --- Executes during object creation, after setting all properties.
function correctdir_CreateFcn(hObject, eventdata, handles)
set(hObject,'BackgroundColor','white');



function inputdir_Callback(hObject, eventdata, handles)
% hObject    handle to inputdir (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
inputdir = get(handles.inputdir,'String'); 
if(inputdir(end)~='/')
    inputdir = strcat(inputdir,'/'); 
end 
set(handles.inputdir,'String',inputdir);
% Hints: get(hObject,'String') returns contents of inputdir as text
%        str2double(get(hObject,'String')) returns contents of inputdir as a double
load_listbox(handles);

% --- Executes during object creation, after setting all properties.
function inputdir_CreateFcn(hObject, eventdata, handles)
% hObject    handle to inputdir (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

set(hObject,'BackgroundColor','white');


% --- Executes on button press in browseinputdir.
function browseinputdir_Callback(hObject, eventdata, handles)
% hObject    handle to browseinputdir (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

dirname = uigetdir;
set(handles.inputdir,'String', dirname);
load_listbox(handles);


function input_file_filter_Callback(hObject, eventdata, handles)
% hObject    handle to input_file_filter (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of input_file_filter as text
%        str2double(get(hObject,'String')) returns contents of input_file_filter as a double

load_listbox(handles);
% --- Executes during object creation, after setting all properties.
function input_file_filter_CreateFcn(hObject, eventdata, handles)
% hObject    handle to input_file_filter (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

set(hObject,'BackgroundColor','white');




function matfile_dir_Callback(hObject, eventdata, handles)
% hObject    handle to matfile_dir (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of matfile_dir as text
%        str2double(get(hObject,'String')) returns contents of matfile_dir as a double
matfile_dir = get(handles.matfile_dir,'String'); 
if(matfile_dir(end)~='/')
    matfile_dir = strcat(matfile_dir,'/'); 
end 
set(handles.matfile_dir,'String',matfile_dir);


% --- Executes during object creation, after setting all properties.
function matfile_dir_CreateFcn(hObject, eventdata, handles)
% hObject    handle to matfile_dir (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

    set(hObject,'BackgroundColor','white');



function mat_file_filter_Callback(hObject, eventdata, handles)
% hObject    handle to mat_file_filter (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of mat_file_filter as text
%        str2double(get(hObject,'String')) returns contents of mat_file_filter as a double
load_listbox(handles);

% --- Executes during object creation, after setting all properties.
function mat_file_filter_CreateFcn(hObject, eventdata, handles)
% hObject    handle to mat_file_filter (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

 set(hObject,'BackgroundColor','white');



function offset_Callback(hObject, eventdata, handles)
% hObject    handle to offset (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of offset as text
%        str2double(get(hObject,'String')) returns contents of offset as a double


% --- Executes during object creation, after setting all properties.
function offset_CreateFcn(hObject, eventdata, handles)
% hObject    handle to offset (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

    set(hObject,'BackgroundColor','white');


function dirname = complete_dirname(dirname)
 if(dirname(end) ~='/')
     dirname = strcat(dirname,'/'); 
 end 
 

