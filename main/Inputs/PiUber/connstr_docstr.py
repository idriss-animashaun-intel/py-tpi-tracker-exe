# -*- coding: utf-8 -*-

from __future__ import print_function

import collections
import re
import textwrap

__all__ = ['connection_params_docstring']


def connection_params_docstring(source=r'C:\Uber\Test\C#Script\ADO.NET'
                                       r'\README_ConnectionStringParams.txt',
                                indent=''):
    # Parse the Uber ConnectionStringParams description from the documentation
    text = open(source).read()

    tag = re.compile(r'^ \s*  \[ (\w+) \(   (.+)  \)\]  $', re.VERBOSE)
    decl = re.compile(r'^ \s* public \s+ (\w+) \s+ (\w+) \s* \{ \s* '
                      r'((?:(?:get|set);\s*)*) \s* \} $', re.VERBOSE)

    tags = {}
    params = collections.OrderedDict()
    for line in text.splitlines():
        m_tag = tag.match(line)
        m_decl = decl.match(line)

        if m_tag:
            t, d = m_tag.groups()
            if d[0] == d[-1] == '"':
                d = d[1:-1]
            tags[t] = d
        elif m_decl:
            type_, name, rw = m_decl.groups()
            tags['Type'] = type_
            params[name] = tags
            tags = {}

    # Munge it into a big docstring
    s = ''
    for p, tags in params.items():
        s += textwrap.fill('{param} ({type}{default}): {description}'.format(
            param=p, type=tags['Type'],
            default=(', default=' + repr(tags['DefaultValue']))
            if 'DefaultValue' in tags else '',
            description=tags['Description']),
            initial_indent=indent, subsequent_indent=indent + ' ' * 4)
        s += '\n'
    return s


if __name__ == '__main__':
    print('\n\n'
          '    List of connection string parameters (for latest updates see\n'
          '    README_ConnectionStringParams.txt in Uber distribution):')
    print(connection_params_docstring(indent=' ' * 8))
