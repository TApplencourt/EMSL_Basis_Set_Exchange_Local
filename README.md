EMSL_Basis_Set_Exchange_Local
=============================
[![Gitter](https://badges.gitter.im/Join Chat.svg)](https://gitter.im/TApplencourt/EMSL_Basis_Set_Exchange_Local?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Create of Local Copy of the famous [EMSL Basis Set Exchange](https://bse.pnl.gov/bse/portal) and use it easily with the API.

* Make a slight copy (40Mo Sqlite3 database) of the EMSL Basis Set Exchange website. Currently avalaible format are :
 * Currently available are : Gamess-us, Gaussian94 and NEWCHEM;
* API for scripting;  
* Quick local access without delay;
* Only need [Python](https://www.python.org/)

##Dependency
* Python >2.6

###### Optional
If you plan to download manually some database -not using the pre existing one- you need :
* [Request](http://docs.python-requests.org/en/latest/) python module. ```$pip install requests``` (do it in a virtual env or with sudo)

##Installation
* Download the git repertory (```$git clone https://github.com/TApplencourt/EMSL_Basis_Set_Exchange_Local.git``` for example)
* That all! You can now, use ```EMSL_api.py```

##Usage
```
EMSL Api.

Usage:
  EMSL_api.py list_basis  [--basis=<basis_name>...]
                          [--atom=<atom_name>...]
                          [--db_path=<db_path>]
                          [--average_mo_number]
  EMSL_api.py list_atoms  --basis=<basis_name>
                          [--db_path=<db_path>]
  EMSL_api.py get_basis_data --basis=<basis_name>
                                [--atom=<atom_name>...]
                                [--db_path=<db_path>]
                                [--with_l]
                                [(--save [--path=<path>])]
  EMSL_api.py list_formats
  EMSL_api.py create_db      --db_path=<db_path>
                             --format=<format>
                             [--no-contraction]
  EMSL_api.py (-h | --help)
  EMSL_api.py --version

Options:
  -h --help         Show this screen.
  --version         Show version.
  --no-contraction  Basis functions are not contracted

<db_path> is the path to the SQLite3 file containing the Basis sets.
By default is $EMSL_API_ROOT/db/Gausian_uk.db

Example of use:
    ./EMSL_api.py list_basis --atom Al --atom U
    ./EMSL_api.py list_basis --atom S --basis 'cc-pV*' --average_mo_number
    ./EMSL_api.py list_atoms --basis ANO-RCC
    ./EMSL_api.py get_basis_data --basis 3-21++G*
```
##Demonstration

![](http://fat.gfycat.com/WelcomePerkyChrysomelid.gif)

(For a beter quality see the [Source](https://asciinema.org/api/asciicasts/15380))

##To do
For now  we can only parse `Gamess-us, Gaussian94 and NEWCHEM` (Thanks to @mattbernst for Gaussian94 and NEWCHEM) basis set type file.

###I need more format!

I realy simple. Just read the few explanation bellow.

You just need to provide a function who will split the basis data who containt all the atoms in atom only.

Sommething like this:
```python
def parse_basis_data_gaussian94(data, name, description, elements, debug=True):
    """Parse the Gaussian94 basis data raw html to get a nice tuple.

    The data-pairs item is actually expected to be a 2 item list:
    [symbol, data]

    e.g. ["Ca", "#BASIS SET..."]

    N.B.: Currently ignores ECP data!

    @param data: raw HTML from BSE
    @type data : unicode
    @param name: basis set name
    @type name : str
    @param des: basis set description
    @type des : str
    @param elements: element symbols e.g. ['H', 'C', 'N', 'O', 'Cl']
    @type elements : list
    @return: (name, description, data-pairs)
    @rtype : tuple
    """
```

Then just add the function in `src.parser_handler.format_dict`. You are ready to go!

Feel free to fork/pull request. 

##Disclaimer
It'is not a official API. Use it with moderation.

In papers where you use the basis sets obtained from the Basis Set Exchange please site this:
>The Role of Databases in Support of Computational Chemistry Calculations
>
>>--<cite>Feller, D.; J. Comp. Chem., 17(13), 1571-1586, 1996.</cite>

>Basis Set Exchange: A Community Database for Computational Sciences
>
>>--<cite>Schuchardt, K.L., Didier, B.T., Elsethagen, T., Sun, L., Gurumoorthi, V., Chase, J., Li, J., and Windus ; T.L.
>>J. Chem. Inf. Model., 47(3), 1045-1052, 2007, doi:10.1021/ci600510j.</cite>

And don't forget: 
>These documents may be freely distributed and used for non-commercial, scientific and educational purposes. 
>-- <cite>http://www.pnl.gov/notices.asp</cite>

