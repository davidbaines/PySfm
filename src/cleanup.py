import SFMTools as sfm

def applyRE():
    '''NOT yet written
    Load a set of regexes from a file and loop through them, applying them to the entire 
    file (markers, newlines, and all).
    Not specific to SFM files; can be used with any text file.
    '''
    pass


if __name__ == '__main__':
    fnamein='Kamus-sh_test.db'
    fnameout='Kamus-sh_out.db'
    print("Starting SFM cleanup processing...")

    fields_narrow = ('lx','se')
    pats_narrow = [ 
        (r'a', r'z'), #replace all aa with zz
        (r'\n+(\n\\)', r'\1') #remove extra whitespace; basically equivalent to rtrim() and print()
    ]

    with open(fnamein, encoding='utf-8') as infile:
        with open(fnameout, mode='w', encoding='utf-8') as outfile:

            records = sfm.SFMRecordReader(infile, "lx")
            outfile.write(records.header)
            rcount = 0
            for record in records:

                #get the record in broken down form
                record = sfm.break_record(record)
                
                #record = regex.apply_regex_narrowly(record, ('lx',))


                #record = sfm.add_missing_gn(record)
                #record = rf_to_so(record)
                #record = handle_rf(record)
                #record = add_field(record, ('ps','pn'), ('ge','gv','gn','de','dn','dv'), ('sn', '\n'))

                #done modifying the record; write it out to the file
                tmp = sfm.join_as_str(record)
                outfile.write(tmp)
                
                rcount += 1
                #if rcount > 5: break


            print("{} records processed. Done.".format(rcount))


    '''

    #by field
    with open('Kamus-sh-tmp.db', encoding='utf-8') as infile:
        with open('Kamus-sh-out.db', mode='w', encoding='utf-8') as outfile:
            i=0
            fields = Sfmfieldreader(infile)
            outfile.write(fields.header)
            for field in fields:
                #write the string out directly
##                outfile.write(field)

                #TEST: break the string, then reconnect it and write it out
                [marker,data] = SfmUtils().breakfield(field)
                spc=" "
                if data[0]=="\n": spc=""
                outfile.write("\\" + marker + spc + data)
#                print(field, end='')

                i+=1
#                if i>5: break  #only process the first few fields

    '''
    
    '''
    #by record
    with open('Kamus-sh-tmp.db', encoding='utf-8') as infile:
        with open('Kamus-sh-out.db', mode='w', encoding='utf-8') as outfile:
            i=0
            records = SFMRecordReader(infile, "lx")
            outfile.write(records.header)
            for record in records:
                tmp = ""
                for field in record:                   
                    #write the string out directly
##                    tmp += field
                    
                    #TEST: break the string, then reconnect it and write it out
                    [marker,data] = SfmUtils().breakfield(field) #records.fields.breakfield(field)
                    spc=" "
                    if data[0]=="\n": spc=""
                    tmp += "\\" + marker + spc + data
                    
#                print(tmp, end='')
                outfile.write(tmp)
                i+=1
#                if i>3: break  #only process the first few records


    print("{} records processed. Done.".format(i))
    '''

