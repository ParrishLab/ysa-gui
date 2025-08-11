.. _configuration:
Configuration
=============

MATLAB
------
Certain features of the application require MATLAB to be installed on your system. 
If you have MATLAB installed in a non-standard location, you will need to manually adjust the location of your MATLAB installation to the default location:

- Windows: ``C:\Program Files\MATLAB\R2024a``
- MacOS: ``/Applications/MATLAB_R2024a.app``

.. note::
  Luckily, the application will automatically detect the MATLAB installation on your system if it is installed in the default location.

.. tip::
  If you cannot install MATLAB on your system, when using the application, make sure the ``Use C++`` option is checked before running an analysis.


Configuring Input Files
-----------------------
Downsampled and exported .brw files are ready to be loaded into YSA.

.. note::
  [Insert ChannelExtract GUI information and download link here]
  
  - Also explain more about exporting & downsampling: What types of downsampled material the GUI can process within an approximate time frame, and the caveat that the spatial resolution can handle up to 64x64 arrays, which is currently the highest spatial resolution offered on the MEA.


To make an .h5 file compatible with YSA, follow these formatting specifications.

Data File (.h5 or other HDF5 extension, e.g. .brw)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

/3BData
~~~~~~~

Raw (Raw dataset values in 1D vector)

- Size: 1xn
- Type: H5T_INTEGER

ChunkSize (Data are stored in chunks of this size)

- Size: 1xn
- Type: H5T_INTEGER


/3BRecInfo
~~~~~~~~~~


**/3BRecInfo/3BMeaChip**

Layout

- Size: ['NRows' 'NCols']
- Type: H5T_INTEGER

NCols

- Size: 1  Type: H5T_INTEGER

NRows

- Size: 1  Type: H5T_INTEGER



**/3BRecInfo/3BMeaStreams**

Chs

- Size: 143  (Number of channels with exported data)
- Type: H5T_COMPOUND  ['Row' 'Col'] (List of the [Row Col] locations of the stored channels)



**/3BRecInfo/3BRecVars**

BitDepth

- Size: 1
- Type: H5T_INTEGER

ExperimentType

- Size: 1
- Type: H5T_INTEGER

MaxVolt (mV)

- Size: 1
- Type: H5T_FLOAT

MinVolt (mV)

- Size: 1
- Type: H5T_FLOAT

NRecFrames (Total number of samples for each channel recorded)

- Size: 1
- Type: H5T_INTEGER

SamplingRate (Hz)

- Size: 1
- Type: H5T_FLOAT

SignalInversion (-1 or 1)

- Size: 1
- Type: H5T_FLOAT
