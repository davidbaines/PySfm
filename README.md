# PySfm
Utilities for processing SFM files, which use backslashed markers to start each field. The most useful tools are probably these:

SFMTools.py - Automatically parses and analyzes  SFM files, especially lexicons. To see how to use it, run it with -h (readme.bat), or look at SFMToolsRun.bat . It can also be loaded as a utility module, which the other scripts often do.

ApplyRE.py - Run a series of regex find/replace operations in order, loading them from a config file (ApplyRE.regex.txt by default). Run it with -h for more info, or look at ApplyRErun.bat . Optionally, you can limit a regex to specific SFM fields; this is often safer/easier, but it's slow. (That one feature requires SFMTools.py, which you can simply put in the same location as ApplyRE.py.)

SFMPS.py - Works around flaws in FLEx import by helping you ensure that sn and ps are correct (and ideally, one to one). Can be run in several modes.



Less useful scripts are:

SFMMinor.py - Identifies and manipulates minor entries, which are tiny entries (for variants or complex forms) that point to a main entry. These often cause import headaches. It's not perfect at handling all homograph and sense number combinations. "When run as a script, it uses SFMTools to build indexes of all words (typically lx and se) and then it compares to them the value in the minor entry's reference field (typically mn). If they match, it then checks the main entry for a reference (e.g. va or se) that matches this minor entry and appends that marker name to the minor entry's reference marker (e.g. changing mn to mnva or mnse). After all this is done, you also have the separate option of saving entries into separate files if they contain any of a set of specified fields. The idea is that you might use this to split out mnse."

SFMSenseNum.py - "This module checks an SFM lexicon's senses for proper sequential numbering." The SFMTools.py analyzer will run this test if it detects that it's located next to it. This script can also be quickly tweaked to do one specific kind of sn fix: "number_subs : Copy and pre-pend to each subsense the number from its parent. Assumption: All subsenses to be numbered begin with a period. All that don't have any period can be treated as full senses here."

SFMToolsUgly.py , cleanup.py , etc. - Somewhat hard-coded or brittle solutions I wrote for specific problems. 

MORE INFO on ApplyRE:

I don't know if you often have to clean up SFM files and other text files, but I do fairly often, so I've written some Python code to help me. (I get frustrated trying to work within the syntax and limitations of CC.) It may not be the most idiomatic Python, but by now I think it's fairly reusable and easy to read, so I thought I'd share it.

My ulterior motive is that if some of you find it useful, you may be able to help me improve the performance of the SFM module.

The first module is ApplyRE.py, which provides classes and a script for running a set of stored regular expressions on an input file. (This is quite similar in concept to  http://projects.palaso.org/projects/2prob , except that mine is in Python rather than .NET, does not have a GUI, and has some extra functions specific to SFM files.)

By default, it reads the regexes in from regex.txt, applies them one by one on lexicon.txt, and saves the result to lexicon-converted.txt. But those defaults can all be overridden via command-line parameters, if the user (or a batch file) knows how to specify those.

In the regex file, individual regexes can be quickly disabled (no need to delete them), and they can be set as multiline for the whole file ('broad'), or as multiline within specific SFM fields' contents ('narrow'). For example, here are two sample regexes that both do the same orthography change: they replace an "x" with "ks" when found after a vowel in the \lx field's contents, without changing other fields or changing \lx to \lks

```regex
  ##Replace post-vocalic x with ks within the vernacular field, \lx
  *
  ^(\\lx\b.*[aeiou])x(.*)$
  \1ks\2

  ##Replace post-vocalic x with ks within the vernacular field, \lx
  lx
  ([aeiou])x
  \1ks
```

The latter could just as easily have specified a list of fields such as "lx se va cf sy an lf gv xv" rather than just "lx", without complicated the regex itself. But the former is able to also modify field markers--e.g. rename non-standard ones to MDF, delete entire fields, or even move fields around.

When applicable, the latter regexes are much easier and safer to write, but the code currently runs VERY slowly on large files. This is because the 'narrow' regexes rely on a second module, SFMTools.py, which is very slow. It lets you iterate through an SFM file record by record, and field by field within each record, with each field broken into halves--marker and data. You change only what you want to, and it can then piece it back into plain text with the original whitespace and Toolbox header info preserved.

Anyway, I would welcome any ideas you might have, especially if there are ways to code this to be faster (in Python, not C, and easy-to-read is preferred). Currently, on a large file, each broad regex takes only a couple hundred milliseconds to complete, but a narrow one takes about 130,000 milliseconds (i.e. about 2 minutes). I'd like to speed this up so a couple dozen narrow regexes could run reasonably quickly (no more than 5 min total?).

Here are the tools and a small sample, in a zip file (a large sample is available on request):
https://www.sugarsync.com/pf/D342747_6399192_132531

Blessings,
Jon

