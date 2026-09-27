from collections import Counter

import pytest

from doc_regions.units import split


TEXT = '''# Title

First paragraph
on two lines.

## Details

- One
  - nested
- Two

| A | B |
| - | - |
| 1 | 2 |

```python
print('hello')
```

<div>
HTML
</div>

> Quoted
> paragraph.

---

[ref]: local.md
'''


def test_top_level_blocks_and_line_maps():
    units = split('doc.md', TEXT)
    assert [(u['kind'], u['first_line'], u['last_line']) for u in units] == [
        ('heading', 1, 1), ('paragraph', 3, 4), ('heading', 6, 6),
        ('list_item', 8, 9), ('list_item', 10, 11), ('table', 12, 14),
        ('code', 16, 18), ('html', 20, 22), ('blockquote', 24, 25),
    ]
    for unit in units:
        assert unit['id'] == f"doc.md:{unit['first_line']}-{unit['last_line']}"
        assert unit['text'] == ''.join(TEXT.splitlines(True)[unit['first_line']-1:unit['last_line']])
        assert not unit['added']
    assert units[0]['heading_path'] == []
    assert units[1]['heading_path'] == ['Title']
    assert units[2]['heading_path'] == ['Title']
    assert units[-1]['heading_path'] == ['Title', 'Details']
    covered = Counter(line for unit in units
                      for line in range(unit['first_line'], unit['last_line'] + 1))
    for line, text in enumerate(TEXT.splitlines(), 1):
        if text.strip() and text != '---' and not text.startswith('[ref]:'):
            assert covered[line] == 1


def test_heading_path_resets_at_same_and_higher_level():
    units = split('doc.md', '# A\n\n### Deep\n\nx\n\n## B\n\ny\n\n# C\n\nz\n')
    assert [u['heading_path'] for u in units if u['kind'] == 'paragraph'] == [
        ['A', 'Deep'], ['A', 'B'], ['C']]


def test_mechanical_lines_never_enter_list_unit():
    text = ('# Title\n\n- Before\n\n'
            '  <!-- [[[cog import sources; cog.out(sources.render("a")) ]]] -->\n'
            '  generated secret\n'
            '  <!-- [[[end]]] -->\n\n'
            '  After\n\n- Next\n')
    units = split('doc.md', text)
    assert all('generated' not in u['text'] and '[[[' not in u['text'] for u in units)
    covered = Counter(line for u in units for line in range(u['first_line'], u['last_line'] + 1))
    assert all(covered[line] == 0 for line in [5, 6, 7])
    assert all(covered[line] == 1 for line in [1, 3, 9, 11])


@pytest.mark.parametrize('base, expected', [(None, [False, False]), ('', [True, True]),
                                           ('# Title\n', [False, True])])
def test_added_uses_base_lines(base, expected):
    assert [u['added'] for u in split('doc.md', '# Title\n\nNew.\n', base)] == expected


def test_partly_edited_unit_is_not_added():
    base = '# Title\n\nKept line\nold line.\n'
    text = '# Title\n\nKept line\nnew line.\n\nAdded unit.\n'
    assert [u['added'] for u in split('doc.md', text, base)] == [False, False, True]


def test_invalid_markers_fail_with_line():
    with pytest.raises(ValueError, match='doc.md:1'):
        split('doc.md', '<!-- [[[end]]] -->\n')
