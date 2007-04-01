PYTHON ODF TOOLS

Py-ODFTools is a Python library for handling OASIS Open Document Format (ODF) 
files. This collection of tools allows analysing, converting and creating 
ODF files.

These utilities attempt to cover the lightweight portions of Rob Weir's
proposal for an OpenDocument Developer's Kit:
http://opendocument.xml.org/node/154

The full OASIS OpenDocument specification can be found here:
http://www.oasis-open.org/specs/index.php#opendocumentv1.0

Project homepage:
http://


This package contains the following files:

1. odf.py
    1.1 Options
    1.2 Examples
    1.3 Attention

2. document.py
    2.1 Methods

3. diff.py



______________________________________________________________________________
1. odf.py 

Provides a powerful command line interface for batch scripting.

One or multiple actions can be done separately to each input file.
Each different output action results in an output file.

Multiple input files can be passed as directories and/or file filters.
File filters can be file names, globs and/or regular expressions.
If a relative or absolute file name is not found, the directory will be
searched for all ODF files which match the filter.
So * would find odc, odf, odg, odi, odm, odp, ods, odt, otg, otp, ots, ott.



Options:
--------

--selftest 

Just executes all unittests and returns.
By default it writes to stderr, but you can write to file or stdout instead.


--help 

Prints the usage guide and options to standard output.


--recursive 

Searches directories recursively.
The optional argument LEVEL specifies the maximum recursion level.
For every file filter the current folder is the start directory.


--include FILE 

All found files must match the include FILE pattern.


--exclude FILE 

All found files must not match the exclude FILE pattern
(after they have matched the --include FILE pattern).


--case-insensitive 

Ignores case for every file name matching, except directory
parts of file arguments on case-sensitive operating systems like UNIX
(use --include instead).


--file changes the default output file name.

The default output file name is the absolute input file name.


--extension-replace 

Changes the output name extension to .txt, .xml, .html or the same ODF 
extension as the input file has.


--extension-append 

Appends .txt, .xml, .html or the same ODF extension as the
input file has (deactivates --extension-replace).


--directory 

Changes the output path (returns if directory doesn't exist).


--force 

Allows overwriting of existing files!


--replace 

Replaces all occurences of a search expression by a replacement
expression before any other action occurs.
Only text nodes of content.xml will be affected.


--tohtml 

Converts the input file to a HTML representation.


--totext 

Converts the input file content.xml to a plain-text representation.


--toxml 

Outputs the input file content.xml.


--toodf 

Outputs the input file even if no data was changed.

Even if --toodf is not given, ODF output will be written if no conversion
was done but data was changed.
No non-ODF data will be written to input file names, even if --force.
The corresponding warning will not be print if --stdout is given and --file
is not given.

All conversion options take an optional argument for writing to a different
output file. It will be preferred over the --file option and disregards the
--extension-* options.


--stdin 

Reads the contents of one input file from stdin prior to processing any
other input files (if data is available). Default output file name is "stdin".


--stdout 

Prints any output except ODF data to the console in addition to
eventually writing output files.


--quiet 

Suppresses all output to stdout.


--verbose 

Provides more informational output.


--list-authors 

Outputs a list of authors for all input files.
The optional argument FILE specifies the output file name.


The preferred order is to pass the file pattern arguments first, then options:
    python odf.py dir/a*.ods --list-authors authors.txt --toxml --extension-append

Especially (optional) option arguments have to follow their options directly:
    python odf.py /*.od[ts] --replace s([e])arch r\\1place
    python odf.py a.odt --tohtml dir/output.html dir/search*.odg



Examples:
---------

Replace text in documents, convert them to text and print the result.

    python odf.py /* --replace s r --totext --stdout


Replace text, convert to HTML and save with appended .html extension.

    python odf.py / --replace s r --tohtml --extension-append


Search recursively, replace text and overwrite only changed input files.

    python odf.py * --replace s r --recursive --force


Search recursively, replace text and overwrite all input files.

    python odf.py . --replace s r --recursive --force --toodf


Search recursively (maximum 2 levels), print authors to stdout and file.

    python odf.py /a* /b/c* --recursive 2 --list-authors authors.txt --stdout


Search multiple directories recursively, filtering by include and exclude

    python odf.py /dir1 /dir2/dir3 --recursive 2 --include job --exclude work -v


Convert document to HTML and text and save with different file names.

    python odf.py a.odt --tohtml b.htm --totext c.log --file=for_unspecified_opts



Attention:
----------

--extension-replace could lead to an output filename of an input file.

--toodf or changed ODF data and no conversions result in ODF output.

Examples:

Write new ODF files even when no data was changed.
    python odf.py * --replace s r --toodf --extension-append

Overwrite input file if data was changed.
    python odf.py a.odt --force --replace s r

Do not overwrite input file EVEN if data was changed! A warning message
will be printed that writing text to input file is not permitted.
    python odf.py a.odt --force --replace s r --totext

Print to stdout but suppress text-to-ODF warning even if data was changed.
    python odf.py a.odt --force --replace s r --totext --stdout

But: write to input file even if data was not changed.
    python odf.py a.odt --force --replace s r --totext --stdout --toodf



______________________________________________________________________________
2. document.py

Provides the document object model and methods for manipulating the document.

Most of these methods are available through the command-line interface, but
a few are not.

Methods:
--------



______________________________________________________________________________
3. diff.py


Not implemented yet.

The goal is to accept two files as input and return a document with the 
differences marked in the "track changes" mode.


