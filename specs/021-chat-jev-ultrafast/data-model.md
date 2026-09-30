# Data model: Jev Ultrafast web agent and API credit offer search

Nothing here is stored by the feature; these are the shapes it reads and
passes along.

## Offer (read from the tracker's `index.json`)

| Field | Use |
| --- | --- |
| `slug` | Identity; compared between the two index snapshots of a block |
| `title`, `provider`, `category`, `amount`, `source_url` | Sent to Jev as the offer's state; shown in the notification |
| `expiry_date` | Set (a date) means the offer states an end date: dropped without a Jev call |
| `status` | Anything other than `active` is dropped |

Other fields (`verified_date`, `verification`, `review_status`, `signup`) are
ignored.

## Block

The period one run examines: `[end − hours, end)`, where `end` is a boundary
of the local day divisible by `hours` (6 by default). Two runs in the same
block examine the same offers.

## Provider (from `providers.toml`)

`name` (table name), `protocol` (`systemone` or `evaluation-model`), `url`,
`key_env`, optional `model` and `headers`. See
[contracts/providers.md](contracts/providers.md).

## Judgment

One Jev `choice` answer per offer: `choice` (`qualifies` or `excluded`),
`probabilities` over both, `confidence`. Valid only when upstream
`validate_choice()` accepts it; an invalid answer fails the run (exit 3).

## Offer history (feature record only)

[offer-history.tsv](offer-history.tsv): `first_seen`, `commit`, `slug`,
`category`, `expiry_date`, `decision`, `ended`, `amount`. See
[research R9](research.md#r9-the-schedule-interval).
