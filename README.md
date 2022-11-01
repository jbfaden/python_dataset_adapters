# python_dataset_adapters
temporary place for code written for python dataset adapters project

This will be moved to the SpacePy project at some point.

# Needed libraries
SpacePy needs the CDF_LIB CDF library, because it uses native code.  The environment 
variable CDF_LIB should be set to the directory which contains the file "libcdf.so"
on Unix systems, Windows will be different.

Also a number of packages are needed.  Here they are:
* pip install hapiclient
* pip install spacepy
* pip install sunpy
* pip install h5netcdf
