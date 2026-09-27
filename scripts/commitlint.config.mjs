import conventionalConfig from '@commitlint/config-conventional';
import conventionalChangelog from 'conventional-changelog-conventionalcommits';
import {constitutionVersionRule} from './constitution_version.ts';

const parserOpts = conventionalChangelog().parser;

export default {
  ...conventionalConfig,
  parserPreset: {parserOpts},
  plugins: [
    {
      rules: {'local/constitution-version': constitutionVersionRule},
    },
  ],
  rules: {
    ...conventionalConfig.rules,
    'local/constitution-version': [2, 'always'],
  },
};
