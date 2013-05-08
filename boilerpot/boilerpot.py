"""
 Copyright Curata, Inc c/o Jack Diederich

 General framework and constants take from "boilerpipe"
 http://code.google.com/p/boilerpipe/
 Copyright (c) 2009, 2010 Christian Kohlschutter

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

__version__ = '0.91'

import re
try:
    from bs4 import BeautifulSoup as BS, Tag, Comment
    bs_version = 4
except ImportError:
    from BeautifulSoup import BeautifulSoup as BS, Tag, Comment
    bs_version = 3

from . import cleaners

actions = {}
actions['a'] = 'anchor'
actions['body'] = 'body'
actions['br'] = 'NOP'
actions['div'] = 'id'
actions['title'] = 'title'
actions['p'] = 'paragraph'
ignorable = ['style', 'script', 'option', 'objects', 'embed', 'applet', 'link', 'abbr', 'acronym', 'noscript']
actions.update(dict.fromkeys(ignorable, 'ignore'))
inline = ['strike', 'u', 'b', 'i', 'em', 'strong', 'span', 'sup', 'code', 'tt',
          'sub', 'var', 'abbr', 'acronym', 'font', 'inline']
actions.update(dict.fromkeys(inline, 'inline'))
blocks = ['li', 'h1', 'h2', 'h3']
actions.update(dict.fromkeys(blocks, 'block'))

def apply_font(start, txt):
    if not txt:
        return start
    delta = re.match(('([+-]\d+)'), txt)
    absolute = re.match('(\d+)', txt)
    if txt == 'smaller':
        return start - 1
    elif txt == 'larger':
        return start + 1
    elif delta:
        try:
            return start + int(delta.group(1))
        except TypeError:
            pass
    elif absolute:
        try:
            return int(absolute.group(1))
        except TypeError:
            pass
    return start

def wc(text):
    return len(filter(None, re.split('\w+', text)))

class Text(object):
    def __init__(self, text='', depth=0, ignore=0, tags=[], ids=[]):
        self.text = cleaners.clean_html(text)
        self.depth = depth
        self.ignore = ignore
        self.tags = tags
        self.ids = ids
        self.labels = set()
        self.wordcount = 0
        self.linecount = 0
        self.link_density = 0
        self.word_density = 0
        self.recalc()

    def recalc(self):
        self.wordcount = wc(self.text)
        self.linecount = self.text.count('\n') + 1
        if self.wordcount:
            self.word_density = float(self.wordcount) / self.linecount
        if 'a' in self.tags:
            self.link_density = float(self.wordcount) / self.tags.count('a')  # not what initDesities() measures exactly

    def merge(self, other):
        self.text += ' ' + other.text
        self.labels |= other.labels
        self.recalc()

    @property
    def is_content(self):
        return 'content' in self.labels and 'ignore' not in self.labels

    def __len__(self):
        return len(self.text)

    def __repr__(self):
        return '<%s depth=%d ignore=%d tags=%r ids=%r labels=%r text=%r>' % (self.__class__.__name__, self.depth, self.ignore, self.tags, self.ids, self.labels, self.text)

def log(msg):
    #print msg
    return

class ParseState(object):
    def __init__(self):
        self.parts = []
        self.title = u''
        self.curr_text = u''
        self.curr_ids = []
        self.tags = []
        self.ignore_depth = 0
        self.anchor_depth = 0
        self.body_depth = 0
        self.font_sizes = [3]


    def flush(self, *labels):
        curr = self.curr_text.strip()
        if curr:
            self.parts.append(Text(self.curr_text, len(self.tags) + 1, self.ignore_depth, self.tags[:], self.curr_ids[:]))
            self.parts[-1].labels |= set(labels)
            log(self.parts[-1])
        self.curr_text = u''

    def tag_start(self, name, attr):
        log('%s START %s %r %r' % ('  ' * len(self.tags), name, self.tags, type(attr)))
        action = actions.get(name, None)
        self.tags.append(name)
        try:
            self.curr_ids.append(attr['id'])
        except KeyError:
            self.curr_ids.append('')
        if action == 'anchor':
            self.anchor_depth += 1
            assert self.anchor_depth == 1, "Anchor tags can't be nested"
        elif action == 'ignore':
            self.flush()
            self.ignore_depth += 1
        elif action == 'body':
            self.flush()
            self.body_depth += 1
        elif action == 'inline':
            self.curr_text = self.curr_text.strip(' ') + u' '
            if name == 'font':
                self.font_sizes.append(apply_font(self.font_sizes[-1], attr.get('size', None)))
        elif action == 'block':
            self.flush()
        elif action == 'paragraph':
            self.flush()
        elif action == 'title':
            self.flush()
        else:
            log('%s BAD %s %s' % ('  ' * len(self.tags), action, name))
            self.flush()
            return

    def characters(self, text):
        log('%s   TEXT %r' % ('  ' * len(self.tags), text))
        if text.strip().startswith('html PUBLIC'):  # hell no
            self.curr_text = u''
            return
        if self.tags[-1] in {'b', 'em', 'i', 'strong'}:
            if wc(text) > 5:
                self.flush()
                self.curr_text += unicode(text)
                self.flush('ignore', 'ignore_inline_' + self.tags[-1])
                return
        self.curr_text += unicode(text)

    def tag_end(self, name):
        log('%s END %s' % ('  ' * len(self.tags), name))
        action = actions.get(name, None)
        if action == 'anchor':
            self.anchor_depth -= 1
        elif action == 'ignore':
            self.flush()
            self.ignore_depth -= 1
        elif action == 'body':
            self.flush()
            self.body_depth -= 1
        elif action == 'inline':
            self.curr_text = self.curr_text.strip() + u' '
            if name == 'font':
                self.font_sizes.pop()
        elif action == 'block':
            self.flush(name, 'heading')
        elif action == 'paragraph':
            self.flush('maybe_content', 'maybe_content_paragraph')
        elif action == 'title':
            self.flush('title')
            self.title = title_cleaner(self.parts[-1].text)
        else:
            self.flush()
        assert name == self.tags.pop()
        self.curr_ids.pop()

    def __str__(self):
        return '<%s %d:%r>' % (self.__class__.__name__, len(self.parts), map(len, self.parts))
        #return '<%s %d:%r>' % (self.__class__.__name__, len(self.parts), [p.text for p in self.parts])

def descend(node, state):
    state.tag_start(node.name.lower(), node)
    for child in node.childGenerator():
        if isinstance(child, Tag):
            descend(child, state)
        elif not isinstance(child, Comment):
            state.characters(unicode(child))
    state.tag_end(node.name.lower())

def soup(html):
    if bs_version == 3:
        return BS(html, convertEntities='html')
    else:
        return BS(html)

def parse_html(html):
    html = cleaners.translate_microsoft(html)
    html = cleaners.translate_nurses(html)
    bs = soup(html)
    state = ParseState()
    descend(bs, state)
    return state

def merge_text_density(blocks):
    for prev, curr in zip([Text()] + blocks, blocks):
        if prev.wordcount and curr.wordcount and (prev.wordcount + curr.wordcount) > 30:
            # roughly similar word densities
            if 0.5 < (prev.word_density / curr.word_density) < 2.0:
                log("\tMerging! %r" %[(curr.is_content, prev.is_content, prev.word_density, curr.word_density)])
                curr.merge(prev)
                prev.labels.add('ignore')
                prev.labels.add('ignore_merge_text_density')
    return

def density_marker(blocks):
    for prev, curr, next in zip([Text()] + blocks, blocks, blocks[1:] + [Text()]):
        log("\nCM %r\n" % [((curr.link_density, curr.wordcount), (prev.link_density, prev.wordcount), (next.link_density, next.wordcount), curr.text)])
        if curr.link_density <= 0.333333:
            if prev.link_density <= 0.555556:
                if curr.word_density <= 9:
                    if next.word_density <= 10:
                        if prev.word_density <= 4:
                            use = False
                        else:
                            use = True
                    else:
                        use = True
                else:
                    if next.word_density:
                        use = True
                    else:
                        use = False
        else:
            use = False
        if use:
            #print "\tIMMA", (use, '%4.2f' % curr.word_density, curr)
            curr.labels.add('content')
            curr.labels.add('content_density_marker')

def li_tags_are_content(blocks):
    tagcount = 999
    for block in blocks:
        if block.is_content and 'likely_content' in block.labels:
            tagcount = len(block.tags)
        elif len(block.tags) > tagcount and 'maybe_content' in block.labels and \
           'li' in block.labels and block.link_density == 0:
            if not block.is_content:
                block.labels.discard('ignore')
                block.labels.add('!ignore_li_tags_are_content')
                block.labels.add('content')
            block.labels.add('content_li_tags_are_content')
        else:
            tagcount = 999

def content_by_taglevel(blocks, minwords=100):
    for block in blocks:
        if 'likely_content' in block.labels:
            main = block
            break
    else:
        return
    for block in blocks:
        if not block.is_content and len(block.tags) == len(main.tags) and block.wordcount >= minwords:
            if not block.is_content:
                block.labels.discard('ignore')
                block.labels.add('!ignore_content_by_taglevel')
                block.labels.add('content')
            block.labels.add('content_content_by_taglevel')

def title_starts_content(blocks):
    it = iter(blocks)
    for block in it:
        if 'title' in block.labels and block.is_content:
            break
    for block in it:
        if 'maybe_conent' in block.labels or 'likely_content' in block.labels:
            if not block.is_content:
                block.labels.discard('ignore')
                block.labels.add('!ignore_title_start_content')
                block.labels.add('content')
            block.labels.add('content_title_start_content')

def largest_block(blocks, expand_same_level=True, minwords=150):
    best = (0, -1)
    for i, block in enumerate(blocks):
        if block.is_content or 'maybe_content' in block.labels:
            if block.wordcount > minwords:
                best = max(best, (block.wordcount, i))
    longest, i = best
    if not longest:
        return
    main = blocks[i]
    main.labels.add('likely_content')
    for block in blocks:
        block.labels.add('maybe_content')
        block.labels.add('maybe_content_largest_block')

    # run to the left and right of best marking adjacent tags as content
    for adjacents in [reversed(blocks[:i]), blocks[i+1:]]:
        for adj in adjacents:
            if len(adj.tags) < len(main.tags):
                break
            elif len(adj.tags) == len(main.tags):
                if not block.is_content:
                    adj.labels.discard('ignore')
                    adj.labels.add('!ignore_largest_block')
                    adj.labels.add('content')
                adj.labels.add('content_largest_block')

def merge_blocks(blocks, content_only=False, same_depth_only=False):
    # we dropped the 'block distance' metric - they just use adjacents
    it = iter(blocks)
    try:
        prev = Text()
        curr = next(it)
        log('\n\t--START MERGE--\n')
        while True:
            log(prev)
            log(curr)
            if not curr.is_content or \
               (content_only and (not curr.is_content or not prev.is_content)) or \
               (same_depth_only and len(curr.tags) != len(prev.tags)):
                log("NOTerging %r" %[(curr.is_content, prev.is_content, len(curr.tags), len(prev.tags))])
                prev = curr
                curr = next(it)
                continue
            else:
                log("\tMerging! %r" %[(curr.is_content, prev.is_content, len(curr.tags), len(prev.tags))])
                # the original doesn't care if prev is not content
                prev.merge(curr)
                curr.labels.add('ignore')
                curr.labels.add('ignore_merge_blocks')
                curr = next(it)
                # prev is NOT advanced
    except StopIteration:  # haters gonna hate
        pass

def ignore_trailing_headlines(blocks):
    for prev, curr in zip([Text()] + blocks, blocks):
        if prev.is_content:
            if 'heading' in curr.labels:
                curr.labels.add('ignore')
                curr.labels.add('ignore_trailing_headlines')
            else:
                break
    return

def ignore_after_content(blocks, minwords=60):
    wordcount = 0
    it = iter(blocks)
    for block in it:
        if block.is_content:
            wordcount += block.wordcount
        if 'end_of_text' in block.labels and wordcount > minwords:
            break
    for block in it:
        block.labels.add('ignore')
        block.labels.add('ignore_after_content')
    return

def ignore_comments(blocks):
    """ lone text pieces seen in the wild
          u'Sign in'
          u'Forgot your password?'
          u'Create AccountSign In'  #youtube
    """
    for block in blocks:
        if block.text.lower().startswith((u'sign in', u'Forgot your password?',
                                          u'Create AccountSign In', u'You are using an outdated browser')):
            block.labels.add('ignore')
            block.labels.add('ignore_ignore_comments')
    return

def content_marker(blocks):
    for prev, curr, next in zip([Text()] + blocks, blocks, blocks[1:] + [Text()]):
        log("\nCM %r\n" % [((curr.link_density, curr.wordcount), (prev.link_density, prev.wordcount), (next.link_density, next.wordcount), curr.text)])
        if curr.link_density > 0.333333:
            continue
        if prev.link_density <= 0.555556:
            if curr.wordcount > 16 and next.wordcount > 15 and prev.wordcount > 4:
                curr.labels.add('content_content_marker1')
                curr.labels.add('content')
            elif prev.is_content and curr.wordcount > 20 and next.wordcount > 7:
                curr.labels.add('maybe_content')
                curr.labels.add('maybe_content_content_marker')
        elif curr.wordcount > 40 and next.wordcount > 17:
            curr.labels.add('content')
            curr.labels.add('content_content_marker2')
        elif curr.wordcount > 100 and 'maybe_content' in curr.labels:
            curr.labels.add('content')
            curr.labels.add('content_content_marker3')
    return

def terminating_blocks(blocks):
    copyright = chr(169)
    for block in blocks:
        text = block.text
        if block.wordcount < 15 and len(text) >= 8:
            if re.match('\d+\s+(comments|users responded in', text, re.IGNORE_CASE) or \
               text.lower().startswith(('comments', copyright + ' reuters', 'please rate this',
                                        'post a comment', 'what you think', 'add your comment',
                                        'add comment', 'reader views', 'have your say',
                                        'reader comments', 'r\xe4tta artikeln',
                                        'thanks for your comments - this feedback is now closed')):
               block.labels.add('end_of_text')
        elif (0.99 < block.link_density < 1.01 and text.lower().startswith('comment')):
            block.labels.add('end_of_text')
    return

def title_cleaner(title):
    splitter = "\s*[\xbb|,:()\-\xa0]+\s*"
    best = sorted(re.split(splitter, title), key=len)[-1]  # longest
    best = best.replace("'", "", 1)
    return best

def simple_filter(html):
    page = parse_html(html)
    blocks = page.parts
    blocks = [block for block in blocks if not block.ignore]
    merge_text_density(blocks)
    merge_blocks(blocks)
    density_marker(blocks)
    page.good = [block for block in blocks if block.is_content]
    largest_block(blocks)
    page.good = [block for block in blocks if block.is_content]
    return page

def article_filter(html):
    page = parse_html(html)
    blocks = page.parts
    log(len(blocks))
    blocks = [block for block in blocks if not block.ignore]
    log(len(blocks))
    content_marker(blocks)
    ignore_after_content(blocks)
    ignore_trailing_headlines(blocks)
    merge_blocks(blocks)
    blocks = [block for block in blocks if block.is_content]
    log(len(blocks))
    merge_blocks(blocks, content_only=True, same_depth_only=True)
    largest_block(blocks)
    title_starts_content(blocks)
    content_by_taglevel(blocks)
    li_tags_are_content(blocks)
    page.good = [block for block in blocks if block.is_content]
    return page

def clean_body(body, title):
    body = body.strip()
    if body and title:
        newbody = cleaners.strip_words(body, title)
        if newbody != body:
            body = cleaners.strip_partial_sentence(body)
    if body:
        newbody = cleaners.strip_timestamp(body)
        if newbody != body:
            body = cleaners.strip_partial_sentence(newbody)

    return body

def meat(html):
    page = article_filter(html)
    blocks = sorted(page.good, key=lambda x:x.wordcount, reverse=True)
    title = page.title
    for p in blocks:
        if 'likely_content' in p.labels:
            best = p.text
            break
    else:
        for p in page.good:
            if 'maybe_content' in p.labels:
                best = p.text
                break
        else:
            return title, u''
    best = clean_body(best, title)
    return title, best

def meat2(html):
    page = simple_filter(html)
    title = page.title
    blocks = sorted(page.good, key=lambda x:x.wordcount)
    if not blocks:
        return title, u''
    best = blocks[-1].text
    best = clean_body(best, title)
    return title, best

def extract_text(html):
    """ take the HTML and attempt to return plain text (minus headers/footers/navigation/etc) """
    for func in [meat, meat2]:
        title, body = func(html)
        if title and body:
            return title, body
    return '', ''

x = u'''
make a rule to mark these down.
INDIANAPOLIS (WISH) - The Clearwater area

This page is problematic, the interstitial headers mess things up.
http://news.pba.com/post/2012/12/20/PBA-Spare-Shots-Barnes-Home-for-Holidays-After-Successful-Gall-Bladder-Removal-Surgery.aspx

use NER or nltk to find what are real sentances (noun verb noun)

* titles are coming out lowercase

Why didn't this trim?
(u'Lets Go Bowling!! ', u"Let's Go Bowling!! \n Tis' the Season to be&nbsp;jolly&nbsp;as the 2012 NCAA")
'''

if __name__ == '__main__':
    print extract_text(open('sample.html').read())
