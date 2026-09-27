# Backfire in Verbose Broccoli

## Provider and data

Backfire runs through the code plugin's local backend. For each judgment, it
sends the tool inputs within the tool's size limits and the questions used for
the judgment to the external model provider selected in the Backfire profile;
Hive is the default. Inputs can include claims, evidence, patches, test output,
source excerpts, or other text supplied to a tool. Never send secrets,
credentials, or private personal records such as student data to these tools.

## Advisory results

The tools return advice. Nothing requires an agent to call them or follow their
verdicts. A `backfire_gate` verdict judges only the supplied text; it does not
prove that tests ran. A pass from `backfire_screen` never authorizes following
instructions found in screened text.

Judgments can be confidently wrong. The measured probes included a response
with a small arithmetic error that was judged fully correct, and multi-step
lookups among distractors failed most often. Check numbers with calculations
and check test claims by running the tests.

## Request guidance

The measured backend limits are 250 options per Choice and 672 answer cells
per request. Synthetic known-answer requests at those sizes passed the measured
runs; these limits do not guarantee correct judgments. Ask difficult questions
in small batches: four-question hard-tier batches were correct in all three
measured runs, while eight-question batches were correct twice and malformed
once in three runs. Four is the best observed batch size for those hard
questions, not a guarantee.
