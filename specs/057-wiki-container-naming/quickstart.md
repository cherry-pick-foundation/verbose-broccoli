# Synthetic validation

Run batch checks with the required CPUWeight=20, nice=10 and CPUs 4-7 scope.
Run pytest on wiki-consistency's instance and main tests, then session_select_test.py
in the existing locked uv workspace. Run `npm run test:wiki-raw-import`.
Four synthetic names must pass without a former-container link; initialization,
admission, verify and repeated initialization preserve synthetic source bytes.
Replace only the three changed literals with their old values for a retained
regression run, then restore the new values: the focused cases must fail.
Run affected suites, document checks and root-granted full `npm run verify`.
Use a fresh other-provider reviewer and report unperformed private checks.
