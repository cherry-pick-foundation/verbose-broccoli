"""Port of jev-mcp 0.9.0 verify; see ../UPSTREAM.md."""

from backfire.lib import RELATION_TO_VERDICT, ensure_unique_ids, normalize_evidence, verify_action
from backfire.tools import text
from backfire.tools.answers import PROVIDER, validate_choice_answer

NAME = 'backfire_verify'

TITLE = 'Verify claims against evidence'

DESCRIPTION = ('Check each claim against provided evidence text with TypeSafe Jev. Returns per claim: verdict '
 '(verified | contradicted | unsupported), full probability distribution, confidence, and whether '
 'the verdict stands on its own (auto) or needs human review. Pattern: '
 'docs.typesafe.ai/cookbooks/citation_check. Pass reports, PR descriptions, or agent briefs as '
 'claims and their cited sources, diffs, or documents as evidence.')

INPUT_SCHEMA = {'$schema': 'http://json-schema.org/draft-07/schema#',
 'type': 'object',
 'properties': {'claims': {'minItems': 1,
                           'type': 'array',
                           'items': {'type': 'string'},
                           'description': 'Claims to verify, e.g. individual factual statements '
                                          'from a report.'},
                'evidence': {'anyOf': [{'type': 'string',
                                        'description': 'A single evidence document.'},
                                       {'type': 'object',
                                        'properties': {'id': {'description': 'Short identifier for '
                                                                             'this evidence item.',
                                                              'type': 'string'},
                                                       'text': {'type': 'string',
                                                                'description': 'The evidence '
                                                                               'text.'}},
                                        'required': ['text'],
                                        'additionalProperties': False,
                                        'description': 'A single evidence item.'},
                                       {'minItems': 1,
                                        'type': 'array',
                                        'items': {'type': 'object',
                                                  'properties': {'id': {'description': 'Short '
                                                                                       'identifier '
                                                                                       'for this '
                                                                                       'evidence '
                                                                                       'item (e.g. '
                                                                                       "'site-html', "
                                                                                       "'rfc-4.1.3').",
                                                                        'type': 'string'},
                                                                 'text': {'type': 'string',
                                                                          'description': 'The '
                                                                                         'evidence '
                                                                                         'text.'}},
                                                  'required': ['text'],
                                                  'additionalProperties': False},
                                        'description': 'Multiple evidence items; each claim is '
                                                       'also matched to the item it rests on.'}]},
                'auto_accept': {'description': 'Verdicts at or above this confidence stand '
                                               "automatically; below it they are flagged 'review'. "
                                               'Default 0.8.',
                                'type': 'number',
                                'minimum': 0,
                                'maximum': 1}},
 'required': ['claims', 'evidence'],
 'additionalProperties': False}

EXECUTION = {'taskSupport': 'forbidden'}


async def call(arguments, judge, *, deadline, record_file):
    auto_accept = arguments.get("auto_accept", 0.8)
    evidence = normalize_evidence(arguments["evidence"])
    claims = ensure_unique_ids([{"text": claim} for claim in arguments["claims"]], "claim")["items"]
    questions = {}
    for claim in claims:
        questions[f"relation_{claim['id']}"] = {
            "type": "choice",
            "instructions": f"How does the evidence relate to claim `{claim['id']}` ({claim['text']})?",
            "criteria": {
                "supports": "The evidence states the claim or directly implies that it is true",
                "contradicts": "The evidence states the opposite of the claim or implies that it is false",
                "says_nothing": "The evidence does not address what the claim asserts, either way",
            },
        }
        if len(evidence) > 1:
            criteria = {item["id"]: None for item in evidence}
            criteria["none"] = "No single evidence item contains the content the claim depends on"
            questions[f"source_{claim['id']}"] = {
                "type": "choice",
                "instructions": f"Which evidence item does claim `{claim['id']}` ({claim['text']}) rest on?",
                "criteria": criteria,
            }
    state = {"purpose": "Verify each claim in claims against the evidence in evidence.",
             "claims": claims, "evidence": evidence}
    result = await judge(state, questions, deadline=deadline, record_file=record_file)
    answers = result["answers"] if isinstance(result.get("answers"), dict) else {}
    rows = []
    for claim in claims:
        relation = answers.get(f"relation_{claim['id']}")
        validated = validate_choice_answer(relation, RELATION_TO_VERDICT)
        source = validate_choice_answer(answers.get(f"source_{claim['id']}"),
                                        [item["id"] for item in evidence] + ["none"])
        valid = validated is not None and (relation.get("confidence") is None or validated["confidence"] is not None)
        if not valid:
            rows.append({"id": claim["id"], "claim": claim["text"], "verdict": "unknown",
                         "probabilities": None, "confidence": None, "status": "invalid_response",
                         "action": "review", "supporting_evidence": None})
            continue
        confidence = validated["confidence"]
        rows.append({
            "id": claim["id"], "claim": claim["text"], "verdict": RELATION_TO_VERDICT[relation["choice"]],
            "probabilities": relation["probabilities"], "confidence": confidence,
            "action": "review" if confidence is None else verify_action(confidence, auto_accept),
            "supporting_evidence": source["choice"] if source and source["choice"] != "none" else None,
        })
    return text({
        "tool": NAME, "model": result["model"], "provider": PROVIDER, "auto_accept": auto_accept,
        "summary": {
            "verified": sum(row["verdict"] == "verified" for row in rows),
            "contradicted": sum(row["verdict"] == "contradicted" for row in rows),
            "unsupported": sum(row["verdict"] == "unsupported" for row in rows),
            "needs_review": sum(row["action"] == "review" for row in rows),
        },
        "results": rows, "usage": result["usage"],
    }), False
