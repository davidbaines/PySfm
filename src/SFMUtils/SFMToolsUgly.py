#! /usr/bin/python3

#import SFMTools as S
import SFMUtils.SFMTools as S # absolute, works
#from . import SFMTools as S # relative, doesn't work
#from .SFMTools import SFMRecord, SFMRecordReader, break_field  #works, but no "as" option
#import .SFMTools as S # fails
#from .SFMTools import * # meh; can't do an as
from collections import defaultdict

INFILE = 'D:/files/aa-synced/jon/otherproj/nias-sitasi/Nias/nias-selatan/kamus-nias-selatan-utf8.txt'
INFILE = 'akawaio.db'
OUTFILE = 'D:/files/aa-synced/jon/otherproj/nias-sitasi/Nias/nias-selatan/kamus-nias-selatan-utf8-fixedvariants2.txt'
OUTFILE = 'akawaio-main.db'
OUTFILE_MINOR = 'D:/files/aa-synced/jon/otherproj/nias-sitasi/Nias/nias-selatan/kamus-nias-selatan-utf8-minor2.txt'
OUTFILE_MINOR = 'akawaio-minor.db'

REC_MKR = 'lx'
VA = 'va_se'
WORDS = ['lx','se']
NO_HOM = ['mn','mnse'] # records containing any of these will be skipped by the homograph checker
MAX_HOM = 99

# The following are specific, messy, SFM-fixing functions which use the core code but aren't used by it. 

''' IDEAS for more functions:
- function for de-wrap (and re-wrap?) lines (parameter: width in characters)
- field-moving function
- "inventory" functions (return a list of all characters in use, or all non-ASCII characters
in use, or all backslash codes in use, etc.)
'''

def __assert(sbtrue, msg='programming error'):
    if not sbtrue:
        print('Error! {}'.format(msg))
        
def __self_test():
    ''' A very minimal test harness. Not very good, and really only tests break_field() so far. '''
    
    print('Begin self-test...')
    lines = ['\\lx test\n', '\sn\n\n1 \n']
    r = S.SFMRecord(lines).as_lists()
    __assert(r[0][0]=='lx', '1 lx')
    __assert(r[0][1]=='test\n', '1 lx val')
    __assert(r[1][0]=='sn', '2 sn (known limitation)')
    __assert(r[1][1]=='\n\n1 \n', '2 sn val (known limitation)')

    lines = ["\l test\n", "\sn\n\n", "\de  blah\n"]
    r = S.SFMRecord(lines).as_lists()
    __assert(r[0][0]=='l', '1 l')
    __assert(r[0][1]=='test\n', '1 l val')
    __assert(r[1][0]=='sn', '2 sn again')
    __assert(r[1][1]=='\n\n', '2 sn val again')
    __assert(r[2][0]=='de', '3 de')
    __assert(r[2][1]==' blah\n', '3 de val')
        
    print('Done with self-test.')

def move_list_item(thelist, xfrom, xto):
    '''Copy the item from position xfrom and insert it just before position xto. Then remove the original.
    
    Assumptions: xfrom and xto are in range.
    '''
    item = thelist.pop(xfrom) #delete it
    if xto > xfrom: xfrom -= 1  #adjust for the deletion if necessary
    thelist.insert(xto, item)


def rf_to_so(record):
    '''Replace rf with so unless rf immediately follows an example field'''

    xset = {"xv", "xe", "xn"}
#    foundRF = set()
#    i, msg = 0, ""

    #first, replace some rf with so
    for i in range (1, len(record)): #assume position 0 is recordmarker
        mkr=record[i][0]
        if mkr == "rf":
            prevmkr=record[i-1][0]
#            nextmkr=""
#            if i+1 < len(record): nextmkr=record[i+1][0]
            if prevmkr in xset: # or nextmkr in xset:
                pass
#                foundRF.add(i) #found a true rf at position i
            else:
                #replace rf with so
                record[i][0]="so"
    return record

def handle_rf(record):
    '''Move, or insert rf fields.
    Takes (and returns) a list of two-string lists.
    - Find each bundle of example fields (any or all of these in any order: xv xe xn) and make
    sure each bundle has an rf above it. This is how:
      - If an rf already exists immediately before the bundle, do nothing.
      - If the rf exists immediately after, move it up
      - If the bundle has no rf yet, insert an empty rf above
      - any field other than xv, xe, or xn closes out the current bundle
      - a second instance of xv, xe, or xn closes out the current bundle (and places an rf between them); these cases s/b checked.
    Assumptions:
    - rf is not the record marker and so will never be the first field
    WARNING: This algorithm missed 3 examples in a data set of about 1,000. Not yet sure why.
    '''

    xset = {"xv", "xe", "xn"}
    foundRF = set()
    i, msg = 0, ""

    #Find each bundle of example fields and deal with it
    foundx = set()
    inBundle = False
    bstart = 0 #start of bundle
    i = 1
    #print("LX = {} len: {}".format(record[0], len(record)))
    while i < len(record):  #note: len will change if blank rf's are inserted
        mkr=record[i][0]
        #print("i={} record[i]: {}".format(i, record[i]))
        #print("foundx: {} inBundle: {} bstart {}".format(foundx, inBundle, bstart))
        if not inBundle:
            if mkr in xset:
                #start a bundle
                inBundle, bstart = True, i
                foundx = {mkr}
            else:
                #ignore non-x field
                pass
        else:
            #we're already in a bundle
            if (mkr in foundx) or (mkr not in xset) or i >= len(record) - 1:
                #close the bundle; MAYBE DO STUFF WITH RF

                if record[bstart-1][0] == "rf":
                    #already got an rf
                    pass
                elif record[i][0] == "rf":
                    #the rf is below; move it up
                    move_list_item(record, i, bstart)
                else:
                    #need an rf; insert a blank one
                    temp=["rf", "\n"]
                    record.insert(bstart, temp)
#                            print("  len is now: {}".format(len(record)))
                    i += 1

                if (mkr in foundx):
                    #an x field closed the bundle, so open a new one right away
                    msg += "- check if the rf inserted between example fields is correct\n\n"
                    #start a bundle
                    inBundle, bstart = True, i
                    foundx = {mkr}
                else:
                    inBundle, bstart = False, 0 #close bundle
                
            else:
                #still in the bundle
                foundx.add(mkr)
        i += 1

    if msg:
        tmp = ["chk", msg]
        record.append(tmp)
    

    return record



def add_missing_gn(rec): 
    '''Insert a non-blank gn field for each sense where glosses and defs are missing. (Hard coded.)
    
    '''
    
    findthese = ('gn','ge','dn','de')
    # ('gn', '-\n')
    parents = ('lx', 'se')
    
    fields = rec.as_lists()

    insertion_points = []
    endtags = ('se')
    
    i, msg = 0, ""  
    bstart = 0 #start of "bundle" ("chunk" might be more accurate)
    in_bundle, found = False, False
    while i < len(fields):  #note: len will change if lines are inserted
        (mkr, val) = fields[i]
#        print("i={} fields[i]: {}".format(i, fields[i]))
        if mkr in parents:
            if in_bundle:
                #close out the old bundle
                if not found:
                    #prepare to insert the requested content...
                    for j in range(i, bstart, -1):
                        if fields[j][0] in ('ps','sn'):
                            #...just after ps or sn
                            fields.insert(j+1, ('gn', '-\n'))
                            i += 1 #compensate
                            break
                    else:
                        #...at the end of the bundle
                        fields.insert(i, ('ps', '\n'))
                        fields.insert(i+1, ('sn', '\n'))
                        fields.insert(i+2, ('gn', '-\n'))
                        i += 3 #compensate
                    
            in_bundle, found = True, False
            #start new bundle
            bstart = i 
        else:
            #mkr not in parents
            if mkr in findthese:
                val2 = val.rstrip().lstrip() #minus whitespace
                if val2 != '':
                    found = True
        i += 1

    if msg:
        tmp = ["chk", msg]
        fields.append(tmp)

    return fields

########## End of general-purpose code. From here on (except for "main"), it's project-specific. ########## 

def fix_corrupted_marker(rec, srcrec, badmkr, goodmkr):
    '''Copies good markers forward from a clean but old record into a newer one that had corrupted markers.
    
    Given a record in which the se fields may have been corrupted into dn, 
    and a clean source record, fix rec if and only if
    - the preceding field markers are identical
    - the data contents of the bad field are identical
    This makes it easier to manually zero in on real differences using a diff/delta tool.
    
    Takes two records. Loops through both records together, one field at a time, quitting if any 
    significant difference is found between the records.
    '''   
    
    
#    rec = break_record(rec_s)
#    srcrec = break_record(srcrec_s)
    
    i, j = -1, -1
    imax, jmax = len(rec)-1, len(srcrec)-1
    while i < imax and j < jmax :
        i += 1
        j += 1
        f, srcf = rec[i], srcrec[j]
        fdata, srcdata = f[1].rstrip(), srcf[1].rstrip()
        if srcf[0] == goodmkr and f[0] == badmkr:
            if fdata == srcdata:
                f[0] = goodmkr  #perform the fix
            else:
                #print("CHECK this record: {}; {}; src {}".format(rec[0], f, srcf))
                pass
        #Quit, if any significant diff is encountered for this record
        if f[0] != srcf[0]: # or fdata != srcdata:
            #markers don't match; make a rough attempt to get back in sync
            if i + 1 > imax or j + 1 > jmax:
                break
            if rec[i+1][0] == srcrec[j+1][0]:
                pass #we'll be fine; markers of the next line match
            else:
                found = False
                for k in range(1, 6):  #look k lines ahead
                    if i + k > imax or j + k > jmax:
                        break
                    if rec[i] == srcrec[j+k]:
                        found = True
                        i -= k
                        break
                    elif rec[i+1] == srcrec[j+k]:
                        found = True
                        i -= k-1
                        break
                    elif rec[i+k] == srcrec[j]:
                        found = True
                        j -= k
                        break
                    elif rec[i+k] == srcrec[j+1]:
                        found = True
                        j -= k-1
                        break
                if not found: break #failed; quit this record
                    
#            if i >= imax or j >= jmax:
#                break
#            if rec[i+1][0] == srcrec[j+1][0]:
#                pass #we'll be fine
#            elif rec[i][0] == srcrec[j+1][0]:
#                i -= 1 #we're just skewed by one
#            elif rec[i+1][0] == srcrec[j][0]:
#                j -= 1 #we're just skewed by one
#            else:
#                if i+1 >= imax or j+1 >= jmax:
#                    break
#                if rec[i][0] == srcrec[j+2][0]:
#                    i -= 2 
#                elif rec[i+2][0] == srcrec[j][0]:
#                    j -= 2 
#                else:
#                    if i+2 >= imax or j+2 >= jmax:
#                        break
#                    if rec[i][0] == srcrec[j+3][0]:
#                        i -= 3 
#                    elif rec[i+3][0] == srcrec[j][0]:
#                        j -= 3 
#                    else:
#                        break #failed

    return rec


def get_lexemes(records):
    '''Given a list of lexical records, returns a list of lexemes. 
    
    Assumes the first field contains the lexeme form. Does not retrieve homograph numbers, nor subentries, variants, etc.
    '''
    lex = []
    for r in records:
        #get data portion of first field
        f = S.break_field(r[0])
        lexeme = f[1].rstrip().lstrip()
        lex.append(lexeme)
    return lex

def insert_lx_for_hm(rec):
    r = rec.as_lists()
    lxval = r[0][1]
    i = 2
    ins_count = 0
    while i < len(r):  #note: len will change if new fields are inserted
        if r[i][0] == 'hm':
            if r[1][0] != 'hm':
                print('WARNING: first hm marker occurs late for this lx: {}'.format(lxval))
            r.insert(i, ('lx', lxval))
            i += 1
            ins_count += 1
        i += 1
#    print('Inserted {} lx fields for lx {}.'.format(ins_count, lxval))
    if ins_count:
#        print('Inserted {} lx fields for this record: \n{}'.format(ins_count, rec.as_string()))
        pass
        
def distinguish_minor_entries(sfm_records):
    lx, se, va = dict(), dict(), dict()
    sfm_records = list(sfm_records)
    for rec in sfm_records: # compile all the possible targets (lx) and co-referents (se and va)
        recdump = rec.as_string()
        rec = rec.as_lists()
        lxval, hmval, = '', ''
        for line in rec:
            if line[0] == 'lx':
                lxval = line[1].strip()
            elif line[0] == 'hm':
                hmval = line[1].strip()
            elif line[0] == 'se':
                val = line[1].strip()
                if not lxval: print("Error for se {}. No lx.".format(val))
                se[val] = lxval+hmval
            elif line[0] == VA:
                val = line[1].strip()
                if not lxval: print("Error for va {}. No lx.".format(val))
                va[val] = lxval+hmval
        lx[lxval+hmval] = recdump
        
    for rec in sfm_records: # check the minor entries
        recdump = rec.as_string()
        rec = rec.as_lists()
        lxval = rec[0][1].strip()
        for line in rec:
            if line[0] == 'mn': # this is a minor entry
                targ = line[1].strip()
                print('For minor entry {}, referencing {}:'.format(lxval, targ))
                print(recdump)
                if targ not in lx:
                    print('  No main entry!')
                if lxval in se:
                    v = se[lxval]
                    print('  Found matching se under lx {}'.format(v))
                    print(lx[v]) 
                if lxval in va:
                    v = va[lxval]
                    print('  Found matching va under lx {}'.format(v))
                    print(lx[v]) 

def safe_add(key, val, dict, label=''):
    ''' Adds a value to a Python dictionary, or fails and prints a message to the screen if it already exists.
    '''
    if key in dict:
        s = "{} Already has an item for key {}.".format(label, S.ascii(key))
        print(s)
    else:
        dict[key] = val
    

def build_indexes(sfm_records):
    ''' Given a list of SFM records, index various fields and return those indexes.
    
    Also, flag individual records as 'main' or 'minor'.
    '''
    
    lxD, seD = dict(), dict()
    mnD, mnseD, = dict(), dict()
    vaD = dict()  # does a given lx have any va fields?
    vaDrev = dict() # what lx entry does a given va value come from?
    i = 0
    for rec in sfm_records:
        lx = rec.find_first('lx')[1].strip()
        hm = rec.find_first('hm')
        if hm: 
            hm = hm[1].strip()
            lx = lx + hm
        safe_add(lx, i, lxD, "Warning for 'lx entries' (no unique homograph number): ")

        se_s = rec.find_values('se')
        for se in se_s:
            safe_add(se, i, seD, "Warning for 'se subentries' (no unique homograph number--may be ok for se): ")

        rec.entry_type = 'main'  # default assumption
            
        mn = rec.find_first(['mn'])
        mnse = rec.find_first(['mnse'])
        va_s = rec.find_values([VA])
        if mn :  # minor entry (for variant); keep track of its mn link
            rec.entry_type = 'minor for va'
            mn = mn[1].strip()
#            mn = mn_s[0][1] # there s/b only one mn field; get its index
#            mn = rec.as_lists()[mn][1].strip() # get its value
            mnD[lx] = mn # index it
            if va_s :
                print("ERROR: Minor entry {} contains both mn {} and va {}".format(lx, mn, va_s))
        elif mnse :
            rec.entry_type = 'minor for se'
            mn = mnse[1].strip()
            mnseD[lx] = mn # index it
            if va_s :
                print("ERROR: Minor entry {} contains both mnse {} and va {}".format(lx, mn, va_s))
            
        elif va_s :  # main entry; keep track of its variants' links
            rec.entry_type = 'main with va'
            vaD[lx] = va_s
            for va in va_s:
                if va in vaDrev:
                    print('Warning! FIX THIS FIRST: both {} and {} reference {}'.format(lx, vaDrev[va], va))
                vaDrev[va] = lx 
            pass
        i += 1    
    return lxD, seD, mnD, mnseD, vaD, vaDrev

def find_above(mkr, L, i = None):
    ''' Find the field mkr in list L and return its index, if it occurs above position i. Else return None. 
    '''
    if i == None: i = len(L)
    while i > 0:
        i -= 1
        if L[i][0] == mkr:
            return i
    return None


def check_duri():
    #This file had multiple senses split into consecutive entries. The script checks how safe it is to merge these.
    print('Checking the Duri file for merge safety...')
    prev_lx, safe, unsafe = '', 0, 0
    with open('D:/files/aa-synced/jon/otherproj/kari-valkama/Duri key terms-UTF8.sfm', encoding='utf-8') as infile:
        sfm_records = S.SFMRecordReader(infile, S.RECORD_MARKER)
        for rec in sfm_records:
            r = rec.as_lists()
            lx = r[0][1]
            sn = rec.find_first('sn')[1]
            if not sn:
                print ('WARNING: no sn field under lx {})'.format(lx))
            if sn and not (sn == '1'):
                # an explicitly numbered sense (2 or higher); safe to merge?
                if lx == prev_lx:
                    safe += 1
                else:
                    unsafe += 1
#                    print('WARNING: {} != {}'.format(lx, prev_lx))
            prev_lx = lx  # move the sliding window
        print("Done. {} are safe to merge; {} are unsafe.".format(safe, unsafe))

def run_sample():
                
    print('RUNNING THE SAMPLE...')    
    with open('lexicon-sample.txt', encoding='utf-8') as infile:
        with open ('lexicon-sample-conv.txt', mode='w', encoding='utf-8') as outfile:
            sfm_records = S.SFMRecordReader(infile, S.RECORD_MARKER)
            count, have_def_field, ps_inserted, sn_inserted = 0, 0, 0, 0
            outfile.write(sfm_records.header)
            for rec in sfm_records:
                count += 1
                rec.as_lists()
                if rec.find_first(['dn', 'de']) > -1: have_def_field += 1  #Empty defs will be counted too
                ps_inserted += rec.insert_field_between( ('lx','se','hm','lc'), ('sn','ge','de','gn','dn'), ('ps', '\n') )
                sn_inserted += rec.insert_field_between( ('ps','pn'), ('ge','de','gn','dn'), ('sn', '\n') )  
                tmp = rec.as_string()
                outfile.write(tmp)
    
    print('{} out of {} total records contained a definition field.'.format(have_def_field, count))
    print('Inserted {} blank \\ps fields directly between headword and sn/gloss/def.'.format(ps_inserted))
    print('Inserted {} blank \\sn fields directly between POS and gloss/def.'.format(sn_inserted))
    print('Success.')
    
    #CHAINING. You can take that output (lexicon-sample-conv.txt) and apply one or more regex files to it
    import os
    os.system('python ApplyRE.py lexicon-sample-conv.txt lexicon-sample-conv.txt regex-sample.txt -o')
#    #Or, like this:
#    import ApplyRE
#    ApplyRE.execute( {'infile': 'lexicon-sample-conv.txt', 'outfile': 'lexicon-sample-conv.txt', 'regexfile': 'regex-sample.txt', 'overwr': True} )




def variants_as_minor():
    '''Supports variants of lx and se, but not of sn.
    '''
    with open(INFILE, encoding='utf-8') as infile:
        sfm_rec = S.SFMRecordReader(infile, REC_MKR)
        header = sfm_rec.header
        sfm_records = list(sfm_rec)  # load entire file into memory

    # Need to be able to follow links. Do one quick pass to index everything.
    lxD, seD, mnD, mnseD, vaD, vaDrev = build_indexes(sfm_records)
    to_add = ''
            
    with open (OUTFILE, mode='w', encoding='utf-8') as outfile:
        outfile.write(header)
        with open (OUTFILE_MINOR, mode='w', encoding='utf-8') as outfile_minor:

            for rec in sfm_records:
                if rec.find(['mn']) : # minor entry (variant)
                    outfile.write(rec.as_string())
                elif rec.find(['mnse']) :
                    # minor entry: complex form
                    outfile_minor.write(rec.as_string()) # omit from outfile
                else:
                    # main entry
                    r = rec.as_lists()
                    lx = r[0][1].strip()
                    vas = rec.find([VA])
                    ses = rec.find('se')
                    lxse = rec.find_values(['lx', 'se'])
                    while vas: 
                        # look at each va, in reverse order
                        _mkr, i = vas.pop()
                    
                        va = r[i][1].strip()
                        print('lx or se {}, with va {}: '.format(lxse, va))
                        mn = mnD.get(va)
                        mnse = mnseD.get(va)
                        if mn:
                            if mn in lxse:
                                pass
#                                print('- match: Minor entry pointing to {}. Matched! va {} '.format(mn, va))
#                                r[i][0] = 'cfva'  # Disabling va to cfva for
                            else:
                                print('- min diff: Minor entry {} found, but it points to a different target: {} .'.format(va, mn))
                        elif mnse:
                            print('Error?? found an lx matching va {} that contains an mnse field: mnse {}'.format(va, mnse))
                        else:
                            print("- no min: No matching minor entry for va {} !".format(va))
                            #TODO: No!! Don't use lx. In ses, find the first se above this va_se field; use that.
                            se = find_above('se', r, i)
                            if se:
                                se = r[se][1].strip()
                                tmp = '\\lx {}\n\\mn {}\n\n'.format(va, se)
                                print("Will add this minor entry: {}".format(tmp))
                                to_add += tmp
                            tmp = lxD.get(va)
                            if tmp: print("- - lxD({}): {}".format(va, tmp))
                            tmp = seD.get(va)
                            if tmp: print("- - seD({}): {}".format(va, tmp))
                            tmp = vaD.get(va)
                            if tmp: print("- - vaD({}): {}".format(va, tmp))
                            tmp = vaDrev.get(va)
                            if tmp: print("- - vaDrev({}): {}".format(va, tmp))
#                                if (res2 != lx): pass  #TODO: ??
                    outfile.write(rec.as_string())
                
    print('PLEASE INSERT THESE minor entries into the file: ')
    print(to_add)

def identify_homographs(sfm_records, markers, ignore=NO_HOM):
    ''' Build an index of all words, grouping the homographs together
    '''
    words = defaultdict(list)
    i = 0
    for rec in sfm_records:
        if not rec.find_first(ignore):
            w = rec.find(markers)
            for mkr, field in w:
                try:
                    mkr, word, hom = rec.get_as_homograph(field)
                    line = "near line #{}".format(rec.location)
                    tmp = [mkr, hom, i, field, line]
                    words[word].append(tmp)
                except ValueError:
                    r = rec.as_lists()
                    print('ERROR: unable to process record; homograph number in field {} is not an integer.'.format(r[field]))
        i += 1
    
    return words

#def remove_first(hom, pointers):
#    ''' Find the first pointer whose second item matches hom, and remove it. Return False if not found. '''
#    if pointers:
#        i = 0
#        while i < len(pointers):
#            if pointers[i][1] == hom:
#                pointers.pop(i)
#                return True
#            i += 1
#    return False

def disp_hom(pointers, sfm_records, sep = "====================\n"):
    s = sep
    for p in pointers:
        rec = sfm_records[p[2]]
        s += rec.as_string() + sep
    return s

def add_hom_to_word(word, pointers, sfm_records, apply = True):
    ''' For a given word form, indicate which homograph numbers should be added to which entries. If "apply" is True, add them.
    
    Print warnings for existing numbers that conflict, but don't fix them.
    '''
    review = False
    
    # The FLEx importer currently needs the homographs (lx and se) to appear in numeric order to avoid bugs (argh!)
    h = 1
    for p in pointers:
        if p[1] and h != p[1]:
            print('ERROR: Homograph number is out of sequence. Please fix manually, then re-run.')
            review = True
        h += 1
    
    # Split the list into already-numbered and not-yet-numbered (preserving order)
    numbered = [p for p in pointers if p[1]]
    notyet = [p for p in pointers if not p[1]]
    if notyet: review = True
    
    # Check for dups
    numD = dict()
    for n in numbered:
        key = n[1]
        if key not in numD:
            numD[key] = 'whatever'
        else:
            print('===== Error: duplicate homograph mumbers. Please fix one or more of these records.')
            print(numbered)
            print('SEE ALSO')
            print(notyet)
            print('=====')
            
            return  # Quit!
    
    # auto-number (WARNING: doesn't bother with hm; just appends the number to lx or se)
    hom = 1
    while (hom < MAX_HOM) and (notyet):
        if hom in numD:
            pass
        elif notyet:
            msg = "Need to assign the number {} to this homograph of {}: {} .".format(hom, word, notyet[0])
            if apply:
                ny = notyet[0]
                rec = sfm_records[ny[2]]
                line = rec.as_lists()[ny[3]]
                line[1] = line[1].strip() + str(hom) + '\n'
                print(msg + " Done.")
            else:
                print(msg)
            notyet.pop(0)
        hom += 1

    # Check for left-overs    
#    if numbered:
#        print("Left-over Error for {}: check for a duplicate homograph(s) of: {}".format(word, numbered))
    if notyet:
        print("STRANGE Left-over Error for {}: we passed the max ({}) and didn't handle these: {}".format(word, MAX_HOM, notyet))
    if review:
        print("Please review the following homographs of {}.".format(word))
        print(disp_hom(pointers, sfm_records))
       

def check_homographs(markers=WORDS):
    ''' Add homograph numbers as needed, but leave alone any explicit numbers that are already there.
    
    Print a message if any of those explicit numbers conflict. (E.g. two explicitly identical lx's. Explicitly identical se's are probably fine.)
    Support homograph-as-number-suffix for lx and se; also support hm under lx.
    '''
    with open(INFILE, encoding='utf-8') as infile:  # load entire file
        sfm_rec = S.SFMRecordReader(infile, REC_MKR)
        header = sfm_rec.header
        sfm_records = list(sfm_rec)

    # Do one pass to index everything.
    words = identify_homographs(sfm_records, markers)
    
    for key in words:
        if len(words[key]) > 1:  # There are homographs
            print("HOMOGRAPHS of {}:\n{}".format(key, words[key]))
            add_hom_to_word(key, words[key], sfm_records)
            
    with open (OUTFILE, mode='w', encoding='utf-8') as outfile:
        outfile.write(header)
        for rec in sfm_records:
            outfile.write(rec.as_string())

if __name__ == '__main__':

    print("\nStarting.")
#    check_homographs()
    variants_as_minor()
        
        
    print("Finished.\n")

