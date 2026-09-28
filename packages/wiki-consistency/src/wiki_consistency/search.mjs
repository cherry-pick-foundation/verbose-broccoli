import {createStore, extractSnippet} from '@tobilu/qmd';

let input = '';
for await (const chunk of process.stdin) input += chunk;

const {
  operation = 'search',
  queries = [],
  documents = {},
} = JSON.parse(input || '{"queries":[],"documents":{}}');
const store = await createStore({dbPath: process.argv[2]});

async function semanticReady() {
  return (
    process.env.QMD_SEMANTIC_AVAILABLE === '1' &&
    (await store.getIndexHealth()).needsEmbedding === 0
  );
}

try {
  if (operation === 'semantic') {
    process.stdout.write(JSON.stringify({semantic: await semanticReady()}));
  } else {
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
      if (
        lookupErrors.length ||
        indexed.size !== expected.length ||
        expected.some(document => indexed.get(document.path) !== document.hash)
      ) {
        error = `qmd ${name} collection is stale; run wiki-consistency index`;
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
