let customConfig = [];
let hasIgnoresFile = false;
try {
  require.resolve('./eslint.ignores.js');
  hasIgnoresFile = true;
} catch {
  // eslint.ignores.js doesn't exist
}

if (hasIgnoresFile) {
  const ignores = require('./eslint.ignores.js');
  customConfig = [{ignores}];
}

module.exports = [...customConfig, ...require('gts')];

// Keep runtime and I/O globals out of domain code.
module.exports.push({
  files: ['plugins/**/domain/**', 'packages/**/domain/**'],
  rules: {
    'no-restricted-globals': [
      'error',
      {name: 'Bun', message: 'Domain code must not use runtime or I/O globals.'},
      {name: 'process', message: 'Domain code must not use runtime or I/O globals.'},
      {name: 'fetch', message: 'Domain code must not use runtime or I/O globals.'},
      {name: 'Request', message: 'Domain code must not use runtime or I/O globals.'},
      {name: 'Response', message: 'Domain code must not use runtime or I/O globals.'},
      {name: 'WebSocket', message: 'Domain code must not use runtime or I/O globals.'},
      {name: 'XMLHttpRequest', message: 'Domain code must not use runtime or I/O globals.'},
      {name: 'localStorage', message: 'Domain code must not use runtime or I/O globals.'},
      {name: 'sessionStorage', message: 'Domain code must not use runtime or I/O globals.'},
      {name: 'globalThis', message: 'Domain code must not reach globals through the global object.'},
      {name: 'self', message: 'Domain code must not reach globals through the global object.'},
      {name: 'window', message: 'Domain code must not reach globals through the global object.'},
      {name: 'global', message: 'Domain code must not reach globals through the global object.'},
    ],
  },
});
