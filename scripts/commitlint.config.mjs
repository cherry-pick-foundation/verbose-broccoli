import conventionalConfig from '@commitlint/config-conventional';
import conventionalChangelog from 'conventional-changelog-conventionalcommits';
import {constitutionVersionRule} from './constitution_version.ts';

const parserOpts = conventionalChangelog().parser;
const commitMode = process.env.CONSTITUTION_VERSION_COMMIT !== undefined;

export default {
  ...conventionalConfig,
  parserPreset: {parserOpts},
  plugins: [
    {
      rules: {'local/constitution-version': constitutionVersionRule},
    },
  ],
  defaultIgnores: !commitMode,
  rules: commitMode
    ? {'local/constitution-version': [2, 'always']}
    : {
        ...conventionalConfig.rules,
        'local/constitution-version': [2, 'always'],
      },
};
