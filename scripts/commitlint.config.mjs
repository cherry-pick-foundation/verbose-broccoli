import conventionalConfig from '@commitlint/config-conventional';
import conventionalChangelog from 'conventional-changelog-conventionalcommits';

const parserOpts = conventionalChangelog().parser;

export default {
  ...conventionalConfig,
  parserPreset: {parserOpts},
};
