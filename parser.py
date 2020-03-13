import sys
import re
import networkx as nx
import matplotlib.pyplot as plt
import operator

def writeLog(string, end='\n'):
    global logFile
    print(f"LOG: {string}", end=end)
    logFile.write(string+end)

def exitLog(string, code=1, end='\n'):
    writeLog(string, end)
    logFile.close()
    sys.exit(code)

# verify command-line arguments
if (len(sys.argv) == 2):
    fileNameSplit = sys.argv[1].split('.')
    fileName = '.'.join(fileNameSplit[0:-1])
    fileExtension = fileNameSplit[-1]
else:
    print(f"ERROR: wrong number of command-line arguments {len(sys.argv) - 1}. Exactly one (the input text file name) must be provided.")
    sys.exit(0)

logFile = open(f"{fileName}.log.{fileExtension}", 'w')

# read specified file
try:
    file = open(f"{fileName}.{fileExtension}", "r")
    fileContents = file.read()
    file.close()
    writeLog(f"Contents of input file {fileName}.{fileExtension} successfully read")
except FileNotFoundError:
    exitLog(f"INVALID FILE: File '{fileName}.{fileExtension}' not found.")

# replace each sequence of whitespace with a single space char
fileContents = ' '.join(fileContents.replace('(', ' ( ').replace(')', ' ) ').replace(',', ' , ').split())

#fileContents = fileContents.replace('\t', ' ').replace('\n', ' ').replace('\r', '')#.replace(', ', ',')

# initialise regex patterns to verify and extract data from the text file itself
#allSetsPattern = re.compile(r'^(?:\w+:\s*(?:(?!\s*\w+:).)+\s*){7}$') # verify file contains seven key: value pairs
#allSetsPattern = re.compile(r'^(?:\w+:\s*(?:(?!\s*\w+:)[\w\s\[\]\=\\\(\)\,])+\s*){7}$') # verify file contains seven key: value pairs
allSetsPattern = re.compile(r'^(?:\w+:\s+(?:(?!\s*\w+:)(?!:).)*\s*){7}$') # verify file contains seven key: value pairs
#oneSetPattern = re.compile(r'(\w+):\s*((?:(?! \w*:).)+)\s*') # extract each key:value pair
oneSetPattern = re.compile(r'(\w+):\s+((?:(?!\s*\w+:)(?!:).)*)') # extract each key:value pair
allPredDefsPattern = re.compile(r'^(?:(?:\w+)\[(?:\d+)\]\s*)+$') # verify predicate definition is name[arity] format
onePredDefPattern = re.compile(r'(\w+)\[(\d+)\]') # retrieve names and arities

# check whole file is valid
if allSetsPattern.match(fileContents) == None:
    exitLog("INVALID FILE: Invalid file format (must be 7 \"key: values\" pairs)")
writeLog("Found 7 \"key: values\" pairs in file")

# add key-value pairs to dictionary
setsDict = {m.groups()[0]: m.groups()[1] for m in oneSetPattern.finditer(fileContents)}

setRules = {
    "variables": [r'\w+'], # '\w' == '[a-zA-Z0-9_]'
    "constants": [r'\w+'],
    "predicates": [r'\w+\[\d+\]'],
    "equality": [r'[\w=\\]+', 1],
    "connectives": [r'[\w\\]+', 5],
    "quantifiers": [r'[\w\\]+', 2],
    "formula": [r'.+']
}

# list set names to make sure they are all there
for setName in setRules:
    if setName not in setsDict:
        exitLog("INVALID FILE: Missing set '{}'".format(setName))
writeLog("Keys/set names are correct")

# init list of symbols
terminalSymbols = {"(", ")", ","}
##  PRODUCTION RULES
# init production rules based on FO logic rules
productionRules = {
    "formula": [
        ("quantifier", "variable", "formula"),
        ("(", "formula", "connective_binary", "formula", ")"),
        ("connective_unary", "formula"),
        ("(", "term", "equality", "term", ")"),
        ("predicate",)
    ],
    "term": [("variable",), ("constant",)],
    "variable": [],
    "constant": [],
    "quantifier": [],
    "connective_unary": [],
    "connective_binary": [],
    "equality": [],
    "predicate": []
}
nonTerminalSymbols = set(productionRules.keys())

# create dictionary and list of symbols, check for duplicates
for (setName, setString) in setsDict.items():
    #print(f">{setName}<|>{setString}<")
    cardinality = None # any
    allowedString = setRules[setName][0]
    if len(setRules[setName]) > 1:
        cardinality = setRules[setName][1]
    if re.compile(fr'^(?:(?:{allowedString})\s*)*$').match(setString) == None:
        exitLog(f"INVALID FILE: Invalid format for set '{setName}' (expected match(es) with regex '{allowedString}', got '{setString}')")
    setContent = [m.group() for m in re.compile(fr'{allowedString}').finditer(setString)]
    if setName == "formula":
        setContent = setContent[0]
    else:
        if setName == "predicates":
            setContent = [m.groups(0) for m in onePredDefPattern.finditer(' '.join(setContent))]
            # convert arities to integers
            for i in range(len(setContent)):
                setContent[i] = (setContent[i][0], int(setContent[i][1]))
            setSymbols = [symbol for symbol, arity in setContent]
        else:
            if (cardinality != None) and (len(setContent) != cardinality):
                exitLog(f"INVALID FILE: Incorrect cardinality for set {setName} (expected {cardinality}, got {len(setContent)})")
            setSymbols = setContent

        for symbol in setSymbols:
            if symbol in terminalSymbols:
                exitLog(f"INVALID FILE: Duplicate symbol ('{symbol}') found in set '{setName}'")
            elif symbol in nonTerminalSymbols:
                exitLog(f"INVALID FILE: Reserved symbol ('{symbol}') found in set '{setName}'")
            terminalSymbols.add(symbol)
    setsDict[setName] = setContent
writeLog("Successfully created symbol lists for terminals and for each input set")

# add production rules based on symbol sets in text file
for variable in setsDict['variables']:
    productionRules['variable'].append((f'{variable}',))

for constant in setsDict['constants']:
    productionRules['constant'].append((f'{constant}',))

for quantifier in setsDict['quantifiers']:
    productionRules['quantifier'].append((f'{quantifier}',))

productionRules["connective_unary"].append((f"{setsDict['connectives'][-1]}",)) # quantifiers, connectives and equality are always in the same order

for connective_binary in setsDict['connectives'][0:-1]:
    productionRules["connective_binary"].append((f'{connective_binary}',))

productionRules['equality'].append((f"{setsDict['equality'][0]}",))

for predicate in setsDict['predicates']:
    symbol = predicate[0]
    arity = predicate[1]
    rule = []
    rule.append(symbol)
    rule.append('(')
    for i in range(arity):
        rule.append('variable')
        if i < arity-1:
            rule.append(',')
    rule.append(')')
    productionRules['predicate'].append(tuple(rule))

# display sets of symbols
displayString = []

displayString.append("TERMINAL SYMBOLS:\n")
displayString.append(' '.join(terminalSymbols))
displayString.append('\n\n')

displayString.append("NON-TERMINAL SYMBOLS:\n")
displayString.append('  '.join(nonTerminalSymbols))
displayString.append('\n\n')

displayString.append("START SYMBOL:\n")
displayString.append('formula')
displayString.append('\n\n')

prefix = [' ', '| ']
displayString.append("PRODUCTION RULES:\n")
for start, productions in productionRules.items():
    startString = f"{start} ->"
    displayString.append(startString)
    for i in range(len(productions)):
        displayString.append(' '* (len(startString)-1) * bool(i)) # note: bool(i) is false/zero only for first element and true/one on all others
        displayString.append(prefix[bool(i)])
        for j in range(len(productions[i])):
            if productions[i][j] in terminalSymbols:
                displayString.append(f"{productions[i][j]} ")
            else:
                displayString.append(f"{productions[i][j]} ")
        displayString.append('\n')
    displayString.append('\n')

formula = setsDict['formula']

displayString.append("FORMULA: \n")
displayString.append(formula)
displayString.append('\n')

displayString = ''.join(displayString)

writeLog("Created production rules")
print(displayString)
grammarFile = open(f"{fileName}.grammar.{fileExtension}", 'w')
grammarFile.write(displayString)
grammarFile.close()
writeLog(f"Grammar saved to {fileName}.grammar.{fileExtension}")

symbolLabels = {
    "formula": "⟨F⟩",
    "term": "⟨T⟩",
    "variable": "⟨V⟩",
    "constant": "⟨C⟩",
    "quantifier": "⟨Q⟩",
    "connective_unary": "⟨C1⟩",
    "connective_binary": "⟨C2⟩",
    "equality": "⟨E⟩",
    "predicate": "⟨P⟩"
}

terminalProductions = ["variable", "constant", "quantifier", "connective_unary", "connective_binary", "equality"]

formulaList = formula.split()

issues = []

nodeID = 0


def match(symbol, pointer = 0, depth = 0):

    global nodeID
    global pos

        
    if symbol in terminalSymbols:
        displaySymbol = f"symbol literal '{symbol}'"
    else:
        displaySymbol = f"production of type '{symbol}'"


    if pointer >= len(formulaList):
        exitLog(f"FORMULA ERROR: Encountered end of formula while checking for {displaySymbol}. Formula is INVALID.")

    # no eof: determine if terminal or non-terminal
    if symbol in terminalSymbols:

        # terminal case: verify that the part of the formula that starts at the pointer starts with the given terminal symbol
        if formulaList[pointer] == symbol: # symbol matches
            # return the match length in order to increment the pointer in the parent function

            leafGraph = nx.DiGraph()
            leafGraph.add_node(nodeID, depth = depth, label = f"'{symbol}'", start = pointer)
            nodeID += 1
            
            return 1, leafGraph

        else: # formula (from pointer) does not start with given symbol
            # no match: return match length as zero

            issue = f"FORMULA ERROR: Expected {displaySymbol} after '{' '.join(formulaList[:pointer])}', got '{formulaList[pointer]}' instead."

            issues.append((pointer, depth, issue))

            return 0, nx.DiGraph()
    else:
        # non-terminal case: verify that the formula (from the pointer) starts with one of the productions
        
        # if there are multiple possible valid formats (productions), check each and add match length to this array so that the longest match length can be found after:
        matchLengths = []
        # iterate through all possible formats (productions) to find the one with the longest match
        for productionFormat in productionRules[symbol]:

            # for each format, reset the pointer to the initial position
            currPointer = pointer

            # for each format, keep track of the match length to save it into the array
            matchLength = 0
            subtreeGraph = nx.DiGraph()
            subtreeGraph.add_node(nodeID, depth = depth, label = symbolLabels[symbol], start = currPointer)
            root = nodeID
            nodeID += 1
            symbolsMatched = 0
            symbolsMatchedList = []
            # iterate through all symbols in the production to match the entire production with the formula (starting at the pointer)
            for productionSymbol in productionFormat:
                # recursively match the required symbol at pointer location
                matchResult, subSubtreeGraph = match(productionSymbol, currPointer+matchLength, depth+1)
                while matchResult == "space":
                    matchLength += 1
                    matchResult, subSubtreeGraph = match(productionSymbol, currPointer+matchLength, depth+1)

                # add the found length to the length of the current match
                matchLength += matchResult

                # if this symbol didn't match, don't bother matching the rest of this production; break and go to the next one
                if matchLength == 0 or matchResult == 0:
                    issue = f"FORMULA ERROR: Expected {displaySymbol} after '{' '.join(formulaList[:currPointer])}', got '{formulaList[currPointer]}' instead."
                    issues.append((currPointer, depth, issue))
                    break
                else:
                    symbolsMatched += 1
                    symbolsMatchedList.append(productionSymbol)
                    subtreeGraph = nx.compose(subtreeGraph, subSubtreeGraph)
                    for n in subSubtreeGraph.nodes.data():
                        if n[1]["depth"] == depth+1:
                            subtreeGraph.add_edge(root, n[0])
                            pass

            # add the production's match length to the list
            matchLengths.append((matchLength, subtreeGraph, symbolsMatched, len(productionFormat), symbolsMatchedList))
        longestMatch = max(matchLengths, key=operator.itemgetter(0))
        if longestMatch[2] == 0:
            issue = f"FORMULA ERROR: Expected {displaySymbol} after '{' '.join(formulaList[:currPointer+longestMatch[0]])}', got '{formulaList[currPointer+longestMatch[0]]}' instead."
            #issue = f"FORMULA ERROR: Expected {displaySymbol} after '{formula[:currPointer+longestMatch[0]]}', got '{formula[currPointer+longestMatch[0]]}' instead."
            issues.append((currPointer+longestMatch[0], depth, issue))
            return 0, nx.DiGraph()
        if longestMatch[2] != longestMatch[3]:
            return 0, nx.DiGraph()
        return longestMatch[0:2]
    
matchLength, G = match('formula')

if matchLength == len(formulaList):
    writeLog("Input file and formula are VALID")
elif matchLength > len(formulaList):
    maxPointer = max(issues, key=operator.itemgetter(0))[0]
    minDepth = min([i for i in issues if i[0] == maxPointer], key=operator.itemgetter(1))[1]
    possibleIssues = [i for i in sorted(issues, key=operator.itemgetter(0,1)) if i[0] == maxPointer and i[1] == minDepth]
    exitLog(possibleIssues[0][2])
    #exitLog(f"FORMULA ERROR: Matched unfinished partial formula '{formula[0:matchLength]}' but failed to match remaining '{formula[matchLength:]}'")
elif matchLength < len(formulaList):
    exitLog(f"FORMULA ERROR: Extra symbol(s) after valid formula could not be matched: '{' '.join(formulaList[matchLength:])}'")

labels = nx.get_node_attributes(G, 'label')

pos = dict()
childrenOf = dict()
parentOf = dict()
width = dict()
maxDepth = 0
sizes = []
colors = []

for node, nodeData in G.nodes.data():
    childrenOf[node] = []
    width[node] = 0
    pos[node] = [0,-nodeData["depth"]]
    maxDepth = max(maxDepth, nodeData["depth"])
    #sizes.append(len(nodeData["label"]*200))
    sizes.append(400)
    colors.append([0.9]*3)

for edge in G.edges():
    childrenOf[edge[0]].append(edge[1])
    parentOf[edge[1]] = edge[0]

    
def getWidth(node):
    global childrenOf
    if len(childrenOf[node]) == 0:
        return len(G.nodes[node]["label"])+4
    else:
        width = 0
        for childNode in childrenOf[node]:
            width += getWidth(childNode)
        return width

def addChildrenOf(node, parentPos=0):
    pointer = parentPos
    w = getWidth(node)
    pointer -= (w-1)/2
    for child in childrenOf[node]:
        pos[child][0] = pointer + (getWidth(child)-1)/2
        addChildrenOf(child, pos[child][0])
        pointer += getWidth(child)
        
rootNode = list(G.nodes.data())[0][0]
addChildrenOf(rootNode)
rootWidth = getWidth(rootNode)


G.add_node("legend")
labels["legend"] = 'LEGEND:\n'+'\n'.join([f"{v}: {k}"for k, v in symbolLabels.items()]) + '\nString literals are in single quotes (\').'
pos["legend"] = [rootWidth*1/4, 0]
colors.append([1]*3)

plt.figure(1, figsize=(20, 12))
nx.draw(G, pos=pos, labels=labels, node_color = colors, node_size = sizes, node_shape = 'o')

plt.savefig(fileName+".png")
exitLog(f"Parse tree saved to {fileName}.png", code=0)