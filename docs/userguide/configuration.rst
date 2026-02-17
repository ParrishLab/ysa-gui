.. _configuration:
Configuration
=============

Configuring Input Files
-----------------------
Downsampled and exported .brw files are ready to be loaded into YSA.

.. note::
  - The ysa-GUI functions best when input files are under 1 GB, depending on the RAM capabilities of your machine:
        - For devices with a RAM of 64 GB, optimal size is < ~1 GB
        - For devices with a RAM of 16 GB, optimal size is < ~500 MB
        - For devices with a RAM of 8 GB, optimal size is < ~300 MB
  - Since raw MEA files can be quite large >100 GB, we recommend using files of an hour or less that are downsampled signals around 100-300 Hz for optimal performance.
  - Spatially downsampling MEA files by selecting specific regions and channels in the MEA recording can also decrease file size
  - The maximum grid size compatible with the ysa-GUI is 64 x 64 (Any grid dimension that can fit within this maximum 64 x 64 grid size are compatible)
        - Most MEA systems have grid sizes of 64 x 64 or less, however if a larger grid size is used, a spatial downsampling that trims channels within the 64 x 64 size will render the data compatible with yse-GUI

   Code to downsample and export .brw MEA files can be found here: https://github.com/ParrishLab/MEA_file_Extract_Downsample.git


Data File (.h5 or other HDF5 extension, e.g. .brw)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To make an .h5 file compatible with YSA, follow these formatting specifications in configuring the data structure.

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

- Size: n  (where n is the number of channels available in the exported data)
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


Example Conversion Code: 3Brain & Utah Array File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The YSA GUI was originally designed to work on .h5 (.brw extension) exports of 3Brain MEA data.
We also took .mat data file output from Utah Array MEA recordings and converted them to a YSA-GUI
compatible format. The code to perform these conversions can be found at the following repo:

https://github.com/ParrishLab/MEA_file_Extract_Downsample.git
