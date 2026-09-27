"""Split agent regions into Markdown block units with source line ranges."""

from difflib import SequenceMatcher

from markdown_it import MarkdownIt

from doc_regions.regions import scan


KINDS = {
    'heading_open': 'heading',
    'paragraph_open': 'paragraph',
    'table_open': 'table',
    'fence': 'code',
    'code_block': 'code',
    'html_block': 'html',
    'blockquote_open': 'blockquote',
}


def split(document, text, base_text=None):
    lines = text.splitlines(keepends=True)
    spans, problems = scan(document, text)
    if problems:
        raise ValueError('\n'.join(
            f"{item['document']}:{item['line']}: {item['message']}" for item in problems))
    mechanical = {line for span in spans for line in range(span['start'], span['end'])}
    masked = ''.join('\n' if index in mechanical else line for index, line in enumerate(lines))
    tokens = MarkdownIt('commonmark').enable('table').parse(masked)
    added = set()
    if base_text is not None:
        for tag, _, _, first, end in SequenceMatcher(
                None, base_text.splitlines(keepends=True), lines, autojunk=False).get_opcodes():
            if tag in ('insert', 'replace'):
                added.update(range(first, end))

    headings, units = [], []
    for index, token in enumerate(tokens):
        kind = KINDS.get(token.type) if token.level == 0 else None
        if token.type == 'list_item_open' and token.level == 1:
            kind = 'list_item'
        if kind is None or token.map is None:
            continue
        if kind == 'heading':
            level = int(token.tag[1:])
            headings = [(depth, title) for depth, title in headings if depth < level]
        heading_path = [title for _, title in headings]
        if kind == 'heading':
            headings.append((level, tokens[index + 1].content))

        first, end = token.map
        cursor = first
        while cursor < end:
            if cursor in mechanical:
                cursor += 1
                continue
            stop = cursor + 1
            while stop < end and stop not in mechanical:
                stop += 1
            if any(line.strip() for line in lines[cursor:stop]):
                units.append(dict(
                    id=f'{document}:{cursor + 1}-{stop}',
                    document=document,
                    heading_path=heading_path,
                    kind=kind,
                    first_line=cursor + 1,
                    last_line=stop,
                    text=''.join(lines[cursor:stop]),
                    added=all(line in added for line in range(cursor, stop)),
                ))
            cursor = stop
    return units
