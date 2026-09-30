# Legal-district codes upstream record

Source: 행정표준코드관리시스템 (Standard Administrative Code Management
System) of the Ministry of the Interior and Safety,
<https://www.code.go.kr>, "법정동코드 전체자료" (legal-district code, full
data).

Request (2026-09-30): `POST https://www.code.go.kr/etc/codeFullDown.do` with
`codeseId=00002`.

`legal-district-codes.zip` is the response, unmodified: 413,346 bytes,
SHA-256 `44b96f4a86ad102057463a05aae8842f1d706d3e9e69d2dfc409023bf75ca56b`.
It holds one file, `법정동코드 전체자료.txt`: CP949, tab-separated, file date
2026-09-17, 2,471,662 bytes, SHA-256
`8cfd829c797270b56243a46e9f1e4e95377c2135153c36909021a35a1e32966a`.

The site states no license for the file; it is public data of a Korean
ministry. Only the province and city/county/district names are used.

Use: `scripts/backfire-regions.ts` reads the ZIP and writes
`../../src/backfire_education/regions.json`; `npm run backfire:regions:check`
compares the two and runs in `npm run verify`. The script also checks the
ZIP's hash above. To update the list, download a new ZIP, replace this file
and the hashes here and in the script, and run `npm run backfire:regions`.
