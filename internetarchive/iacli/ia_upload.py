"""Upload files to Archive.org via the Internet Archive's S3 like server API.

IA-S3 Documentation: https://archive.org/help/abouts3.txt

usage:
    ia upload [--verbose] [--debug] <identifier>
              (<file>... | - --remote-name=<name>)
              [--metadata=<key:value>...] [--header=<key:value>...]
              [--no-derive] [--ignore-bucket]
    ia upload --help

options:
    -h, --help
    -v, --verbose                  Print upload status to stdout.
    -d, --debug                    Print S3 request parameters to stdout and
                                   exit without sending request.
    -r, --remote-name=<name>       When uploading data from stdin, this option
                                   sets the remote filename.
    -m, --metadata=<key:value>...  Metadata to add to your item.
    -H, --header=<key:value>...    S3 HTTP headers to send with your request.
    -n, --no-derive                Do not derive uploaded files.
    -i, --ignore-bucket            Destroy and respecify all metadata.

"""
import sys
import subprocess
import tempfile
import xml.dom.minidom

from docopt import docopt

from internetarchive import upload
from internetarchive.iacli.argparser import get_args_dict, get_xml_text


# main()
#_________________________________________________________________________________________
def main(argv):
    args = docopt(__doc__, argv=argv)

    if args['--verbose'] and not args['--debug']:
        sys.stdout.write('getting item: {0}\n'.format(args['<identifier>']))

    upload_kwargs = dict(
        metadata=get_args_dict(args['--metadata']),
        headers=get_args_dict(args['--header']),
        debug=args['--debug'],
        queue_derive=True if args['--no-derive'] is False else False,
        ignore_preexisting_bucket=args['--ignore-bucket'],
        verbose=args['--verbose'],
    )

    # Upload stdin.
    if args['<file>'] == ['-'] and not args['-']:
        sys.stderr.write('--remote-name is required when uploading from stdin.\n')
        subprocess.call(['ia', 'upload', '--help'])
        sys.exit(1)
    if args['-']:
        local_file = tempfile.TemporaryFile()
        local_file.write(sys.stdin.read())
        local_file.seek(0)
        upload_kwargs['key'] = args['--remote-name']
    # Upload files.
    else:
        local_file = args['<file>']

    response = upload(args['<identifier>'], local_file, **upload_kwargs)

    if args['--debug']:
        for i, r in enumerate(response):
            if i != 0:
                sys.stdout.write('---\n')
            headers = '\n'.join([' {0}: {1}'.format(k,v) for (k,v) in r.headers.items()])
            sys.stdout.write('Endpoint:\n {0}\n\n'.format(r.url))
            sys.stdout.write('HTTP Headers:\n{0}\n'.format(headers))
    else:
        for resp in response:
            if resp.status_code == 200:
                continue
            error = xml.dom.minidom.parseString(resp.content)
            code = get_xml_text(error.getElementsByTagName('Code'))
            msg = get_xml_text(error.getElementsByTagName('Message'))
            sys.stderr.write('error "{0}" ({1}): {2}\n'.format(code, resp.status_code, msg))
            sys.exit(1)
