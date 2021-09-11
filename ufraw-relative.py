#! /usr/bin/python3

import sys, getopt, os.path, xml.dom.minidom, posixpath as path

def makeRelativeTo ( xdoc, nodename, outputPath ):
  xdoc.getElementsByTagName(nodename)[0].childNodes[0].data = path.relpath ( xdoc.getElementsByTagName(nodename)[0].childNodes[0].data, outputPath )

def convert ( filename, nobackup ):
  xdoc = xml.dom.minidom.parse(filename)
  outputPath = xdoc.getElementsByTagName("OutputPath")[0].childNodes[0].data
  makeRelativeTo ( xdoc, "InputFilename", outputPath )
  makeRelativeTo ( xdoc, "OutputFilename", outputPath )
  makeRelativeTo ( xdoc, "OutputPath", outputPath )
  if not nobackup:
    os.replace ( filename, filename+'.bak' )
  xdoc.writexml ( open(filename,'w') )

def main ( scriptname, argv ):
  syntax = '''Convert absolute path in UFRaw companion files into relative to the output path

  Syntax: {scriptname} -h
          {scriptname} [<options>...] <filenames>...
          
  Options:
    -n, --nobackup: do not create backup file
  '''
  optNobackup = False
  try:
    opts, args = getopt.gnu_getopt ( argv, 'hn', ['help','nobackup'] )
  except getopt.GetoptError:
    print ( syntax.format(scriptname=scriptname) )
    sys.exit(2)
  for opt, arg in opts:
    if opt == '-h' or opt == '--help':
      print ( syntax.format(scriptname=scriptname) )
      sys.exit()
    elif opt == '-n' or opt == '--nobackup':
      optNobackup = True
  for arg in args:
    convert ( arg, optNobackup )

if __name__ == "__main__":
  main ( os.path.basename(sys.argv[0]), sys.argv[1:] )
   
