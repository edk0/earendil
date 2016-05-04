#!/usr/bin/env python3

import argparse
import json
import io
import os.path

def data_to_markdown(data, f):
    with open(os.path.join(os.path.split(__file__)[0], 'make-doc.header.md')) as j:
        header = j.read()
    f.write(header.format(**data))
    f.write('\n\n')
    
    for section in data['sections']:
        f.write('## {} {{#section-{}}}\n\n'.format(section['title'], section['name']))
        for msg in data['messages']:
            if msg['section'] != section['name']:
                continue

            f.write('### {} {{#msg-{}}}\n'.format(msg['format'], msg['name']))
            f.write('Name: *{}*\n\n'.format(msg['name']))

            if 'related' in msg:
                f.write('Related: ')
                first = True
                for rel in msg['related']:
                    if not first:
                        f.write(', ')
                    first = False
                    f.write('*[{0}](#msg-{0})*'.format(rel))
                f.write('.\n\n')

            if 'documentation' in msg:
                f.write(msg['documentation'])
                f.write('\n')

p = argparse.ArgumentParser()
p.add_argument('input', type=argparse.FileType('r'))
p.add_argument('output', type=argparse.FileType('w'))
p.add_argument('--html', action='store_true', default=False)

if __name__ == "__main__":
    args = p.parse_args()
    data = json.load(args.input)

    out = args.output
    if args.html:
        out = io.StringIO()
    data_to_markdown(data, out)
    out.write('\n')

    if args.html:
        import markdown
        html = markdown.markdown(out.getvalue(), extensions=['extra', 'toc'], safe_mode='escape')
        args.output.write(html)
        args.output.write('\n')
