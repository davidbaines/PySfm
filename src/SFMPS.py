#! /usr/bin/python3

'''
To get standard MDF to import into FLEx, you either need to:
- infer: make sure each \ps has only one child \sn, by copying \ps as needed. Or,
- push: move/copy \ps down below each of its children
You can choose either algorithm by setting the ACTION constant below.
If your file is inconsistent (i.e. partially pushed), you can do a:
- selective push, a push which only affects entries/subentries where a \ps occurs 
before the first \sn.
'''

from SFMUtils import SFMTools as sfm
import argparse

DEFAULT_FILE = 'lexicon.txt' # note: folders in file paths should use forward slashes; or, double backslashes work too, on Windows.
OUTFILE_EXT = '.tmp.txt'  # used if no output file is specified

# Important constants
REC_MKR = 'lx'
#SE = 'se'
PS = 'ps'
SN = 'sn'
EMPTY_PS = 'unknown\n'   # once LT-10739 is fixed, this could just be '\n'
EMPTY_SN = '1\n'  # can just be '\n' but if subsenses are involved, explicitly numbering, and then checking the numbers, is better.

# Constants used just by the 'push' and 'infer' functions
WORD_MKRS = 'lx', 'se'
EDGES = ('se', 'ps') # fields like dt could be thrown in just for good measure
SES = ('se')

# Temporary overrides for the Muna lexicon
#EDGES = ('se', 'ps', 'seco')
#SES = ('se', 'seco')

# Other
HELP_COPY = "Copy ps, or undo push (recommended and default): Where ps is found first (not preceded by sn), will copy ps down above subsequent sn fields. Will infer an 'empty' ps where missing. If sn is found above ps, will invert them ('undo' push)."
HELP_UNDO_PUSH = "'Undo' push ps down: Wherever sn is found first (not preceded by ps), will either move the ps up or insert an 'empty' ps."
HELP_PUSH = "Push ps down below sn (produces non-standard MDF), much like Solid's quick fix. Where ps is found first (not preceded by sn), will push/copy ps down below subsequent sn fields. If there are none, will instead add an empty sn above the ps."
DEBUG_LEVEL = 1

def debug(msg):
    if DEBUG_LEVEL > 1:
        print(msg)

def get_args():
    ''' Parse any command line arguments (all are optional). '''
    parser = argparse.ArgumentParser(description='Check/restructure {} and {} in an SFM file. WARNING: back up first, and check its work! (Diff tools like Winmerge or KDiff3 help.). For more info, open the .py file in a text editor and read the comments.'.format(PS, SN))
    parser.add_argument('infile', default=DEFAULT_FILE, nargs='?', help='the input file (default: {})'.format(DEFAULT_FILE))
    parser.add_argument('outfile', nargs='?', help='the output file to save to (default: infile plus {})'.format(OUTFILE_EXT))
    parser.add_argument('-c', '--copyps', dest='copyps', default=False, action='store_const', const=True, 
                        help=HELP_COPY + ' Causes -p or -u to be ignored.')
    parser.add_argument('-u', '--undopush', dest='undopush', default=False, action='store_const', const=True, 
                        help=HELP_UNDO_PUSH + ' Causes -p to be ignored.')
    parser.add_argument('-p', '--pushpsdown', dest='pushpsdown', default=False, action='store_const', const=True, 
                        help=HELP_PUSH)
    return vars(parser.parse_args())


def push_ps_down (record):
    ''' If non-empty ps occurs above one or more sn fields within scope, copy it down and then delete it.
    
    If no sn lines are found below the ps line, insert an sn immediately above it. 
    (Formerly, when finished, it would delete ps if it's empty. That would help simplify messy data, 
    but it's not a good idea yet due to this FLEx issue: LT-10739) 
    '''

    rec = record.as_lists()
    offset = 0
    lxval = rec[0][1].strip()
    lxval = sfm.ascii(lxval) #so non-unicode consoles won't crash
    
    # find each occurrence of ps and deal with it
    pss = record.find(PS, 1)
    for _m, ps in pss:
        i = ps + offset
        if not rec[i][1].strip():
            rec[i][1] = EMPTY_PS
        mrk, val = rec[i]
        val = val.strip()
        
        if not mrk == PS:
            raise Exception("Programming error! Lost track of where the {} fields are.".format(PS))
            
        sns = record.find(SN, i+1, EDGES)
        if sns and val:
            debug( 'Push: For word {} near line {}, pushing {} (at {}) down to {} sense(s)'.format(lxval, record.location, PS, i, len(sns)) )
            offset2 = 0
            for _m, j in sns:
                rec.insert(j + offset2 + 1, rec[i])
                offset2 += 1
            offset += offset2
            val = '' # mark the original ps for deletion
        elif val:
            debug('Insert: For word {} near line {}. No {} fields found. Inserting a new {} above {} instead.'.format(lxval, record.location, SN, SN, PS))
            rec.insert(i, [SN, EMPTY_SN])
            offset += 1

        if not val: 
            # delete original ps
#            print( 'Delete: for word {} near line {}, deleting ps (at {})'.format(lxval, record.location, i) )
            rec.pop(i)
            offset -= 1
    
    return record.as_string()


def selective_push (record):
    ''' Either apply push_ps_down(), or do nothing, depending on how ps and sn are ordered.
    '''

    # TODO: Delete split_record and use the new object method instead
    def split_record(record, mkrs):
        ''' Given a record of type SFMRecord and a list of root markers, split it into multiple records.
        
        mkrs would typically be ['lx', 'se'], or just ['lx']
        '''
        
        words = record.find(mkrs)
        c = len(words)
        recs = []
        if c > 1 :
            r = record.as_lists()
            i = 0
            while i < c:
                begin = words[i][1]
                if i >= c - 1:
                    end = len(r)
                else:
                    end = words[i+1][1]
                wordlines = r[begin:end]
                recs.append(sfm.SFMRecord(wordlines))
                i += 1
        else: # only one word
            recs.append(record)
        return recs        

    # selective push
    rlist = split_record(record, WORD_MKRS)
    outstring = ''
    
    for record in rlist:
    
        rec = record.as_lists()
        lxval = rec[0][1].strip()
        
        either = record.find([PS, SN], 1)
        if (either) and (either[0][0] == PS):
            outstring += push_ps_down(record)
        else:
            debug("ignoring word near line {} because {} is not found before {}".format(record.location, PS, SN))
            x = record.as_string()
#            print(x)
            outstring += x

    return outstring



def copy_ps(record):
    ''' Make ps and sn one-to-one, by copying each ps down just above any of its child sn's that don't have their own yet.
    '''
    
    rec = record.as_lists()
    offset = 0
    lxval = rec[0][1].strip()
    
    pss = record.find(PS)
    for _m, index in pss:
        i = index + offset # in case we inserted ps's or sn's during an earlier pass
        mkr, val = rec[i]
        
        if mkr != PS:
            raise Exception("Programming error! Lost track of where the {} fields are.".format(PS))
        if not val.strip():
            rec[i][1] = EMPTY_PS  # e.g. can replace \ps with \ps unknown
            
        sns = record.find(SN, i+1, [PS])  # find all sn's between this ps and any following ps
        if sns and len(sns) > 1:
#            print( 'for word {}, copying {} (at {}) down to {} sense(s)'.format(lxval, PS, i, len(sns)-1) )
            offset_sn = 0
            sns = sns[1:]  #ignore the first child sn
            for _m, index2 in sns:
                rec.insert(index2 + offset_sn, rec[i])  # copy rec[i]
                offset_sn += 1
            offset += offset_sn
    
    return record.as_string()

def undo_push(record):
    ''' Where sn occurs first, put ps above it. E.g. if ps has already been pushed down under 
    its subsequent sn, move it back up. Otherwise, infer a blank ps.
    
    Do not undo all the way back to ps and sn as one-to-many. '''

    match = record.find_first([PS,SN])
    if not match or match[0] == PS:
        return record.as_string() # no change
    
    matches = record.find([SN])
    pieces = record.split(['sn'])  # split the (sub)entry into senses
    s = ''
    s += pieces[0].as_string() # use the first chunk (prior to the first sn) unmodified
    if len(pieces) > 1:
        pieces = pieces[1:]
        for rec in pieces:
            L = rec.as_lists()
            m = rec.find([PS])
            if not m:  # infer an empty ps
                blank = [PS, EMPTY_PS]
                L.insert(0, blank)
                s += rec.as_string()
            else:
                if len(m) > 1:
                    print('WARNING (in entry beginning near line {}): multiple ps under a single sn. Skipping that sense--please fix manually'.format(rec.location))
                    print('  near here: {}...'.format(rec.as_lists()[:5]))
                else:  # just one ps found; move it to the top of the sense
                    m = m[0][1]
                    ps = L.pop(m)
                    L.insert(0, ps)
                s += rec.as_string()
    return s

def selective_copy(record):
    ''' If ps occurs first, and before multiple sn, copy ps so there's one above each sn. 
    If sn occurs one-to-one before a ps, move the ps up.
    Assumption: no single entry or subentry mixes the two structures. (It may insert a spurious ps 
    line in such cases.)
    
    Return a string.
    '''
    match = record.find_first([PS,SN])
    if match and match[0] == PS:
        return copy_ps(record)
    elif match and match[0] == SN:
        return undo_push(record)
    else:
        return record.as_string()


def execute(args):
    ''' Split out any subentries, then pass each (sub)entry into the chosen function for processing.
    '''

    def split_out_subentries(sfm_records):
        ''' Chop entries more finely, so that each subentry is its own record for now.
        
        Fields at the end of a record will simply be treated as part of the last subentry, if one exists.
        (That's safe to do in this case.)
        '''
        recs = []
        
        for record in sfm_records:
            pieces = record.split(SES)
            for piece in pieces:
                recs.append(piece)
    
        return recs
    
    print('Enter SFMPS.py -h to learn the command line options.')
    print('===== This script is intended to help bring ps and sn into a consistent relationship. It targets a one-to-one relationship, to work around an FLEx import problem (https://jira.sil.org/browse/LT-9353).')
    print("It's best to follow standard MDF (ps as parent of sn), but you can also do sn above ps.")
    print("SUGGESTION: give ALL your empty ps an 'unknown' value, to work around a FLEx import issue: https://jira.sil.org/browse/LT-10739.")
    print("\nWARNING: use at your own risk, and check the output with a diff tool such as WinMerge or KDiff3.=====\n")
    in_fname = args['infile']
    out_fname = args['outfile']
    if not out_fname:
        out_fname = in_fname + OUTFILE_EXT

    # Decide what to do based on the passed parameters
    func = selective_copy
    msg = HELP_COPY
    if args['pushpsdown']:
        func = selective_push
        msg = HELP_PUSH
    if args['undopush']:
        func = undo_push
        msg = HELP_UNDO_PUSH
    if args['copyps']:
        func = selective_copy
        msg = HELP_COPY

    with open(in_fname, encoding='utf-8') as infile:
        sfm_records = sfm.SFMRecordReader(infile, REC_MKR)
        print("Splitting each entry into 'word' chunks wherever subentries ({}) are found...".format(EDGES))
        recs = split_out_subentries(sfm_records)
        print("Running the selected function (described below)...\n" + msg)
        
        with open (out_fname, mode='w', encoding='utf-8') as outfile:
            outfile.write(sfm_records.header)

            for record in recs:
                outfile.write(func(record))
#                outfile.write('\n\n=====\n')
#                outfile.write(record.as_string())  #to see the subentry breaks
        
    print('Done. Output saved to this file: {}'.format(out_fname))


if __name__ == '__main__':
    args = get_args() # get args as a dictionary
    execute(args)
  

