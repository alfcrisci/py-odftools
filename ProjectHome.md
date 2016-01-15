This project is a collection of tools for analyzing, converting and creating files in the ISO standard OpenDocument format.

The utilities attempt to cover the lightweight portions of OpenOffice.org's ODF Toolkit project (sans UNO), as well as Rob Weir's proposal for an OpenDocument Developer's Kit:

http://odftoolkit.openoffice.org/

http://opendocument.xml.org/node/154


See also:
http://opendocumentfellowship.com/projects/odfpy

## Current Features ##

### Command-line interface: ###

  * Powerful interface for batch scripting
  * Output document contents as HTML, XML or plain text
  * Print a list of authors for all input files
  * Regular-expression replacement of strings inside the document
  * Convert an ODF document to and from SQLite as a binary string blob
  * Written entirely in Python, so it's usable anywhere Python is available

### Additional library functions: ###

  * Parse and serialize ODF documents
  * Get individual document components (content, styles, metadata, app settings, etc.), as an XML string
  * Extract objects embedded in the document using regular expressions or UNIX-style glob patterns
  * Determine the correct file extension based on the mimetype
  * Scan a directory for ODF files