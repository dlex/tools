#!/usr/bin/python3

from datetime import datetime
from sys import stderr
from locale import getpreferredencoding
import argparse

parser = argparse.ArgumentParser(description='Convert PINs export file into PasswordSafe import file')
parser.add_argument('in_file', metavar='source_file', type=str, help='PINs export file for input')
parser.add_argument('out_file', metavar='target_file', type=str, help='PasswordSafe plain text import file to be produced. File is overwritten if exists')
parser.add_argument('--in-encoding', metavar='encoding', type=str, default=getpreferredencoding(), help=f'encoding for the input file (default: {getpreferredencoding()})')
parser.add_argument('--strict', help='Fail conversion if a record processing fails')

args = parser.parse_args()

def try_parse_date(res: datetime, s: str, format: str):
  if res != datetime.min:
    return res
  try:
    return datetime.strptime ( s, format )
  except ValueError:
    return datetime.min

def parse_date(s: str):
  res = datetime.min
  if not s in ['','Никогда','Never']:
    res = try_parse_date ( res, s, '%d.%m.%Y' )
    res = try_parse_date ( res, s, '%Y-%m-%d' )
    res = try_parse_date ( res, s, '%d/%m/%Y' )
  return res

with open(args.in_file,mode='rt',encoding=args.in_encoding,errors='strict') as in_file, open(args.out_file,mode='wt',encoding='utf-8',errors='strict') as out_file:
  read_lines = set()
  # input/output line no being processed, 0 = header line
  in_line_no = -1 
  out_line_no = 0
  blank_line_no = 0
  dupe_line_no = 0
  failed_line_no = 0
  for in_line in in_file:
    in_line_no += 1
    in_line = in_line.strip('\n')
    if in_line == '':
      blank_line_no += 1
      continue
    if in_line in read_lines:
      dupe_line_no += 1
      continue
      
    try:
      read_lines.add(in_line)     
      src = in_line.split('\t')

      if in_line_no == 0:
        category_si = src.index('Category')
        system_si = src.index('System')
        user_si = src.index('User')
        password_si = src.index('Password')
        url_si = src.index('URL/Comments')
        email_si = src.index('Custom')
        start_date_si = src.index('Start date')
        expires_si = src.index('Expires')
        more_si = src.index('More info')
        dst = [ 
          'Group/Title', 'Username', 
          'Password', 'URL', 'e-mail', 
          'Created Time', 
          'Password Expiry Date',
          'Notes'
        ]
      else:
        email_v = ''
        notes_v = ''
        if src[email_si]!='':
          if '@' in src[email_si]:
            email_v = src[email_si]
          else:
            notes_v = src[email_si]
        
        created_time_v = parse_date ( src[start_date_si] )
        expiry_time_v = parse_date ( src[expires_si] )
          
        if src[more_si]!='':
          if notes_v!='':
            notes_v += u'»'
          notes_v += src[more_si].replace('||',u'»')
          
        dst = [ 
          f"{src[category_si]}.{src[system_si]}", src[user_si], 
          src[password_si] if src[password_si]!='' else '---', src[url_si], email_v, 
          created_time_v.strftime('%Y/%m/%d %H:%M:%S') if created_time_v!=datetime.min else '',
          expiry_time_v.strftime('%Y/%m/%d %H:%M:%S') if expiry_time_v!=datetime.min else '',
          notes_v if notes_v!='' else '""'
        ]
        
      print ( '\t'.join(dst), file=out_file )
      out_line_no += 1
  
    except Exception as ex:
      print ( f'Error while processing line {in_line_no}: {ex}. Line: "{in_line}"', file=stderr )
      if in_line_no == 0 or args.strict:
        raise
      failed_line_no += 1
  else:
    in_line_no += 1

if in_line_no > 0:
  print ( f'{in_line_no} input line(s) processed, including 1 header, {blank_line_no} blank, {dupe_line_no} dupe, and {failed_line_no} failed line(s)' )
else:
  print ( 'Input file is empty' )
if out_line_no > 0:
  print ( f'{out_line_no-1} record(s) written' )
