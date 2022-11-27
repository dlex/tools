#!/usr/bin/python3

from datetime import datetime, timedelta
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
    res = try_parse_date ( res, s, '%m/%d/%Y' )
  return res

def format_history(when: datetime, pwd: str):
  return f"{when.strftime('%Y/%m/%d %H:%M:%S')} {len(pwd):04x} {pwd}"

PWS_LF = u'»'
system_tt = str.maketrans('.',PWS_LF)

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
          'History',
          'Notes'
        ]
      else:
        email_v = ''
        notes_v = []
        if src[email_si]!='':
          if '@' in src[email_si]:
            email_v = src[email_si]
          else:
            notes_v.append ( src[email_si] )
        
        created_time_v = parse_date ( src[start_date_si] )
        expiry_time_v = parse_date ( src[expires_si] )
        
        if src[more_si]!='':
          notes_v += src[more_si].split('||')
          
        # convert "old" records in the notes into password history
        history_v = []
        notes_v_copy = []
        for n in notes_v:
          nl = n.lower()
          oldpwd_str = ''
          if nl.startswith('old: '):
            oldpwd_str = n[5:]
          elif nl.startswith('olds: '):
            oldpwd_str = n[6:]
          elif nl.startswith('was: '):
            oldpwd_str = n[5:]
          elif nl.startswith('old pwd: '):
            oldpwd_str = n[9:]
          elif nl.startswith('old pwds: '):
            oldpwd_str = n[10:]
          elif nl.startswith('old pass: '):
            oldpwd_str = n[10:]
          elif nl.startswith('password was: '):
            oldpwd_str = n[14:]
          if oldpwd_str == '':
            notes_v_copy.append(n)
          else:
            oldpwd_part = oldpwd_str.partition(' ')
            one_pwd_per_line = True
            if oldpwd_part[2] == '':
              # one token in the line => one pass in the line, date 'unknown'
              oldwhen = datetime(1970,1,1,0,0,0) 
            else:
              # two or more tokens in the line
              oldwhen = parse_date(oldpwd_part[2].rstrip())
              if oldwhen != datetime.min:
                # second token is a date
                oldpwd_str = oldpwd_part[0]
              else:
                # second token is not a date => can be another pass
                one_pwd_per_line = False
                # this one's date 'unknown'
                oldwhen = datetime(1970,1,1,0,0,0)
            if one_pwd_per_line:
              history_v.append ( format_history(oldwhen,oldpwd_str) )
            else:
              oldpwd_split = oldpwd_str.split()
              for p in oldpwd_split:
                history_v.append ( format_history(oldwhen,p) )
        
        notes_vj = PWS_LF.join(notes_v_copy)
        dst = [ 
          f"{src[category_si]}.{src[system_si].translate(system_tt)}", src[user_si], 
          src[password_si] if src[password_si]!='' else '---', src[url_si], email_v, 
          created_time_v.strftime('%Y/%m/%d %H:%M:%S') if created_time_v!=datetime.min else '',
          expiry_time_v.strftime('%Y/%m/%d %H:%M:%S') if expiry_time_v!=datetime.min else '',
          # history header: smmnn, s: status (0,1), mm: passwords to keep, nn: password now in the history
          f"1{len(history_v):02x}{len(history_v):02x} {' '.join(history_v)}" if history_v!=[] else '',
          notes_vj if notes_vj!='' else '""'
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
