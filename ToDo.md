## To Fix ##

_If the problem is specific, consider using the issues tracking system._

Unit tests: toHtml tests are broken

## To Add ##


### Command line ###
  * Review options, names and descriptions
  * Determine how to handle stdout and stdin using command-line args
    * stdout seems to be a reasonable default for most text output, e.g. authors


### ODF generation ###
  * Take:
    * File path (list of file paths)
    * File stream passed to function
    * String passed as an option (useful for shell scripting)
  * Convert other formats to basic ODF documents
    * HTML
      * Convert an HTML string to an ODF Document object (content)
      * Follow CSS style tags and stylesheet links (style)
      * Follow embedded objects, copy, save in ODF document
    * Plain Text
    * ReStructured Text
      * http://docutils.sf.net/
    * LaTeX
      * Good reasons to attempt lossless translations:
        * Allow group editing of documents by both plain-text editors like emacs and word processors like OOo.
        * Lots of powerful tools already exist for LaTeX
        * Easier for diff if xml diffing gets too hairy
    * Character-separated values:
      * Default for spreadsheets? Implement for spreadsheets only?
      * Comma and tab are pretty standard, but the function should take an arbitrary separator (maybe make tab the default)


### HTML output ###
  * CSS translation
    * See cssutils
    * Copy style names verbatim, in element tags and associated CSS stylesheet
    * The stylesheet in the header will be extracted from `styles.xml`
    * Needs a separate function/module for translating between ODF XML and CSS
  * Embedded objects / images
    * Where do I put the extracted objects? New subdirectory, existing directory? Create a new folder for the html output package?
    * If the object can't be displayed, create a link and some reasonable text in its place
  * Forms


### Other plain-text output ###
  * ReStructured Text
  * LaTeX
  * Wiki markup
    * NB: there's more than one kind


### Other OpenDocument types ###
  * **Spreadsheets**
    * A series of ODF tables.
    * Problem: dealing with formulas and charts effectively
      * Plain text --> csv
      * HTML --> ignore functions, just print values in tables, embed charts as graphics
      * 
    * Reasonable applications:
      * Convert spreadsheet tables to database tables
      * Handle data with other statistical software -- R, SAS, Stata, SPSS, plot...
  * **Drawings**
    * An ODF drawing file is a sequence of draw pages.
  * **Presentation**
    * Same as an ODF drawing, but with optionall additional declarations in the prelude
    * Reasonable applications:
      * Convert to/from basic outlines (.odt, XML, plaintext) and flowcharts (graphvis)
        * this could be a pit for endless tinkering -- and therefore cool
      * HTML, obviously -- create a new folder for a sequence of html pages
  * **Chart**
    * Charts are always contained within othe XML documents. The containing document **may** provide data for the chart -- or the data table (a table element) may instead be included in the chart itself.
    * Reasonable applications:
      * There are powerful graphing applications outside OOo and Koffice -- export to their input formats
      * Convert to a pure SVG image, losing the data table
      * Extract just the data table, wherever it is.


### Diff ###
  * See [Xmldiff](http://freshmeat.net/projects/xmldiff/)
  * Per-word diffing of `contents.xml` from each file is a good place to start; `styles.xml` is nice to have.
    * ENH: Let the user select which components are included in the diff operation
  * ENH: Re-implement "track changes" as a diff patch to be included in the ODF file.


### Merge/Concatenate ###
  * Command-line syntax could take the general form of a Python list comprehension. Automatically extract DOM nodes from each input document and join the output list of nodes into a new document.
```
    [some_transform(node) for node in some_filter(input_file_1, input_file_2)]
```

  * **Document templating system**
    * e.g. set up an interface for generating new documents with a predetermined set of styles, including headers, footers etc.
    * Also make an interface for generating reports using this system.


### Miscellaneous functions: ###
  * Compact document:
    * Clean up styles: If two or more styles have the same attributes, pick one name for all of them and delete the other styles.
    * Normalize nodes: If adjacent text nodes have no stylistic difference, merge them
    * Extreme: clear app settings and pointless metadata
      * define "pointless" -- everything that's not required by the ODF specification?



## Links ##

  * OpenOffice.org's ODF Toolkit project: http://odftoolkit.openoffice.org/

  * Rob Weir's proposal for an OpenDocument Developer's Kit: http://opendocument.xml.org/node/154

  * Bob Sutor's Dr. ODF project/blog series: http://www.sutor.com/newsite/blog-open/?cat=93




