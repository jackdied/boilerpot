"""
 Copyright Curata, Inc c/o Jack Diederich

 The author licenses this file to You under the Apache License, Version 2.0
 (the "License"); you may not use this file except in compliance with
 the License.  You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""
import functools
import re

try:
    from nltk.metrics.distance import edit_distance
except ImportError:
    # nltk not installed, punt
    def edit_distance(a, b):
        return len(set(a) ^ set(b)) + abs(len(a) - len(b))

def translate_microsoft(txt):
    """ turn word document ungliness into ascii """
    # double quotes
    txt = txt.replace(u"\u201c", '"')
    txt = txt.replace(u"\u201d", '"')
    # signle quotes
    txt = txt.replace(u"\u2018", "'")
    txt = txt.replace(u"\u2019", "'")
    txt = txt.replace(u"\u02BC", "'")
    # invisible spaces.  So nothings - nothings that take up space.
    txt = txt.replace(u"\u2063", " ")
    # these are ... and then the guy farted, right in front of the priest!
    txt = txt.replace(u"\u2026", "...")
    # bullets
    txt = txt.replace(u"\u2022", "-")
    txt = txt.replace(u"\u25cf", "-")
    # longdash
    txt = txt.replace(u"\u2012", "-")
    txt = txt.replace(u"\u2013", "-")
    txt = txt.replace(u"\u2014", "-")
    txt = txt.replace(u"\u2015", "-")
    txt = txt.replace(u"\u2053", "-")
    txt = txt.replace(u"\u2E3A", "-")
    txt = txt.replace(u"\u2E3B", "-")
    # a space is a space
    txt = txt.replace(u"\u2025", ' ')
    txt = txt.replace(u"\xa0", ' ')
    return txt

entities = {'nbsp': ' ',
            'mdash': '-',
            'quot': "'",
            'lsquo': "'",
            'rsquo': "'",
            'ldquo': '"',
            'rdquo': '"',
           }

def translate_html_entities(html):
    parts = []
    curr = 0
    for m in re.finditer('&#([xX]?)([0-9a-fA-F]+);', html):
        parts.append(html[curr:m.start()])
        ishex, number = m.groups()
        value = unichr(int(number, base=(16 if (ishex) else 10)))
        parts.append(value)
        curr = m.end()
    parts.append(html[curr:])
    html = ''.join(parts)
    for code, translation in entities.items():
        html = html.replace('&%s;' % code, translation)
    return html

def translate_nurses(txt):
    txt = txt.replace('\r\n', '\n')
    txt = txt.replace('\r', '\n')
    return txt

def translate_whitespace(txt):
    txt = txt.replace('\t', ' ')
    txt = re.sub(' +', ' ', txt)
    txt = txt.replace(' \n', '\n')
    txt = txt.replace('\n ', '\n')
    txt = re.sub(' +', ' ', txt)
    txt = txt.replace('\n\n', '\n')
    return txt

def clean_html(html):
    return translate_whitespace(translate_microsoft(translate_html_entities(html)))

def strip_letters(raw, letters):
    """ this looks questionable. """
    iraw = 0
    ilets = 0
    while letters[ilets:] and raw[iraw:]:
        if raw[iraw].lower() == letters[ilets].lower():
            ilets += 1
        iraw += 1
    return raw[iraw:]

def strip_words(text, strip_this):
    """ if text starts with something that looks like stip_this then strip it """
    letters = functools.partial(re.sub, '[^a-z]+', '')
    ltext = letters(text.lower())
    lstrip = letters(strip_this.lower())

    best = (4, 0, '')
    for i in range(1, 1 + min(50, len(ltext), len(lstrip))):
        a, b = ltext[:i], lstrip[:i]
        score = (float(edit_distance(a, b)) / len(b), -len(b), b)
        if score < best:
            best = score
    density, length, letters = best
    if best[0] > 0.1 or abs(length) < min(len(lstrip), 10):
        return text
    return strip_letters(text, letters).lstrip(' .?;:()-\t\n')

def strip_partial_sentence(text):
    return re.sub('^[^.?]{0,10}(\.|\?)\s*', '', text)

def strip_timestamp(text):
    """ try to remove things that look like dates at the start of text """
    # u"Published Thursday, Dec. 20, 2012 7:00AM EST With the so-called Mayan"
    # u'Garden City, NY (PRWEB) December 18, 2012 This weekend Bob Smith'
    best = 0
    regexps = ['(\d{1,2}\D+20\d\d)',
               '(\d{1,2}(:\d\d)+\s*(AM|PM|a\.m\.|p\.m\.)?\s*(ET|EST|EDT|PT|PST|PDT|CT|CST|CDT)?)',
               '(\d{1,2}(:\d\d)*\s*(AM|PM|A\.M\.|P\.M\.)?\s*(ET|EST|EDT|PT|PST|PDT|CT|CST|CDT))',
              ]
    for pattern, m in [(pattern, re.search(pattern, text[:50], re.IGNORECASE)) for pattern in regexps]:
        if m:
            best = max(best, m.end())
    return text[best:].strip()

