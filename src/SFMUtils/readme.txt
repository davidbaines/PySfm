
I don't know if you often have to clean up SFM files and other text files, but I do fairly often, so I've written some Python code to help me. (I get frustrated trying to work within the syntax and limitations of CC.) It may not be the most idiomatic Python, but by now I think it's fairly reusable and easy to read, so I thought I'd share it.

My ulterior motive is that if some of you find it useful, you may be able to help me improve the performance of the SFM module.

The first module is ApplyRE.py, which provides classes and a script for running a set of stored regular expressions on an input file. (This is quite similar in concept to  http://projects.palaso.org/projects/2prob , except that mine is in Python rather than .NET, does not have a GUI, and has some extra functions specific to SFM files.)

By default, it reads the regexes in from regex.txt, applies them one by one on lexicon.txt, and saves the result to lexicon-converted.txt. But those defaults can all be overridden via command-line parameters, if the user (or a batch file) knows how to specify those.

In the regex file, individual regexes can be quickly disabled (no need to delete them), and they can be set as multiline for the whole file ('broad'), or as multiline within specific SFM fields' contents ('narrow'). For example, here are two sample regexes that both do the same orthography change: they replace an "x" with "ks" when found after a vowel in the \lx field's contents, without changing other fields or changing \lx to \lks

-----------------
##Replace post-vocalic x with ks within the vernacular field, \lx
*
^(\\lx\b.*[aeiou])x(.*)$
\1ks\2

##Replace post-vocalic x with ks within the vernacular field, \lx
lx
([aeiou])x
\1ks
-----------------

The latter could just as easily have specified a list of fields such as "lx se va cf sy an lf gv xv" rather than just "lx", without complicated the regex itself. But the former is able to also modify field markers--e.g. rename non-standard ones to MDF, delete entire fields, or even move fields around.

When applicable, the latter regexes are much easier and safer to write, but the code currently runs VERY slowly on large files. This is because the 'narrow' regexes rely on a second module, SFMTools.py, which is very slow. It lets you iterate through an SFM file record by record, and field by field within each record, with each field broken into halves--marker and data. You change only what you want to, and it can then piece it back into plain text with the original whitespace and Toolbox header info preserved.

Anyway, I would welcome any ideas you might have, especially if there are ways to code this to be faster (in Python, not C, and easy-to-read is preferred). Currently, on a large file, each broad regex takes only a couple hundred milliseconds to complete, but a narrow one takes about 130,000 milliseconds (i.e. about 2 minutes). I'd like to speed this up so a couple dozen narrow regexes could run reasonably quickly (no more than 5 min total?).

Here are the tools and a small sample, in a zip file (a large sample is available on request):
https://www.sugarsync.com/pf/D342747_6399192_132531

Blessings,
Jon

