EMSL_Basis_Set_Exchange_Local
=============================

Create of Local Copy of the famous EMSL Basis Set Exhange. No more lag and a API for scripting.

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
