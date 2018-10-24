# -*- coding: utf-8 -*-

# Copyright (C) 2011-2018 RhodeCode GmbH
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
Renderer for markup languages with ability to parse using rst or markdown
"""

import re
import os
import lxml
import logging
import urlparse
import bleach

from mako.lookup import TemplateLookup
from mako.template import Template as MakoTemplate

from docutils.core import publish_parts
from docutils.parsers.rst import directives
from docutils import writers
from docutils.writers import html4css1
import markdown

from rhodecode.lib.markdown_ext import GithubFlavoredMarkdownExtension
from rhodecode.lib.utils2 import (
    safe_str, safe_unicode, md5_safe, MENTIONS_REGEX)

log = logging.getLogger(__name__)

# default renderer used to generate automated comments
DEFAULT_COMMENTS_RENDERER = 'rst'


class CustomHTMLTranslator(writers.html4css1.HTMLTranslator):
    """
    Custom HTML Translator used for sandboxing potential
    JS injections in ref links
    """

    def visit_reference(self, node):
        if 'refuri' in node.attributes:
            refuri = node['refuri']
            if ':' in refuri:
                prefix, link = refuri.lstrip().split(':', 1)
                prefix = prefix or ''

                if prefix.lower() == 'javascript':
                    # we don't allow javascript type of refs...
                    node['refuri'] = 'javascript:alert("SandBoxedJavascript")'

        # old style class requires this...
        return html4css1.HTMLTranslator.visit_reference(self, node)


class RhodeCodeWriter(writers.html4css1.Writer):
    def __init__(self):
        writers.Writer.__init__(self)
        self.translator_class = CustomHTMLTranslator


def relative_links(html_source, server_paths):
    if not html_source:
        return html_source

    try:
        from lxml.html import fromstring
        from lxml.html import tostring
    except ImportError:
        log.exception('Failed to import lxml')
        return html_source

    try:
        doc = lxml.html.fromstring(html_source)
    except Exception:
        return html_source

    for el in doc.cssselect('img, video'):
        src = el.attrib.get('src')
        if src:
            el.attrib['src'] = relative_path(src, server_paths['raw'])

    for el in doc.cssselect('a:not(.gfm)'):
        src = el.attrib.get('href')
        if src:
            raw_mode = el.attrib['href'].endswith('?raw=1')
            if raw_mode:
                el.attrib['href'] = relative_path(src, server_paths['raw'])
            else:
                el.attrib['href'] = relative_path(src, server_paths['standard'])

    return lxml.html.tostring(doc)


def relative_path(path, request_path, is_repo_file=None):
    """
    relative link support, path is a rel path, and request_path is current
    server path (not absolute)

    e.g.

    path = '../logo.png'
    request_path= '/repo/files/path/file.md'
    produces: '/repo/files/logo.png'
    """
    # TODO(marcink): unicode/str support ?
    # maybe=> safe_unicode(urllib.quote(safe_str(final_path), '/:'))

    def dummy_check(p):
        return True  # assume default is a valid file path

    is_repo_file = is_repo_file or dummy_check
    if not path:
        return request_path

    path = safe_unicode(path)
    request_path = safe_unicode(request_path)

    if path.startswith((u'data:', u'javascript:', u'#', u':')):
        # skip data, anchor, invalid links
        return path

    is_absolute = bool(urlparse.urlparse(path).netloc)
    if is_absolute:
        return path

    if not request_path:
        return path

    if path.startswith(u'/'):
        path = path[1:]

    if path.startswith(u'./'):
        path = path[2:]

    parts = request_path.split('/')
    # compute how deep we need to traverse the request_path
    depth = 0

    if is_repo_file(request_path):
        # if request path is a VALID file, we use a relative path with
        # one level up
        depth += 1

    while path.startswith(u'../'):
        depth += 1
        path = path[3:]

    if depth > 0:
        parts = parts[:-depth]

    parts.append(path)
    final_path = u'/'.join(parts).lstrip(u'/')

    return u'/' + final_path


class MarkupRenderer(object):
    RESTRUCTUREDTEXT_DISALLOWED_DIRECTIVES = ['include', 'meta', 'raw']

    MARKDOWN_PAT = re.compile(r'\.(md|mkdn?|mdown|markdown)$', re.IGNORECASE)
    RST_PAT = re.compile(r'\.re?st$', re.IGNORECASE)
    JUPYTER_PAT = re.compile(r'\.(ipynb)$', re.IGNORECASE)
    PLAIN_PAT = re.compile(r'^readme$', re.IGNORECASE)

    URL_PAT = re.compile(r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]'
                         r'|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)')

    extensions = ['codehilite', 'extra', 'def_list', 'sane_lists']
    output_format = 'html4'
    markdown_renderer = markdown.Markdown(
        extensions, enable_attributes=False, output_format=output_format)

    markdown_renderer_flavored = markdown.Markdown(
        extensions + [GithubFlavoredMarkdownExtension()],
        enable_attributes=False, output_format=output_format)

    # extension together with weights. Lower is first means we control how
    # extensions are attached to readme names with those.
    PLAIN_EXTS = [
        # prefer no extension
        ('', 0),  # special case that renders READMES names without extension
        ('.text', 2), ('.TEXT', 2),
        ('.txt', 3), ('.TXT', 3)
    ]

    RST_EXTS = [
        ('.rst', 1), ('.rest', 1),
        ('.RST', 2), ('.REST', 2)
    ]

    MARKDOWN_EXTS = [
        ('.md', 1), ('.MD', 1),
        ('.mkdn', 2), ('.MKDN', 2),
        ('.mdown', 3), ('.MDOWN', 3),
        ('.markdown', 4), ('.MARKDOWN', 4)
    ]

    def _detect_renderer(self, source, filename=None):
        """
        runs detection of what renderer should be used for generating html
        from a markup language

        filename can be also explicitly a renderer name

        :param source:
        :param filename:
        """

        if MarkupRenderer.MARKDOWN_PAT.findall(filename):
            detected_renderer = 'markdown'
        elif MarkupRenderer.RST_PAT.findall(filename):
            detected_renderer = 'rst'
        elif MarkupRenderer.JUPYTER_PAT.findall(filename):
            detected_renderer = 'jupyter'
        elif MarkupRenderer.PLAIN_PAT.findall(filename):
            detected_renderer = 'plain'
        else:
            detected_renderer = 'plain'

        return getattr(MarkupRenderer, detected_renderer)

    @classmethod
    def bleach_clean(cls, text):
        from .bleach_whitelist import markdown_attrs, markdown_tags
        allowed_tags = markdown_tags
        allowed_attrs = markdown_attrs

        try:
            return bleach.clean(text, tags=allowed_tags, attributes=allowed_attrs)
        except Exception:
            return 'UNPARSEABLE TEXT'

    @classmethod
    def renderer_from_filename(cls, filename, exclude):
        """
        Detect renderer markdown/rst from filename and optionally use exclude
        list to remove some options. This is mostly used in helpers.
        Returns None when no renderer can be detected.
        """
        def _filter(elements):
            if isinstance(exclude, (list, tuple)):
                return [x for x in elements if x not in exclude]
            return elements

        if filename.endswith(
                tuple(_filter([x[0] for x in cls.MARKDOWN_EXTS if x[0]]))):
            return 'markdown'
        if filename.endswith(tuple(_filter([x[0] for x in cls.RST_EXTS if x[0]]))):
            return 'rst'

        return None

    def render(self, source, filename=None):
        """
        Renders a given filename using detected renderer
        it detects renderers based on file extension or mimetype.
        At last it will just do a simple html replacing new lines with <br/>

        :param file_name:
        :param source:
        """

        renderer = self._detect_renderer(source, filename)
        readme_data = renderer(source)
        return readme_data

    @classmethod
    def _flavored_markdown(cls, text):
        """
        Github style flavored markdown

        :param text:
        """

        # Extract pre blocks.
        extractions = {}

        def pre_extraction_callback(matchobj):
            digest = md5_safe(matchobj.group(0))
            extractions[digest] = matchobj.group(0)
            return "{gfm-extraction-%s}" % digest
        pattern = re.compile(r'<pre>.*?</pre>', re.MULTILINE | re.DOTALL)
        text = re.sub(pattern, pre_extraction_callback, text)

        # Prevent foo_bar_baz from ending up with an italic word in the middle.
        def italic_callback(matchobj):
            s = matchobj.group(0)
            if list(s).count('_') >= 2:
                return s.replace('_', r'\_')
            return s
        text = re.sub(r'^(?! {4}|\t)\w+_\w+_\w[\w_]*', italic_callback, text)

        # Insert pre block extractions.
        def pre_insert_callback(matchobj):
            return '\n\n' + extractions[matchobj.group(1)]
        text = re.sub(r'\{gfm-extraction-([0-9a-f]{32})\}',
                      pre_insert_callback, text)

        return text

    @classmethod
    def urlify_text(cls, text):
        def url_func(match_obj):
            url_full = match_obj.groups()[0]
            return '<a href="%(url)s">%(url)s</a>' % ({'url': url_full})

        return cls.URL_PAT.sub(url_func, text)

    @classmethod
    def plain(cls, source, universal_newline=True, leading_newline=True):
        source = safe_unicode(source)
        if universal_newline:
            newline = '\n'
            source = newline.join(source.splitlines())

        rendered_source = cls.urlify_text(source)
        source = ''
        if leading_newline:
            source += '<br />'
        source += rendered_source.replace("\n", '<br />')
        return source

    @classmethod
    def markdown(cls, source, safe=True, flavored=True, mentions=False,
                 clean_html=True):
        """
        returns markdown rendered code cleaned by the bleach library
        """

        if flavored:
            markdown_renderer = cls.markdown_renderer_flavored
        else:
            markdown_renderer = cls.markdown_renderer

        if mentions:
            mention_pat = re.compile(MENTIONS_REGEX)

            def wrapp(match_obj):
                uname = match_obj.groups()[0]
                return ' **@%(uname)s** ' % {'uname': uname}
            mention_hl = mention_pat.sub(wrapp, source).strip()
            # we extracted mentions render with this using Mentions false
            return cls.markdown(mention_hl, safe=safe, flavored=flavored,
                                mentions=False)

        source = safe_unicode(source)

        try:
            if flavored:
                source = cls._flavored_markdown(source)
            rendered = markdown_renderer.convert(source)
        except Exception:
            log.exception('Error when rendering Markdown')
            if safe:
                log.debug('Fallback to render in plain mode')
                rendered = cls.plain(source)
            else:
                raise

        if clean_html:
            rendered = cls.bleach_clean(rendered)
        return rendered

    @classmethod
    def rst(cls, source, safe=True, mentions=False, clean_html=False):
        if mentions:
            mention_pat = re.compile(MENTIONS_REGEX)

            def wrapp(match_obj):
                uname = match_obj.groups()[0]
                return ' **@%(uname)s** ' % {'uname': uname}
            mention_hl = mention_pat.sub(wrapp, source).strip()
            # we extracted mentions render with this using Mentions false
            return cls.rst(mention_hl, safe=safe, mentions=False)

        source = safe_unicode(source)
        try:
            docutils_settings = dict(
                [(alias, None) for alias in
                 cls.RESTRUCTUREDTEXT_DISALLOWED_DIRECTIVES])

            docutils_settings.update({
                'input_encoding': 'unicode', 'report_level': 4})

            for k, v in docutils_settings.iteritems():
                directives.register_directive(k, v)

            parts = publish_parts(source=source,
                                  writer=RhodeCodeWriter(),
                                  settings_overrides=docutils_settings)
            rendered = parts["fragment"]
            if clean_html:
                rendered = cls.bleach_clean(rendered)
            return parts['html_title'] + rendered
        except Exception:
            log.exception('Error when rendering RST')
            if safe:
                log.debug('Fallbacking to render in plain mode')
                return cls.plain(source)
            else:
                raise

    @classmethod
    def jupyter(cls, source, safe=True):
        from rhodecode.lib import helpers

        from traitlets.config import Config
        import nbformat
        from nbconvert import HTMLExporter
        from nbconvert.preprocessors import Preprocessor

        class CustomHTMLExporter(HTMLExporter):
            def _template_file_default(self):
                return 'basic'

        class Sandbox(Preprocessor):

            def preprocess(self, nb, resources):
                sandbox_text = 'SandBoxed(IPython.core.display.Javascript object)'
                for cell in nb['cells']:
                    if safe and 'outputs' in cell:
                        for cell_output in cell['outputs']:
                            if 'data' in cell_output:
                                if 'application/javascript' in cell_output['data']:
                                    cell_output['data']['text/plain'] = sandbox_text
                                    cell_output['data'].pop('application/javascript', None)
                return nb, resources

        def _sanitize_resources(resources):
            """
            Skip/sanitize some of the CSS generated and included in jupyter
            so it doesn't messes up UI so much
            """

            # TODO(marcink): probably we should replace this with whole custom
            # CSS set that doesn't screw up, but jupyter generated html has some
            # special markers, so it requires Custom HTML exporter template with
            # _default_template_path_default, to achieve that

            # strip the reset CSS
            resources[0] = resources[0][resources[0].find('/*! Source'):]
            return resources

        def as_html(notebook):
            conf = Config()
            conf.CustomHTMLExporter.preprocessors = [Sandbox]
            html_exporter = CustomHTMLExporter(config=conf)

            (body, resources) = html_exporter.from_notebook_node(notebook)
            header = '<!-- ## IPYTHON NOTEBOOK RENDERING ## -->'
            js = MakoTemplate(r'''
            <!-- Load mathjax -->
                <!-- MathJax configuration -->
                <script type="text/x-mathjax-config">
                MathJax.Hub.Config({
                    jax: ["input/TeX","output/HTML-CSS", "output/PreviewHTML"],
                    extensions: ["tex2jax.js","MathMenu.js","MathZoom.js", "fast-preview.js", "AssistiveMML.js", "[Contrib]/a11y/accessibility-menu.js"],
                    TeX: {
                        extensions: ["AMSmath.js","AMSsymbols.js","noErrors.js","noUndefined.js"]
                    },
                    tex2jax: {
                        inlineMath: [ ['$','$'], ["\\(","\\)"] ],
                        displayMath: [ ['$$','$$'], ["\\[","\\]"] ],
                        processEscapes: true,
                        processEnvironments: true
                    },
                    // Center justify equations in code and markdown cells. Elsewhere
                    // we use CSS to left justify single line equations in code cells.
                    displayAlign: 'center',
                    "HTML-CSS": {
                        styles: {'.MathJax_Display': {"margin": 0}},
                        linebreaks: { automatic: true },
                        availableFonts: ["STIX", "TeX"]
                    },
                    showMathMenu: false
                });
                </script>
                <!-- End of mathjax configuration -->
                <script src="${h.asset('js/src/math_jax/MathJax.js')}"></script>
            ''').render(h=helpers)

            css = '<style>{}</style>'.format(
                ''.join(_sanitize_resources(resources['inlining']['css'])))

            body = '\n'.join([header, css, js, body])
            return body, resources

        notebook = nbformat.reads(source, as_version=4)
        (body, resources) = as_html(notebook)
        return body


class RstTemplateRenderer(object):

    def __init__(self):
        base = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        rst_template_dirs = [os.path.join(base, 'templates', 'rst_templates')]
        self.template_store = TemplateLookup(
            directories=rst_template_dirs,
            input_encoding='utf-8',
            imports=['from rhodecode.lib import helpers as h'])

    def _get_template(self, templatename):
        return self.template_store.get_template(templatename)

    def render(self, template_name, **kwargs):
        template = self._get_template(template_name)
        return template.render(**kwargs)
