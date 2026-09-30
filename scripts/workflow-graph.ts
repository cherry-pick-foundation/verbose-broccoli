export const graphCommands = [
  {
    choice: 'impact',
    when: 'Before changing an existing file or checking its consumers after an edit.',
    command: 'npm run workflow -- --task <id> --graph impact --file <path>',
    returns:
      'Raw dependency-cruiser JSON for files changed from the base and the selected file’s dependents.',
  },
  {
    choice: 'symbol',
    when: 'Before changing or removing a symbol; select its identifier by 1-based line and UTF-16 column.',
    command:
      'npm run workflow -- --task <id> --graph symbol --file <path> --line <n> --column <n>',
    returns:
      'Raw dependency-cruiser JSON, TypeScript definitions, references and calls.',
  },
  {
    choice: 'policy',
    when: 'After imports, package boundaries, or file structure change, including deletions.',
    command: 'npm run workflow -- --task <id> --graph policy',
    returns:
      'Raw dependency-cruiser JSON for repository-wide static import-policy checks.',
  },
];
