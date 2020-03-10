# First Order Logic Compiler
## How to run the program
* Ensure the following prerequisites are installed:
  * Python, version 3.7.4
  * Python modules ‘sys’, ‘re’, ‘operator’, ‘networkx’, ‘matplotlib’
  * Command-line terminal
* Place input text file in the same directory as parser.py
* In a command-line window, run ‘python parser.txt \<yourfile>.txt’, replacing \<yourfile>.txt with the name of the input file
* Result:
  * If your input file is valid, the production rules for first-order logic using the input sets will be saved to \<yourfile>.grammar.txt and displayed in the terminal. If not, the program will indicate where the problem is and immediately exit.
  * The program will tell you if your formula is valid or not. If not, it will indicate where the problem is and immediately exit.
  * If your formula is valid, its parse tree will be saved to \<yourfile>.png.
  * A log file, \<yourfile>.log.txt, will be produced, containing information about the validity of the input file and formula. This information is also displayed in the terminal as it is added.
  
## Input file format
* The input file must contain the 7 set names, each followed by the contents of that set.
* The set names are as follows:
  * variables
  * constants
  * predicates
  * equality
  * connectives
  * quantifiers
  * formula
* Sets ‘variables’ and ‘constants’ can have any finite cardinality >= 0, and each element must be alphanumeric (including underscores)
* Set ‘predicates’ can also have any finite cardinality, and each element must have an alphanumeric (including underscores) string followed by a number in square brackets (e.g. P[3])
* Set ‘equality’ contains exactly one string corresponding to =. This string must be alphanumeric including underscores, equals signs and backslashes.
* Set ‘connectives’ contains exactly five strings corresponding to ∧,∨,⇒,⇔,¬ in that order. These strings must be alphanumeric including underscores and backslashes.
* Set ‘quantifiers’ contains exactly two strings corresponding to ∃,∀ in that order. These strings must be alphanumeric including underscores and backslashes.
* Set ‘formula’ contains a formula constructed only from the elements of the previous six along with the characters ‘(‘, ‘)’ and ‘,’
* Newlines and spaces are removed in the program and therefore have no effect on the input file.
* Example input files (valid and invalid) are provided in the Examples/ folder.

## Output file format
* The grammar file will contain the grammar of the provided language and the formula itself. The grammar consists of the following sets:
  * Terminal symbols
  * Non-terminal symbols
  * Start symbol
  * Production rules
* The parse tree image will contain the parse tree itself and the legend for the parse tree.
* The log file will contain information about the success or failure of each phase of the program's execution.
