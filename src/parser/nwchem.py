#            _
# |\ |      /  |_   _  ._ _
# | \| \/\/ \_ | | (/_ | | |
#
import json


def extract_basis_nwchem(data, name):
    """Extract atomic orbital, charge density fitting, or exchange
    correlation functional basis data from a text region passed in as
    data. The charge density fitting and exchange correlation functional
    basis set data are employed for density functional calculations.

    @param data: text region containing basis set data
    @type data : str
    @param name: name of basis type: "ao basis", "cd basis", or "xc basis"
    @type name : str
    @return: per-element basis set chunks
    @rtype : list
    """

    begin_marker = """BASIS "{0}" PRINT""".format(name)
    end_marker = "END"

    # search for the basis set data begin marker
    # calling "upper" on data because original data has inconsistent
    # capitalization
    begin = data.upper().find(begin_marker.upper())
    end = data.upper().find(end_marker, begin)

    # No basis data found
    if begin == -1:
        return []

    trimmed = data[begin + len(begin_marker): end - len(end_marker)].strip()

    chunks = []
    lines = []

    # group lines of data delimited by #BASIS SET... into per-element chunks
    for line in trimmed.split("\n"):
        if line.upper().startswith("#BASIS SET"):
            if lines:
                chunks.append(lines)
            lines = [line]
        else:
            lines.append(line)

    # handle trailing chunk that is not followed by another #BASIS SET...
    if lines and (not chunks or lines != chunks[-1]):
        chunks.append(lines)

    # join lines back into solid text blocks
    chunks = ["\n".join(c) for c in chunks]
    return chunks


def extract_ecp_nwchem(data):
    """Extract the effective core potential basis data from a text region
    passed in as data.

    @param data: text region containing ECP data
    @type data : str
    @return: per-element effective core potential chunks
    @rtype : list
    """

    ecp_begin_mark = "ECP\n"
    ecp_end_mark = "END"
    ecp_begin = data.upper().find(ecp_begin_mark)
    ecp_end = data.upper().find(ecp_end_mark, ecp_begin)
    ecp_region = ""

    if ecp_begin > -1 and ecp_end > -1:
        ecp_region = data[
            ecp_begin +
            len(ecp_begin_mark): ecp_end -
            len(ecp_end_mark)].strip()

    # No ECP data, so return empty list
    else:
        return []

    chunks = []
    lines = []

    # group lines of data delimited by XX nelec YY into chunks, e.g.
    # "Zn nelec 18" begins a zinc ECP
    for line in ecp_region.split("\n"):
        if line.lower().find(" nelec ") > -1:
            if lines:
                chunks.append(lines)
            lines = [line]
        else:
            lines.append(line)

    # handle trailing chunk that is not followed by another XX nelec YY..
    if lines and (not chunks or lines != chunks[-1]):
        chunks.append(lines)

    # join lines back into solid text blocks
    chunks = ["\n".join(c) for c in chunks]
    return chunks


def unpack_nwchem_basis_block(data):
    """Unserialize a NWChem basis data block and extract components

    @param data: a JSON of basis set data, perhaps containing many types
    @type data : str
    @return: unpacked data
    @rtype : dict
    """

    unpacked = json.loads(data)
    return unpacked


def parse_basis_data_nwchem(data, name, description, elements, debug=True):
    """Parse the NWChem basis data raw html to get a nice tuple.

    The data-pairs item is actually expected to be a 2 item list:
    [symbol, data]

    e.g. ["Ca", "#BASIS SET..."]

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

    unused_elements = set([e.upper() for e in elements])

    def extract_symbol(txt):
        for sline in txt.split("\n"):
            if not sline.startswith("#"):
                try:
                    symbol = sline[:3].strip().split()[0]
                    return symbol
                except IndexError:
                    continue

        raise ValueError("Can't find element symbol in {0}".format(txt))

    ao_chunks = extract_basis_nwchem(data, "ao basis")
    cd_chunks = extract_basis_nwchem(data, "cd basis")
    xc_chunks = extract_basis_nwchem(data, "xc basis")
    ecp_chunks = extract_ecp_nwchem(data)

    if not any([ao_chunks, cd_chunks, xc_chunks, ecp_chunks]):
        str_ = "No basis set data found while attempting to process {0} ({1})"
        raise ValueError(str_.format(name, description))

    # Tag all used elements, whether from ordinary AO basis or ECP section
    for chunk in ao_chunks + cd_chunks + xc_chunks + ecp_chunks:
        try:
            symbol = extract_symbol(chunk)
            unused_elements.remove(symbol.upper())
        except KeyError:
            pass

    if unused_elements:
        msg = "Warning: elements {0} left over for {1}"
        print msg.format(list(unused_elements), name)

    # Form packed chunks, turn packed chunks into pairs
    used_elements = set()
    packed = {}

    for cgroup, gname in [(ao_chunks, "ao basis"), (cd_chunks, "cd basis"),
                          (xc_chunks, "xc basis"), (ecp_chunks, "ecp")]:
        for chunk in cgroup:
            symbol = extract_symbol(chunk)

            # Expand entry, e.g. add ecp data for Na after it has ao basis
            try:
                idx, ch = packed[symbol]
                ch[gname] = chunk
                chunk_dict = ch.copy()
            # Create fresh entry, e.g. add Na with initial ao basis
            except KeyError:
                chunk_dict = {gname: chunk}
                idx = len(used_elements)
                used_elements.add(symbol)

            packed[symbol] = (idx, chunk_dict)

    """
        for chunk in ao_chunks:
            symbol = extract_symbol(chunk)
            chunk_dict = {"ao basis" : chunk}
            idx = len(used_elements)
            used_elements.add(symbol)
            packed[symbol] = (idx, chunk_dict)

        for chunk in ecp_chunks:
            symbol = extract_symbol(chunk)
            #add ECP data if existing chunk, else create fresh chunk
            try:
                idx, ch = packed[symbol]
                ch["ecp"] = chunk
                chunk_dict = ch.copy()
            except KeyError:
                chunk_dict = {"ecp" : chunk}
                idx = len(used_elements)
                used_elements.add(symbol)
            packed[symbol] = (idx, chunk_dict)
        """

    values = sorted(packed.values())

    # Assign (Symbol, Serialized) to final pairs
    pairs = []
    for idx, chunk in values:
        symbol = extract_symbol(chunk.get("ao basis")
                                or chunk.get("cd basis")
                                or chunk.get("xc basis")
                                or chunk.get("ecp"))
        serialized = json.dumps(chunk)
        pairs.append([symbol, serialized])
    return [name, description, pairs]


def check_NWChem(str_type):
    """Check is the orbital type is handle by gamess"""

    assert len(str_type) == 1

    if str_type in "S P D".split():
        return True
    elif str_type > "I" or str_type in "K L M".split():
        raise BaseException
    else:
        return True
