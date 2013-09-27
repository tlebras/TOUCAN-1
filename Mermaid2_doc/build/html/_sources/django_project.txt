Django project presentation
===========================

The Mermaid2 django project is made of 3 main directory :

- Mermaid2 : The main project directory containing the important file settings.py
- Mermaid2_db : Main application. Contains the files models.py and api.py. Those files are essentials to build the database and the Tastypie API.
- ingest_data : Directory containing the tools necessary to ingest data into the database.

Django files like urls.py, views.py, forms.py are not used at this point in the project. 
The web front-end is managed by the API.
All the tools needed to ingest data into the database are in the file ingest.py
