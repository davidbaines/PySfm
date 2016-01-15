#! /usr/bin/python3

'''This Python 3.x module provides functions for identifying and working with minor entries in an SFM lexicon.
When run as a script, it uses SFMTools to build indexes of all words (typically lx and se) and then it 
compares to them the value in the minor entry's reference field (typically mn). If they match, it then 
checks the main entry for a reference (e.g. va or se) that matches this minor entry and appends that 
marker name to the minor entry's reference marker (e.g. changing mn to mnva or mnse).

After all this is done, you also have the separate option of saving entries into separate files if they 
contain any of a set of specified fields. The idea is that you might use this to split out mnse.
'''

from SFMUtils import SFMTools as sfm # You'll want to review the constants there as well.

#INFILE = 'D:/files/aa-synced/jon/otherproj/vandenberg-muna/Muna Dict 13 Dec 2012 utf8.txt'
INFILE = 'D:/files/aa-synced/jon/otherproj/pular-oumar-bah/My Shoebox Settings/Dictionnaire pular.db'
INFILE = 'Akawaio.db'

MINOR_MKRS = ('mnse', 'mnva') # typically 'mn'; entries containing these markers will be processed as minor entries
#MINOR_MKRS = ('mnxx',)
#MINOR_MKRS += ('cf', 'cflx',)  # for Akawaio
DONT_INDEX_IF = MINOR_MKRS # entries containing these fields are definitely minor entries; that is, redundant rather than homographs of the se/va
SPLIT_OUT = () # entries containing these markers will be split into separate files


#SPLIT_OUT = ('mnse', 'mn', 'mnva', 'mnvavalx', 'mnvalx', 'mnvase')
#SPLIT_OUT = MINOR_MKRS
SPLIT_OUT = ('mn', 'xyz')

BACKREF_MKRS = ('va', 'se') # will be appended when they match; e.g. turning mn into mnva or mnse
#BACKREF_MKRS += ('vase', 'valx')
#BACKREF_MKRS += ('vasn', 'seco')
BACKREF_MKRS += ('valx', 'lxS', 'lxW', 'vaN', 'vaW', 'vaS', 'vaSW', 'vaNW', 'vaNS', 'vaNSW')

def execute():
    in_fname = INFILE
    out_fname = INFILE + '.out.txt'
    # generate output filenames and open them (SPLIT_OUT can be a list of any length)
    temp = [[x, INFILE + '.' + x + '.txt'] for x in SPLIT_OUT]
    out_fnames = dict(temp)
    out_files = dict()
    for o in out_fnames:
        fn = out_fnames[o]
        f = open(fn, mode='w', encoding='utf-8')
        out_files[o] = f
        f.write("File created by SFMMinor.py while splitting out minor entries marked by {}\n\n".format(o))

    with open(in_fname, encoding='utf-8') as infile:
        sfm_records = sfm.SFMRecordReader(infile)
        recs = list(sfm_records)  # load entire file into memory
        entries, _entries_stripped = sfm.build_indexes(recs, exclude_fields=DONT_INDEX_IF)

        with open(out_fname, mode='w', encoding='utf-8') as outfile:
            outfile.write(sfm_records.header)

            for rec in recs:
                r = rec.as_lists()
                is_minor = rec.find_first(MINOR_MKRS)
                if is_minor:
                    minlx = r[0][1].strip()
                    report = "Probable minor entry {} identified due to link {}".format(minlx, str(is_minor))
                    #Strip it down to ASCII so the console can handle it
                    report = report.encode('ascii', 'replace')
                    #print(report)
                    mn = is_minor[1].strip()
                    matches = [main[2] for main in entries[mn]]
                    if len(matches) > 1:
                        print("ERROR: ambiguous link.")
                        print(report)
                    for main in matches:
                        for bref in BACKREF_MKRS:
                            found = main.find_values(bref)
                            if minlx in found:
                                #The following needs to be stripped down to ASCII
                                #print("  Main entry found ({}); it mentions the minor entry here: {} {}".format(main.as_lists()[0], bref, str(found)))
                                if not is_minor[0].endswith(bref):
                                    #The following needs to be stripped down to ASCII
                                    #print("  Updating the minor entry by appending {} to marker {}.".format(bref, is_minor[0]))
                                    is_minor[0] += bref
#                                print(rec.as_string())
                                break
                
                s = rec.as_string()
                if SPLIT_OUT:
                    found = rec.find_first(SPLIT_OUT)
                    if found:
                        f = out_files[found[0]]
                        #The following needs to be stripped down to ASCII
                        #print("  Removing entry {} from the main file since it contains field {}; saving it in {} instead".format(rec.as_lists()[0], found, f))
                        f.write(s) # write the minor entry out to the appropriate separate file
                        s = ''
                outfile.write(s)
    
    print("Done writing to file {}".format(out_fname))
    for o in out_files:
        out_files[o].close()
        print("Done writing to file {}".format(out_fnames[o]))


if __name__ == '__main__':
    execute()


