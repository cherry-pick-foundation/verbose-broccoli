# Regions Contract

## Markers

A mechanical region is a Cog block written in HTML comments:

```markdown
<!-- [[[cog import doc_sources; cog.out(doc_sources.skill_table("plugins/*/skills/*/SKILL.md")) ]]] -->
| Package | Owned skills |
| --- | --- |
| ... generated rows ... |
<!-- [[[end]]] -->
```

- The code is one line with exactly two statements: `import <module>` and
  `cog.out(<module>.<function>(<arguments>))`. `<module>` is the configured
  generator module; `<function>` is a public function of it.
- Every argument is a string literal naming a repository-relative file or
  glob; these are the region's sources. Keyword arguments are not allowed.
- Regions do not nest. Every start marker has one end marker before the next
  start marker.
- Markers may appear anywhere a Markdown HTML block can; the generator's
  output must end with a newline.

## Generators

- A generator reads only its named sources and returns a string. The same
  source bytes give the same output.
- It uses no network, clock, random value, environment variable or
  machine-specific path, and writes no file.
- Each generator has a test with a fixture source and its exact expected
  output, and a test that it raises when a source is missing.

## Check (`doc-regions check`)

Fails, printing each problem with document and line, when:

1. markers are unbalanced or nested;
2. a region's code is not the allowed shape, calls an unknown function, or
   names a source that does not exist;
3. Cog's `--check` finds a region whose text differs from its generator's
   output (the failure shows Cog's diff and names `deno task doc-regions:update`);
4. lychee in offline mode finds a link to a missing local file or heading in a
   target document;
5. a configured path does not exist, or a path is in both lists.

The check writes no file and does not touch the Git index. External URLs are
not followed. Report-only documents are not checked, so the check never
requires an edit to them.

## Update (`doc-regions update`)

Runs the shape checks 1, 2 and 5, then `cog -r` on every target with a
mechanical region. Only region text changes; a second run changes nothing.
On a shape failure it changes no file.
