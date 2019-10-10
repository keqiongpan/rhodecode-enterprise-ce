# -*- coding: utf-8 -*-

# Copyright (C) 2010-2019 RhodeCode GmbH
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

"""
Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""

import os
import random
import hashlib
import StringIO
import textwrap
import urllib
import math
import logging
import re
import time
import string
import hashlib
from collections import OrderedDict

import pygments
import itertools
import fnmatch
import bleach

from pyramid import compat
from datetime import datetime
from functools import partial
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import (
    get_lexer_by_name, get_lexer_for_filename, get_lexer_for_mimetype)

from pyramid.threadlocal import get_current_request

from webhelpers.html import literal, HTML, escape
from webhelpers.html.tools import *
from webhelpers.html.builder import make_tag
from webhelpers.html.tags import auto_discovery_link, checkbox, css_classes, \
    end_form, file, form as wh_form, hidden, image, javascript_link, link_to, \
    link_to_if, link_to_unless, ol, required_legend, select, stylesheet_link, \
    submit, text, password, textarea, title, ul, xml_declaration, radio
from webhelpers.html.tools import auto_link, button_to, highlight, \
    js_obfuscate, mail_to, strip_links, strip_tags, tag_re
from webhelpers.text import chop_at, collapse, convert_accented_entities, \
    convert_misc_entities, lchop, plural, rchop, remove_formatting, \
    replace_whitespace, urlify, truncate, wrap_paragraphs
from webhelpers.date import time_ago_in_words
from webhelpers.paginate import Page as _Page
from webhelpers.html.tags import _set_input_attrs, _set_id_attr, \
    convert_boolean_attrs, NotGiven, _make_safe_id_component
from webhelpers2.number import format_byte_size

from rhodecode.lib.action_parser import action_parser
from rhodecode.lib.ext_json import json
from rhodecode.lib.utils import repo_name_slug, get_custom_lexer
from rhodecode.lib.utils2 import str2bool, safe_unicode, safe_str, \
    get_commit_safe, datetime_to_time, time_to_datetime, time_to_utcdatetime, \
    AttributeDict, safe_int, md5, md5_safe
from rhodecode.lib.markup_renderer import MarkupRenderer, relative_links
from rhodecode.lib.vcs.exceptions import CommitDoesNotExistError
from rhodecode.lib.vcs.backends.base import BaseChangeset, EmptyCommit
from rhodecode.lib.index.search_utils import get_matching_line_offsets
from rhodecode.config.conf import DATE_FORMAT, DATETIME_FORMAT
from rhodecode.model.changeset_status import ChangesetStatusModel
from rhodecode.model.db import Permission, User, Repository
from rhodecode.model.repo_group import RepoGroupModel
from rhodecode.model.settings import IssueTrackerSettingsModel


log = logging.getLogger(__name__)


DEFAULT_USER = User.DEFAULT_USER
DEFAULT_USER_EMAIL = User.DEFAULT_USER_EMAIL


def asset(path, ver=None, **kwargs):
    """
    Helper to generate a static asset file path for rhodecode assets

    eg. h.asset('images/image.png', ver='3923')

    :param path: path of asset
    :param ver: optional version query param to append as ?ver=
    """
    request = get_current_request()
    query = {}
    query.update(kwargs)
    if ver:
        query = {'ver': ver}
    return request.static_path(
        'rhodecode:public/{}'.format(path), _query=query)


default_html_escape_table = {
    ord('&'): u'&amp;',
    ord('<'): u'&lt;',
    ord('>'): u'&gt;',
    ord('"'): u'&quot;',
    ord("'"): u'&#39;',
}


def html_escape(text, html_escape_table=default_html_escape_table):
    """Produce entities within text."""
    return text.translate(html_escape_table)


def chop_at_smart(s, sub, inclusive=False, suffix_if_chopped=None):
    """
    Truncate string ``s`` at the first occurrence of ``sub``.

    If ``inclusive`` is true, truncate just after ``sub`` rather than at it.
    """
    suffix_if_chopped = suffix_if_chopped or ''
    pos = s.find(sub)
    if pos == -1:
        return s

    if inclusive:
        pos += len(sub)

    chopped = s[:pos]
    left = s[pos:].strip()

    if left and suffix_if_chopped:
        chopped += suffix_if_chopped

    return chopped


def shorter(text, size=20, prefix=False):
    postfix = '...'
    if len(text) > size:
        if prefix:
            # shorten in front
            return postfix + text[-(size - len(postfix)):]
        else:
            return text[:size - len(postfix)] + postfix
    return text


def _reset(name, value=None, id=NotGiven, type="reset", **attrs):
    """
    Reset button
    """
    _set_input_attrs(attrs, type, name, value)
    _set_id_attr(attrs, id, name)
    convert_boolean_attrs(attrs, ["disabled"])
    return HTML.input(**attrs)

reset = _reset
safeid = _make_safe_id_component


def branding(name, length=40):
    return truncate(name, length, indicator="")


def FID(raw_id, path):
    """
    Creates a unique ID for filenode based on it's hash of path and commit
    it's safe to use in urls

    :param raw_id:
    :param path:
    """

    return 'c-%s-%s' % (short_id(raw_id), md5_safe(path)[:12])


class _GetError(object):
    """Get error from form_errors, and represent it as span wrapped error
    message

    :param field_name: field to fetch errors for
    :param form_errors: form errors dict
    """

    def __call__(self, field_name, form_errors):
        tmpl = """<span class="error_msg">%s</span>"""
        if form_errors and field_name in form_errors:
            return literal(tmpl % form_errors.get(field_name))


get_error = _GetError()


class _ToolTip(object):

    def __call__(self, tooltip_title, trim_at=50):
        """
        Special function just to wrap our text into nice formatted
        autowrapped text

        :param tooltip_title:
        """
        tooltip_title = escape(tooltip_title)
        tooltip_title = tooltip_title.replace('<', '&lt;').replace('>', '&gt;')
        return tooltip_title


tooltip = _ToolTip()

files_icon = u'<i class="file-breadcrumb-copy tooltip icon-clipboard clipboard-action" data-clipboard-text="{}" title="Copy the full path"></i>'


def files_breadcrumbs(repo_name, commit_id, file_path, at_ref=None, limit_items=False, linkify_last_item=False):
    if isinstance(file_path, str):
        file_path = safe_unicode(file_path)

    route_qry = {'at': at_ref} if at_ref else None

    # first segment is a `..` link to repo files
    root_name = literal(u'<i class="icon-home"></i>')
    url_segments = [
        link_to(
            root_name,
            route_path(
                'repo_files',
                repo_name=repo_name,
                commit_id=commit_id,
                f_path='',
                _query=route_qry),
        )]

    path_segments = file_path.split('/')
    last_cnt = len(path_segments) - 1
    for cnt, segment in enumerate(path_segments):
        if not segment:
            continue
        segment_html = escape(segment)

        last_item = cnt == last_cnt

        if last_item and linkify_last_item is False:
            # plain version
            url_segments.append(segment_html)
        else:
            url_segments.append(
                link_to(
                    segment_html,
                    route_path(
                        'repo_files',
                        repo_name=repo_name,
                        commit_id=commit_id,
                        f_path='/'.join(path_segments[:cnt + 1]),
                        _query=route_qry),
                ))

    limited_url_segments = url_segments[:1] + ['...'] + url_segments[-5:]
    if limit_items and len(limited_url_segments) < len(url_segments):
        url_segments = limited_url_segments

    full_path = file_path
    icon = files_icon.format(escape(full_path))
    if file_path == '':
        return root_name
    else:
        return literal(' / '.join(url_segments) + icon)


def files_url_data(request):
    matchdict = request.matchdict

    if 'f_path' not in matchdict:
        matchdict['f_path'] = ''

    if 'commit_id' not in matchdict:
        matchdict['commit_id'] = 'tip'

    return json.dumps(matchdict)


def code_highlight(code, lexer, formatter, use_hl_filter=False):
    """
    Lex ``code`` with ``lexer`` and format it with the formatter ``formatter``.

    If ``outfile`` is given and a valid file object (an object
    with a ``write`` method), the result will be written to it, otherwise
    it is returned as a string.
    """
    if use_hl_filter:
        # add HL filter
        from rhodecode.lib.index import search_utils
        lexer.add_filter(search_utils.ElasticSearchHLFilter())
    return pygments.format(pygments.lex(code, lexer), formatter)


class CodeHtmlFormatter(HtmlFormatter):
    """
    My code Html Formatter for source codes
    """

    def wrap(self, source, outfile):
        return self._wrap_div(self._wrap_pre(self._wrap_code(source)))

    def _wrap_code(self, source):
        for cnt, it in enumerate(source):
            i, t = it
            t = '<div id="L%s">%s</div>' % (cnt + 1, t)
            yield i, t

    def _wrap_tablelinenos(self, inner):
        dummyoutfile = StringIO.StringIO()
        lncount = 0
        for t, line in inner:
            if t:
                lncount += 1
            dummyoutfile.write(line)

        fl = self.linenostart
        mw = len(str(lncount + fl - 1))
        sp = self.linenospecial
        st = self.linenostep
        la = self.lineanchors
        aln = self.anchorlinenos
        nocls = self.noclasses
        if sp:
            lines = []

            for i in range(fl, fl + lncount):
                if i % st == 0:
                    if i % sp == 0:
                        if aln:
                            lines.append('<a href="#%s%d" class="special">%*d</a>' %
                                         (la, i, mw, i))
                        else:
                            lines.append('<span class="special">%*d</span>' % (mw, i))
                    else:
                        if aln:
                            lines.append('<a href="#%s%d">%*d</a>' % (la, i, mw, i))
                        else:
                            lines.append('%*d' % (mw, i))
                else:
                    lines.append('')
            ls = '\n'.join(lines)
        else:
            lines = []
            for i in range(fl, fl + lncount):
                if i % st == 0:
                    if aln:
                        lines.append('<a href="#%s%d">%*d</a>' % (la, i, mw, i))
                    else:
                        lines.append('%*d' % (mw, i))
                else:
                    lines.append('')
            ls = '\n'.join(lines)

        # in case you wonder about the seemingly redundant <div> here: since the
        # content in the other cell also is wrapped in a div, some browsers in
        # some configurations seem to mess up the formatting...
        if nocls:
            yield 0, ('<table class="%stable">' % self.cssclass +
                      '<tr><td><div class="linenodiv" '
                      'style="background-color: #f0f0f0; padding-right: 10px">'
                      '<pre style="line-height: 125%">' +
                      ls + '</pre></div></td><td id="hlcode" class="code">')
        else:
            yield 0, ('<table class="%stable">' % self.cssclass +
                      '<tr><td class="linenos"><div class="linenodiv"><pre>' +
                      ls + '</pre></div></td><td id="hlcode" class="code">')
        yield 0, dummyoutfile.getvalue()
        yield 0, '</td></tr></table>'


class SearchContentCodeHtmlFormatter(CodeHtmlFormatter):
    def __init__(self, **kw):
        # only show these line numbers if set
        self.only_lines = kw.pop('only_line_numbers', [])
        self.query_terms = kw.pop('query_terms', [])
        self.max_lines = kw.pop('max_lines', 5)
        self.line_context = kw.pop('line_context', 3)
        self.url = kw.pop('url', None)

        super(CodeHtmlFormatter, self).__init__(**kw)

    def _wrap_code(self, source):
        for cnt, it in enumerate(source):
            i, t = it
            t = '<pre>%s</pre>' % t
            yield i, t

    def _wrap_tablelinenos(self, inner):
        yield 0, '<table class="code-highlight %stable">' % self.cssclass

        last_shown_line_number = 0
        current_line_number = 1

        for t, line in inner:
            if not t:
                yield t, line
                continue

            if current_line_number in self.only_lines:
                if last_shown_line_number + 1 != current_line_number:
                    yield 0, '<tr>'
                    yield 0, '<td class="line">...</td>'
                    yield 0, '<td id="hlcode" class="code"></td>'
                    yield 0, '</tr>'

                yield 0, '<tr>'
                if self.url:
                    yield 0, '<td class="line"><a href="%s#L%i">%i</a></td>' % (
                        self.url, current_line_number, current_line_number)
                else:
                    yield 0, '<td class="line"><a href="">%i</a></td>' % (
                        current_line_number)
                yield 0, '<td id="hlcode" class="code">' + line + '</td>'
                yield 0, '</tr>'

                last_shown_line_number = current_line_number

            current_line_number += 1

        yield 0, '</table>'


def hsv_to_rgb(h, s, v):
    """ Convert hsv color values to rgb """

    if s == 0.0:
        return v, v, v
    i = int(h * 6.0)  # XXX assume int() truncates!
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6
    if i == 0:
        return v, t, p
    if i == 1:
        return q, v, p
    if i == 2:
        return p, v, t
    if i == 3:
        return p, q, v
    if i == 4:
        return t, p, v
    if i == 5:
        return v, p, q


def unique_color_generator(n=10000, saturation=0.10, lightness=0.95):
    """
    Generator for getting n of evenly distributed colors using
    hsv color and golden ratio. It always return same order of colors

    :param n: number of colors to generate
    :param saturation: saturation of returned colors
    :param lightness: lightness of returned colors
    :returns: RGB tuple
    """

    golden_ratio = 0.618033988749895
    h = 0.22717784590367374

    for _ in xrange(n):
        h += golden_ratio
        h %= 1
        HSV_tuple = [h, saturation, lightness]
        RGB_tuple = hsv_to_rgb(*HSV_tuple)
        yield map(lambda x: str(int(x * 256)), RGB_tuple)


def color_hasher(n=10000, saturation=0.10, lightness=0.95):
    """
    Returns a function which when called with an argument returns a unique
    color for that argument, eg.

    :param n: number of colors to generate
    :param saturation: saturation of returned colors
    :param lightness: lightness of returned colors
    :returns: css RGB string

    >>> color_hash = color_hasher()
    >>> color_hash('hello')
    'rgb(34, 12, 59)'
    >>> color_hash('hello')
    'rgb(34, 12, 59)'
    >>> color_hash('other')
    'rgb(90, 224, 159)'
    """

    color_dict = {}
    cgenerator = unique_color_generator(
        saturation=saturation, lightness=lightness)

    def get_color_string(thing):
        if thing in color_dict:
            col = color_dict[thing]
        else:
            col = color_dict[thing] = cgenerator.next()
        return "rgb(%s)" % (', '.join(col))

    return get_color_string


def get_lexer_safe(mimetype=None, filepath=None):
    """
    Tries to return a relevant pygments lexer using mimetype/filepath name,
    defaulting to plain text if none could be found
    """
    lexer = None
    try:
        if mimetype:
            lexer = get_lexer_for_mimetype(mimetype)
        if not lexer:
            lexer = get_lexer_for_filename(filepath)
    except pygments.util.ClassNotFound:
        pass

    if not lexer:
        lexer = get_lexer_by_name('text')

    return lexer


def get_lexer_for_filenode(filenode):
    lexer = get_custom_lexer(filenode.extension) or filenode.lexer
    return lexer


def pygmentize(filenode, **kwargs):
    """
    pygmentize function using pygments

    :param filenode:
    """
    lexer = get_lexer_for_filenode(filenode)
    return literal(code_highlight(filenode.content, lexer,
                                  CodeHtmlFormatter(**kwargs)))


def is_following_repo(repo_name, user_id):
    from rhodecode.model.scm import ScmModel
    return ScmModel().is_following_repo(repo_name, user_id)


class _Message(object):
    """A message returned by ``Flash.pop_messages()``.

    Converting the message to a string returns the message text. Instances
    also have the following attributes:

    * ``message``: the message text.
    * ``category``: the category specified when the message was created.
    """

    def __init__(self, category, message):
        self.category = category
        self.message = message

    def __str__(self):
        return self.message

    __unicode__ = __str__

    def __html__(self):
        return escape(safe_unicode(self.message))


class Flash(object):
    # List of allowed categories.  If None, allow any category.
    categories = ["warning", "notice", "error", "success"]

    # Default category if none is specified.
    default_category = "notice"

    def __init__(self, session_key="flash", categories=None,
                 default_category=None):
        """
        Instantiate a ``Flash`` object.

        ``session_key`` is the key to save the messages under in the user's
        session.

        ``categories`` is an optional list which overrides the default list
        of categories.

        ``default_category`` overrides the default category used for messages
        when none is specified.
        """
        self.session_key = session_key
        if categories is not None:
            self.categories = categories
        if default_category is not None:
            self.default_category = default_category
        if self.categories and self.default_category not in self.categories:
            raise ValueError(
                "unrecognized default category %r" % (self.default_category,))

    def pop_messages(self, session=None, request=None):
        """
        Return all accumulated messages and delete them from the session.

        The return value is a list of ``Message`` objects.
        """
        messages = []

        if not session:
            if not request:
                request = get_current_request()
            session = request.session

        # Pop the 'old' pylons flash messages. They are tuples of the form
        # (category, message)
        for cat, msg in session.pop(self.session_key, []):
            messages.append(_Message(cat, msg))

        # Pop the 'new' pyramid flash messages for each category as list
        # of strings.
        for cat in self.categories:
            for msg in session.pop_flash(queue=cat):
                messages.append(_Message(cat, msg))
        # Map messages from the default queue to the 'notice' category.
        for msg in session.pop_flash():
            messages.append(_Message('notice', msg))

        session.save()
        return messages

    def json_alerts(self, session=None, request=None):
        payloads = []
        messages = flash.pop_messages(session=session, request=request)
        if messages:
            for message in messages:
                subdata = {}
                if hasattr(message.message, 'rsplit'):
                    flash_data = message.message.rsplit('|DELIM|', 1)
                    org_message = flash_data[0]
                    if len(flash_data) > 1:
                        subdata = json.loads(flash_data[1])
                else:
                    org_message = message.message
                payloads.append({
                    'message': {
                        'message': u'{}'.format(org_message),
                        'level': message.category,
                        'force': True,
                        'subdata': subdata
                    }
                })
        return json.dumps(payloads)

    def __call__(self, message, category=None, ignore_duplicate=True,
                 session=None, request=None):

        if not session:
            if not request:
                request = get_current_request()
            session = request.session

        session.flash(
            message, queue=category, allow_duplicate=not ignore_duplicate)


flash = Flash()

#==============================================================================
# SCM FILTERS available via h.
#==============================================================================
from rhodecode.lib.vcs.utils import author_name, author_email
from rhodecode.lib.utils2 import credentials_filter, age, age_from_seconds
from rhodecode.model.db import User, ChangesetStatus

capitalize = lambda x: x.capitalize()
email = author_email
short_id = lambda x: x[:12]
hide_credentials = lambda x: ''.join(credentials_filter(x))


import pytz
import tzlocal
local_timezone = tzlocal.get_localzone()


def age_component(datetime_iso, value=None, time_is_local=False):
    title = value or format_date(datetime_iso)
    tzinfo = '+00:00'

    # detect if we have a timezone info, otherwise, add it
    if time_is_local and isinstance(datetime_iso, datetime) and not datetime_iso.tzinfo:
        force_timezone = os.environ.get('RC_TIMEZONE', '')
        if force_timezone:
            force_timezone = pytz.timezone(force_timezone)
        timezone = force_timezone or local_timezone
        offset = timezone.localize(datetime_iso).strftime('%z')
        tzinfo = '{}:{}'.format(offset[:-2], offset[-2:])

    return literal(
        '<time class="timeago tooltip" '
        'title="{1}{2}" datetime="{0}{2}">{1}</time>'.format(
            datetime_iso, title, tzinfo))


def _shorten_commit_id(commit_id, commit_len=None):
    if commit_len is None:
        request = get_current_request()
        commit_len = request.call_context.visual.show_sha_length
    return commit_id[:commit_len]


def show_id(commit, show_idx=None, commit_len=None):
    """
    Configurable function that shows ID
    by default it's r123:fffeeefffeee

    :param commit: commit instance
    """
    if show_idx is None:
        request = get_current_request()
        show_idx = request.call_context.visual.show_revision_number

    raw_id = _shorten_commit_id(commit.raw_id, commit_len=commit_len)
    if show_idx:
        return 'r%s:%s' % (commit.idx, raw_id)
    else:
        return '%s' % (raw_id, )


def format_date(date):
    """
    use a standardized formatting for dates used in RhodeCode

    :param date: date/datetime object
    :return: formatted date
    """

    if date:
        _fmt = "%a, %d %b %Y %H:%M:%S"
        return safe_unicode(date.strftime(_fmt))

    return u""


class _RepoChecker(object):

    def __init__(self, backend_alias):
        self._backend_alias = backend_alias

    def __call__(self, repository):
        if hasattr(repository, 'alias'):
            _type = repository.alias
        elif hasattr(repository, 'repo_type'):
            _type = repository.repo_type
        else:
            _type = repository
        return _type == self._backend_alias


is_git = _RepoChecker('git')
is_hg = _RepoChecker('hg')
is_svn = _RepoChecker('svn')


def get_repo_type_by_name(repo_name):
    repo = Repository.get_by_repo_name(repo_name)
    if repo:
        return repo.repo_type


def is_svn_without_proxy(repository):
    if is_svn(repository):
        from rhodecode.model.settings import VcsSettingsModel
        conf = VcsSettingsModel().get_ui_settings_as_config_obj()
        return not str2bool(conf.get('vcs_svn_proxy', 'http_requests_enabled'))
    return False


def discover_user(author):
    """
    Tries to discover RhodeCode User based on the autho string. Author string
    is typically `FirstName LastName <email@address.com>`
    """

    # if author is already an instance use it for extraction
    if isinstance(author, User):
        return author

    # Valid email in the attribute passed, see if they're in the system
    _email = author_email(author)
    if _email != '':
        user = User.get_by_email(_email, case_insensitive=True, cache=True)
        if user is not None:
            return user

    # Maybe it's a username, we try to extract it and fetch by username ?
    _author = author_name(author)
    user = User.get_by_username(_author, case_insensitive=True, cache=True)
    if user is not None:
        return user

    return None


def email_or_none(author):
    # extract email from the commit string
    _email = author_email(author)

    # If we have an email, use it, otherwise
    # see if it contains a username we can get an email from
    if _email != '':
        return _email
    else:
        user = User.get_by_username(
            author_name(author), case_insensitive=True, cache=True)

    if user is not None:
            return user.email

    # No valid email, not a valid user in the system, none!
    return None


def link_to_user(author, length=0, **kwargs):
    user = discover_user(author)
    # user can be None, but if we have it already it means we can re-use it
    # in the person() function, so we save 1 intensive-query
    if user:
        author = user

    display_person = person(author, 'username_or_name_or_email')
    if length:
        display_person = shorter(display_person, length)

    if user:
        return link_to(
            escape(display_person),
            route_path('user_profile', username=user.username),
            **kwargs)
    else:
        return escape(display_person)


def link_to_group(users_group_name, **kwargs):
    return link_to(
        escape(users_group_name),
        route_path('user_group_profile', user_group_name=users_group_name),
        **kwargs)


def person(author, show_attr="username_and_name"):
    user = discover_user(author)
    if user:
        return getattr(user, show_attr)
    else:
        _author = author_name(author)
        _email = email(author)
        return _author or _email


def author_string(email):
    if email:
        user = User.get_by_email(email, case_insensitive=True, cache=True)
        if user:
            if user.first_name or user.last_name:
                return '%s %s &lt;%s&gt;' % (
                    user.first_name, user.last_name, email)
            else:
                return email
        else:
            return email
    else:
        return None


def person_by_id(id_, show_attr="username_and_name"):
    # attr to return from fetched user
    person_getter = lambda usr: getattr(usr, show_attr)

    #maybe it's an ID ?
    if str(id_).isdigit() or isinstance(id_, int):
        id_ = int(id_)
        user = User.get(id_)
        if user is not None:
            return person_getter(user)
    return id_


def gravatar_with_user(request, author, show_disabled=False):
    _render = request.get_partial_renderer(
        'rhodecode:templates/base/base.mako')
    return _render('gravatar_with_user', author, show_disabled=show_disabled)


tags_paterns = OrderedDict((
    ('lang', (re.compile(r'\[(lang|language)\ \=\&gt;\ *([a-zA-Z\-\/\#\+\.]*)\]'),
             '<div class="metatag" tag="lang">\\2</div>')),

    ('see', (re.compile(r'\[see\ \=\&gt;\ *([a-zA-Z0-9\/\=\?\&amp;\ \:\/\.\-]*)\]'),
            '<div class="metatag" tag="see">see: \\1 </div>')),

    ('url', (re.compile(r'\[url\ \=\&gt;\ \[([a-zA-Z0-9\ \.\-\_]+)\]\((http://|https://|/)(.*?)\)\]'),
            '<div class="metatag" tag="url"> <a href="\\2\\3">\\1</a> </div>')),

    ('license', (re.compile(r'\[license\ \=\&gt;\ *([a-zA-Z0-9\/\=\?\&amp;\ \:\/\.\-]*)\]'),
                '<div class="metatag" tag="license"><a href="http:\/\/www.opensource.org/licenses/\\1">\\1</a></div>')),

    ('ref', (re.compile(r'\[(requires|recommends|conflicts|base)\ \=\&gt;\ *([a-zA-Z0-9\-\/]*)\]'),
            '<div class="metatag" tag="ref \\1">\\1: <a href="/\\2">\\2</a></div>')),

    ('state', (re.compile(r'\[(stable|featured|stale|dead|dev|deprecated)\]'),
              '<div class="metatag" tag="state \\1">\\1</div>')),

    # label in grey
    ('label', (re.compile(r'\[([a-z]+)\]'),
              '<div class="metatag" tag="label">\\1</div>')),

    # generic catch all in grey
    ('generic', (re.compile(r'\[([a-zA-Z0-9\.\-\_]+)\]'),
                '<div class="metatag" tag="generic">\\1</div>')),
))


def extract_metatags(value):
    """
    Extract supported meta-tags from given text value
    """
    tags = []
    if not value:
        return tags, ''

    for key, val in tags_paterns.items():
        pat, replace_html = val
        tags.extend([(key, x.group()) for x in pat.finditer(value)])
        value = pat.sub('', value)

    return tags, value


def style_metatag(tag_type, value):
    """
    converts tags from value into html equivalent
    """
    if not value:
        return ''

    html_value = value
    tag_data = tags_paterns.get(tag_type)
    if tag_data:
        pat, replace_html = tag_data
        # convert to plain `unicode` instead of a markup tag to be used in
        # regex expressions. safe_unicode doesn't work here
        html_value = pat.sub(replace_html, unicode(value))

    return html_value


def bool2icon(value, show_at_false=True):
    """
    Returns boolean value of a given value, represented as html element with
    classes that will represent icons

    :param value: given value to convert to html node
    """

    if value:  # does bool conversion
        return HTML.tag('i', class_="icon-true")
    else:  # not true as bool
        if show_at_false:
            return HTML.tag('i', class_="icon-false")
        return HTML.tag('i')

#==============================================================================
# PERMS
#==============================================================================
from rhodecode.lib.auth import HasPermissionAny, HasPermissionAll, \
HasRepoPermissionAny, HasRepoPermissionAll, HasRepoGroupPermissionAll, \
HasRepoGroupPermissionAny, HasRepoPermissionAnyApi, get_csrf_token, \
csrf_token_key


#==============================================================================
# GRAVATAR URL
#==============================================================================
class InitialsGravatar(object):
    def __init__(self, email_address, first_name, last_name, size=30,
                 background=None, text_color='#fff'):
        self.size = size
        self.first_name = first_name
        self.last_name = last_name
        self.email_address = email_address
        self.background = background or self.str2color(email_address)
        self.text_color = text_color

    def get_color_bank(self):
        """
        returns a predefined list of colors that gravatars can use.
        Those are randomized distinct colors that guarantee readability and
        uniqueness.

        generated with: http://phrogz.net/css/distinct-colors.html
        """
        return [
            '#bf3030', '#a67f53', '#00ff00', '#5989b3', '#392040', '#d90000',
            '#402910', '#204020', '#79baf2', '#a700b3', '#bf6060', '#7f5320',
            '#008000', '#003059', '#ee00ff', '#ff0000', '#8c4b00', '#007300',
            '#005fb3', '#de73e6', '#ff4040', '#ffaa00', '#3df255', '#203140',
            '#47004d', '#591616', '#664400', '#59b365', '#0d2133', '#83008c',
            '#592d2d', '#bf9f60', '#73e682', '#1d3f73', '#73006b', '#402020',
            '#b2862d', '#397341', '#597db3', '#e600d6', '#a60000', '#736039',
            '#00b318', '#79aaf2', '#330d30', '#ff8080', '#403010', '#16591f',
            '#002459', '#8c4688', '#e50000', '#ffbf40', '#00732e', '#102340',
            '#bf60ac', '#8c4646', '#cc8800', '#00a642', '#1d3473', '#b32d98',
            '#660e00', '#ffd580', '#80ffb2', '#7391e6', '#733967', '#d97b6c',
            '#8c5e00', '#59b389', '#3967e6', '#590047', '#73281d', '#665200',
            '#00e67a', '#2d50b3', '#8c2377', '#734139', '#b2982d', '#16593a',
            '#001859', '#ff00aa', '#a65e53', '#ffcc00', '#0d3321', '#2d3959',
            '#731d56', '#401610', '#4c3d00', '#468c6c', '#002ca6', '#d936a3',
            '#d94c36', '#403920', '#36d9a3', '#0d1733', '#592d4a', '#993626',
            '#cca300', '#00734d', '#46598c', '#8c005e', '#7f1100', '#8c7000',
            '#00a66f', '#7382e6', '#b32d74', '#d9896c', '#ffe680', '#1d7362',
            '#364cd9', '#73003d', '#d93a00', '#998a4d', '#59b3a1', '#5965b3',
            '#e5007a', '#73341d', '#665f00', '#00b38f', '#0018b3', '#59163a',
            '#b2502d', '#bfb960', '#00ffcc', '#23318c', '#a6537f', '#734939',
            '#b2a700', '#104036', '#3d3df2', '#402031', '#e56739', '#736f39',
            '#79f2ea', '#000059', '#401029', '#4c1400', '#ffee00', '#005953',
            '#101040', '#990052', '#402820', '#403d10', '#00ffee', '#0000d9',
            '#ff80c4', '#a66953', '#eeff00', '#00ccbe', '#8080ff', '#e673a1',
            '#a62c00', '#474d00', '#1a3331', '#46468c', '#733950', '#662900',
            '#858c23', '#238c85', '#0f0073', '#b20047', '#d9986c', '#becc00',
            '#396f73', '#281d73', '#ff0066', '#ff6600', '#dee673', '#59adb3',
            '#6559b3', '#590024', '#b2622d', '#98b32d', '#36ced9', '#332d59',
            '#40001a', '#733f1d', '#526600', '#005359', '#242040', '#bf6079',
            '#735039', '#cef23d', '#007780', '#5630bf', '#66001b', '#b24700',
            '#acbf60', '#1d6273', '#25008c', '#731d34', '#a67453', '#50592d',
            '#00ccff', '#6600ff', '#ff0044', '#4c1f00', '#8a994d', '#79daf2',
            '#a173e6', '#d93662', '#402310', '#aaff00', '#2d98b3', '#8c40ff',
            '#592d39', '#ff8c40', '#354020', '#103640', '#1a0040', '#331a20',
            '#331400', '#334d00', '#1d5673', '#583973', '#7f0022', '#4c3626',
            '#88cc00', '#36a3d9', '#3d0073', '#d9364c', '#33241a', '#698c23',
            '#5995b3', '#300059', '#e57382', '#7f3300', '#366600', '#00aaff',
            '#3a1659', '#733941', '#663600', '#74b32d', '#003c59', '#7f53a6',
            '#73000f', '#ff8800', '#baf279', '#79caf2', '#291040', '#a6293a',
            '#b2742d', '#587339', '#0077b3', '#632699', '#400009', '#d9a66c',
            '#294010', '#2d4a59', '#aa00ff', '#4c131b', '#b25f00', '#5ce600',
            '#267399', '#a336d9', '#990014', '#664e33', '#86bf60', '#0088ff',
            '#7700b3', '#593a16', '#073300', '#1d4b73', '#ac60bf', '#e59539',
            '#4f8c46', '#368dd9', '#5c0073'
        ]

    def rgb_to_hex_color(self, rgb_tuple):
        """
        Converts an rgb_tuple passed to an hex color.

        :param rgb_tuple: tuple with 3 ints represents rgb color space
        """
        return '#' + ("".join(map(chr, rgb_tuple)).encode('hex'))

    def email_to_int_list(self, email_str):
        """
        Get every byte of the hex digest value of email and turn it to integer.
        It's going to be always between 0-255
        """
        digest = md5_safe(email_str.lower())
        return [int(digest[i * 2:i * 2 + 2], 16) for i in range(16)]

    def pick_color_bank_index(self, email_str, color_bank):
        return self.email_to_int_list(email_str)[0] % len(color_bank)

    def str2color(self, email_str):
        """
        Tries to map in a stable algorithm an email to color

        :param email_str:
        """
        color_bank = self.get_color_bank()
        # pick position (module it's length so we always find it in the
        # bank even if it's smaller than 256 values
        pos = self.pick_color_bank_index(email_str, color_bank)
        return color_bank[pos]

    def normalize_email(self, email_address):
        import unicodedata
        # default host used to fill in the fake/missing email
        default_host = u'localhost'

        if not email_address:
            email_address = u'%s@%s' % (User.DEFAULT_USER, default_host)

        email_address = safe_unicode(email_address)

        if u'@' not in email_address:
            email_address = u'%s@%s' % (email_address, default_host)

        if email_address.endswith(u'@'):
            email_address = u'%s%s' % (email_address, default_host)

        email_address = unicodedata.normalize('NFKD', email_address)\
            .encode('ascii', 'ignore')
        return email_address

    def get_initials(self):
        """
        Returns 2 letter initials calculated based on the input.
        The algorithm picks first given email address, and takes first letter
        of part before @, and then the first letter of server name. In case
        the part before @ is in a format of `somestring.somestring2` it replaces
        the server letter with first letter of somestring2

        In case function was initialized with both first and lastname, this
        overrides the extraction from email by first letter of the first and
        last name. We add special logic to that functionality, In case Full name
        is compound, like Guido Von Rossum, we use last part of the last name
        (Von Rossum) picking `R`.

        Function also normalizes the non-ascii characters to they ascii
        representation, eg Ą => A
        """
        import unicodedata
        # replace non-ascii to ascii
        first_name = unicodedata.normalize(
            'NFKD', safe_unicode(self.first_name)).encode('ascii', 'ignore')
        last_name = unicodedata.normalize(
            'NFKD', safe_unicode(self.last_name)).encode('ascii', 'ignore')

        # do NFKD encoding, and also make sure email has proper format
        email_address = self.normalize_email(self.email_address)

        # first push the email initials
        prefix, server = email_address.split('@', 1)

        # check if prefix is maybe a 'first_name.last_name' syntax
        _dot_split = prefix.rsplit('.', 1)
        if len(_dot_split) == 2 and _dot_split[1]:
            initials = [_dot_split[0][0], _dot_split[1][0]]
        else:
            initials = [prefix[0], server[0]]

        # then try to replace either first_name or last_name
        fn_letter = (first_name or " ")[0].strip()
        ln_letter = (last_name.split(' ', 1)[-1] or " ")[0].strip()

        if fn_letter:
            initials[0] = fn_letter

        if ln_letter:
            initials[1] = ln_letter

        return ''.join(initials).upper()

    def get_img_data_by_type(self, font_family, img_type):
        default_user = """
        <svg xmlns="http://www.w3.org/2000/svg"
        version="1.1" x="0px" y="0px" width="{size}" height="{size}"
        viewBox="-15 -10 439.165 429.164"

        xml:space="preserve"
        style="background:{background};" >

        <path d="M204.583,216.671c50.664,0,91.74-48.075,
                 91.74-107.378c0-82.237-41.074-107.377-91.74-107.377
                 c-50.668,0-91.74,25.14-91.74,107.377C112.844,
                 168.596,153.916,216.671,
                 204.583,216.671z" fill="{text_color}"/>
        <path d="M407.164,374.717L360.88,
                 270.454c-2.117-4.771-5.836-8.728-10.465-11.138l-71.83-37.392
                 c-1.584-0.823-3.502-0.663-4.926,0.415c-20.316,
                 15.366-44.203,23.488-69.076,23.488c-24.877,
                 0-48.762-8.122-69.078-23.488
                 c-1.428-1.078-3.346-1.238-4.93-0.415L58.75,
                 259.316c-4.631,2.41-8.346,6.365-10.465,11.138L2.001,374.717
                 c-3.191,7.188-2.537,15.412,1.75,22.005c4.285,
                 6.592,11.537,10.526,19.4,10.526h362.861c7.863,0,15.117-3.936,
                 19.402-10.527 C409.699,390.129,
                 410.355,381.902,407.164,374.717z" fill="{text_color}"/>
        </svg>""".format(
            size=self.size,
            background='#979797',  # @grey4
            text_color=self.text_color,
            font_family=font_family)

        return {
            "default_user": default_user
        }[img_type]

    def get_img_data(self, svg_type=None):
        """
        generates the svg metadata for image
        """
        fonts = [
            '-apple-system',
             'BlinkMacSystemFont',
             'Segoe UI',
             'Roboto',
             'Oxygen-Sans',
             'Ubuntu',
             'Cantarell',
             'Helvetica Neue',
             'sans-serif'
        ]
        font_family = ','.join(fonts)
        if svg_type:
            return self.get_img_data_by_type(font_family, svg_type)

        initials = self.get_initials()
        img_data = """
        <svg xmlns="http://www.w3.org/2000/svg" pointer-events="none"
             width="{size}" height="{size}"
             style="width: 100%; height: 100%; background-color: {background}"
             viewBox="0 0 {size} {size}">
            <text text-anchor="middle" y="50%" x="50%" dy="0.35em"
                  pointer-events="auto" fill="{text_color}"
                  font-family="{font_family}"
                  style="font-weight: 400; font-size: {f_size}px;">{text}
            </text>
        </svg>""".format(
            size=self.size,
            f_size=self.size/2.05,  # scale the text inside the box nicely
            background=self.background,
            text_color=self.text_color,
            text=initials.upper(),
            font_family=font_family)

        return img_data

    def generate_svg(self, svg_type=None):
        img_data = self.get_img_data(svg_type)
        return "data:image/svg+xml;base64,%s" % img_data.encode('base64')


def initials_gravatar(email_address, first_name, last_name, size=30):
    svg_type = None
    if email_address == User.DEFAULT_USER_EMAIL:
        svg_type = 'default_user'
    klass = InitialsGravatar(email_address, first_name, last_name, size)
    return klass.generate_svg(svg_type=svg_type)


def gravatar_url(email_address, size=30, request=None):
    request = get_current_request()
    _use_gravatar = request.call_context.visual.use_gravatar
    _gravatar_url = request.call_context.visual.gravatar_url

    _gravatar_url = _gravatar_url or User.DEFAULT_GRAVATAR_URL

    email_address = email_address or User.DEFAULT_USER_EMAIL
    if isinstance(email_address, unicode):
        # hashlib crashes on unicode items
        email_address = safe_str(email_address)

    # empty email or default user
    if not email_address or email_address == User.DEFAULT_USER_EMAIL:
        return initials_gravatar(User.DEFAULT_USER_EMAIL, '', '', size=size)

    if _use_gravatar:
        # TODO: Disuse pyramid thread locals. Think about another solution to
        # get the host and schema here.
        request = get_current_request()
        tmpl = safe_str(_gravatar_url)
        tmpl = tmpl.replace('{email}', email_address)\
                   .replace('{md5email}', md5_safe(email_address.lower())) \
                   .replace('{netloc}', request.host)\
                   .replace('{scheme}', request.scheme)\
                   .replace('{size}', safe_str(size))
        return tmpl
    else:
        return initials_gravatar(email_address, '', '', size=size)


class Page(_Page):
    """
    Custom pager to match rendering style with paginator
    """

    def _get_pos(self, cur_page, max_page, items):
        edge = (items / 2) + 1
        if (cur_page <= edge):
            radius = max(items / 2, items - cur_page)
        elif (max_page - cur_page) < edge:
            radius = (items - 1) - (max_page - cur_page)
        else:
            radius = items / 2

        left = max(1, (cur_page - (radius)))
        right = min(max_page, cur_page + (radius))
        return left, cur_page, right

    def _range(self, regexp_match):
        """
        Return range of linked pages (e.g. '1 2 [3] 4 5 6 7 8').

        Arguments:

        regexp_match
            A "re" (regular expressions) match object containing the
            radius of linked pages around the current page in
            regexp_match.group(1) as a string

        This function is supposed to be called as a callable in
        re.sub.

        """
        radius = int(regexp_match.group(1))

        # Compute the first and last page number within the radius
        # e.g. '1 .. 5 6 [7] 8 9 .. 12'
        # -> leftmost_page  = 5
        # -> rightmost_page = 9
        leftmost_page, _cur, rightmost_page = self._get_pos(self.page,
                                                            self.last_page,
                                                            (radius * 2) + 1)
        nav_items = []

        # Create a link to the first page (unless we are on the first page
        # or there would be no need to insert '..' spacers)
        if self.page != self.first_page and self.first_page < leftmost_page:
            nav_items.append(self._pagerlink(self.first_page, self.first_page))

        # Insert dots if there are pages between the first page
        # and the currently displayed page range
        if leftmost_page - self.first_page > 1:
            # Wrap in a SPAN tag if nolink_attr is set
            text = '..'
            if self.dotdot_attr:
                text = HTML.span(c=text, **self.dotdot_attr)
            nav_items.append(text)

        for thispage in xrange(leftmost_page, rightmost_page + 1):
            # Hilight the current page number and do not use a link
            if thispage == self.page:
                text = '%s' % (thispage,)
                # Wrap in a SPAN tag if nolink_attr is set
                if self.curpage_attr:
                    text = HTML.span(c=text, **self.curpage_attr)
                nav_items.append(text)
            # Otherwise create just a link to that page
            else:
                text = '%s' % (thispage,)
                nav_items.append(self._pagerlink(thispage, text))

        # Insert dots if there are pages between the displayed
        # page numbers and the end of the page range
        if self.last_page - rightmost_page > 1:
            text = '..'
            # Wrap in a SPAN tag if nolink_attr is set
            if self.dotdot_attr:
                text = HTML.span(c=text, **self.dotdot_attr)
            nav_items.append(text)

        # Create a link to the very last page (unless we are on the last
        # page or there would be no need to insert '..' spacers)
        if self.page != self.last_page and rightmost_page < self.last_page:
            nav_items.append(self._pagerlink(self.last_page, self.last_page))

        ## prerender links
        #_page_link = url.current()
        #nav_items.append(literal('<link rel="prerender" href="%s?page=%s">' % (_page_link, str(int(self.page)+1))))
        #nav_items.append(literal('<link rel="prefetch" href="%s?page=%s">' % (_page_link, str(int(self.page)+1))))
        return self.separator.join(nav_items)

    def pager(self, format='~2~', page_param='page', partial_param='partial',
        show_if_single_page=False, separator=' ', onclick=None,
        symbol_first='<<', symbol_last='>>',
        symbol_previous='<', symbol_next='>',
        link_attr={'class': 'pager_link', 'rel': 'prerender'},
        curpage_attr={'class': 'pager_curpage'},
        dotdot_attr={'class': 'pager_dotdot'}, **kwargs):

        self.curpage_attr = curpage_attr
        self.separator = separator
        self.pager_kwargs = kwargs
        self.page_param = page_param
        self.partial_param = partial_param
        self.onclick = onclick
        self.link_attr = link_attr
        self.dotdot_attr = dotdot_attr

        # Don't show navigator if there is no more than one page
        if self.page_count == 0 or (self.page_count == 1 and not show_if_single_page):
            return ''

        from string import Template
        # Replace ~...~ in token format by range of pages
        result = re.sub(r'~(\d+)~', self._range, format)

        # Interpolate '%' variables
        result = Template(result).safe_substitute({
            'first_page': self.first_page,
            'last_page': self.last_page,
            'page': self.page,
            'page_count': self.page_count,
            'items_per_page': self.items_per_page,
            'first_item': self.first_item,
            'last_item': self.last_item,
            'item_count': self.item_count,
            'link_first': self.page > self.first_page and \
                    self._pagerlink(self.first_page, symbol_first) or '',
            'link_last': self.page < self.last_page and \
                    self._pagerlink(self.last_page, symbol_last) or '',
            'link_previous': self.previous_page and \
                    self._pagerlink(self.previous_page, symbol_previous) \
                    or HTML.span(symbol_previous, class_="pg-previous disabled"),
            'link_next': self.next_page and \
                    self._pagerlink(self.next_page, symbol_next) \
                    or HTML.span(symbol_next, class_="pg-next disabled")
        })

        return literal(result)


#==============================================================================
# REPO PAGER, PAGER FOR REPOSITORY
#==============================================================================
class RepoPage(Page):

    def __init__(self, collection, page=1, items_per_page=20,
                 item_count=None, url=None, **kwargs):

        """Create a "RepoPage" instance. special pager for paging
        repository
        """
        self._url_generator = url

        # Safe the kwargs class-wide so they can be used in the pager() method
        self.kwargs = kwargs

        # Save a reference to the collection
        self.original_collection = collection

        self.collection = collection

        # The self.page is the number of the current page.
        # The first page has the number 1!
        try:
            self.page = int(page)  # make it int() if we get it as a string
        except (ValueError, TypeError):
            self.page = 1

        self.items_per_page = items_per_page

        # Unless the user tells us how many items the collections has
        # we calculate that ourselves.
        if item_count is not None:
            self.item_count = item_count
        else:
            self.item_count = len(self.collection)

        # Compute the number of the first and last available page
        if self.item_count > 0:
            self.first_page = 1
            self.page_count = int(math.ceil(float(self.item_count) /
                                            self.items_per_page))
            self.last_page = self.first_page + self.page_count - 1

            # Make sure that the requested page number is the range of
            # valid pages
            if self.page > self.last_page:
                self.page = self.last_page
            elif self.page < self.first_page:
                self.page = self.first_page

            # Note: the number of items on this page can be less than
            #       items_per_page if the last page is not full
            self.first_item = max(0, (self.item_count) - (self.page *
                                                          items_per_page))
            self.last_item = ((self.item_count - 1) - items_per_page *
                              (self.page - 1))

            self.items = list(self.collection[self.first_item:self.last_item + 1])

            # Links to previous and next page
            if self.page > self.first_page:
                self.previous_page = self.page - 1
            else:
                self.previous_page = None

            if self.page < self.last_page:
                self.next_page = self.page + 1
            else:
                self.next_page = None

        # No items available
        else:
            self.first_page = None
            self.page_count = 0
            self.last_page = None
            self.first_item = None
            self.last_item = None
            self.previous_page = None
            self.next_page = None
            self.items = []

        # This is a subclass of the 'list' type. Initialise the list now.
        list.__init__(self, reversed(self.items))


def breadcrumb_repo_link(repo):
    """
    Makes a breadcrumbs path link to repo

    ex::
        group >> subgroup >> repo

    :param repo: a Repository instance
    """

    path = [
        link_to(group.name, route_path('repo_group_home', repo_group_name=group.group_name),
                title='last change:{}'.format(format_date(group.last_commit_change)))
        for group in repo.groups_with_parents
    ] + [
        link_to(repo.just_name, route_path('repo_summary', repo_name=repo.repo_name),
                title='last change:{}'.format(format_date(repo.last_commit_change)))
    ]

    return literal(' &raquo; '.join(path))


def breadcrumb_repo_group_link(repo_group):
    """
    Makes a breadcrumbs path link to repo

    ex::
        group >> subgroup

    :param repo_group: a Repository Group instance
    """

    path = [
        link_to(group.name,
                route_path('repo_group_home', repo_group_name=group.group_name),
                title='last change:{}'.format(format_date(group.last_commit_change)))
        for group in repo_group.parents
    ] + [
        link_to(repo_group.name,
                route_path('repo_group_home', repo_group_name=repo_group.group_name),
                title='last change:{}'.format(format_date(repo_group.last_commit_change)))
    ]

    return literal(' &raquo; '.join(path))


def format_byte_size_binary(file_size):
    """
    Formats file/folder sizes to standard.
    """
    if file_size is None:
        file_size = 0

    formatted_size = format_byte_size(file_size, binary=True)
    return formatted_size


def urlify_text(text_, safe=True):
    """
    Extrac urls from text and make html links out of them

    :param text_:
    """

    url_pat = re.compile(r'''(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@#.&+]'''
                         '''|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)''')

    def url_func(match_obj):
        url_full = match_obj.groups()[0]
        return '<a href="%(url)s">%(url)s</a>' % ({'url': url_full})
    _newtext = url_pat.sub(url_func, text_)
    if safe:
        return literal(_newtext)
    return _newtext


def urlify_commits(text_, repository):
    """
    Extract commit ids from text and make link from them

    :param text_:
    :param repository: repo name to build the URL with
    """

    URL_PAT = re.compile(r'(^|\s)([0-9a-fA-F]{12,40})($|\s)')

    def url_func(match_obj):
        commit_id = match_obj.groups()[1]
        pref = match_obj.groups()[0]
        suf = match_obj.groups()[2]

        tmpl = (
            '%(pref)s<a class="%(cls)s" href="%(url)s">'
            '%(commit_id)s</a>%(suf)s'
        )
        return tmpl % {
            'pref': pref,
            'cls': 'revision-link',
            'url': route_url('repo_commit', repo_name=repository, commit_id=commit_id),
            'commit_id': commit_id,
            'suf': suf
        }

    newtext = URL_PAT.sub(url_func, text_)

    return newtext


def _process_url_func(match_obj, repo_name, uid, entry,
                      return_raw_data=False, link_format='html'):
    pref = ''
    if match_obj.group().startswith(' '):
        pref = ' '

    issue_id = ''.join(match_obj.groups())

    if link_format == 'html':
        tmpl = (
            '%(pref)s<a class="%(cls)s" href="%(url)s">'
            '%(issue-prefix)s%(id-repr)s'
            '</a>')
    elif link_format == 'rst':
        tmpl = '`%(issue-prefix)s%(id-repr)s <%(url)s>`_'
    elif link_format == 'markdown':
        tmpl = '[%(issue-prefix)s%(id-repr)s](%(url)s)'
    else:
        raise ValueError('Bad link_format:{}'.format(link_format))

    (repo_name_cleaned,
     parent_group_name) = RepoGroupModel()._get_group_name_and_parent(repo_name)

    # variables replacement
    named_vars = {
        'id': issue_id,
        'repo': repo_name,
        'repo_name': repo_name_cleaned,
        'group_name': parent_group_name
    }
    # named regex variables
    named_vars.update(match_obj.groupdict())
    _url = string.Template(entry['url']).safe_substitute(**named_vars)

    def quote_cleaner(input_str):
        """Remove quotes as it's HTML"""
        return input_str.replace('"', '')

    data = {
        'pref': pref,
        'cls': quote_cleaner('issue-tracker-link'),
        'url': quote_cleaner(_url),
        'id-repr': issue_id,
        'issue-prefix': entry['pref'],
        'serv': entry['url'],
    }
    if return_raw_data:
        return {
            'id': issue_id,
            'url': _url
        }
    return tmpl % data


def get_active_pattern_entries(repo_name):
    repo = None
    if repo_name:
        # Retrieving repo_name to avoid invalid repo_name to explode on
        # IssueTrackerSettingsModel but still passing invalid name further down
        repo = Repository.get_by_repo_name(repo_name, cache=True)

    settings_model = IssueTrackerSettingsModel(repo=repo)
    active_entries = settings_model.get_settings(cache=True)
    return active_entries


def process_patterns(text_string, repo_name, link_format='html', active_entries=None):

    allowed_formats = ['html', 'rst', 'markdown']
    if link_format not in allowed_formats:
        raise ValueError('Link format can be only one of:{} got {}'.format(
                         allowed_formats, link_format))

    active_entries = active_entries or get_active_pattern_entries(repo_name)
    issues_data = []
    newtext = text_string

    for uid, entry in active_entries.items():
        log.debug('found issue tracker entry with uid %s', uid)

        if not (entry['pat'] and entry['url']):
            log.debug('skipping due to missing data')
            continue

        log.debug('issue tracker entry: uid: `%s` PAT:%s URL:%s PREFIX:%s',
                  uid, entry['pat'], entry['url'], entry['pref'])

        try:
            pattern = re.compile(r'%s' % entry['pat'])
        except re.error:
            log.exception(
                'issue tracker pattern: `%s` failed to compile',
                entry['pat'])
            continue

        data_func = partial(
            _process_url_func, repo_name=repo_name, entry=entry, uid=uid,
            return_raw_data=True)

        for match_obj in pattern.finditer(text_string):
            issues_data.append(data_func(match_obj))

        url_func = partial(
            _process_url_func, repo_name=repo_name, entry=entry, uid=uid,
            link_format=link_format)

        newtext = pattern.sub(url_func, newtext)
        log.debug('processed prefix:uid `%s`', uid)

    return newtext, issues_data


def urlify_commit_message(commit_text, repository=None, active_pattern_entries=None):
    """
    Parses given text message and makes proper links.
    issues are linked to given issue-server, and rest is a commit link

    :param commit_text:
    :param repository:
    """
    def escaper(string):
        return string.replace('<', '&lt;').replace('>', '&gt;')

    newtext = escaper(commit_text)

    # extract http/https links and make them real urls
    newtext = urlify_text(newtext, safe=False)

    # urlify commits - extract commit ids and make link out of them, if we have
    # the scope of repository present.
    if repository:
        newtext = urlify_commits(newtext, repository)

    # process issue tracker patterns
    newtext, issues = process_patterns(newtext, repository or '',
                                       active_entries=active_pattern_entries)

    return literal(newtext)


def render_binary(repo_name, file_obj):
    """
    Choose how to render a binary file
    """

    filename = file_obj.name

    # images
    for ext in ['*.png', '*.jpg', '*.ico', '*.gif']:
        if fnmatch.fnmatch(filename, pat=ext):
            alt = escape(filename)
            src = route_path(
                'repo_file_raw', repo_name=repo_name,
                commit_id=file_obj.commit.raw_id,
                f_path=file_obj.path)
            return literal(
                '<img class="rendered-binary" alt="{}" src="{}">'.format(alt, src))


def renderer_from_filename(filename, exclude=None):
    """
    choose a renderer based on filename, this works only for text based files
    """

    # ipython
    for ext in ['*.ipynb']:
        if fnmatch.fnmatch(filename, pat=ext):
            return 'jupyter'

    is_markup = MarkupRenderer.renderer_from_filename(filename, exclude=exclude)
    if is_markup:
        return is_markup
    return None


def render(source, renderer='rst', mentions=False, relative_urls=None,
           repo_name=None):

    def maybe_convert_relative_links(html_source):
        if relative_urls:
            return relative_links(html_source, relative_urls)
        return html_source

    if renderer == 'plain':
        return literal(
            MarkupRenderer.plain(source, leading_newline=False))

    elif renderer == 'rst':
        if repo_name:
            # process patterns on comments if we pass in repo name
            source, issues = process_patterns(
                source, repo_name, link_format='rst')

        return literal(
            '<div class="rst-block">%s</div>' %
            maybe_convert_relative_links(
                MarkupRenderer.rst(source, mentions=mentions)))

    elif renderer == 'markdown':
        if repo_name:
            # process patterns on comments if we pass in repo name
            source, issues = process_patterns(
                source, repo_name, link_format='markdown')

        return literal(
            '<div class="markdown-block">%s</div>' %
            maybe_convert_relative_links(
                MarkupRenderer.markdown(source, flavored=True,
                                        mentions=mentions)))

    elif renderer == 'jupyter':
        return literal(
            '<div class="ipynb">%s</div>' %
            maybe_convert_relative_links(
                MarkupRenderer.jupyter(source)))

    # None means just show the file-source
    return None


def commit_status(repo, commit_id):
    return ChangesetStatusModel().get_status(repo, commit_id)


def commit_status_lbl(commit_status):
    return dict(ChangesetStatus.STATUSES).get(commit_status)


def commit_time(repo_name, commit_id):
    repo = Repository.get_by_repo_name(repo_name)
    commit = repo.get_commit(commit_id=commit_id)
    return commit.date


def get_permission_name(key):
    return dict(Permission.PERMS).get(key)


def journal_filter_help(request):
    _ = request.translate
    from rhodecode.lib.audit_logger import ACTIONS
    actions = '\n'.join(textwrap.wrap(', '.join(sorted(ACTIONS.keys())), 80))

    return _(
        'Example filter terms:\n' +
        '     repository:vcs\n' +
        '     username:marcin\n' +
        '     username:(NOT marcin)\n' +
        '     action:*push*\n' +
        '     ip:127.0.0.1\n' +
        '     date:20120101\n' +
        '     date:[20120101100000 TO 20120102]\n' +
        '\n' +
        'Actions: {actions}\n' +
        '\n' +
        'Generate wildcards using \'*\' character:\n' +
        '     "repository:vcs*" - search everything starting with \'vcs\'\n' +
        '     "repository:*vcs*" - search for repository containing \'vcs\'\n' +
        '\n' +
        'Optional AND / OR operators in queries\n' +
        '     "repository:vcs OR repository:test"\n' +
        '     "username:test AND repository:test*"\n'
    ).format(actions=actions)


def not_mapped_error(repo_name):
    from rhodecode.translation import _
    flash(_('%s repository is not mapped to db perhaps'
            ' it was created or renamed from the filesystem'
            ' please run the application again'
            ' in order to rescan repositories') % repo_name, category='error')


def ip_range(ip_addr):
    from rhodecode.model.db import UserIpMap
    s, e = UserIpMap._get_ip_range(ip_addr)
    return '%s - %s' % (s, e)


def form(url, method='post', needs_csrf_token=True, **attrs):
    """Wrapper around webhelpers.tags.form to prevent CSRF attacks."""
    if method.lower() != 'get' and needs_csrf_token:
        raise Exception(
            'Forms to POST/PUT/DELETE endpoints should have (in general) a ' +
            'CSRF token. If the endpoint does not require such token you can ' +
            'explicitly set the parameter needs_csrf_token to false.')

    return wh_form(url, method=method, **attrs)


def secure_form(form_url, method="POST", multipart=False, **attrs):
    """Start a form tag that points the action to an url. This
    form tag will also include the hidden field containing
    the auth token.

    The url options should be given either as a string, or as a
    ``url()`` function. The method for the form defaults to POST.

    Options:

    ``multipart``
        If set to True, the enctype is set to "multipart/form-data".
    ``method``
        The method to use when submitting the form, usually either
        "GET" or "POST". If "PUT", "DELETE", or another verb is used, a
        hidden input with name _method is added to simulate the verb
        over POST.

    """
    from webhelpers.pylonslib.secure_form import insecure_form

    if 'request' in attrs:
        session = attrs['request'].session
        del attrs['request']
    else:
        raise ValueError(
            'Calling this form requires request= to be passed as argument')

    form = insecure_form(form_url, method, multipart, **attrs)
    token = literal(
        '<input type="hidden" id="{}" name="{}" value="{}">'.format(
        csrf_token_key, csrf_token_key, get_csrf_token(session)))

    return literal("%s\n%s" % (form, token))


def dropdownmenu(name, selected, options, enable_filter=False, **attrs):
    select_html = select(name, selected, options, **attrs)

    select2 = """
        <script>
            $(document).ready(function() {
                  $('#%s').select2({
                      containerCssClass: 'drop-menu %s',
                      dropdownCssClass: 'drop-menu-dropdown',
                      dropdownAutoWidth: true%s
                  });
            });
        </script>
    """

    filter_option = """,
                        minimumResultsForSearch: -1
    """
    input_id = attrs.get('id') or name
    extra_classes = ' '.join(attrs.pop('extra_classes', []))
    filter_enabled = "" if enable_filter else filter_option
    select_script = literal(select2 % (input_id, extra_classes, filter_enabled))

    return literal(select_html+select_script)


def get_visual_attr(tmpl_context_var, attr_name):
    """
    A safe way to get a variable from visual variable of template context

    :param tmpl_context_var: instance of tmpl_context, usually present as `c`
    :param attr_name: name of the attribute we fetch from the c.visual
    """
    visual = getattr(tmpl_context_var, 'visual', None)
    if not visual:
        return
    else:
        return getattr(visual, attr_name, None)


def get_last_path_part(file_node):
    if not file_node.path:
        return u'/'

    path = safe_unicode(file_node.path.split('/')[-1])
    return u'../' + path


def route_url(*args, **kwargs):
    """
    Wrapper around pyramids `route_url` (fully qualified url) function. 
    """
    req = get_current_request()
    return req.route_url(*args, **kwargs)


def route_path(*args, **kwargs):
    """
    Wrapper around pyramids `route_path` function.
    """
    req = get_current_request()
    return req.route_path(*args, **kwargs)


def route_path_or_none(*args, **kwargs):
    try:
        return route_path(*args, **kwargs)
    except KeyError:
        return None


def current_route_path(request, **kw):
    new_args = request.GET.mixed()
    new_args.update(kw)
    return request.current_route_path(_query=new_args)


def api_call_example(method, args):
    """
    Generates an API call example via CURL
    """
    args_json = json.dumps(OrderedDict([
        ('id', 1),
        ('auth_token', 'SECRET'),
        ('method', method),
        ('args', args)
    ]))
    return literal(
        "curl {api_url} -X POST -H 'content-type:text/plain' --data-binary '{data}'"
        "<br/><br/>SECRET can be found in <a href=\"{token_url}\">auth-tokens</a> page, "
        "and needs to be of `api calls` role."
        .format(
            api_url=route_url('apiv2'),
            token_url=route_url('my_account_auth_tokens'),
            data=args_json))


def notification_description(notification, request):
    """
    Generate notification human readable description based on notification type
    """
    from rhodecode.model.notification import NotificationModel
    return NotificationModel().make_description(
        notification, translate=request.translate)


def go_import_header(request, db_repo=None):
    """
    Creates a header for go-import functionality in Go Lang
    """

    if not db_repo:
        return
    if 'go-get' not in request.GET:
        return

    clone_url = db_repo.clone_url()
    prefix = re.split(r'^https?:\/\/', clone_url)[-1]
    # we have a repo and go-get flag,
    return literal('<meta name="go-import" content="{} {} {}">'.format(
        prefix, db_repo.repo_type, clone_url))


def reviewer_as_json(*args, **kwargs):
    from rhodecode.apps.repository.utils import reviewer_as_json as _reviewer_as_json
    return _reviewer_as_json(*args, **kwargs)


def get_repo_view_type(request):
    route_name = request.matched_route.name
    route_to_view_type = {
        'repo_changelog': 'commits',
        'repo_commits': 'commits',
        'repo_files': 'files',
        'repo_summary': 'summary',
        'repo_commit': 'commit'
    }

    return route_to_view_type.get(route_name)
