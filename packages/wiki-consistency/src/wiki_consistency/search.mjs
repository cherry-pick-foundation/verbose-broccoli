import {createStore, extractSnippet} from '@tobilu/qmd';

let input = '';
for await (const chunk of process.stdin) input += chunk;

const queries = JSON.parse(input || '[]');
const store = await createStore({dbPath: process.argv[2]});
const hits = [];

try {
  for (const query of queries) {
    const options = {limit: query.limit, collection: query.collection};
    for (const hit of await store.searchLex(query.text, options)) {
      hits.push({
        query: query.id,
        collection: hit.collectionName,
        filepath: hit.filepath,
        line: extractSnippet(hit.body, query.text, 300, hit.chunkPos).line,
        score: hit.score,
        mode: 'lex',
      });
    }
    if (process.env.QMD_SEMANTIC_AVAILABLE === '1') {
      for (const hit of await store.searchVector(query.text, options)) {
        hits.push({
          query: query.id,
          collection: hit.collectionName,
          filepath: hit.filepath,
          line: extractSnippet(hit.body, query.text, 300, hit.chunkPos).line,
          score: hit.score,
          mode: 'vec',
        });
      }
    }
  }
  process.stdout.write(JSON.stringify(hits));
} finally {
  await store.close();
}
