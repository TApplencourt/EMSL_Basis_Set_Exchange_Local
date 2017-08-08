#  __                            _
# /__  _.      _  _ o  _. ._    (_| |_|_
# \_| (_| |_| _> _> | (_| | |     |   |
#
from __future__ import print_function

import sys


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

    # Each basis set block starts and ends with ****. Find the region
    # containing all the basis blocks using the first and last ****.
    mark = "****"
    begin = data.find(mark)
    end = data.rfind(mark)

    if begin == -1 or end == -1:
        if debug:
            print(data)
        str_ = " No basis set data found while attempting to process {} ({})"
        raise ValueError(str_.format(name, description))

    trimmed = data[begin + len(mark): end - len(mark)].strip()
    chunks = []
    lines = []

    # group lines of data delimited by mark into per-element chunks
    for line in trimmed.split("\n"):
        if line.startswith(mark):
            if lines:
                chunks.append(lines)
            lines = [line]
        else:
            lines.append(line)

    # handle trailing chunk that is not followed by another basis set block
    # also remove the marker lines from the chunk itself
    if lines and (not chunks or lines != chunks[-1]):
        chunks.append(lines)

    # join lines back into solid text blocks
    chunks = ["\n".join([L for L in c if mark not in L]) for c in chunks]

    # check each block for element and assign symbols to final pairs
    pairs = []
    unused_elements = set([e.upper() for e in elements])
    for chunk in chunks:
        # get first 3 chars of first line in block
        symbol = chunk.split("\n")[0][:3].strip()
        try:
            unused_elements.remove(symbol.upper())
        except KeyError:
            if debug:
                msg = "Warning: already processed {}\n".format(symbol)
                sys.stderr.write(msg)
        pairs.append([symbol, chunk])

    if unused_elements:
        msg = "Warning: elements {} left over for {}".format(
            list(unused_elements),
            name)
        print(msg)

    return (name, description, pairs)
