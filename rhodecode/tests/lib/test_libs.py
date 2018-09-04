# -*- coding: utf-8 -*-

# Copyright (C) 2010-2018 RhodeCode GmbH
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
Package for testing various lib/helper functions in rhodecode
"""

import datetime
import string
import mock
import pytest

from rhodecode.tests import no_newline_id_generator
from rhodecode.tests.utils import run_test_concurrently

from rhodecode.lib import rc_cache
from rhodecode.lib.helpers import InitialsGravatar
from rhodecode.lib.utils2 import AttributeDict

from rhodecode.model.db import Repository, CacheKey


def _urls_for_proto(proto):
    return [
        ('%s://127.0.0.1' % proto, ['%s://' % proto, '127.0.0.1'],
         '%s://127.0.0.1' % proto),
        ('%s://marcink@127.0.0.1' % proto, ['%s://' % proto, '127.0.0.1'],
         '%s://127.0.0.1' % proto),
        ('%s://marcink:pass@127.0.0.1' % proto, ['%s://' % proto, '127.0.0.1'],
         '%s://127.0.0.1' % proto),
        ('%s://127.0.0.1:8080' % proto, ['%s://' % proto, '127.0.0.1', '8080'],
         '%s://127.0.0.1:8080' % proto),
        ('%s://domain.org' % proto, ['%s://' % proto, 'domain.org'],
         '%s://domain.org' % proto),
        ('%s://user:pass@domain.org:8080' % proto,
         ['%s://' % proto, 'domain.org', '8080'],
         '%s://domain.org:8080' % proto),
    ]

TEST_URLS = _urls_for_proto('http') + _urls_for_proto('https')


@pytest.mark.parametrize("test_url, expected, expected_creds", TEST_URLS)
def test_uri_filter(test_url, expected, expected_creds):
    from rhodecode.lib.utils2 import uri_filter
    assert uri_filter(test_url) == expected


@pytest.mark.parametrize("test_url, expected, expected_creds", TEST_URLS)
def test_credentials_filter(test_url, expected, expected_creds):
    from rhodecode.lib.utils2 import credentials_filter
    assert credentials_filter(test_url) == expected_creds


@pytest.mark.parametrize("str_bool, expected", [
    ('t', True),
    ('true', True),
    ('y', True),
    ('yes', True),
    ('on', True),
    ('1', True),
    ('Y', True),
    ('yeS', True),
    ('Y', True),
    ('TRUE', True),
    ('T', True),
    ('False', False),
    ('F', False),
    ('FALSE', False),
    ('0', False),
    ('-1', False),
    ('', False)
])
def test_str2bool(str_bool, expected):
    from rhodecode.lib.utils2 import str2bool
    assert str2bool(str_bool) == expected


@pytest.mark.parametrize("text, expected", reduce(lambda a1,a2:a1+a2, [
[
(pref+"", []),
(pref+"Hi there @marcink", ['marcink']),
(pref+"Hi there @marcink and @bob", ['bob', 'marcink']),
(pref+"Hi there @marcink\n", ['marcink']),
(pref+"Hi there @marcink and @bob\n", ['bob', 'marcink']),
(pref+"Hi there marcin@rhodecode.com", []),
(pref+"Hi there @john.malcovic and @bob\n", ['bob', 'john.malcovic']),
(pref+"This needs to be reviewed: (@marcink,@john)", ["john", "marcink"]),
(pref+"This needs to be reviewed: (@marcink, @john)", ["john", "marcink"]),
(pref+"This needs to be reviewed: [@marcink,@john]", ["john", "marcink"]),
(pref+"This needs to be reviewed: (@marcink @john)", ["john", "marcink"]),
(pref+"@john @mary, please review", ["john", "mary"]),
(pref+"@john,@mary, please review", ["john", "mary"]),
(pref+"Hej @123, @22john,@mary, please review", ['123', '22john', 'mary']),
(pref+"@first hi there @marcink here's my email marcin@email.com "
 "@lukaszb check @one_more22 it pls @ ttwelve @D[] @one@two@three ", ['first', 'lukaszb', 'marcink', 'one', 'one_more22']),
(pref+"@MARCIN    @maRCiN @2one_more22 @john please see this http://org.pl", ['2one_more22', 'john', 'MARCIN', 'maRCiN']),
(pref+"@marian.user just do it @marco-polo and next extract @marco_polo", ['marco-polo', 'marco_polo', 'marian.user']),
(pref+"user.dot  hej ! not-needed maril@domain.org", []),
(pref+"\n@marcin", ['marcin']),
]
for pref in ['', '\n', 'hi !', '\t', '\n\n']]), ids=no_newline_id_generator)
def test_mention_extractor(text, expected):
    from rhodecode.lib.utils2 import extract_mentioned_users
    got = extract_mentioned_users(text)
    assert sorted(got, key=lambda x: x.lower()) == got
    assert set(expected) == set(got)

@pytest.mark.parametrize("age_args, expected, kw", [
    ({}, u'just now', {}),
    ({'seconds': -1}, u'1 second ago', {}),
    ({'seconds': -60 * 2}, u'2 minutes ago', {}),
    ({'hours': -1}, u'1 hour ago', {}),
    ({'hours': -24}, u'1 day ago', {}),
    ({'hours': -24 * 5}, u'5 days ago', {}),
    ({'months': -1}, u'1 month ago', {}),
    ({'months': -1, 'days': -2}, u'1 month and 2 days ago', {}),
    ({'years': -1, 'months': -1}, u'1 year and 1 month ago', {}),
    ({}, u'just now', {'short_format': True}),
    ({'seconds': -1}, u'1sec ago', {'short_format': True}),
    ({'seconds': -60 * 2}, u'2min ago', {'short_format': True}),
    ({'hours': -1}, u'1h ago', {'short_format': True}),
    ({'hours': -24}, u'1d ago', {'short_format': True}),
    ({'hours': -24 * 5}, u'5d ago', {'short_format': True}),
    ({'months': -1}, u'1m ago', {'short_format': True}),
    ({'months': -1, 'days': -2}, u'1m, 2d ago', {'short_format': True}),
    ({'years': -1, 'months': -1}, u'1y, 1m ago', {'short_format': True}),
])
def test_age(age_args, expected, kw, baseapp):
    from rhodecode.lib.utils2 import age
    from dateutil import relativedelta
    n = datetime.datetime(year=2012, month=5, day=17)
    delt = lambda *args, **kwargs: relativedelta.relativedelta(*args, **kwargs)

    def translate(elem):
        return elem.interpolate()

    assert translate(age(n + delt(**age_args), now=n, **kw)) == expected


@pytest.mark.parametrize("age_args, expected, kw", [
    ({}, u'just now', {}),
    ({'seconds': 1}, u'in 1 second', {}),
    ({'seconds': 60 * 2}, u'in 2 minutes', {}),
    ({'hours': 1}, u'in 1 hour', {}),
    ({'hours': 24}, u'in 1 day', {}),
    ({'hours': 24 * 5}, u'in 5 days', {}),
    ({'months': 1}, u'in 1 month', {}),
    ({'months': 1, 'days': 1}, u'in 1 month and 1 day', {}),
    ({'years': 1, 'months': 1}, u'in 1 year and 1 month', {}),
    ({}, u'just now', {'short_format': True}),
    ({'seconds': 1}, u'in 1sec', {'short_format': True}),
    ({'seconds': 60 * 2}, u'in 2min', {'short_format': True}),
    ({'hours': 1}, u'in 1h', {'short_format': True}),
    ({'hours': 24}, u'in 1d', {'short_format': True}),
    ({'hours': 24 * 5}, u'in 5d', {'short_format': True}),
    ({'months': 1}, u'in 1m', {'short_format': True}),
    ({'months': 1, 'days': 1}, u'in 1m, 1d', {'short_format': True}),
    ({'years': 1, 'months': 1}, u'in 1y, 1m', {'short_format': True}),
])
def test_age_in_future(age_args, expected, kw, baseapp):
    from rhodecode.lib.utils2 import age
    from dateutil import relativedelta
    n = datetime.datetime(year=2012, month=5, day=17)
    delt = lambda *args, **kwargs: relativedelta.relativedelta(*args, **kwargs)

    def translate(elem):
        return elem.interpolate()

    assert translate(age(n + delt(**age_args), now=n, **kw)) == expected


@pytest.mark.parametrize("sample, expected_tags", [
    # entry
    ((
             ""
     ),
     [

     ]),
    # entry
    ((
        "hello world [stale]"
     ),
     [
         ('state', '[stale]'),
     ]),
    # entry
    ((
         "hello world [v2.0.0] [v1.0.0]"
     ),
     [
         ('generic', '[v2.0.0]'),
         ('generic', '[v1.0.0]'),
     ]),
    # entry
    ((
             "he[ll]o wo[rl]d"
     ),
     [
         ('label', '[ll]'),
         ('label', '[rl]'),
     ]),
    # entry
    ((
        "hello world [stale]\n[featured]\n[stale] [dead] [dev]"
     ),
     [
         ('state', '[stale]'),
         ('state', '[featured]'),
         ('state', '[stale]'),
         ('state', '[dead]'),
         ('state', '[dev]'),
     ]),
    # entry
    ((
        "hello world \n\n [stale] \n [url =&gt; [name](http://rc.com)]"
     ),
     [
        ('state', '[stale]'),
        ('url', '[url =&gt; [name](http://rc.com)]'),
     ]),
    # entry
    ((
            "[url =&gt; [linkNameJS](javascript:alert(document.domain))]\n"
            "[url =&gt; [linkNameHTTP](http://rhodecode.com)]\n"
            "[url =&gt; [linkNameHTTPS](https://rhodecode.com)]\n"
            "[url =&gt; [linkNamePath](/repo_group)]\n"
     ),
     [
         ('generic', '[linkNameJS]'),
         ('url', '[url =&gt; [linkNameHTTP](http://rhodecode.com)]'),
         ('url', '[url =&gt; [linkNameHTTPS](https://rhodecode.com)]'),
         ('url', '[url =&gt; [linkNamePath](/repo_group)]'),
     ]),
    # entry
    ((
        "hello pta[tag] gog [[]] [[] sda ero[or]d [me =&gt;>< sa]"
        "[requires] [stale] [see<>=&gt;] [see =&gt; http://url.com]"
        "[requires =&gt; url] [lang =&gt; python] [just a tag] "
        "<html_tag first='abc' attr=\"my.url?attr=&another=\"></html_tag>"
        "[,d] [ =&gt; ULR ] [obsolete] [desc]]"
    ),
     [
        ('label', '[desc]'),
        ('label', '[obsolete]'),
        ('label', '[or]'),
        ('label', '[requires]'),
        ('label', '[tag]'),
        ('state', '[stale]'),
        ('lang', '[lang =&gt; python]'),
        ('ref', '[requires =&gt; url]'),
        ('see', '[see =&gt; http://url.com]'),

     ]),

], ids=no_newline_id_generator)
def test_metatag_extraction(sample, expected_tags):
    from rhodecode.lib.helpers import extract_metatags
    tags, value = extract_metatags(sample)
    assert sorted(tags) == sorted(expected_tags)


@pytest.mark.parametrize("tag_data, expected_html", [

    (('state', '[stable]'), '<div class="metatag" tag="state stable">stable</div>'),
    (('state', '[stale]'), '<div class="metatag" tag="state stale">stale</div>'),
    (('state', '[featured]'), '<div class="metatag" tag="state featured">featured</div>'),
    (('state', '[dev]'), '<div class="metatag" tag="state dev">dev</div>'),
    (('state', '[dead]'), '<div class="metatag" tag="state dead">dead</div>'),

    (('label', '[personal]'), '<div class="metatag" tag="label">personal</div>'),
    (('generic', '[v2.0.0]'), '<div class="metatag" tag="generic">v2.0.0</div>'),

    (('lang', '[lang =&gt; JavaScript]'), '<div class="metatag" tag="lang">JavaScript</div>'),
    (('lang', '[lang =&gt; C++]'), '<div class="metatag" tag="lang">C++</div>'),
    (('lang', '[lang =&gt; C#]'), '<div class="metatag" tag="lang">C#</div>'),
    (('lang', '[lang =&gt; Delphi/Object]'), '<div class="metatag" tag="lang">Delphi/Object</div>'),
    (('lang', '[lang =&gt; Objective-C]'), '<div class="metatag" tag="lang">Objective-C</div>'),
    (('lang', '[lang =&gt; .NET]'), '<div class="metatag" tag="lang">.NET</div>'),

    (('license', '[license =&gt; BSD 3-clause]'), '<div class="metatag" tag="license"><a href="http:\/\/www.opensource.org/licenses/BSD 3-clause">BSD 3-clause</a></div>'),
    (('license', '[license =&gt; GPLv3]'), '<div class="metatag" tag="license"><a href="http:\/\/www.opensource.org/licenses/GPLv3">GPLv3</a></div>'),
    (('license', '[license =&gt; MIT]'), '<div class="metatag" tag="license"><a href="http:\/\/www.opensource.org/licenses/MIT">MIT</a></div>'),
    (('license', '[license =&gt; AGPLv3]'), '<div class="metatag" tag="license"><a href="http:\/\/www.opensource.org/licenses/AGPLv3">AGPLv3</a></div>'),

    (('ref', '[requires =&gt; RepoName]'), '<div class="metatag" tag="ref requires">requires: <a href="/RepoName">RepoName</a></div>'),
    (('ref', '[recommends =&gt; GroupName]'), '<div class="metatag" tag="ref recommends">recommends: <a href="/GroupName">GroupName</a></div>'),
    (('ref', '[conflicts =&gt; SomeName]'), '<div class="metatag" tag="ref conflicts">conflicts: <a href="/SomeName">SomeName</a></div>'),
    (('ref', '[base =&gt; SomeName]'), '<div class="metatag" tag="ref base">base: <a href="/SomeName">SomeName</a></div>'),

    (('see', '[see =&gt; http://rhodecode.com]'), '<div class="metatag" tag="see">see: http://rhodecode.com </div>'),

    (('url', '[url =&gt; [linkName](https://rhodecode.com)]'), '<div class="metatag" tag="url"> <a href="https://rhodecode.com">linkName</a> </div>'),
    (('url', '[url =&gt; [example link](https://rhodecode.com)]'), '<div class="metatag" tag="url"> <a href="https://rhodecode.com">example link</a> </div>'),
    (('url', '[url =&gt; [v1.0.0](https://rhodecode.com)]'), '<div class="metatag" tag="url"> <a href="https://rhodecode.com">v1.0.0</a> </div>'),

])
def test_metatags_stylize(tag_data, expected_html):
    from rhodecode.lib.helpers import style_metatag
    tag_type,value = tag_data
    assert style_metatag(tag_type, value) == expected_html


@pytest.mark.parametrize("tmpl_url, email, expected", [
    ('http://test.com/{email}', 'test@foo.com', 'http://test.com/test@foo.com'),

    ('http://test.com/{md5email}', 'test@foo.com', 'http://test.com/3cb7232fcc48743000cb86d0d5022bd9'),
    ('http://test.com/{md5email}', 'testąć@foo.com', 'http://test.com/978debb907a3c55cd741872ab293ef30'),

    ('http://testX.com/{md5email}?s={size}', 'test@foo.com', 'http://testX.com/3cb7232fcc48743000cb86d0d5022bd9?s=24'),
    ('http://testX.com/{md5email}?s={size}', 'testąć@foo.com', 'http://testX.com/978debb907a3c55cd741872ab293ef30?s=24'),

    ('{scheme}://{netloc}/{md5email}/{size}', 'test@foo.com', 'https://server.com/3cb7232fcc48743000cb86d0d5022bd9/24'),
    ('{scheme}://{netloc}/{md5email}/{size}', 'testąć@foo.com', 'https://server.com/978debb907a3c55cd741872ab293ef30/24'),

    ('http://test.com/{email}', 'testąć@foo.com', 'http://test.com/testąć@foo.com'),
    ('http://test.com/{email}?size={size}', 'test@foo.com', 'http://test.com/test@foo.com?size=24'),
    ('http://test.com/{email}?size={size}', 'testąć@foo.com', 'http://test.com/testąć@foo.com?size=24'),
])
def test_gravatar_url_builder(tmpl_url, email, expected, request_stub):
    from rhodecode.lib.helpers import gravatar_url

    def fake_tmpl_context(_url):
        _c = AttributeDict()
        _c.visual = AttributeDict()
        _c.visual.use_gravatar = True
        _c.visual.gravatar_url = _url
        return _c

    # mock pyramid.threadlocals
    def fake_get_current_request():
        request_stub.scheme = 'https'
        request_stub.host = 'server.com'

        request_stub._call_context = fake_tmpl_context(tmpl_url)
        return request_stub

    with mock.patch('rhodecode.lib.helpers.get_current_request',
                    fake_get_current_request):

        grav = gravatar_url(email_address=email, size=24)
        assert grav == expected


@pytest.mark.parametrize(
    "email, first_name, last_name, expected_initials, expected_color", [

        ('test@rhodecode.com', '', '', 'TR', '#8a994d'),
        ('marcin.kuzminski@rhodecode.com', '', '', 'MK', '#6559b3'),
        # special cases of email
        ('john.van.dam@rhodecode.com', '', '', 'JD', '#526600'),
        ('Guido.van.Rossum@rhodecode.com', '', '', 'GR', '#990052'),
        ('Guido.van.Rossum@rhodecode.com', 'Guido', 'Van Rossum', 'GR', '#990052'),

        ('rhodecode+Guido.van.Rossum@rhodecode.com', '', '', 'RR', '#46598c'),
        ('pclouds@rhodecode.com', 'Nguyễn Thái', 'Tgọc Duy', 'ND', '#665200'),

        ('john-brown@foo.com', '', '', 'JF', '#73006b'),
        ('admin@rhodecode.com', 'Marcin', 'Kuzminski', 'MK', '#104036'),
        # partials
        ('admin@rhodecode.com', 'Marcin', '', 'MR', '#104036'),  # fn+email
        ('admin@rhodecode.com', '', 'Kuzminski', 'AK', '#104036'),  # em+ln
        # non-ascii
        ('admin@rhodecode.com', 'Marcin', 'Śuzminski', 'MS', '#104036'),
        ('marcin.śuzminski@rhodecode.com', '', '', 'MS', '#73000f'),

        # special cases, LDAP can provide those...
        ('admin@', 'Marcin', 'Śuzminski', 'MS', '#aa00ff'),
        ('marcin.śuzminski', '', '', 'MS', '#402020'),
        ('null', '', '', 'NL', '#8c4646'),
        ('some.@abc.com', 'some', '', 'SA', '#664e33')
])
def test_initials_gravatar_pick_of_initials_and_color_algo(
        email, first_name, last_name, expected_initials, expected_color):
    instance = InitialsGravatar(email, first_name, last_name)
    assert instance.get_initials() == expected_initials
    assert instance.str2color(email) == expected_color


def test_initials_gravatar_mapping_algo():
    pos = set()
    instance = InitialsGravatar('', '', '')
    iterations = 0

    variations = []
    for letter1 in string.ascii_letters:
        for letter2 in string.ascii_letters[::-1][:10]:
            for letter3 in string.ascii_letters[:10]:
                variations.append(
                    '%s@rhodecode.com' % (letter1+letter2+letter3))

    max_variations = 4096
    for email in variations[:max_variations]:
        iterations += 1
        pos.add(
            instance.pick_color_bank_index(email,
                                           instance.get_color_bank()))

    # we assume that we have match all 256 possible positions,
    # in reasonable amount of different email addresses
    assert len(pos) == 256
    assert iterations == max_variations


@pytest.mark.parametrize("tmpl, repo_name, overrides, prefix, expected", [
    (Repository.DEFAULT_CLONE_URI, 'group/repo1', {}, '', 'http://vps1:8000/group/repo1'),
    (Repository.DEFAULT_CLONE_URI, 'group/repo1', {'user': 'marcink'}, '', 'http://marcink@vps1:8000/group/repo1'),
    (Repository.DEFAULT_CLONE_URI, 'group/repo1', {}, '/rc', 'http://vps1:8000/rc/group/repo1'),
    (Repository.DEFAULT_CLONE_URI, 'group/repo1', {'user': 'user'}, '/rc', 'http://user@vps1:8000/rc/group/repo1'),
    (Repository.DEFAULT_CLONE_URI, 'group/repo1', {'user': 'marcink'}, '/rc', 'http://marcink@vps1:8000/rc/group/repo1'),
    (Repository.DEFAULT_CLONE_URI, 'group/repo1', {'user': 'user'}, '/rc/', 'http://user@vps1:8000/rc/group/repo1'),
    (Repository.DEFAULT_CLONE_URI, 'group/repo1', {'user': 'marcink'}, '/rc/', 'http://marcink@vps1:8000/rc/group/repo1'),
    ('{scheme}://{user}@{netloc}/_{repoid}', 'group/repo1', {}, '', 'http://vps1:8000/_23'),
    ('{scheme}://{user}@{netloc}/_{repoid}', 'group/repo1', {'user': 'marcink'}, '', 'http://marcink@vps1:8000/_23'),
    ('http://{user}@{netloc}/_{repoid}', 'group/repo1', {'user': 'marcink'}, '', 'http://marcink@vps1:8000/_23'),
    ('http://{netloc}/_{repoid}', 'group/repo1', {'user': 'marcink'}, '', 'http://vps1:8000/_23'),
    ('https://{user}@proxy1.server.com/{repo}', 'group/repo1', {'user': 'marcink'}, '', 'https://marcink@proxy1.server.com/group/repo1'),
    ('https://{user}@proxy1.server.com/{repo}', 'group/repo1', {}, '', 'https://proxy1.server.com/group/repo1'),
    ('https://proxy1.server.com/{user}/{repo}', 'group/repo1', {'user': 'marcink'}, '', 'https://proxy1.server.com/marcink/group/repo1'),
])
def test_clone_url_generator(tmpl, repo_name, overrides, prefix, expected):
    from rhodecode.lib.utils2 import get_clone_url

    class RequestStub(object):
        def request_url(self, name):
            return 'http://vps1:8000' + prefix

        def route_url(self, name):
            return self.request_url(name)

    clone_url = get_clone_url(
        request=RequestStub(),
        uri_tmpl=tmpl,
        repo_name=repo_name, repo_id=23, **overrides)
    assert clone_url == expected


def _quick_url(text, tmpl="""<a class="revision-link" href="%s">%s</a>""", url_=None):
    """
    Changes `some text url[foo]` => `some text <a href="/">foo</a>

    :param text:
    """
    import re
    # quickly change expected url[] into a link
    URL_PAT = re.compile(r'(?:url\[)(.+?)(?:\])')

    def url_func(match_obj):
        _url = match_obj.groups()[0]
        return tmpl % (url_ or '/some-url', _url)
    return URL_PAT.sub(url_func, text)


@pytest.mark.parametrize("sample, expected", [
  ("",
   ""),
  ("git-svn-id: https://svn.apache.org/repos/asf/libcloud/trunk@1441655 13f79535-47bb-0310-9956-ffa450edef68",
   "git-svn-id: https://svn.apache.org/repos/asf/libcloud/trunk@1441655 13f79535-47bb-0310-9956-ffa450edef68"),
  ("from rev 000000000000",
   "from rev url[000000000000]"),
  ("from rev 000000000000123123 also rev 000000000000",
   "from rev url[000000000000123123] also rev url[000000000000]"),
  ("this should-000 00",
   "this should-000 00"),
  ("longtextffffffffff rev 123123123123",
   "longtextffffffffff rev url[123123123123]"),
  ("rev ffffffffffffffffffffffffffffffffffffffffffffffffff",
   "rev ffffffffffffffffffffffffffffffffffffffffffffffffff"),
  ("ffffffffffff some text traalaa",
   "url[ffffffffffff] some text traalaa"),
   ("""Multi line
   123123123123
   some text 123123123123
   sometimes !
   """,
   """Multi line
   url[123123123123]
   some text url[123123123123]
   sometimes !
   """)
], ids=no_newline_id_generator)
def test_urlify_commits(sample, expected):
    def fake_url(self, *args, **kwargs):
        return '/some-url'

    expected = _quick_url(expected)

    with mock.patch('rhodecode.lib.helpers.route_url', fake_url):
        from rhodecode.lib.helpers import urlify_commits
        assert urlify_commits(sample, 'repo_name') == expected


@pytest.mark.parametrize("sample, expected, url_", [
    ("",
     "",
     ""),
    ("https://svn.apache.org/repos",
     "url[https://svn.apache.org/repos]",
     "https://svn.apache.org/repos"),
    ("http://svn.apache.org/repos",
     "url[http://svn.apache.org/repos]",
     "http://svn.apache.org/repos"),
    ("from rev a also rev http://google.com",
     "from rev a also rev url[http://google.com]",
     "http://google.com"),
    ("""Multi line
     https://foo.bar.com
     some text lalala""",
     """Multi line
     url[https://foo.bar.com]
     some text lalala""",
     "https://foo.bar.com")
], ids=no_newline_id_generator)
def test_urlify_test(sample, expected, url_):
    from rhodecode.lib.helpers import urlify_text
    expected = _quick_url(expected, tmpl="""<a href="%s">%s</a>""", url_=url_)
    assert urlify_text(sample) == expected


@pytest.mark.parametrize("test, expected", [
  ("", None),
  ("/_2", '2'),
  ("_2", '2'),
  ("/_2/", '2'),
  ("_2/", '2'),

  ("/_21", '21'),
  ("_21", '21'),
  ("/_21/", '21'),
  ("_21/", '21'),

  ("/_21/foobar", '21'),
  ("_21/121", '21'),
  ("/_21/_12", '21'),
  ("_21/rc/foo", '21'),

])
def test_get_repo_by_id(test, expected):
    from rhodecode.model.repo import RepoModel
    _test = RepoModel()._extract_id_from_repo_name(test)
    assert _test == expected


def test_invalidation_context(baseapp):
    repo_id = 999

    cache_namespace_uid = 'cache_repo_instance.{}_{}'.format(
        repo_id, CacheKey.CACHE_TYPE_README)
    invalidation_namespace = CacheKey.REPO_INVALIDATION_NAMESPACE.format(
        repo_id=repo_id)
    region = rc_cache.get_or_create_region('cache_repo_longterm', cache_namespace_uid)

    calls = [1, 2]

    @region.conditional_cache_on_arguments(namespace=cache_namespace_uid)
    def _dummy_func(cache_key):
        val = calls.pop(0)
        return 'result:{}'.format(val)

    inv_context_manager = rc_cache.InvalidationContext(
        uid=cache_namespace_uid, invalidation_namespace=invalidation_namespace)

    # 1st call, fresh caches
    with inv_context_manager as invalidation_context:
        should_invalidate = invalidation_context.should_invalidate()
        if should_invalidate:
            result = _dummy_func.refresh('some-key')
        else:
            result = _dummy_func('some-key')

        assert isinstance(invalidation_context, rc_cache.FreshRegionCache)
        assert should_invalidate is True

        assert 'result:1' == result
        # should be cached so calling it twice will give the same result !
        result = _dummy_func('some-key')
        assert 'result:1' == result

    # 2nd call, we create a new context manager, this should be now key aware, and
    # return an active cache region
    with inv_context_manager as invalidation_context:
        should_invalidate = invalidation_context.should_invalidate()
        assert isinstance(invalidation_context, rc_cache.ActiveRegionCache)
        assert should_invalidate is False

    # Mark invalidation
    CacheKey.set_invalidate(invalidation_namespace)

    # 3nd call, fresh caches
    with inv_context_manager as invalidation_context:
        should_invalidate = invalidation_context.should_invalidate()
        if should_invalidate:
            result = _dummy_func.refresh('some-key')
        else:
            result = _dummy_func('some-key')

        assert isinstance(invalidation_context, rc_cache.FreshRegionCache)
        assert should_invalidate is True

        assert 'result:2' == result

        # cached again, same result
        result = _dummy_func('some-key')
        assert 'result:2' == result


def test_invalidation_context_exception_in_compute(baseapp):
    repo_id = 888

    cache_namespace_uid = 'cache_repo_instance.{}_{}'.format(
        repo_id, CacheKey.CACHE_TYPE_README)
    invalidation_namespace = CacheKey.REPO_INVALIDATION_NAMESPACE.format(
        repo_id=repo_id)
    region = rc_cache.get_or_create_region('cache_repo_longterm', cache_namespace_uid)

    @region.conditional_cache_on_arguments(namespace=cache_namespace_uid)
    def _dummy_func(cache_key):
        raise Exception('Error in cache func')

    with pytest.raises(Exception):
        inv_context_manager = rc_cache.InvalidationContext(
            uid=cache_namespace_uid, invalidation_namespace=invalidation_namespace)

        # 1st call, fresh caches
        with inv_context_manager as invalidation_context:
            should_invalidate = invalidation_context.should_invalidate()
            if should_invalidate:
                _dummy_func.refresh('some-key-2')
            else:
                _dummy_func('some-key-2')


@pytest.mark.parametrize('execution_number', range(5))
def test_cache_invalidation_race_condition(execution_number, baseapp):
    import time

    repo_id = 777

    cache_namespace_uid = 'cache_repo_instance.{}_{}'.format(
        repo_id, CacheKey.CACHE_TYPE_README)
    invalidation_namespace = CacheKey.REPO_INVALIDATION_NAMESPACE.format(
        repo_id=repo_id)
    region = rc_cache.get_or_create_region('cache_repo_longterm', cache_namespace_uid)

    @run_test_concurrently(25)
    def test_create_and_delete_cache_keys():
        time.sleep(0.2)

        @region.conditional_cache_on_arguments(namespace=cache_namespace_uid)
        def _dummy_func(cache_key):
            val = 'async'
            return 'result:{}'.format(val)

        inv_context_manager = rc_cache.InvalidationContext(
            uid=cache_namespace_uid, invalidation_namespace=invalidation_namespace)

        # 1st call, fresh caches
        with inv_context_manager as invalidation_context:
            should_invalidate = invalidation_context.should_invalidate()
            if should_invalidate:
                _dummy_func.refresh('some-key-3')
            else:
                _dummy_func('some-key-3')

        # Mark invalidation
        CacheKey.set_invalidate(invalidation_namespace)

    test_create_and_delete_cache_keys()
