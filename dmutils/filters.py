from __future__ import unicode_literals
import re
from markdown import markdown
from flask import Markup
from jinja2 import evalcontextfilter, escape
import pendulum


def markdown_filter(text, *args, **kwargs):
    return markdown(text, ['markdown.extensions.abbr'], *args, **kwargs)


def smartjoin(input):
    list_to_join = list(input)
    if len(list_to_join) > 1:
        return '{} and {}'.format(', '.join(list_to_join[:-1]), list_to_join[-1])
    elif len(list_to_join) == 1:
        return '{}'.format(list_to_join[0])
    else:
        return ''


def format_links(text):
    url_match = re.compile(r"""(
                                (?:https?://|www\.)    # start with http:// or www.
                                (?:[^\s<>"'/?#]+)      # domain doesn't have these characters
                                (?:[^\s<>"']+)         # post-domain part of URL doesn't have these characters
                                [^\s<>,"'\.]           # no dot at end
                                )""", re.X)
    matched_urls = url_match.findall(text)
    if matched_urls:
        link = '<a href="{0}" class="break-link" rel="external">{0}</a>'
        plaintext_link = '<span class="break-link">{0}</span>'
        text_array = url_match.split(text)
        formatted_text_array = []
        for partial_text in text_array:
            if partial_text in matched_urls:
                if partial_text.startswith('www'):
                    url = plaintext_link.format(Markup.escape(partial_text))
                else:
                    url = link.format(Markup.escape(partial_text))
                formatted_text_array.append(url)
            else:
                partial_text = Markup.escape(partial_text)
                formatted_text_array.append(partial_text)
        formatted_text = Markup(''.join(formatted_text_array))
        return formatted_text
    else:
        return text


def timesince(before, now=None, default="just now"):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    """

    before = pendulum.instance(before)

    if now:
        now = pendulum.instance(now)
    else:
        now = pendulum.now('UTC')

    if now == before:
        return default

    with pendulum.test(now):
        return before.diff_for_humans()

    return default


@evalcontextfilter
def nl2br(eval_ctx, value):
    # http://jinja.pocoo.org/docs/2.9/api/#custom-filters
    value = value.strip()
    _paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')
    result = u'\n'.join(u'<p>%s</p>' % p.strip().replace('\n', Markup('<br>\n') if p.strip() != '' else '')
                        for p in _paragraph_re.split(escape(value)))
    if eval_ctx and eval_ctx.autoescape:
        result = Markup(result)
    return result
