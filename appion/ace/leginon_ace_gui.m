function varargout = leginon_ace_gui(varargin)
% For help use "doc leginon_ace_gui"
%
% Copyright 2004 Satya P. Mallick 

% Begin Initialization : DONOT EDIT 
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @leginon_ace_gui_OpeningFcn, ...
                   'gui_OutputFcn',  @leginon_ace_gui_OutputFcn, ...
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

% --- Executes just before leginon_ace_gui is made visible.
function leginon_ace_gui_OpeningFcn(hObject, eventdata, handles, varargin)
% This function has no output args, see OutputFcn.
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% varargin   command line arguments to leginon_ace_gui (see VARARGIN)

% Choose default command line output for leginon_ace_gui

handles.output = hObject;
% Update handles structure
guidata(hObject, handles);
acecolor = [0.8 0.8 0.85]; 
set(handles.mainwindow,'Color',acecolor); 
set(handles.uipanel3,'BackgroundColor',acecolor);
set(handles.title,'BackgroundColor',acecolor);
set(handles.expnamepanel,'BackgroundColor',acecolor);
set(handles.runnamepanel,'BackgroundColor',acecolor);
set(handles.databasepanel,'BackgroundColor',acecolor);
set(handles.dirpanel,'BackgroundColor',acecolor);
set(handles.booleanpanel,'BackgroundColor',acecolor);
set(handles.filetypepanel,'BackgroundColor',acecolor);
set(handles.viewertext,'BackgroundColor',acecolor);
set(handles.leginon1,'BackgroundColor',acecolor);
set(handles.leginon2,'BackgroundColor',acecolor);
set(handles.astig,'BackgroundColor',acecolor);
set(handles.display,'BackgroundColor',acecolor);
set(handles.write2db,'BackgroundColor',acecolor);
set(handles.foc,'BackgroundColor',acecolor);
set(handles.efar,'BackgroundColor',acecolor);
set(handles.enr,'BackgroundColor',acecolor);
set(handles.kvtext,'BackgroundColor',acecolor);
set(handles.pstext,'BackgroundColor',acecolor);
set(handles.matstr,'BackgroundColor',acecolor);
set(handles.parentdirstring,'BackgroundColor',acecolor);
set(handles.opimagesdirstring,'BackgroundColor',acecolor);
set(handles.tempdirstring,'BackgroundColor',acecolor);
set(handles.msgboardpanel,'BackgroundColor',acecolor);
set(handles.msg,'BackgroundColor',acecolor);
set(handles.advancedpanel,'BackgroundColor',acecolor);
set(handles.edgethpanel,'BackgroundColor',acecolor);
set(handles.powerfactorpanel,'BackgroundColor',acecolor);
set(handles.powercarbontext,'BackgroundColor',acecolor);
set(handles.powericetext,'BackgroundColor',acecolor);
set(handles.edgeicetext,'BackgroundColor',acecolor);
set(handles.edgecarbontext,'BackgroundColor',acecolor);
set(handles.fieldsizetext,'BackgroundColor',acecolor);
set(handles.overlaptext,'BackgroundColor',acecolor);
set(handles.himagpanel,'BackgroundColor',acecolor);
set(handles.resampletext,'BackgroundColor',acecolor);
set(handles.drange,'BackgroundColor',acecolor);
set(handles.autoselect,'BackgroundColor',acecolor);

axes(handles.logo1);
im = imread('ucsd_logo.bmp');
imshow(im);
axis off;
axes(handles.logo2);
im = imread('tsri_logo.png');
imshow(im);
axis off;
%set(handles.mainwindow,'HandleVisibility','off');
set(handles.display,'Value',1);
update_expdir(handles);
diary('session.log');
% UIWAIT makes leginon_ace_gui wait for user response (see UIRESUME)
% uiwait(handles.mainwindow);

% --- Outputs from this function are returned to the command line.
function varargout = leginon_ace_gui_OutputFcn(hObject, eventdata, handles)
% varargout  cell array for returning output args (see VARARGOUT);
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Get default command line output from handles structure
varargout{1} = handles.output;


% --- Executes on button press in Leginon1.
function leginon1_Callback(hObject, eventdata, handles)
% hObject    handle to Leginon1 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of Leginon1
update_filefilters(handles);
update_msg(handles);
load_listbox(handles);
set(handles.kv,'Enable','on');
set(handles.ps,'Enable','on');
set(handles.kv,'BackgroundColor','white');
set(handles.ps,'BackgroundColor','white');
function leginon1_CreateFcn(hObject, eventdata, handles)
set(hObject,'Value',0);

% --- Executes on button press in Leginon2.
function leginon2_Callback(hObject, eventdata, handles)
% hObject    handle to Leginon2 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% Hint: get(hObject,'Value') returns toggle state of Leginon2
update_filefilters(handles);
update_msg(handles);
load_listbox(handles);
set(handles.kv,'Enable','off');
set(handles.ps,'Enable','off');
set(handles.kv ,'BackgroundColor',get(0,'defaultUicontrolBackgroundColor'));
set(handles.ps ,'BackgroundColor',get(0,'defaultUicontrolBackgroundColor'));


function leginon2_CreateFcn(hObject, eventdata, handles)
set(hObject,'Value',1);
% --- Executes on button press in done.
%function done_Callback(hObject, eventdata, handles)
% hObject    handle to done (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)



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


set(hObject,'BackgroundColor',get(0,'defaultUicontrolBackgroundColor'));



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
%if ispc
%    set(hObject,'BackgroundColor','white');
%else
set(hObject,'BackgroundColor',get(0,'defaultUicontrolBackgroundColor'));
%end

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


% --- Executes on button press in write2db.
function write2db_Callback(hObject, eventdata, handles)
% hObject    handle to write2db (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of write2db



function parentdir_Callback(hObject, eventdata, handles)
% hObject    handle to parentdir (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of parentdir as text
%        str2double(get(hObject,'String')) returns contents of parentdir as a double
update_text(handles);


% --- Executes during object creation, after setting all properties.
function parentdir_CreateFcn(hObject, eventdata, handles)
% hObject    handle to parentdir (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
set(hObject,'BackgroundColor','white');


function matfilesdir_Callback(hObject, eventdata, handles)
  update_text(handles);

function matfilesdir_CreateFcn(hObject, eventdata, handles)
  set(hObject,'BackgroundColor','white');


function outimagedir_Callback(hObject, eventdata, handles)
  update_text(handles);
  update_perlviewer(handles);

function outimagedir_CreateFcn(hObject, eventdata, handles)
  set(hObject,'BackgroundColor','white');

% --- Executes on button press in foc.
function foc_Callback(hObject, eventdata, handles)
  load_listbox(handles);
  update_msg(handles);

% --- Executes on button press in efar.
function efar_Callback(hObject, eventdata, handles)
  load_listbox(handles);
  update_msg(handles);


% --- Executes on button press in enr.
function enr_Callback(hObject, eventdata, handles)
  load_listbox(handles);
  update_msg(handles);


function tempdir_Callback(hObject, eventdata, handles)
  update_text(handles);

% --- Executes during object creation, after setting all properties.
function tempdir_CreateFcn(hObject, eventdata, handles)
% hObject    handle to tempdir (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

set(hObject,'BackgroundColor','white');
% --- Executes on button press in browse.
function browse_Callback(hObject, eventdata, handles)
% hObject    handle to browse (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
dirname = uigetdir(get(handles.parentdir,'String'));
if(dirname~=0)
    set(handles.parentdir,'String',dirname);
    update_text(handles);
end


function done_Callback(hObject, eventdata, handles)

update_perlviewer(handles);
set(handles.mainwindow,'Visible','off');
pause(1);

if(get(handles.leginon1,'Value'))
    leginon1=1;
else
    leginon1=0;
end

if(leginon1)
    ps = str2num(get(handles.ps,'String'));
    kv = str2num(get(handles.kv,'String'));
else
    ps = 0;
    kv = 0;
end
expname = get(handles.expname,'String'); % Experiment name
runname = get(handles.runname,'String');
parentdir = get(handles.parentdirstring,'String'); % The directory where u want to store the results
typelist = [];
if(get(handles.foc,'Value'))
    typelist = 1;
end
if(get(handles.efar,'Value'))
    typelist = [typelist 2];
end
if(get(handles.enr,'Value'))
    typelist = [typelist 3];
end


display=get(handles.display,'Value');           % Set display to get images of different stages in opimages directory
stig = get(handles.astig,'Value');             % Set stig to do astigmatism calculation also.
matfiledir = get(handles.matfilesdir,'String'); % Directory for mat files
outimagedir = get(handles.outimagedir,'String'); % Derectory for output graphs
tempdir = get(handles.tempdirstring,'String');  % Temporary files directory. If running two copies of leginon_ace
% simulatenous from a single directory, use separate tempdirs so that
% temporary files donot conflict. For example: You
% might want to process the odd images and even images
% on two separate machines simultaneously.
write2db = get(handles.write2db,'value');
%%%%%%%% End User Setup

edgethcarbon = str2num(get(handles.edgecarbon,'String'));
edgethice = str2num(get(handles.edgeice,'String'));
pfcarbon = str2num(get(handles.powercarbon,'String'));
pfice = str2num(get(handles.powerice,'String'));
overlap = str2num(get(handles.overlap,'String'));
fieldsize = str2num(get(handles.fieldsize,'String'));
resamplefr = str2num(get(handles.resample,'String'));
drange = get(handles.drange,'Value');
mkdir(tempdir);
save(strcat(tempdir,'aceconfig.mat'),'edgethcarbon','edgethice','pfcarbon','pfice','overlap','fieldsize','resamplefr','drange');



fprintf('Processing: Start\n');
filefilters = [{get(handles.foc_filter,'String')};{get(handles.efar_filter,'String')};{get(handles.enr_filter,'String')}];
foc_file_index = [];
efar_file_index = [];
enr_file_index = [];

if(get(handles.foc,'Value') && ~get(handles.efar,'Value') && ~get(handles.enr,'Value'))
    foc_file_index = get(handles.filelistbox,'Value');
elseif(~get(handles.foc,'Value') && get(handles.efar,'Value') && ~get(handles.enr,'Value'))
    efar_file_index =get(handles.filelistbox,'Value');
elseif(~get(handles.foc,'Value') && ~get(handles.efar,'Value') && get(handles.enr,'Value'))
    enr_file_index =get(handles.filelistbox,'Value');
elseif(get(handles.foc,'Value') && get(handles.efar,'Value') && ~get(handles.enr,'Value'))
    nfocfiles = length(dir(strcat(get(handles.expdir,'String'),get(handles.foc_filter,'String'))));
    file_index = get(handles.filelistbox,'Value');
    ind = find(file_index <=nfocfiles);
    ind1 = find(file_index > nfocfiles);

    if(length(ind)>0)
        foc_file_index = file_index(ind);
    end
    if(length(ind1))
        efar_file_index = file_index(ind1)-nfocfiles;
    end
elseif(get(handles.foc,'Value') && ~get(handles.efar,'Value') && get(handles.enr,'Value'))
    nfocfiles = length(dir(strcat(get(handles.expdir,'String'),get(handles.foc_filter,'String'))));
    file_index = get(handles.filelistbox,'Value');
    ind = find(file_index <=nfocfiles);
    ind1 = find(file_index > nfocfiles);
    if(length(ind)>0)
        foc_file_index = file_index(ind);
    end
    if(length(ind1)>0)
        efar_file_index = file_index(ind1)-nfocfiles;
    end
elseif(~get(handles.foc,'Value') && get(handles.efar,'Value') && get(handles.enr,'Value'))
    nefarfiles = length(dir(strcat(get(handles.expdir,'String'),get(handles.efar_filter,'String'))));
    file_index = get(handles.filelistbox,'Value');
    ind = find(file_index <=nefarfiles);
    ind1 = find(file_index >nefarfiles);
    if(length(ind)>0)
        efar_file_index = file_index(ind);
    end
    if(length(ind1))
        enr_file_index = file_index(ind1)-nefarfiles;
    end
elseif(get(handles.foc,'Value') && get(handles.efar,'Value') && get(handles.enr,'Value'))
    nfocfiles = length(dir(strcat(get(handles.expdir,'String'),get(handles.foc_filter,'String'))));
    nefarfiles = length(dir(strcat(get(handles.expdir,'String'),get(handles.efar_filter,'String'))));
    file_index = get(handles.filelistbox,'Value');
    ind = find(file_index <=nfocfiles);
    ind1 = find(file_index <=nfocfiles+nefarfiles & file_index > nfocfiles);
    ind2 = find(file_index > nfocfiles+nefarfiles );

    if(length(ind)>0)
        foc_file_index = file_index(ind);
    end
    if(length(ind1)>0)
        efar_file_index = file_index(ind1)-nfocfiles;
    end
    if(length(ind2)>0)
        enr_file_index = file_index(ind2)-nfocfiles-nefarfiles;
    end

end
fileindices = {foc_file_index efar_file_index enr_file_index};

if(isempty(cell2mat(fileindices)))
    fprintf('Please select (highlight) atleast one file\n');
    fprintf('Left Click : Selects one file\n');
    fprintf('Left Click + CTRL : Selects multiple files\n');
    fprintf('Left Click + SHIFT : Selects multiple continuously listed files\n');
else
    leginon_ace(leginon1,ps,kv,expname,runname,parentdir,matfiledir,outimagedir,tempdir,typelist,display,stig,write2db,filefilters,fileindices);
end
fprintf('Processing: End\n');
set(handles.mainwindow,'Visible','on');
%clean up directory if no errors occurred
delete('session.log')
delete('perlviewer.pl')
rmdir(tempdir,'s')

function expname_Callback(hObject, eventdata, handles)
  update_expdir(handles);
  update_text(handles);
  update_msg(handles);
  update_perlviewer(handles);
  load_listbox(handles);


% --- Executes during object creation, after setting all properties.
function expname_CreateFcn(hObject, eventdata, handles)

function update_text(handles)
s0 = get(handles.parentdir,'String');
s1 = get(handles.expname,'String');
s2 = get(handles.matfilesdir,'String');
s3 = get(handles.outimagedir,'String');
s4 = get(handles.tempdir,'String');

set(handles.parentdirstring,'String',strcat(s0,'/'));
set(handles.matstr,'String',strcat(s0,'/',s1,'/',s2,'/'));
set(handles.opimagesdirstring,'String',strcat(s0,'/',s1,'/',s3,'/'));
set(handles.tempdirstring,'String',strcat('./',s4,'/'));


function update_msg(handles)
dirname = get(handles.expdir,'String');

if(length(dirname)>0)
    list_foc = dir(strcat(dirname,get(handles.foc_filter,'String')));
    list_efar = dir(strcat(dirname,get(handles.efar_filter,'String')));
    list_enr = dir(strcat(dirname,get(handles.enr_filter,'String')));
    num_files = get(handles.foc,'Value')*length(list_foc) +get(handles.efar,'Value')*length(list_efar) + get(handles.enr,'Value')*length(list_enr)  ;
    sel_files = get(handles.filelistbox,'Value');
    set(handles.msg,'String',{strcat(num2str(num_files),' files found.'); strcat(num2str(length(sel_files)),' files selected.')});
else
    set(handles.msg,'String','Invalid experiment name ');
end


% --- Executes on button press in view.
function view_Callback(hObject, eventdata, handles)
% hObject    handle to view (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
perl('perlviewer.pl');



function viewer_Callback(hObject, eventdata, handles)
% hObject    handle to viewer (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of viewer as text
%        str2double(get(hObject,'String')) returns contents of viewer as a double

update_perlviewer(handles);
% --- Executes during object creation, after setting all properties.
function viewer_CreateFcn(hObject, eventdata, handles)
% hObject    handle to viewer (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
set(hObject,'BackgroundColor','white');


function update_perlviewer(handles);
fid = fopen('perlviewer.pl','w');
fprintf(fid,'#!/usr/bin/perl\n');
fprintf(fid,strcat('system("',get(handles.viewer,'String'),'\t',get(handles.opimagesdirstring,'String'),'&")'));
fclose(fid);
!chmod 755 perlviewer.pl


% --- Executes on selection change in filelistbox.
function filelistbox_Callback(hObject, eventdata, handles)
% hObject    handle to filelistbox (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: contents = get(hObject,'String') returns filelistbox contents as cell array
%        contents{get(hObject,'Value')} returns selected item from filelistbox
update_msg(handles);

% --- Executes during object creation, after setting all properties.
function filelistbox_CreateFcn(hObject, eventdata, handles)
% hObject    handle to filelistbox (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until afterP all CreateFcns called

% Hint: listbox controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

set(hObject,'BackgroundColor','white');
set(hObject,'Max',2,'Min',0);


function load_listbox(handles)
list = '' ;
dirname = get(handles.expdir,'String');
if(get(handles.foc,'Value'))
    filefilter = get(handles.foc_filter,'String');
    dir_struct = dir(strcat(dirname,filefilter));
    list = {dir_struct.name}';
end
if(get(handles.efar,'Value'))
    filefilter = get(handles.efar_filter,'String');
    dir_struct = dir(strcat(dirname,filefilter));
    list = [list; {dir_struct.name}'];
end
if(get(handles.enr,'Value'))
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
        acename = strrep (dirname,'rawdata','ctf_ace');
        dirname = strcat(dirname,'/');
        set(handles.expdir,'String',dirname);
        set(handles.parentdir,'String',acename);
    else
        set(handles.expdir,'String','');
        set(handles.parentdir,'String','');
    end

end



function foc_filter_Callback(hObject, eventdata, handles)
% hObject    handle to foc_filter (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of foc_filter as text
%        str2double(get(hObject,'String')) returns contents of foc_filter as a double
load_listbox(handles);
update_msg(handles);
% --- Executes during object creation, after setting all properties.
function foc_filter_CreateFcn(hObject, eventdata, handles)
% hObject    handle to foc_filter (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
set(hObject,'BackgroundColor','white');
set(hObject,'String','*fc.mrc');



function efar_filter_Callback(hObject, eventdata, handles)
% hObject    handle to efar_filter (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of efar_filter as text
%        str2double(get(hObject,'String')) returns contents of efar_filter as a double
load_listbox(handles);
update_msg(handles);
% --- Executes during object creation, after setting all properties.
function efar_filter_CreateFcn(hObject, eventdata, handles)
% hObject    handle to efar_filter (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.


set(hObject,'BackgroundColor','white');
set(hObject,'String','*ef.mrc');



function enr_filter_Callback(hObject, eventdata, handles)
% hObject    handle to enr_filter (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of enr_filter as text
%        str2double(get(hObject,'String')) returns contents of enr_filter as a double
load_listbox(handles);
update_msg(handles);
% --- Executes during object creation, after setting all properties.
function enr_filter_CreateFcn(hObject, eventdata, handles)
% hObject    handle to enr_filter (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
set(hObject,'BackgroundColor','white');
set(hObject,'String','*en.mrc');


function update_filefilters(handles)
if(get(handles.leginon1,'Value') )
    set(handles.foc_filter,'String','*.*.*.foc.mrc');
    set(handles.efar_filter,'String','*.*.*.002.mrc');
    set(handles.enr_filter,'String','*.*.*.001.mrc');
else
    set(handles.foc_filter,'String','*fc.mrc');
    set(handles.efar_filter,'String','*ef.mrc');
    set(handles.enr_filter,'String','*en.mrc');
end



function edgecarbon_Callback(hObject, eventdata, handles)
% hObject    handle to edgecarbon (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edgecarbon as text
%        str2double(get(hObject,'String')) returns contents of edgecarbon as a double


% --- Executes during object creation, after setting all properties.
function edgecarbon_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edgecarbon (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

set(hObject,'BackgroundColor','white');
set(hObject,'String',0.8);


function edgeice_Callback(hObject, eventdata, handles)
% hObject    handle to edgeice (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edgeice as text
%        str2double(get(hObject,'String')) returns contents of edgeice as a double


% --- Executes during object creation, after setting all properties.
function edgeice_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edgeice (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

set(hObject,'BackgroundColor','white');
set(hObject,'String',0.6);



function powercarbon_Callback(hObject, eventdata, handles)
% hObject    handle to powercarbon (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of powercarbon as text
%        str2double(get(hObject,'String')) returns contents of powercarbon as a double


% --- Executes during object creation, after setting all properties.
function powercarbon_CreateFcn(hObject, eventdata, handles)
% hObject    handle to powercarbon (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

set(hObject,'BackgroundColor','white');
set(hObject,'String',0.9);



function powerice_Callback(hObject, eventdata, handles)
% hObject    handle to powerice (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of powerice as text
%        str2double(get(hObject,'String')) returns contents of powerice as a double


% --- Executes during object creation, after setting all properties.
function powerice_CreateFcn(hObject, eventdata, handles)
% hObject    handle to powerice (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

set(hObject,'BackgroundColor','white');
set(hObject,'String',0.3);


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


% --- Executes on button press in help.
function help_Callback(hObject, eventdata, handles)
% hObject    handle to help (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
doc leginon_ace_gui


% --- Executes on button press in report.
function report_Callback(hObject, eventdata, handles)
diary off
edit session.log;


% --- Executes during object creation, after setting all properties.
function runname_CreateFcn(hObject, eventdata, handles)
% hObject    handle to runname (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

set(hObject,'BackgroundColor','white');


% --- Executes on button press in database.
function database_Callback(hObject, eventdata, handles)
% hObject    handle to database (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
edit connect_db.m



function resample_Callback(hObject, eventdata, handles)
% hObject    handle to resample (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of resample as text
%        str2double(get(hObject,'String')) returns contents of resample as a double


% --- Executes during object creation, after setting all properties.
function resample_CreateFcn(hObject, eventdata, handles)
% hObject    handle to resample (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.

set(hObject,'BackgroundColor','white');


% --- Executes on button press in drange.
function drange_Callback(hObject, eventdata, handles)
% hObject    handle to drange (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of drange


% --- Executes on button press in autoselect.
function autoselect_Callback(hObject, eventdata, handles)

ind = [];
flist = get(handles.filelistbox,'String');
templist = dir(strcat(get(handles.matstr,'String'),'*.mat'));
mlist = strvcat(templist.name);
for i=1:length(flist)
    tempind = strmatch(strcat(flist{i},'.mat'),mlist,'exact');
    if(isempty(tempind))
        ind = [ind i];
    end
end
set(handles.filelistbox,'Value',ind);
update_msg(handles)

% --- Executes on button press in checkbox11.
function checkbox11_Callback(hObject, eventdata, handles)
% hObject    handle to checkbox11 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hint: get(hObject,'Value') returns toggle state of checkbox11



function edit24_Callback(hObject, eventdata, handles)
% hObject    handle to edit24 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Hints: get(hObject,'String') returns contents of edit24 as text
%        str2double(get(hObject,'String')) returns contents of edit24 as a double


% --- Executes during object creation, after setting all properties.
function edit24_CreateFcn(hObject, eventdata, handles)
% hObject    handle to edit24 (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    empty - handles not created until after all CreateFcns called

% Hint: edit controls usually have a white background on Windows.
%       See ISPC and COMPUTER.
if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end


