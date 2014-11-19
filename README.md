EMSL_Basis_Set_Exchange_Local
=============================

Create of Local Copy of the famous [EMSL Basis Set Exchange](https://bse.pnl.gov/bse/portal) and use it easily with the API.

* Make a slight copy (40Mo Sqlite3 database) of the EMSL Basis Set Exchange website (One database for all the basis set of one format);
* API for scripting ;  
* Quick local access without delay ;
* Only need [Python](https://www.python.org/) and [Request](http://docs.python-requests.org/en/latest/) module.

##Dependancy
* Python >2.6
* Request ```pip install requests```

##Installation
* Download the git (```$ git clone https://github.com/TApplencourt/EMSL_Basis_Set_Exchange_Local.git``` for example)
* ```cd``` into & run ```$ ./setup.py```
* ```source EMSL_api.rc```
* Done ! You can now, use ```EMSL_api.py``` or use all the python fonction inside ```./src```

##Usage
```
EMSL Api.

Usage:
  EMSL_api.py get_list_basis <db_path>
  EMSL_api.py get_list_elements <db_path> <basis_name>
  EMSL_api.py get_basis_data <db_path> <basis_name> <elts>...
  EMSL_api.py get_list_formats
  EMSL_api.py create_db <db_path> <format> [--no-contraction]
  EMSL_api.py (-h | --help)
  EMSL_api.py --version

Options:
  -h --help         Show this screen.
  --version         Show version.
  --no-contraction  Basis functions are not contracted

<db_path> is the path to the SQLite3 file containing the Basis sets.
```

##To do
For now  we can only parse Gaussian-US basis set type file. (Look at ```./src/EMSL_utility.py#EMSL_dump.basis_data_row_to_array```)

Feel free to fork/pull request. 

##Disclaimer
It'is not a official API. Use it with moderation.

>These documents may be freely distributed and used for non-commercial, scientific and educational purposes. 
>-- <cite>http://www.pnl.gov/notices.asp</cite>

