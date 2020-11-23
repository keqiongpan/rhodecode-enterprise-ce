# -*- coding: utf-8 -*-

# Copyright (C) 2010-2020 RhodeCode GmbH
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License, version 3
# (only), as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This program is dual-licensed. If you wish to learn more about the
# RhodeCode Enterprise Edition, including its added features, Support services,
# and proprietary license terms, please see https://rhodecode.com/licenses/

import re
import markdown
import xml.etree.ElementTree as etree

from markdown.extensions import Extension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.smart_strong import SmartEmphasisExtension
from markdown.extensions.tables import TableExtension
from markdown.inlinepatterns import Pattern

import gfm


class InlineProcessor(Pattern):
    """
    Base class that inline patterns subclass.
    This is the newer style inline processor that uses a more
    efficient and flexible search approach.
    """

    def __init__(self, pattern, md=None):
        """
        Create an instant of an inline pattern.
        Keyword arguments:
        * pattern: A regular expression that matches a pattern
        """
        self.pattern = pattern
        self.compiled_re = re.compile(pattern, re.DOTALL | re.UNICODE)

        # Api for Markdown to pass safe_mode into instance
        self.safe_mode = False
        self.md = md

    def handleMatch(self, m, data):
        """Return a ElementTree element from the given match and the
        start and end index of the matched text.
        If `start` and/or `end` are returned as `None`, it will be
        assumed that the processor did not find a valid region of text.
        Subclasses should override this method.
        Keyword arguments:
        * m: A re match object containing a match of the pattern.
        * data: The buffer current under analysis
        Returns:
        * el: The ElementTree element, text or None.
        * start: The start of the region that has been matched or None.
        * end: The end of the region that has been matched or None.
        """
        pass  # pragma: no cover


class SimpleTagInlineProcessor(InlineProcessor):
    """
    Return element of type `tag` with a text attribute of group(2)
    of a Pattern.
    """
    def __init__(self, pattern, tag):
        InlineProcessor.__init__(self, pattern)
        self.tag = tag

    def handleMatch(self, m, data):  # pragma: no cover
        el = etree.Element(self.tag)
        el.text = m.group(2)
        return el, m.start(0), m.end(0)


class SubstituteTagInlineProcessor(SimpleTagInlineProcessor):
    """ Return an element of type `tag` with no children. """
    def handleMatch(self, m, data):
        return etree.Element(self.tag), m.start(0), m.end(0)


class Nl2BrExtension(Extension):
    BR_RE = r'\n'

    def extendMarkdown(self, md, md_globals):
        br_tag = SubstituteTagInlineProcessor(self.BR_RE, 'br')
        md.inlinePatterns.add('nl', br_tag, '_end')


class GithubFlavoredMarkdownExtension(Extension):
    """
    An extension that is as compatible as possible with GitHub-flavored
    Markdown (GFM).

    This extension aims to be compatible with the variant of GFM that GitHub
    uses for Markdown-formatted gists and files (including READMEs). This
    variant seems to have all the extensions described in the `GFM
    documentation`_, except:

    - Newlines in paragraphs are not transformed into ``br`` tags.
    - Intra-GitHub links to commits, repositories, and issues are not
      supported.

    If you need support for features specific to GitHub comments and issues,
    please use :class:`mdx_gfm.GithubFlavoredMarkdownExtension`.

    .. _GFM documentation: https://guides.github.com/features/mastering-markdown/
    """

    def extendMarkdown(self, md, md_globals):
        # Built-in extensions
        Nl2BrExtension().extendMarkdown(md, md_globals)
        FencedCodeExtension().extendMarkdown(md, md_globals)
        SmartEmphasisExtension().extendMarkdown(md, md_globals)
        TableExtension().extendMarkdown(md, md_globals)

        # Custom extensions
        gfm.AutolinkExtension().extendMarkdown(md, md_globals)
        gfm.AutomailExtension().extendMarkdown(md, md_globals)
        gfm.HiddenHiliteExtension([
            ('guess_lang', 'False'),
            ('css_class', 'highlight')
        ]).extendMarkdown(md, md_globals)
        gfm.SemiSaneListExtension().extendMarkdown(md, md_globals)
        gfm.SpacedLinkExtension().extendMarkdown(md, md_globals)
        gfm.StrikethroughExtension().extendMarkdown(md, md_globals)
        gfm.TaskListExtension([
            ('list_attrs', {'class': 'checkbox'})
        ]).extendMarkdown(md, md_globals)


# Global Vars
URLIZE_RE = '(%s)' % '|'.join([
    r'<(?:f|ht)tps?://[^>]*>',
    r'\b(?:f|ht)tps?://[^)<>\s]+[^.,)<>\s]',
    r'\bwww\.[^)<>\s]+[^.,)<>\s]',
    r'[^(<\s]+\.(?:com|net|org)\b',
])


class UrlizePattern(markdown.inlinepatterns.Pattern):
    """ Return a link Element given an autolink (`http://example/com`). """
    def handleMatch(self, m):
        url = m.group(2)

        if url.startswith('<'):
            url = url[1:-1]

        text = url

        if not url.split('://')[0] in ('http','https','ftp'):
            if '@' in url and not '/' in url:
                url = 'mailto:' + url
            else:
                url = 'http://' + url

        el = markdown.util.etree.Element("a")
        el.set('href', url)
        el.text = markdown.util.AtomicString(text)
        return el


class UrlizeExtension(markdown.Extension):
    """ Urlize Extension for Python-Markdown. """

    def extendMarkdown(self, md, md_globals):
        """ Replace autolink with UrlizePattern """
        md.inlinePatterns['autolink'] = UrlizePattern(URLIZE_RE, md)
