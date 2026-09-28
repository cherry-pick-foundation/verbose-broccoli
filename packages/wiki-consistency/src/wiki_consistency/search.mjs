import {existsSync, readFileSync} from 'node:fs';
import fastGlob from 'fast-glob';
import {createStore, extractSnippet} from '@tobilu/qmd';
// Relies on qmd 2.8.3's internal module; qmd exports no scan helper.
import {
  getRealPath,
  hashContent,
  isPathInsideDir,
  normalizePathSeparators,
  resolve,
  splitGlobMask,
} from '../../node_modules/@tobilu/qmd/dist/store.js';

const excludedDirs = [
  'node_modules',
  '.git',
  '.cache',
  'vendor',
  'dist',
  'build',
];

let input = '';
for await (const chunk of process.stdin) input += chunk;

const {
  operation = 'search',
  queries = [],
  roots = {},
  collection,
} = JSON.parse(input || '{"queries":[],"roots":{}}');
const store = await createStore({dbPath: process.argv[2]});

async function currentDocuments(root) {
  if (typeof root !== 'string' || !existsSync(root)) return [];
  const allFiles = await fastGlob(splitGlobMask('**/*.md'), {
    cwd: root,
    onlyFiles: true,
    followSymbolicLinks: false,
    dot: false,
    ignore: excludedDirs.map(directory => `**/${directory}/**`),
  });
  const files = allFiles.filter(
    file => !file.split('/').some(part => part.startsWith('.')),
  );
  const documents = [];
  for (const relativeFile of files) {
    const filepath = getRealPath(resolve(root, relativeFile));
    if (!isPathInsideDir(root, filepath)) continue;
    let content;
    try {
      content = readFileSync(filepath, 'utf-8');
    } catch {
      continue;
    }
    if (!content.trim()) continue;
    documents.push({
      path: normalizePathSeparators(relativeFile),
      hash: await hashContent(content),
    });
  }
  return documents;
}

async function semanticReady() {
  return (
    process.env.QMD_SEMANTIC_AVAILABLE === '1' &&
    (await store.getIndexHealth()).needsEmbedding === 0
  );
}

try {
  if (operation === 'semantic') {
    process.stdout.write(JSON.stringify({semantic: await semanticReady()}));
  } else if (operation === 'chunk-count') {
    const result = store.internal.db
      .prepare(
        "SELECT COUNT(DISTINCT vectors.hash || '_' || vectors.seq) AS count " +
          'FROM content_vectors AS vectors ' +
          'JOIN documents ON documents.hash = vectors.hash AND documents.active = 1 ' +
          'WHERE documents.collection = ?',
      )
      .get(collection);
    process.stdout.write(JSON.stringify({count: Number(result.count)}));
  } else if (operation === 'counts') {
    const counts = {};
    for (const name of ['pages', 'evidence']) {
      counts[name] = (await currentDocuments(roots[name])).length;
    }
    process.stdout.write(JSON.stringify(counts));
  } else {
    const documents = {};
    for (const name of ['pages', 'evidence']) {
      documents[name] = await currentDocuments(roots[name]);
    }
    const collections = await store.listCollections();
    let error = null;
    for (const name of ['pages', 'evidence']) {
      if (!collections.some(collection => collection.name === name)) {
        error = `qmd ${name} collection is missing; run wiki-consistency index`;
        break;
      }
      const pattern = `${name}/**/*.md`;
      const {docs, errors} = await store.multiGet(pattern, {
        maxBytes: Number.MAX_SAFE_INTEGER,
      });
      const indexed = new Map(
        docs
          .filter(result => !result.skipped)
          .map(({doc}) => [
            doc.filepath.slice(`qmd://${name}/`.length),
            doc.hash,
          ]),
      );
      const expected = documents[name] || [];
      const lookupErrors = errors.filter(
        error => !error.startsWith(`No files matched pattern: ${pattern}`),
      );
      const expectedByPath = new Map(
        expected.map(({path, hash}) => [path, hash]),
      );
      const differences = [];
      for (const [path, hash] of expectedByPath) {
        if (!indexed.has(path)) differences.push({kind: 'added', path});
        else if (indexed.get(path) !== hash)
          differences.push({kind: 'changed', path});
      }
      for (const path of indexed.keys()) {
        if (!expectedByPath.has(path))
          differences.push({
            kind: existsSync(resolve(roots[name], path)) ? 'empty' : 'deleted',
            path,
          });
      }
      differences.sort((left, right) =>
        left.path < right.path ? -1 : left.path > right.path ? 1 : 0,
      );
      if (lookupErrors.length || differences.length) {
        const details = differences
          .slice(0, 5)
          .map(({kind, path}) => `${kind}: ${path}`);
        if (differences.length > details.length) {
          details.push(`${differences.length - details.length} more`);
        }
        if (!details.length) {
          details.push(`${lookupErrors.length} lookup errors`);
        }
        const emptyFiles = differences.some(({kind}) => kind === 'empty');
        error =
          `qmd ${name} collection is stale; ${details.join(', ')}; ` +
          (emptyFiles
            ? 'fill or delete empty files (running index alone cannot clear them because qmd keeps their old rows), then '
            : '') +
          'run wiki-consistency index';
        break;
      }
    }

    const semantic = !error && (await semanticReady());
    if (error) {
      process.stdout.write(JSON.stringify({error}));
    } else {
      const hits = [];
      for (const query of queries) {
        const options = {limit: query.limit, collection: query.collection};
        const allowedPaths =
          query.collection === 'evidence' && Array.isArray(query.allowed_paths)
            ? new Set(query.allowed_paths)
            : null;
        const addHits = (results, mode) => {
          for (const hit of results) {
            const prefix = `qmd://${query.collection}/`;
            const path = hit.filepath.startsWith(prefix)
              ? hit.filepath.slice(prefix.length)
              : hit.filepath;
            if (allowedPaths && !allowedPaths.has(path)) continue;
            hits.push({
              query: query.id,
              collection: hit.collectionName,
              filepath: hit.filepath,
              line: extractSnippet(hit.body, query.text, 300, hit.chunkPos)
                .line,
              score: hit.score,
              mode,
            });
          }
        };
        addHits(await store.searchLex(query.text, options), 'lex');
        if (semantic) {
          addHits(await store.searchVector(query.text, options), 'vec');
        }
      }
      process.stdout.write(JSON.stringify({hits}));
    }
  }
} finally {
  await store.close();
}
