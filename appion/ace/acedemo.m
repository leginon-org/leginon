function varargout = acedemo(varargin)
%
% DESCRIPTION: 
%     A GUI for Automated CTF Estimation.
%
% USAGE: 
%     Use "doc acedemo" for details. 
%
% Copyright 2004 Satya P. Mallick 

% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @acedemo_OpeningFcn, ...
                   'gui_OutputFcn',  @acedemo_OutputFcn, ...
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


% --- Executes just before acedemo is made visible.
function acedemo_OpeningFcn(hObject, eventdata, handles, varargin)
% This function has no output args, see OutputFcn.
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% varargin   command line arguments to acedemo (see VARARGIN)

% Choose default command line output for acedemo
handles.output = hObject;

% Update handles structure
guidata(hObject, handles);
acecolor = [0.8 0.8 0.85]; 
set(handles.mainwindow,'Color',acecolor); 
set(handles.fileanddirpanel,'BackgroundColor',acecolor); 
set(handles.micrograph,'BackgroundColor',acecolor); 
set(handles.kvtext,'BackgroundColor',acecolor); 
set(handles.pstext,'BackgroundColor',acecolor); 
set(handles.dforigtext,'BackgroundColor',acecolor); 
set(handles.cstext,'BackgroundColor',acecolor); 
set(handles.matfilesdirtext,'BackgroundColor',acecolor); 
set(handles.outimagedirtext,'BackgroundColor',acecolor); 
set(handles.tempfiledirtext,'BackgroundColor',acecolor);
set(handles.mediumpanel,'BackgroundColor',acecolor); 
set(handles.carbon,'BackgroundColor',acecolor); 
set(handles.ice,'BackgroundColor',acecolor); 
set(handles.advancedpanel,'BackgroundColor',acecolor); 
set(handles.carbonthtext,'BackgroundColor',acecolor); 
set(handles.icethtext,'BackgroundColor',acecolor); 
set(handles.carbonpftext,'BackgroundColor',acecolor); 
set(handles.icepftext,'BackgroundColor',acecolor); 
set(handles.edgepanel,'BackgroundColor',acecolor); 
set(handles.powerpanel,'BackgroundColor',acecolor); 
set(handles.avgpanel,'BackgroundColor',acecolor); 
set(handles.overlaptext,'BackgroundColor',acecolor); 
set(handles.fieldtext,'BackgroundColor',acecolor); 
set(handles.booleanpanel,'BackgroundColor',acecolor); 
set(handles.astig,'BackgroundColor',acecolor); 
set(handles.display,'BackgroundColor',acecolor); 
set(handles.title,'BackgroundColor',acecolor); 
set(handles.himagpanel,'BackgroundColor',acecolor); 
set(handles.resampletext,'BackgroundColor',acecolor); 
set(handles.drange,'BackgroundColor',acecolor); 
set(handles.browse,'BackgroundColor',acecolor); 

% axes(handles.logo1);
% im = imread('ucsd_logo.bmp');
% imshow(im);
% axes(handles.logo2);
% im = imread('tsri_logo.png');
% imshow(im);

% UIWAIT makes acedemo wait for user response (see UIRESUME)
% uiwait(handles.mainwindow);
% set(handles.display,'Value',0); 
%set(handles.mainwindow,'HandleVisibility','off'); 
% --- Outputs from this function are returned to the command line.
function varargout = acedemo_OutputFcn(hObject, eventdata, handles) 
% varargout  cell array for returning output args (see VARARGOUT);
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Get default command line output from handles structure
varargout{1} = handles.output;



%function filename_Callback(hObject, eventdata, handles)
% hObject    handle to filename (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of filename as text
%        str2double(get(hObject,'String')) returns contents of filename as a double


% --- Executes during object creation, after setting all properties.
%function filename_CreateFcn(hObject, eventdata, handles)
% hObject    handle to filename (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

%    set(hObject,'BackgroundColor','white');


% --- Executes on button press in browse.
function browse_Callback(hObject, eventdata, handles)
% hObject    handle to browse (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
dirname = uigetdir(); 
set(handles.dirname,'String',dirname,'Value',[]); 
load_listbox(handles);

function kv_Callback(hObject, eventdata, handles)
% hObject    handle to kv (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of kv as text
%        str2double(get(hObject,'String')) returns contents of kv as a double


% --- Executes during object creation, after setting all properties.
function kv_CreateFcn(hObject, eventdata, handles)
% hObject    handle to kv (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

    set(hObject,'BackgroundColor','white');



function ps_Callback(hObject, eventdata, handles)
% hObject    handle to ps (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of ps as text
%        str2double(get(hObject,'String')) returns contents of ps as a double


% --- Executes during object creation, after setting all properties.
function ps_CreateFcn(hObject, eventdata, handles)
% hObject    handle to ps (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

    set(hObject,'BackgroundColor','white');

function cs_Callback(hObject, eventdata, handles)
% hObject    handle to cs (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of cs as text
%        str2double(get(hObject,'String')) returns contents of cs as a double


% --- Executes during object creation, after setting all properties.
function cs_CreateFcn(hObject, eventdata, handles)
% hObject    handle to cs (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

    set(hObject,'BackgroundColor','white');




function matfilesdir_Callback(hObject, eventdata, handles)
% hObject    handle to matfilesdir (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of matfilesdir as text
%        str2double(get(hObject,'String')) returns contents of matfilesdir as a double


% --- Executes during object creation, after setting all properties.
function matfilesdir_CreateFcn(hObject, eventdata, handles)
% hObject    handle to matfilesdir (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

    set(hObject,'BackgroundColor','white');



function outimagedir_Callback(hObject, eventdata, handles)
% hObject    handle to outimagedir (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of outimagedir as text
%        str2double(get(hObject,'String')) returns contents of outimagedir as a double


% --- Executes during object creation, after setting all properties.
function outimagedir_CreateFcn(hObject, eventdata, handles)
% hObject    handle to outimagedir (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

    set(hObject,'BackgroundColor','white');



function tempdir_Callback(hObject, eventdata, handles)
% hObject    handle to tempdir (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of tempdir as text
%        str2double(get(hObject,'String')) returns contents of tempdir as a double


% --- Executes during object creation, after setting all properties.
function tempdir_CreateFcn(hObject, eventdata, handles)
% hObject    handle to tempdir (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

    set(hObject,'BackgroundColor','white');


% --- Executes on button press in astig.
function astig_Callback(hObject, eventdata, handles)
% hObject    handle to astig (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of astig


% --- Executes on button press in display.
function display_Callback(hObject, eventdata, handles)
% hObject    handle to display (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of display



function carbonedgeth_Callback(hObject, eventdata, handles)
% hObject    handle to carbonedgeth (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of carbonedgeth as text
%        str2double(get(hObject,'String')) returns contents of carbonedgeth as a double


% --- Executes during object creation, after setting all properties.
function carbonedgeth_CreateFcn(hObject, eventdata, handles)
% hObject    handle to carbonedgeth (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

    set(hObject,'BackgroundColor','white');



function iceedgeth_Callback(hObject, eventdata, handles)
% hObject    handle to iceedgeth (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of iceedgeth as text
%        str2double(get(hObject,'String')) returns contents of iceedgeth as a double


% --- Executes during object creation, after setting all properties.
function iceedgeth_CreateFcn(hObject, eventdata, handles)
% hObject    handle to iceedgeth (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

    set(hObject,'BackgroundColor','white');



function carbonpf_Callback(hObject, eventdata, handles)
% hObject    handle to carbonpf (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of carbonpf as text
%        str2double(get(hObject,'String')) returns contents of carbonpf as a double


% --- Executes during object creation, after setting all properties.
function carbonpf_CreateFcn(hObject, eventdata, handles)
% hObject    handle to carbonpf (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

    set(hObject,'BackgroundColor','white');



function icepf_Callback(hObject, eventdata, handles)
% hObject    handle to icepf (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of icepf as text
%        str2double(get(hObject,'String')) returns contents of icepf as a double


% --- Executes during object creation, after setting all properties.
function icepf_CreateFcn(hObject, eventdata, handles)
% hObject    handle to icepf (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

    set(hObject,'BackgroundColor','white');



function overlap_Callback(hObject, eventdata, handles)
% hObject    handle to overlap (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of overlap as text
%        str2double(get(hObject,'String')) returns contents of overlap as a double


% --- Executes during object creation, after setting all properties.
function overlap_CreateFcn(hObject, eventdata, handles)
% hObject    handle to overlap (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

    set(hObject,'BackgroundColor','white');


function fieldsize_Callback(hObject, eventdata, handles)
% hObject    handle to fieldsize (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of fieldsize as text
%        str2double(get(hObject,'String')) returns contents of fieldsize as a double


% --- Executes during object creation, after setting all properties.
function fieldsize_CreateFcn(hObject, eventdata, handles)
% hObject    handle to fieldsize (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

    set(hObject,'BackgroundColor','white');


% --- Executes on button press in process.
function process_Callback(hObject, eventdata, handles)
% hObject    handle to process (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

tempdir = get(handles.tempdir,'String'); 
if(tempdir(end)~='/')
    tempdir = strcat(tempdir,'/'); 
end

matfiles = get(handles.matfilesdir,'String'); 
if(matfiles(end)~='/')
    matfiles = strcat(matfiles,'/'); 
end

opimages = get(handles.outimagedir,'String'); 
if(opimages(end)~='/')
    opimages = strcat(opimages,'/'); 
end


V = str2num(get(handles.kv,'String'));
Cs = str2num(get(handles.cs,'String'));
ps = str2num(get(handles.ps,'String'));
 

stig = get(handles.astig,'Value'); 
medium_carbon = get(handles.carbon,'Value'); 
if(medium_carbon)
    medium = 'carbon'; 
else 
    medium = 'ice'; 
end 
display = get(handles.display,'Value'); 
dforig = str2num(get(handles.dforig,'String'))*1e-6; 
outfile = strcat(tempdir, 'logfile.txt'); 
%filename = get(handles.filename,'String'); 

edgethcarbon = str2num(get(handles.carbonedgeth,'String')); 
edgethice = str2num(get(handles.iceedgeth,'String')); 
pfcarbon = str2num(get(handles.carbonpf,'String')); 
pfice = str2num(get(handles.icepf,'String')); 
overlap = str2num(get(handles.overlap,'String')); 
fieldsize = str2num(get(handles.fieldsize,'String')); 
drange = get(handles.drange,'Value'); 
resamplefr = str2num(get(handles.resample,'String')); 

mkdir(tempdir); 
mkdir(matfiles); 
mkdir(opimages); 

setscopeparams(V,Cs,ps,tempdir);
scopeparams = [V,Cs,ps];

save(strcat(tempdir,'aceconfig.mat'),'edgethcarbon','edgethice','pfcarbon','pfice','overlap','fieldsize','resamplefr','drange'); 

set(handles.mainwindow,'Visible','off'); 
list_index = get(handles.filelist,'Value');
list = get(handles.filelist,'String');
dirname = get(handles.dirname,'String');
if(dirname(end)~='/')
    dirname = strcat(dirname,'/'); 
end 
pause(1); 
fprintf('Processing: Start\n'); 

for i=1:length(list_index) 
  
    filename = cell2mat(list(list_index(i)));
    if stig
        ctfparams = measureAstigmatism(strrep(filename, '.mrc', ''), strcat(dirname,filename),outfile, opimages, matfiles, 1,stig,medium,dforig,tempdir, resamplefr); 
    else
        ctfparams = ace(strcat(dirname,filename),outfile,1,stig,medium,dforig,tempdir); 
    end
    
    im1 = imread(strcat(tempdir,'im1.png'));
    im2 = imread(strcat(tempdir,'im2.png')); 
    imwrite(im1,strcat(opimages,filename,'1.png')); 
    imwrite(im2,strcat(opimages,filename,'2.png')); 
    save(strcat(matfiles,filename,'.mat'),'ctfparams','scopeparams');  
    if(display)
        figure;
        imshow(strcat(opimages,filename,'2.png'));
        figure;
        imshow(strcat(opimages,filename,'1.png'));
    end
end 
set(handles.mainwindow,'Visible','on');
fprintf('Processing: End\n'); 

function defocus_Callback(hObject, eventdata, handles)
% hObject    handle to defocus (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of defocus as text
%        str2double(get(hObject,'String')) returns contents of defocus as a double


% --- Executes during object creation, after setting all properties.
function defocus_CreateFcn(hObject, eventdata, handles)
% hObject    handle to defocus (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

    set(hObject,'BackgroundColor','white');


function dforig_Callback(hObject, eventdata, handles)
% hObject    handle to dforig (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of dforig as text
%        str2double(get(hObject,'String')) returns contents of dforig as a double


% --- Executes during object creation, after setting all properties.
function dforig_CreateFcn(hObject, eventdata, handles)
% hObject    handle to dforig (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

    set(hObject,'BackgroundColor','white');


% --- Executes on button press in carbon.
function carbon_Callback(hObject, eventdata, handles)
% hObject    handle to carbon (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of carbon


% --- Executes on button press in ice.
function ice_Callback(hObject, eventdata, handles)
% hObject    handle to ice (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of ice


% --- Executes on button press in help.
function help_Callback(hObject, eventdata, handles)
doc acedemo


% --- Executes on selection change in filelist.
function filelist_Callback(hObject, eventdata, handles)
% hObject    handle to filelist (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = get(hObject,'String') returns filelist contents as cell array
%        contents{get(hObject,'Value')} returns selected item from filelist


% --- Executes during object creation, after setting all properties.
function filelist_CreateFcn(hObject, eventdata, handles)
% hObject    handle to filelist (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: listbox controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

set(hObject,'BackgroundColor','white');


function load_listbox(handles)
list = '' ; 
dirname = get(handles.dirname,'String');
if(dirname(end)~='/')
    dirname = strcat(dirname,'/');
end 
filefilter = get(handles.filefilter,'String'); 
dir_struct = dir(strcat(dirname,filefilter));
list = {dir_struct.name}'; 
set(handles.filelist,'String',list);%,'Value',[])

function dirname_Callback(hObject, eventdata, handles)
% hObject    handle to dirname (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of dirname as text
%        str2double(get(hObject,'String')) returns contents of dirname as a double
dirname = get(handles.dirname,'String'); 
list_of_dirs = dir(dirname); 
ind = find([list_of_dirs(:).isdir]==1); 
fprintf('Listing directories in %s\n',dirname);
fprintf('%s\n',list_of_dirs(ind).name);
if(dirname(end)~='/')
    dirname = strcat(dirname,'/');
    set(handles.dirname,'String',dirname);
end 
load_listbox(handles); 

% --- Executes during object creation, after setting all properties.
function dirname_CreateFcn(hObject, eventdata, handles)
% hObject    handle to dirname (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

set(hObject,'BackgroundColor','white');



function filefilter_Callback(hObject, eventdata, handles)
% hObject    handle to filefilter (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of filefilter as text
%        str2double(get(hObject,'String')) returns contents of filefilter as a double

load_listbox(handles);
% --- Executes during object creation, after setting all properties.
function filefilter_CreateFcn(hObject, eventdata, handles)
% hObject    handle to filefilter (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

set(hObject,'BackgroundColor','white');


% --- Executes on button press in drange.
function drange_Callback(hObject, eventdata, handles)
% hObject    handle to drange (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of drange



function resample_Callback(hObject, eventdata, handles)
% hObject    handle to resample (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)



% --- Executes during object creation, after setting all properties.
function resample_CreateFcn(hObject, eventdata, handles)
% hObject    handle to resample (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called


set(hObject,'BackgroundColor','white');



