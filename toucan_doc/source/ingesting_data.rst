Ingesting data
==============

The tools necessary to add data to the database are in the file ingest.py in the ingest_data folder.

All needed is to call the function read_data() with 3 arguments:

- The file object, obtained using the open(<filename>, 'r') function.
- The ID number for the instrument used. 
- The name of the file (character sting).

An example of the code used is in the file main.py.
