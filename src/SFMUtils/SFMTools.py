#! /usr/bin/python3

'''This Python 3.x module provides utility classes and functions for:
- reading in SFM markers and data in a way that preserves the data as precisely as possible (e.g. preserving spaces and blank lines)
- analyzing the file's field markers and data.
- applying changes to the data consistently.
It can also be run as a script (runs diagnostics).

WARNING: An output file may be generated on each run, silently overwriting past versions of the same file. But these files typically 
are labeled as .tmp or .temp anyway.

If run as a script (see the execute function), it will take the input file (plain text, ASCII or unicode) and will output a report file. 
You can specify the input file via the console, or else just name your input file to match the provided default.
If you use it often, you can 'install' it by adding the SFMUtils folder to your Windows PATH. 
Appending ";.PY;.PYW" to the PATHEXT variable will allow you to leave off the ".py" . More details here:
http://linguisticsoftware.wordpress.com/2012/11/23/running-python-scripts-conveniently-under-windows/



Sample command-line calls (the first just displays help; the second specifies an input file):
python SFMTools.py -h
python SFMTools.py input.txt

In Windows, use the py launcher instead; you may want to create a batch file that you can easily double-click to run this. But don't name it SFMTools.bat
- Example 1:
py SFMTools.py
pause
- Example 2:
C:\Python32\python.exe SFMTools.py "C:\temp\myfile.txt" "C:\temp\myfile-report.txt"
pause

'''

import re, io, argparse

import sys
print("Running under Python {}".format(sys.version.split()[0]))
#print("sys.path : {}".format(sys.path))
from collections import defaultdict
import unicodedata

# import nltk_contrib #TODO: use or remove this


# Constants:
HEADER_TAG = '\\_'
BOM = 62579
RECORD_MARKER = 'lx'

DEFAULT_FILE = 'lexicon.txt' # note: folders in file paths should use forward slashes; or, double backslashes work too, on Windows.
OUTFILE_EXT = '.report.txt'
TALLY_FIELDS = ('ps', 'pn', 'lf', 'sn')
ENTRY_FIELDS = ('lx', 'se',)
VARIANT_LINK_FIELDS = ('va', 'vase', 'vasn', 'valx', 'vaN', 'vaNS', 'vaNSW', 'vaNW', 'vaS', 'vaSW', 'vaW')
LINK_FIELDS = ('cf', 'cflx', 'lxS', 'lxW',  'cfse', 'cfsn', 'sy', 'mn', 'mnse', 'mnva', 'an', 'lv', )  # fields whose target entries ought to exist (not necessarily true of va)
#LINK_FIELDS += ('va', 'vase', 'vasn')
LINK_FIELDS += ('ccf', 'cdiff')
LINK_FIELDS += ('cfcpx', 'cfroot')
PS = 'ps'
SN = 'sn'
HM = 'hm'

# To temporarily override the above constants, copy them below and tweak them
TALLY_FIELDS = ('ps', 'pn', 'lf', 'sn', 'hm', 'pdl', 'un', 'unsn', 'bw', 'es', 'dl', 'vn')
#ENTRY_FIELDS = ('lx', 'se')

def get_args():
    ''' Parse any command line arguments (all are optional). Only relevant when run as a script.'''
    parser = argparse.ArgumentParser(description='Parse and analyze an SFM file. For more info, open the .py file in a text editor and read the comments.')
    parser.add_argument('infile', default=DEFAULT_FILE, nargs='?', help='the input file (default: {})'.format(DEFAULT_FILE))
    parser.add_argument('outfile', nargs='?', help='the output file to save to (default: infile plus {})'.format(OUTFILE_EXT))
    return vars(parser.parse_args())

def ascii(s):
    '''Given a (unicode) string, force it to use ASCII characters only. E.g. this is safe to print to a Windows console.
    
    The returned string may have LOST SOME INFORMATION, in which case a tilde will be prefixed to it.'''
    s2 = unicodedata.normalize('NFKD', s)
    b = s2.encode('ASCII', 'replace')
    s3 = b.decode()
    if s3 != s:
        s3 = "~" + s3
    return s3

def bad_encoding(filename, enc='utf-8', max=9):
    '''Return a list of up to max error strings for lines in the file not encoded in the specified encoding. 
    
    Otherwise, return an empty list.'''
    
    errors = []
    line = None
    with open(filename, encoding=enc) as f:
        i = 0
        while True:
            try:
                i += 1
                line = f.readline()
            except UnicodeDecodeError:
                errors.append('UnicodeDecodeError: Could not read line {} as {}.'.format(i, enc))
            if not line or len(errors) > max:
                break

    return errors


def break_field(field):
    ''' Take a string and break it into its marker and data (i.e. into a list of two strings).
    
    The input string must be in standard format, beginning with a \ then a marker followed
    by either a space or a field-final newline. Any data (optional) must follow the space. 
    It tries hard to preserve the data as it was, so if there are additional spaces, it will 
    not trim them. (That can easily be done as a separate, intentional step.)
    Examples:
    - "\lx test\n" yields ["lx", "test\n"]
    - "\sn\n\n" yields ["sn", "\n\n"]
    - "\de  blah\n" yields ["de", " blah\n"]
    Warning:
    - "\sn\n\n1 \n" yields ["sn\n\n1", "\n"] 
    '''

    if not field.startswith("\\"): raise ValueError("string must begin with \\")

    pos = -1
#    tmp = field.find("\n")
#    if (tmp != -1) and (tmp < len(field)):
#        pos = tmp
    tmp = field.find(" ")
    if (tmp != -1):
        pos = tmp
    
    if pos < 2 and pos != -1 : raise ValueError("field marker must come before any spaces")


    breakat = len(field) #default assumption: it's all marker and no data
    if pos != -1 : #the line has at least one space; break on it and omit it
        breakat = pos
        data = field[breakat + 1:]
    else:           
        #no space found
        nlpos = field.find("\n")
        if nlpos != -1: breakat = nlpos #break at the first newline
        data = field[breakat:]

    marker = field[1:breakat]
    return [marker, data]

def split_list(alist, indices):
    ''' Given a list and a list of indexes/indices, split the list at those locations to return a list of lists. '''
    return [alist[i:j] for i, j in zip([0]+indices, indices+[None])]

class SFMRecord:
    ''' Represents a single record from an SFM file. This is passed in as a list of strings and can be retrieved in two ways:
    - as a list of fields, in which each field is itself a two-value list (marker and content)
    - as a single (multi-line) string
    '''
    
    def __init__(self, rec_lines=None, cursor=None):
        ''' Given a list of lines of text, parse them into the lines of an SFM record object
        
        Optionally, the file location can be specified (mainly for reporting).'''

        self.location = cursor
        brokenfields = []
        if rec_lines:
            for field in rec_lines:
                br = break_field(field)
#                if isinstance(field, str):
#                    #TODO: ?? maybe use hasattr instead, checking for the existence of the startswith() method
#                    br = break_field(field)
#                else: #assume it's already the right kind of list
#                    br = field
                brokenfields.append(br)
        self._fields_split = brokenfields

    @classmethod
    def from_lists(cls, the_lists, cursor=None):
        ''' An alternate constructor that starts from already-parsed data '''
        obj = cls(cursor=cursor)
        obj._fields_split = the_lists
        return obj
    
    def as_lists(self):
        ''' Return the record as a list of fields. (Each list is itself a two-value list: marker, value.) 
        
        Note that the calling code can modify that list's contents as it pleases prior to calling the as_string() method.
        '''
        return self._fields_split
    
    def as_string(self):
        ''' Take a broken-down record and piece it back together as a single string.
        '''
#        return join_as_str(self._fields_split)
        tmp = ''
        for field in self._fields_split:
            #join everything back into a string
            tmp += '\\' + field[0]
            if not field[1].startswith('\n'): tmp += ' ' #put back the space between the marker and its data
            tmp += field[1]
        return tmp

    
    def split(self, markers):
        ''' Split this record into multiple records wherever marker(s) found. Return a list of records.
        
        Example: rec.split(['se']) will split out each subentry as its own record. (Warning: any trailing
        markers at the lx level occurring at the end will end up in the last subentry.)
        '''
        matches = self.find(markers) # returns a list of tuples (marker, index)
        if matches:
            # split into multiple new SFMRecord objects
            recs = []
            indexes = [x[1] for x in matches]  # we just need a list of indexes
            chunks = split_list(self.as_lists(), indexes)
            for chunk in chunks:
                r = SFMRecord.from_lists(chunk, cursor=self.location) # create a new SFMRecord
                recs.append(r)
            return recs
        else:
            # just return the existing object (in a list)
            return [self]

    def find_first(self, targets):
        ''' Return the first occurrence of any of the target fields in the record, or None if not found.
        '''
        if not targets: return None
        ret = None
        i = 0
        for field in self.as_lists():
            mkr = field[0]
            if mkr in targets:
                ret = field
                break
            i += 1
        return ret
    
    
    def find(self, targets, start=0, bounds=[]):
        ''' Find all occurrences of the desired marker(s) at or after the start index but before any bounding markers.
        
        Return a list of tuples, where each tuple is a marker and an index.
        '''
        rec = self.as_lists()
        i = start
        sns = []
        while i < len(rec):
            mrk = rec[i][0]
            if mrk in targets:
                sns.append((mrk, i))
                #TODO: append the value too, rec[i][1]
            elif mrk in bounds:
                break
            i += 1
        return sns

    def find_values(self, targets, start=0, bounds=[]):
        ''' Do a find but just return the values (no indexes, and stripped)
        '''
        sns = self.find(targets, start, bounds)
        L = self.as_lists()
        return [L[v][1].strip() for _m,v in sns]

    def insert_field_between(self, first, second, insert_this):
        ''' If second is found immediately after first, insert something between them.
        
        first and second are lists/tuples/sets of at least one marker name each.
        insert_this is a (marker, value) pair.
        For example, the following inserts a blank sn field between ps and ge, or between pn and ge, etc.
          count = rec.insert_field_between( ('ps','pn'), ('ge','de'), ('sn', '\n') )
        '''
        fields = self._fields_split
#        found_first = False
        i, insertion_points = 1, []
        
        #find any occurrences of second preceded by first
        while i < len(fields):
            if fields[i][0] in second:
                if fields[i-1][0] in first:
                    insertion_points.append(i)
            i += 1
        
        #insert between each pair that was found
        comp = 0
        for i in insertion_points:
            fields.insert(i + comp, insert_this)
            comp += 1 #compensate
        
        return len(insertion_points)

    def get_as_homograph(self, i=0, hm=[HM]):
        ''' Given an index to a field, return that field along with anything that looks like a homograph number for it.
        
        Throws a ValueError if the value in an hm field cannot be cast to an int.
        Warning: MDF defines hm as applying to lx (not se). Note: if you instead append a number to an se, the FLEx importer does understand that.
        Limitation: Only finds hm when it is located immediately after its lx or se .'''
        #TODO: Fix this limitation or raise an error/warning; we can't really assume this unless we somehow ensure it with pre-checking E.g. unless this regex gives zero results on the whole file:
        # (\\(?!(lx|se)).*)(\r\n)(\\hm\b.*)
        
        hom = None
        fields = self.as_lists()
        mkr, val = fields[i]
        val = val.strip()
        if i+1 < len(fields) and fields[i+1][0] in hm:
            hom = fields[i+1][1].strip()
        else:  # no hm field; check the end of the word itself
            tmp = re.findall(r'^(\D+)(\d+)[ ]*$', val)
            if tmp:
                val, hom = tmp[0]
        if hom: 
            hom = int(hom)
        return mkr, val, hom

class SFMFieldReader:
    ''' An iterator that returns the contents of an SFM file, one field at a time.

    Since this is a one-way iterator that only reads data as needed, it s/b
    memory efficient and should start quickly.
    Initialization requires:
    - A file handle
    Assumptions:
    - The file is already opened in readable mode
    - We can "ignore" any \_ lines at the beginning of the file (just dumping them into the header)
      TO DO: store header as a list of strings (one per field) rather than one string
    - If a line begins with \, everything after it before a space or newline is
    part of the marker. (There's no testing for bogus characters here.)

    Initialization requires:
    - A string, or an open file that's ready to be read from.
    - The record marker (with no leading slash).   
    Assumption:
    - We can ignore any \_ lines at the beginning of the file (just save them untouched as header info)

    '''

#    header="" #to store any lines that precede the first true record in the file
#    buffer="" #used for ONE LINE of lookahead (so, it's not really much of a buffer)

    def __iter__(self):
        return self

    def __init__(self, sfmfile):
        ''' Deal with the first line or two of the file.'''

        self.header="" #to store any lines that precede the first true record in the file
        self.buffer="" #used for ONE LINE of lookahead (so, it's not really much of a buffer)
        
        if isinstance(sfmfile, str): #if a string of data was passed instead of a file handle
            sfmfile = io.StringIO(sfmfile)
        self.afile = sfmfile
        self.nomore = False
        tmp = self.afile.readline()
        self.cursor = 1  #TODO: changing this to 0 maybe is better but is buggy! . Also, the number for the first record in the file is off by one.
        if ord(tmp[0]) == BOM: 
            tmp = tmp[1:]  #strip off the Byte Order Mark for now
            self.header += BOM  #but make sure the file doesn't get changed
        while True:
            if not tmp:
                self.nomore = True #end of file
                break
            elif (not tmp.startswith('\\')) or tmp.startswith(HEADER_TAG): 
                self.header += tmp  #still in header
            else:
                self._buffer = tmp  #found the first record
                break
            tmp = self.afile.readline()
            self.cursor += 1
        pass
                            
    def __next__(self):
        ''' Returns the next one. (This is the method a for loop will call.)
        '''
        if self.nomore: raise StopIteration #we ran out of fields last time
        field = ""
        if self._buffer:
            #use the left-over line from last time as our starting point
            field = self._buffer
            self._buffer = ""

        while True:
            temp = self.afile.readline()
            self.cursor += 1  #TODO: figure out why this gets off track
            if not temp:
                self.nomore = True #end of file; next time, we'll raise a StopIteration
                break
            elif temp.startswith('\\'):
                self._buffer = temp #save this line for later
                break
            else:
                field += temp #still in the same field; append and keep going
        return field


class SFMRecordReader:
    
    ''' An iterator that returns the contents of an SFM file one record at a time (using SFMFieldReader).
    '''

    def __iter__(self):       
        return self

    def __init__(self, dictfile, recordmarker=RECORD_MARKER):
        self.recordmarker = recordmarker
        self._buffer=""  #used for one FIELD of lookahead
        self.nomore=False
        self._fields = SFMFieldReader(dictfile)
        self.header = self._fields.header  #any lines that precede the first true record in the file

        #find the first record's first line; dump into the header any fields found before that
        while True:
            [mkr, _data] = break_field(self._fields._buffer)  #peek at the buffer
            if mkr == self.recordmarker: break
            else:  #we're not at the first record yet; add this 'field' to the header to preserve it, and move on
                self.header += self._fields.__next__()

    def __next__(self):
        if self.nomore: raise StopIteration #we ran out of fields last time
        lines=[]
        firstfield = True
        cur = self._fields.cursor - 1  #TODO: fix (shouldn't need the -1)
        if self._buffer:
            #use the \lx field from last time as our starting point
            lines.append(self._buffer)
            self._buffer = ""
            firstfield = False
        halt=False
        while not halt:
            try:
                temp = self._fields.__next__()
                [mkr, _data] = break_field(temp)
                if mkr == self.recordmarker and not firstfield:
                    self._buffer=temp #done; save this line/field for later
                    halt=True
                else:
                    firstfield=False
                    lines.append(temp) #append; keep going
            except StopIteration:
                self.nomore=True #next time, we'll raise a StopIteration ourselves
                halt=True
        #TODO: test using try with break instead of halt=True.
        return SFMRecord(lines, cur)


def get_stats(recs, tally_fields=TALLY_FIELDS, entry_fields=ENTRY_FIELDS):
    ''' Given an iterable of SFM records, compile stats about the SFM file. Return a report string.
    
    Assumptions:
    - The markers will all be basic ASCII. Unicode characters beyond the ASCII will be tallied if found in the field values.
    '''

    def count_uni(ustr, valD):
        ''' Given a unicode string and a defaultdict, tally up any non-ASCII characters found in the string.
        '''
        for c in ustr:
            if ord(c) > 127:
                valD[c] += 1

    def check_misplaced_hm(rec, hm='hm', lx=RECORD_MARKER):
        ''' Given an SFMRecord, print a warning if it contains an hm field that's not immediately after a record marker.'''
        report = ''
        lxval = rec.as_lists()[0][1].strip()
        loc = "entry [{}] near line {}".format(lxval, rec.location)
        msg = "  MDF defines homograph numbers as applying to lx (not se). Note: if you instead append a number to an se, the FLEx importer does understand that."
        matches = rec.find([hm])
        if len(matches) > 1:
            report += "WARNING: multiple {} fields found in a single record: {}\n{}\n".format(hm, loc, msg)
        elif matches and matches[0][1] != 1:
            report += "WARNING: {} field was found somewhere other than as the second field: {}\n{}\n".format(hm, loc, msg)
        return report

    rep = ''
    uniD = defaultdict(lambda: int(0)) # unicode characters and counts
    numD = defaultdict(lambda: int(0)) # markers whose values sometimes end in numbers, and counts
    mkrD = defaultdict(lambda: list([0, 0])) # key = SFM markers; val = two counts (total, and non-empty)
    valD = dict()
    for f in tally_fields:
        valD[f] = defaultdict(lambda: int(0)) # key = values for selected markers (e.g. ps, lf); val = count
    rec_count, entry_count = 0, 0
    ps_first_count, sn_first_count, neither_count, ps_missing_count = 0, 0, 0, 0
	#TODO: also count the number of blank PS fields; if > 0 report problem with LT-10739
    for rec in recs:
        rec_count += 1

        rstr = rec.as_string()
        try:  # Are there any non-ASCII characters here?
            tmp = rstr.encode('ascii')
        except UnicodeEncodeError:  #  Yup. Count them.
            count_uni(rstr, uniD)

        rep += check_misplaced_hm(rec)

        r = rec.as_lists()
        for mkr, val in r:
            if mkr != mkr.strip():
                raise Exception("PARSE ERROR! marker name contains whitespace")
            if mkr in entry_fields:
                entry_count += 1
            if mkr in tally_fields:
                if val.endswith('\n'):
                  val = val[:-1]
                valD[mkr][val] += 1
            val = val.strip()
            mkrD[mkr][0] += 1  # count marker occurrence
            if val:
                mkrD[mkr][1] += 1  # count non-empty occurrence
            tmp = re.findall(r'^.*(\D+)(\d+)$', val) # finds a number at the end of the line, when the whole field is not numeric
            if tmp:
                numD[mkr] += 1

        if not rec.find([PS]):
            ps_missing_count += 1

        either = rec.find([PS, SN])
        if either:
            mkr = either[0][0]
            if mkr == PS:
                ps_first_count += 1
            else:
                sn_first_count += 1
#                rep += '\n\n== ' + str(rec.as_lists())
        else:
            neither_count += 1
    rep += "\n"

    
    rep += "Record count ({}): {}\n".format(RECORD_MARKER, rec_count)
    rep += "Entry count ({}): {}\n".format(entry_fields, entry_count)
    rep += "SFM markers (non-empty count , total count , name):\n"
    L = sorted(mkrD.items(), key=lambda x: x[1][1])  # each item from items() looks like this: ('rf', [5269],[3]) . The x[1][1] grabs the 3 count.
    for m in L:
        rep += "  {} , {} , {}\n".format(m[1][1], m[1][0], m[0])
    rep += "\n"

    rep += "Checked (very roughly) the relative order of {} and {} (Having a mix of hierarchies is bad! Standard MDF has ps above one or more sn, but limiting it to one sn per ps imports better into FLEx. LT-9353 LT-10739):\n".format(PS, SN)
    rep += "  {} occurred first in {} records\n".format(PS, ps_first_count)
    rep += "  {} occurred first in {} records\n".format(SN, sn_first_count)
    rep += "  neither one occurred in {} records\n".format(neither_count)
    rep += "Checked roughly for missing {}; it is missing in {} records.\n".format(PS, ps_missing_count)    
    rep += "In both cases, only checked records, not individual senses/subentries.\n"
    rep += "WARNING: If importing into FLEx, empty ps fields are a problem. If you have any, consider using find/replace to insert an explicit 'unknown' value (LT-10739, LT-14038).\n\n"

    #TODO: consider removing the numD code altogether, now that we have check_links()
#    rep += "Fields ending in numbers preceded by non-number(s):\n"
#    if numD:
#        L = sorted(numD.items(), key=lambda x: x[1]) 
#        for m in L:
#            rep += "  {} {}\n".format(m[1], m[0])
#        rep += "  If these are link fields these may be fragile links. Consider running a link/homograph checker.\n"
#    else:
#        rep += "  None found. This suggests that there are no fragile links in this file. \n"
#    rep += "\n"

    rep += "Non-ASCII characters (characters above char 127):\n"
    rep += " count , char , code point , name\n"
    L = sorted(uniD.items(), key=lambda x: x[1])
    for m in L:
        ch = m[0]
        code = ch.encode('unicode-escape').decode()
        count = m[1]
        rep += "  {} , {} , {} , {}\n".format(count, ch, code, unicodedata.name(ch, ''))
    rep += "\n"

    rep += "Tallying values for specified fields... ({})\n".format([x[0] for x in valD.items()])
    for v in valD:
        L = valD[v].items()
        if L:
            rep += "Tallied values for field {}: \n".format(v)
            L = sorted(L, key=lambda x: x[0].casefold())  # x[0] to sort by value; x[1] to sort by count
            for m in L:
                rep += "  {} [{}]\n".format(m[1], m[0])
    rep += "\n"
    
    return rep

class NumStripper:
    ''' A utility class for quickly stripping off numbers using precompiled regexes. Conceptually a singleton.'''
    re_strip_sense_num = re.compile(r"\s+\d+$", flags = re.LOCALE | re.MULTILINE | re.UNICODE)
    re_strip_hom_num = re.compile(r"\d+$", re.LOCALE | re.MULTILINE | re.UNICODE)

    @classmethod
    def strip_sense_num(cls, val):
        ''' Strip off whitespace, and any sense number (is always preceded by a space) from the end of the string. '''
        # TODO: Rename function, and return a tuple instead        

        val = val.strip()
        if not val:
            return ''
        elif val[-1].isdigit():
            match = re.findall(cls.re_strip_sense_num, val)
            if match:
                val2 = val.split(match[0])[0].strip()
                if val2:
                    return val2
                    
        return val

    @classmethod
    def strip_hom_num(cls, val):
        ''' First strip off any whitespace or sense number, then strip off any homograph number. '''
        # TODO: rename to split_hom_num and return a tuple instead (the second part w/b null if no homograph)
        val = cls.strip_sense_num(val)
        if val and val[-1].isdigit():
            match = re.findall(cls.re_strip_hom_num, val)
            if match:
                val2 = val.split(match[0])[0].strip()
                if val2:
                    return val2
        return val

def build_indexes(recs, entry_fields=ENTRY_FIELDS, exclude_fields=[]):
    ''' Given a list of records, return a dict for looking up each word form. Also return a dict
    indexed on the stripped wordforms (i.e. without homograph numbers).

    When testing link fields, you'll know the link is safe if the lookup returns a list of length 1.'''

    #Outdated note: In the stripped case, we don't treat homograph numbers and senses as link unique-ifiers 
    #because the FLEx importer doesn't reliably handle them (LT-10733).

    #TODO: Replace this with a class that just includes two ways of looking up a word (i.e. with or without homograph number),
    # and can return just the values that specifically match or else all values that could confuse the FLEx importer.
    # Store (in the index) pointers to the actual SFMRecord objects? I.e. so the calling code can fix them.

    entries = defaultdict(lambda: list([]))  # key is a word (lx or se), value is a list (index, location in file)
    entries_stripped = defaultdict(lambda: list([]))  # key is a word (lx or se), value is a list (index, location in file)

    i = 0
    for rec in recs:
        fields = rec.as_lists()
        j = 0
        if not rec.find_first(exclude_fields):  # e.g. if not a minor entry (the most typical exclusion)
            for f, val in fields:
                if f in entry_fields:
                    val = val.strip() # just a whitespace strip; don't strip any numbers yet
                    if j+1 < len(fields) and fields[j+1][0] == HM: # is the next field \hm ?
                        val += fields[j+1][1].strip()  # append the homograph number
                    #TODO: ? Consider finding a homograph number that is lurking in a non-adjacent hm field.
                    #TODO: ?? Consider splitting out se's
                    #TODO: ??? Consider including a list of the sense numbers in explicit sn fields (for more precise checking)
                    entries[val].append([i, rec.location, rec])
                    val_s = NumStripper.strip_hom_num(val)
                    entries_stripped[val_s].append([i, rec.location, rec])
                j += 1
        i += 1
    return entries, entries_stripped


def check_links(recs, link_fields=LINK_FIELDS, entry_fields=ENTRY_FIELDS, variant_fields=VARIANT_LINK_FIELDS):
    ''' For each link field in each record, check whether the link's target exists and is totally unique. 
    
    Limitation: For sense-specific links, doesn't check whether that numbered sense actually exists.
    Limitation: Won't complain about a link to "abba2" if only a single "abba" entry exists.'''

    #TODO: incorporate homograph numbers from hm fields
    #TODO: check citation form fields (lc, lse) in addition to lexeme form fields (lx, se)

    def check_link(val, entries, snippet):
        ''' Return an empty string if the link is ok. Otherwise, return an error/warning message. '''
        msg = None
        if val in entries and entries[val]:
            if len(entries[val]) > 1:
                msg = "ERROR: ambiguous link (multiple matches) in {}\n".format(snippet)
            else:
                pass # link is good
        else:
            msg = "WARNING: broken link in {} There is no record for that link target.\n".format(snippet)
        return msg
    
    good, bad, unsure = 0, 0, 0  # counters
    rep = '\nChecking links...  (for link fields {} targeting {})\n'.format(link_fields, entry_fields)
    entries, entries_stripped = build_indexes(recs, entry_fields)
    
    for rec in recs:
        L = rec.as_lists()
        lxval = L[0][1].strip()
        loc = rec.location
        j = 0
        for f, val in L:
            if f in link_fields:
                val = val.strip()
                val_s = NumStripper.strip_hom_num(val)
                snippet = "record ({}), which is near line {}; link in field {} (line {}?) pointing to target ({}).".format(lxval, loc, f, loc + j, val)
                msg_s = check_link(val_s, entries_stripped, snippet)
                if msg_s:
                    msg = check_link(val, entries, snippet) # re-check, non-stripped
                    if msg:  # still not clearly a good link
                        if val == val_s:
                            rep += msg_s
                        else:
                            rep += msg
                        bad += 1
                    else:
                        pass # the FLEx bug mentioned below has now been fixed
                        #rep += "POTENTIAL " + msg_s + " Actually, this is probably not a data error; might be problem for FLEx import, but only if homographs aren't numbered 'normally'. (LT-10733)\n"
                        #unsure += 1
                else:
                    good += 1
                    # The link is good. Now, check whether the targeted variant says I am its variant (circular)
                    if f in variant_fields:
                        if val in entries and entries[val]:
                            for _m, _n, entry in entries[val]:
                                for backref in entry.find_values(variant_fields):
                                    if NumStripper.strip_hom_num(backref) == NumStripper.strip_hom_num(lxval):
                                        rep += "VARIANT ERROR: entries {} and {} each refer to the other as the variant.\n".format(lxval, entry.as_lists()[0][1])
                                
                    
            j += 1
                
    rep += "Problematic (ambiguous or broken) links: {}\nClearly good links: {}\n".format(bad, good)
    #rep += "Problematic (ambiguous or broken) links: {}\nPossibly ambiguous (only for FLEx import) if homograph numbering/sorting isn't 'optimal' (bug LT-10733): {}\nClearly good links: {}\n".format(bad, unsure, good)
    
    return rep

def execute(args):
    ''' Being run as a script, so run diagnostics on the SFM file. '''
    print('Enter SFMTools.py -h to learn the command line options.')
    print('Starting... Verifying that the whole file is unicode (UTF-8)...')
    in_fname = args['infile']
    out_fname = args['outfile']
    if not out_fname:
        out_fname = in_fname + OUTFILE_EXT
    tmp = bad_encoding(in_fname, 'utf-8')
    if tmp:
        print('Aborted. (Can only process SFM files that are UTF-8 unicode.)')
        print(tmp)
        return
    
    with open(in_fname, encoding='utf-8') as infile:
        sfm_records = SFMRecordReader(infile)
        sfm_records = list(sfm_records)  # load entire file into memory
        with open (out_fname, mode='w', encoding='utf-8-sig') as outfile:  # The -sig includes a BOM, for explicit unicode
            outfile.write("Checking file {}... Verified that the whole file can be read in as unicode (UTF-8).\n".format(out_fname))
            report = get_stats(sfm_records)
            outfile.write(report)
            report2 = check_links(sfm_records)
            outfile.write(report2)
            report3 = "\nTrying to check numbering of senses/subsenses: delegating the task to SFMSenseNum.py...\n"
            try:
                import SFMSenseNum
                report3 += SFMSenseNum.check_sense_numbers(sfm_records) 
            except ImportError:
                report3 += "  Skipping test. Unable to find and import that module.\n"
            outfile.write(report3)
            print("The following console output may not display special characters. (On Windows, this is a limitation of the console.) See the output file for a proper unicode report.")
            try:
                print(ascii(report))
                print(ascii(report2))
                print(ascii(report3))
            except UnicodeEncodeError:  # But this won't happen if wrapped with ascii() above 
                print('Could not print report to the console due to unicode characters.')
    print('Done. Output saved to this file: {}'.format(out_fname))


if __name__ == '__main__':
    args = get_args() #get args as a dictionary
    execute(args)


