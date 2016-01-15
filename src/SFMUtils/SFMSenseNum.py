#! /usr/bin/python3

DESC = "This module checks an SFM lexicon's senses for proper sequential numbering. SFMTools.py uses it to do this check."
CHECK_ONLY = True  # setting this to false does one very specific kind of 'fix', and doesn't check the numbering.

import SFMTools as sfm
REC_MKR = 'lx'
SUBENTRY_MKRS = ['se','seco']

DEFAULT_FILE = 'lexicon.txt' # note: folders in file paths should use forward slashes; or, double backslashes work too, on Windows.
OUTFILE_EXT = '.renum.tmp.txt'  # used if no output file is specified
DEFAULT_FILE = 'D:/files/aa-synced/jon/otherproj/vandenberg-muna/Muna Dict 13 Dec 2012 utf8.txt'

def split_out_subentries(sfm_records, mkrs=['se']):
    ''' Chop entries more finely, so that each subentry is its own record for now.
    
    Fields at the end of a record will simply be treated as part of the last subentry, if one exists.
    (That's safe to do in this case.)
    '''
    recs = []
    
    for record in sfm_records:
        pieces = record.split(mkrs)
        for piece in pieces:
            recs.append(piece)

    return recs

def in_sequence(s1, s2, strict=True):
    '''Determine whether two sense numbers are in sequence. Note that 1.2, 2.1 is considered valid here, 
    unless strict is True, in which case you it will expect the more typical 1.2, 2, presumably followed by 2, 2.1 .
    An empty sense field is considered to mean "sense 1".
    '''
    if s1 == '': s1 = '1'
    if s2 == '': s2 = '1'
    s1a, s1b = s1,''
    s2a, s2b = s2,''

    if '.' in s1:
        s1a, s1b = s1.rsplit(sep='.', maxsplit=1)
    if '.' in s2:
        s2a, s2b = s2.rsplit(sep='.', maxsplit=1)

#    try:
#    except ValueError:
#        pass
#        return False

    try:
        if not (s1b or s2b): # neither number contains a dot
            if int(s1a) + 1 == int(s2a):  # (might crash)
                return True
            else:
                return False
        elif s1b and not s2b: # only the first number contains a dot
            return in_sequence(s1a, s2a)
        elif s2b and not s1b: # only the second number contains a dot; must therefore be 1
            return (s2b == '1')
        else: # both numbers contain a dot
            if s1a == s2a:
                return in_sequence(s1b, s2b)
            else:
                if strict:
                    return False
                return in_sequence(s1a, s2a) and (s2b == '1')

    except ValueError:
        return False

    return False # programming error; we fell through :)


def check_order(rec, mkrs=['sn'], strict=True):
    msg = ''
    vals = rec.find_values(mkrs)
    pass
    if len(vals) > 1:
        vals = ['0'] + vals # since we expect the first actual number to be 1
        for i in range(len(vals)-1):
            if not in_sequence(vals[i], vals[i+1], strict):
                msg += rec.as_string()
                break

    pass
    return msg

    
def number_subs(rec, mkrs=['sn']):
    ''' Copy and pre-pend to each subsense the number from its parent.
    
    Assumption: All subsenses to be numbered begin with a period. All that don't have any period can be treated as full senses here.'''
    
    parent_sn = ''
    r = rec.as_lists()
    full, empty = 0, 0 #counters
    for line in r:
        if line[0] in mkrs:
            sn = line[1].strip()
            if sn:
                full += 1
                if sn.startswith('.'):
                    if parent_sn:
                        line[1] = parent_sn + line[1]
                    else:
                        print('WARNING: Cannot number a subsense in (sub)entry {}. No parent sense exists.'.format(r[0]))
                elif '.' in sn:
                    pass # ignore already-numbered subsenses
                else:  # found a potential parent sense
                    if parent_sn:
                        if not in_sequence(parent_sn, sn):
                            print('WARNING: Numbers out of sequence for some parent senses in record {}'.format(r[0]))
                    else:
                        if not (int(sn) == 1):
                            print('WARNING: Start number of senses is not 1, in record {}'.format(r[0]))
                    parent_sn = sn
            else: # found an empty sense--cannot use for numbering
                empty += 1
                parent_sn = ''
    if full and empty:
        print('WARNING: MIX of empty and non-empty sn fields in a single entry or subentry: {}'.format(r[0]))

def unit_tests():
    # make sure in_sequence() correctly compares two sense numbers
    if not in_sequence('1', '1.1'): return False
    if not in_sequence('3.3', '4'): return False
    if not in_sequence('3.2.5', '3.2.6'): return False
    if not in_sequence('0', '1'): return False
    if not in_sequence('0', ''): return False

    if in_sequence('4', '3'): return False
    if in_sequence('1.2', '2.3'): return False
    if in_sequence('1.2.3', '2.3.4'): return False

    if not in_sequence('1.2', '2.1', strict=False): return False
    if in_sequence('1.2', '2.1', strict=True): return False
    
    return True

def check_sense_numbers(recs, mkrs=['sn'], strict=True):
    """ Does pure checking only (doesn't write to any output file). Called by SFMTools. """ 
    report = "  Checking numbering of (sub)senses (strict = {}). Only explicit sense fields {} will be checked, and only if found twice or more per word form.\n".format(strict, mkrs)

    count = 0
    recs = split_out_subentries(recs, SUBENTRY_MKRS)

    for record in recs:
        if check_order(record, mkrs):
            count += 1
            word = record.as_lists()[0]
            report += "  Probable misnumbering of (sub)senses for this {}: {}\n".format(word[0], word[1].strip())

    report += "  Found {} record(s) with apparent numbering problems.\n".format(count)
    return report

def main():
    print(DESC)
    
    if not unit_tests():
        print('Unit tests failed. Something is broken in this script; quitting.')
        return
    
    in_fname = DEFAULT_FILE
    out_fname = DEFAULT_FILE + OUTFILE_EXT
    print("Opening {}".format(in_fname))
    with open(in_fname, encoding='utf-8') as infile:
        sfm_records = sfm.SFMRecordReader(infile, REC_MKR)
        recs = split_out_subentries(sfm_records, SUBENTRY_MKRS)
        
        with open (out_fname, mode='w', encoding='utf-8') as outfile:
            if CHECK_ONLY:
                outfile.write("CHECK the numbering of the following records (a partial subset).\n\n")
            else:
                outfile.write(sfm_records.header)

            for record in recs:
                if CHECK_ONLY:
                    msg = check_order(record)
                    if msg:
                        outfile.write(msg)
                else:
                    number_subs(record)
                    outfile.write(record.as_string())
    print("Done. Saved to {}".format(out_fname))

if __name__ == '__main__':
    main()
