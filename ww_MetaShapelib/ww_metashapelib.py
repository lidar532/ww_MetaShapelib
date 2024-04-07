# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/ww_MetaShapelib.ipynb.

# %% auto 0
__all__ = ['asof', 'MetaShapeReference', 'read_metashape_reference_file_into_dataframe',
           'read_metashape_reference_file_total_errors', 'MetaShape_ref_total_errors',
           'read_metashape_reference_dir_total_errors', 'MetaShape_Cal_Data', 'read_metashape_camera_cal_file',
           'read_openCV_camera_cal_file', 'metashape_cal_to_tsai']

# %% ../nbs/ww_MetaShapelib.ipynb 2
import datetime as              dt
import pandas   as              pd
import csv
import numpy    as              np
from   glob    import           glob
import re
import os
from   io    import             StringIO
from pathlib import             Path, PurePosixPath, PureWindowsPath
import xml.etree.ElementTree as ET

# %% ../nbs/ww_MetaShapelib.ipynb 5
# The asof data for this version of the library.
asof = '2024-0407-0052'

# %% ../nbs/ww_MetaShapelib.ipynb 17
class MetaShapeReference:
  def __init__(self, filename):
    self.filename      = filename
    self.df            = None
    self.meta          = None
    self.total_error   = None
    self.data          = None

# %% ../nbs/ww_MetaShapelib.ipynb 19
def read_metashape_reference_file_into_dataframe(
    filename           # Metashape reference filename to read.
    ) -> pd.DataFrame: # MetashapeReference class data structure.
  """
  Read a Metashape reference file into a MetashapeReference class
  and save the data in a Pandas dataframe.  Also save the filename, the
  metadata from the comment above the header line, the total_error as
  a Pandas Dataframe, and the contents of the specified file in string,
  in the returned data structure.
  """

  # Create the Matashape data structure, and save the filename in it.
  ref = MetaShapeReference( filename )

  # Extract the root filename
  ref.root_filename = PurePosixPath(filename).name

  # Read the file into a list of lines. so we can get rid of the "#" at the start
  # of the header line.
  with open(filename, 'r') as f:
    data = f.readlines()

  # Save the whole thing for possible debugging.
  ref.data = data

  # Save the meta data in the data structure in case the user wants it.
  ref.meta = data[0]

  # Get rid of the "#" at the start of the header line.
  if data[1][0:6] == '#Label':
    data[1] = data[1][1:]

  # Convert the list to a string
  ds = ''.join( data )

  # Read the string into a Pandas dataframe and store in the data structure.
  ref.df = pd.read_csv( StringIO(ds), comment='#')

  # Read the last line of the file into a Pandas dataframe and store in the data structure.
  # This line has the total error for several columns.
  ref.total_error = pd.read_csv( StringIO( data[-1] ), names=ref.df.columns ).dropna(axis=1)
  ref.total_error.replace( to_replace="#Total error", value=ref.root_filename, inplace=True )

  # Return the data structure.
  return ref

# %% ../nbs/ww_MetaShapelib.ipynb 26
def read_metashape_reference_file_total_errors( 
    filename:str   # Filename of a MetaShape reference file. 
) ->object:        # Pandas dataframe containing the entries from the `Total Error` line  in the file.
  """
  Reads a `MetaShape` reference file into a Pandas Dataframe.
  """
  df = read_metashape_reference_file_into_dataframe( filename )
  s = df.df['Label'][0].split('.')[0]
  dtime = dt.datetime.strptime(s, '%Y%m%d-%H%M%S')
  df.total_error['datetime'] = dtime
  return df.total_error

# %% ../nbs/ww_MetaShapelib.ipynb 31
class MetaShape_ref_total_errors:
  """
  This class is populated with the `Total Error` values from the Agisoft MetaShape reference export file.  It 
  is populated by the `read_metashape_reference_dir_total_errors()` function. Once populated it will 
  containt the path name `self.path` of the directory where the reference files are located, and a Pandas
  Dataframe `self.df` which contains the actual data from the `Total Errors`.
  """
  def __init__(self):
    self.path   = None
    self.df     = None

# %% ../nbs/ww_MetaShapelib.ipynb 33
def read_metashape_reference_dir_total_errors(
    dir_path:str,         # Path to MetaShape reference data files.
    mask:str='*-ref.txt'  # Mask to select the reference files.
    ) -> object:          # Class with path and dataframe attributes
  """
  Reads all MetaShape files matching `mask` in the specified `path`.  The `Total Error`
  from each file is extracted and loaded into a row in a Pandas Dataframe which is 
  returned to the user for analysis.  
  """
  df = pd.DataFrame()
  rv = MetaShape_ref_total_errors()
  rv.path = dir_path
  for f in glob(f'{dir_path}/{mask}'):
    dfn = read_metashape_reference_file_total_errors( f )
    df = pd.concat( [df, dfn] )
  v = df.pop('datetime')            # Move 'datetime' to be the second column
  df.insert(1, 'datetime', v)
  df.reset_index(drop=True, inplace=True)
  rv.df = df
  return rv

# %% ../nbs/ww_MetaShapelib.ipynb 39
class MetaShape_Cal_Data():
  def __init__(self):
    self.filename   = None
    self.datetime   = None
    self.projection = None
    self.units      = None
    self.pixel_size = None
    self.f          = None
    self.cx         = None
    self.cy         = None
    self.width      = None
    self.height     = None
    self.error      = None

# %% ../nbs/ww_MetaShapelib.ipynb 41
def read_metashape_camera_cal_file(
    filename,              # The MetaShape xml calibration file to read.
    pixel_size  = 5.5e-6,  # Pixel size in meters.
    units = 'pixels',      # Can be "pixels", "m", or "mm"
    rv = 'dict',           # R value. Can be "dict" or "df" or "class"
    debug=False            #
    ) -> dict:             #
  """
  Read a Metashape xml camera calibration file into a dictionary. Values
  can be converted from pixels to meters, or millimeters. Be sure to
  specify the pixel size in meters.
  """
  cd = MetaShape_Cal_Data()    # class to hold data.
  cal = { "filename" : Path(filename),   # filename.split("/")[-1],
         "pixel_size": pixel_size,
          "units"     : units
        }
  cd.filename   = Path(filename)
  cd.pixel_size = pixel_size
  cd.units      = units
  try:
    tree = ET.parse( filename )
    root = tree.getroot()
  except:
    cd.error = f"Et.parse( {filename} ) failed."
    return cd

  if debug:
    print(f'debug: root.tag:{root.tag}')
  if root.tag == 'calibration':
    for child in root:
      if debug:
        print(f'debug: {child.tag:10s} = {child.text}')
      if child.tag == 'projection':
        cd.projection = cal[child.tag] = child.text
      elif child.tag == 'date':
        cd.datetime = cal[child.tag] = dt.datetime.strptime( child.text,"%Y-%m-%dT%H:%M:%SZ" )
      else:
        cal[child.tag] = float(child.text)

    if units != 'pixels':
      if units   == 'm':
        scale = 1.0
      elif units == 'mm':
        scale = 1000.0

      cd.f      = cal['f' ]      * cd.pixel_size * scale
      cd.cx     = cal['cx']     * cd.pixel_size * scale
      cd.cy     = cal['cy']     * cd.pixel_size * scale
      cd.width  = cal['width']  * cd.pixel_size * scale
      cd.height = cal['height'] * cd.pixel_size * scale

      for k in ['f', 'cx', 'cy', 'width', 'height']:
        cal[k] = cal[k] * cal['pixel_size'] * scale

    if rv == 'class':
      cd.error = 'None'
      return cd
    elif rv == 'dict':
      return cal
    elif rv == 'df':
      df = pd.DataFrame( [ cal ] )
      return df
  else:
    cd.error = f"Not a MetaShape calibration file, lacks <calibration> tag."
    return cd

# %% ../nbs/ww_MetaShapelib.ipynb 52
class read_openCV_camera_cal_file:
  """
  Read an OpenCV Camera xml Calibration file.
  """
  def __init__(self, filename ):
    tree = ET.parse( filename )
    root = tree.getroot()
    tree.getroot()

    #self.filename = filename.split("/")[-1]
    filepath = Path( filename )
    self.filename  = filepath  #filepath.name
    self.datetime = root.findall('calibration_Time')[0].text
    self.image_Width = root.findall('image_Width')[0].text
    self.image_Height = root.findall('image_Height')[0].text

    self.Camera_Matrix_rows = int(root.findall('Camera_Matrix/rows')[0].text)
    self.Camera_Matrix_cols = int(root.findall('Camera_Matrix/cols')[0].text)
    self.Camera_Matrix_data = root.findall('Camera_Matrix/data')[0].text
    lst = root.findall('Camera_Matrix/data')[0].text.strip()
    x = re.split('[ \n]+', lst )
    self.Camera_Matrix_data = np.array(x, dtype=float)
    self.Camera_Matrix_data.reshape( self.Camera_Matrix_rows,self.Camera_Matrix_cols)

    self.Distortion_Coefficients_rows = int(root.findall('Distortion_Coefficients/rows')[0].text)
    self.Distortion_Coefficients_cols = int(root.findall('Distortion_Coefficients/cols')[0].text)
    lst = root.findall('Distortion_Coefficients/data')[0].text.strip()
    x = re.split('[ \n]+', lst )
    self.Distortion_Coefficients_data = np.array(x, dtype=float)

    # Add as a MetaShape class.
    self.metashape = MetaShape_Cal_Data()
    self.metashape.units        = 'pixels'
    self.metashape.pixel_size   = 5.5e-6
    self.metashape.projection   = 'frame'
    self.metashape.filename     = filepath
    self.metashape.datetime     = self.datetime
    self.metashape.width        = self.image_Width
    self.metashape.height       = self.image_Height
    self.metashape.f            = self.Camera_Matrix_data[0]
    self.metashape.cx           = self.Camera_Matrix_data[2]
    self.metashape.cy           = self.Camera_Matrix_data[5]
    self.metashape.k1           = self.Distortion_Coefficients_data[0]
    self.metashape.k2           = self.Distortion_Coefficients_data[1]
    self.metashape.k3           = self.Distortion_Coefficients_data[4]
    self.metashape.p1           = self.Distortion_Coefficients_data[3]
    self.metashape.p2           = self.Distortion_Coefficients_data[2]

# %% ../nbs/ww_MetaShapelib.ipynb 56
def metashape_cal_to_tsai( df,               # MetaShape cal dataframe.
                          save=True,         # True to save tasi to a file.
                           tsai_file='',     # An optional filename to write the tsai data too.
                           path=".",         # Path to save the file to.
                           return_str=False, # True if you want the tsai string returned.
                           debug=False       # True debug tis module.
                           ) -> str:         # Returns the entire tsai cal string.
  """
  Convert a `MetaShape` camera calibration Pandas Dataframe to a tsai file.
  """

  # Compute the tsai values from the Metashape cal dataframe.
  fu  = fv = df.f[0]
  cu  = df.width[0]  / 2 + 0.5 - 1.0 + df.cx[0]
  cv  = df.height[0] / 2 + 0.5 - 1.0 + df.cy[0]
  k1  = df.k1[0];   k2 = df.k2[0];   p1 = df.p1[0];   p2 = df.p2[0]

  # Generate tsai string.
  tsai_str = \
       "VERSION_4\nPINHOLE\n"\
      f"{fu = :15.12f}\n{fv = :15.12f}\n{cu = :15.12f}\n{cv = :15.12f}\n"\
      "u_direction = 1  0  0\n"\
      "v_direction = 0  1  0\n"\
      "w_direction = 0  0  1\n"\
      "C = 0 0 0\nR = 1 0 0 0 1 0 0 0 1\n"\
      "pitch = 1.0\nTSAI\n"\
      f"{k1 = :15.12f}\n{k2 = :15.12f}\n{p1 = :15.12f}\n{p2 = :15.12f}\n"

  # Save it to a file.  Generate the file name from the agisoft filename.
  if save:
    if tsai_file:
      tsai_fn = Path(path+"/"+tsai_file)
      if debug:
        print(f'Debug: {tsai_fn=}')
    else:
      # tsai_fn = df.filename[0].split(".")[0]+".tsai"
      tsai_fn = Path(path+"/"+df.filename[0].name).with_suffix('.tsai')
      if debug:
        print(f'Debug: {tsai_fn=}')
      # tsai_fn.with_suffix('.tsai')
    with open( tsai_fn, 'w') as tsai_file:
      tsai_file.write( tsai_str )

  if debug:
    print(f'debug: {tsai_str:s}')

  # Return the tsai string if return_str=True
  if return_str:
    return tsai_str
