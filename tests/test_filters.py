# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from dmutils.filters import markdown_filter, smartjoin, format_links, timesince
from datetime import datetime, timedelta


def test_markdown_filter_produces_markup():

    markdown_string = """## H2 title

- List item 1
- List item 2

Paragraph
**Bold**
*Emphasis*

HTML is an abbreviation.

*[HTML]: Hyper Text Markup Language
"""

    html_string = """<h2>H2 title</h2>
<ul>
<li>List item 1</li>
<li>List item 2</li>
</ul>
<p>Paragraph
<strong>Bold</strong>
<em>Emphasis</em></p>
<p><abbr title="Hyper Text Markup Language">HTML</abbr> is an abbreviation.</p>"""

    assert markdown_filter(markdown_string) == html_string


def test_smartjoin_for_more_than_one_item():
    list_to_join = ['one', 'two', 'three', 'four']
    filtered_string = 'one, two, three and four'
    assert smartjoin(list_to_join) == filtered_string


def test_smartjoin_for_one_item():
    list_to_join = ['one']
    filtered_string = 'one'
    assert smartjoin(list_to_join) == filtered_string


def test_smartjoin_for_empty_list():
    list_to_join = []
    filtered_string = ''
    assert smartjoin(list_to_join) == filtered_string


def test_format_link():
    link = 'http://www.example.com'
    formatted_link = '<a href="http://www.example.com" class="break-link" rel="external">http://www.example.com</a>'
    assert format_links(link) == formatted_link


def test_format_link_without_protocol():
    link = 'www.example.com'
    formatted_link = '<span class="break-link">www.example.com</span>'
    assert format_links(link) == formatted_link


def test_format_link_with_text():
    text = 'This is the Greek Γ Δ Ε Ζ Η Θ Ι Κ Λ link: http://www.exΔmple.com'
    formatted_text = 'This is the Greek Γ Δ Ε Ζ Η Θ Ι Κ Λ link: <a href="http://www.exΔmple.com" class="break-link" rel="external">http://www.exΔmple.com</a>'  # noqa
    assert format_links(text) == formatted_text


def test_format_link_and_text_escapes_extra_html():
    text = 'This is the <strong>link</strong>: http://www.example.com'
    formatted_text = 'This is the &lt;strong&gt;link&lt;/strong&gt;: <a href="http://www.example.com" class="break-link" rel="external">http://www.example.com</a>'  # noqa
    assert format_links(text) == formatted_text


def test_format_link_does_not_die_horribly():
    text = 'This is the URL that made a previous regex die horribly' \
           'https://something&lt;span&gt;what&lt;/span&gt;something.com'
    formatted_text = 'This is the URL that made a previous regex die horribly' \
                     '<a href="https://something&amp;lt;span&amp;gt;what&amp;lt;/span&amp;gt;something.com" ' \
                     'class="break-link" rel="external">https://something&amp;lt;span&amp;gt;what&amp;lt;/span'\
                     '&amp;gt;something.com</a>'
    assert format_links(text) == formatted_text


def test_multiple_urls():
    text = 'This is the first link http://www.example.com and this is the second http://secondexample.com.'  # noqa
    formatted_text = 'This is the first link <a href="http://www.example.com" class="break-link" '\
        'rel="external">http://www.example.com</a> and this is the second '\
        '<a href="http://secondexample.com" class="break-link" rel="external">http://secondexample.com</a>.'
    assert format_links(text) == formatted_text


def test_no_links_no_change():
    text = 'There are no Greek Γ Δ Ε Ζ Η Θ Ι Κ Λ links.'
    assert format_links(text) == text


def test_timesince():
    now = datetime.utcnow()
    times = [
        now,

        now - timedelta(seconds=1),
        now - timedelta(seconds=2),

        now - timedelta(minutes=1),
        now - timedelta(minutes=2),

        now - timedelta(hours=1),
        now - timedelta(hours=2),

        now - timedelta(days=1),
        now - timedelta(days=2),

        now - timedelta(days=7),
        now - timedelta(days=14),

        now - timedelta(days=30),
        now - timedelta(days=60),

        now - timedelta(days=365),
        now - timedelta(days=365*2),
    ]

    texts = [
        'just now',

        '1 second ago',
        '2 seconds ago',

        '1 minute ago',
        '2 minutes ago',

        '1 hour ago',
        '2 hours ago',

        '1 day ago',
        '2 days ago',

        '1 week ago',
        '2 weeks ago',

        '1 month ago',
        '2 months ago',

        '1 year ago',
        '2 years ago',
    ]

    for i, time in enumerate(times):
        assert timesince(time, now) == texts[i]
