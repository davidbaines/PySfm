from SFMUtils import SFMTools as S
from SFMUtils import SFMToolsUgly as sfm

if __name__ == '__main__':
    fnamesrc = r'D:\files\aa-synced\jon\aa-do-medium\tado\tado-saku\2009-05\erik\erik-from-kingston-sd-card\what janet sent erik 1\2009-03 kamustado given to Erik March 2009 - no dt - sort.db'
    fnamesrc = r'D:\files\aa-synced\jon\aa-do-medium\tado\tado-saku\2009-05\erik\erik-from-kingston-sd-card\kamustado-from-erik\2009-06-30-kamustado-from-erik-jv-no-dt.db'
    fnamein = r'D:\files\aa-synced\jon\aa-do-medium\tado\tado-saku\2009-05\erik\2010-03-10-kamustado-from-erik-no-dt-fixed7.db'
    fnameout = r'D:\files\aa-synced\jon\aa-do-medium\tado\tado-saku\2009-05\erik\2010-03-10-kamustado-from-erik-no-dt-fixed8tmp.db'
    print("Replacing corrupted se back from dn to se ...")

    with open(fnamein, encoding='utf-8') as infile:
        with open(fnamesrc, encoding='utf-8') as srcfile:
            with open(fnameout, mode='w', encoding='utf-8') as outfile:

                srcrecords = list(S.SFMRecordReader(srcfile, "lx"))
                srclexemes = sfm.get_lexemes(srcrecords)
                
                rec = S.SFMRecordReader(infile, "lx")
                outfile.write(rec.header)
                records = list(rec)
                lexemes = sfm.get_lexemes(records) #just for convenience
                
                r, s = -1, -1  
                while r < len(records):
                    r += 1
                    s += 1
                    if r >= len(records) or s >= len(srcrecords):
                        break
    
                    #get the record in broken down form
                    record = sfm.break_record(records[r])
                    
                    dofix = True
                    if lexemes[r] != srclexemes[s]:
                        #mis-aligned; try to find a match within the next 5 src records
                        dofix = False
                        for j in range(1, 6):
                            if s+j >= len(srclexemes): break
                            if srclexemes[s+j] == lexemes[r]:
                                #found a match; re-align
                                s = s+j
                                dofix = True
                                break
#                        if not found:
#                            r += 1
#                            continue #skip this record entirely

                    if dofix:
                        srcrecord = sfm.break_record(srcrecords[s])
                        for k in range(0,8): #in case there are multiple clusters; e.g. xv xn xv xn xv xn
                            record = sfm.fix_corrupted_marker(record, srcrecord, 'dn', 'se')
                            record = sfm.fix_corrupted_marker(record, srcrecord, 'dn', 'xv')
                            record = sfm.fix_corrupted_marker(record, srcrecord, 'dn', 'xn')
                            record = sfm.fix_corrupted_marker(record, srcrecord, 'xv', 'mn')
                    else:
                        #print("skipping record {} (srcrecord is {})".format(lexemes[r], lexemes[s]))
                        s -= 1 #don't really increment this counter till next time
    
                    #done modifying the record; write it out to the file
                    tmp = sfm.join_as_str(record)
                    outfile.write(tmp)
                    #outfile.write(record)
                    
                    if r % 100 == 0 : 
                        print('{}. done with {}'.format(r, record[0]))
    
    
                print("{} records processed. Done.".format(r))
                
