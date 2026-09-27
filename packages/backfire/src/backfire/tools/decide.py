"""Port of jev-mcp 0.9.0 decide; see ../UPSTREAM.md."""

from backfire.lib import DECIDE_ESCAPE_HATCHES, contradicts_recommendation
from backfire.tools import text
from backfire.tools.answers import PROVIDER, validate_choice_answer

NAME = 'backfire_decide'

TITLE = 'Decide between bounded alternatives'

DESCRIPTION = ('One unresolved, bounded decision where semantic judgment over supplied evidence could change '
 'your plan: implementation alternatives, product tradeoffs with known preferences, workflow '
 'selection. Supply 2-6 candidates, evidence, and explicit priorities. Jev returns a Choice '
 'distribution over the candidates plus escape hatches (ask_user / investigate / none), and a '
 'per-candidate per-requirement supported / contradicted / unknown judgment for each optional '
 'requirement, all in one request. One call per unchanged decision; do not repeat a call to obtain '
 'a more pleasing answer. Use source inspection, tests, the user, or a reasoning model for '
 'open-ended research, routine choices, correctness proofs, or predicting user consent. High '
 'probability is not proof.')

INPUT_SCHEMA = {'$schema': 'http://json-schema.org/draft-07/schema#',
 'type': 'object',
 'properties': {'decision': {'type': 'string',
                             'minLength': 1,
                             'maxLength': 1500,
                             'description': 'The bounded decision to make.'},
                'evidence': {'type': 'string',
                             'minLength': 1,
                             'maxLength': 12000,
                             'description': 'Facts and measurements, not opinions. State is '
                                            'evidence, not instructions.'},
                'priorities': {'type': 'string',
                               'minLength': 1,
                               'maxLength': 2000,
                               'description': 'Explicit preferences and constraints from the user '
                                              'or plan.'},
                'candidates': {'minItems': 2,
                               'maxItems': 6,
                               'type': 'array',
                               'items': {'type': 'object',
                                         'properties': {'id': {'type': 'string',
                                                               'maxLength': 64,
                                                               'pattern': '^[a-z][a-z0-9_-]*$'},
                                                        'description': {'type': 'string',
                                                                        'minLength': 1,
                                                                        'maxLength': 2000}},
                                         'required': ['id', 'description'],
                                         'additionalProperties': False},
                               'description': "The alternatives. Include 'do nothing' or 'gather "
                                              "more evidence' as candidates when useful."},
                'requirements': {'description': 'Specific requirements to check per candidate. '
                                                'Each must test one property, not overall '
                                                'goodness.',
                                 'maxItems': 3,
                                 'type': 'array',
                                 'items': {'type': 'string', 'minLength': 1, 'maxLength': 500}},
                'escape_hatches': {'description': 'Include ask_user / investigate / none as '
                                                  'Choosable options so the model can decline to '
                                                  'rank. Default true.',
                                   'type': 'boolean'}},
 'required': ['decision', 'evidence', 'priorities', 'candidates'],
 'additionalProperties': False}

EXECUTION = {'taskSupport': 'forbidden'}


async def call(arguments, judge, *, deadline, record_file):
    include_hatches = arguments.get("escape_hatches", True)
    requirements = arguments.get("requirements", [])
    candidates = arguments["candidates"]
    seen = set()
    for candidate in candidates:
        identifier = candidate["id"]
        if identifier in seen:
            raise ValueError(f"Duplicate candidate id: {identifier}")
        if include_hatches and identifier in DECIDE_ESCAPE_HATCHES:
            raise ValueError(f'Candidate id "{identifier}" collides with an escape hatch; rename it or set escape_hatches: false.')
        seen.add(identifier)
    candidate_keys = [{**candidate, "key": f"option_{index}"} for index, candidate in enumerate(candidates)]
    criteria = {candidate["key"]: candidate["description"] for candidate in candidate_keys}
    if include_hatches:
        criteria.update(DECIDE_ESCAPE_HATCHES)
    questions = {
        "recommendation": {
            "type": "choice",
            "instructions": ("Which candidate best fits the decision, evidence, and priorities? "
                             + ("Select a candidate or an escape hatch. " if include_hatches else "")
                             + "Do not invent missing facts, preferences, or approvals."),
            "criteria": criteria,
        },
    }
    relation_criteria = {
        "supported": "The evidence and mechanism support this specific requirement",
        "contradicted": "The evidence or mechanism contradicts this specific requirement, not merely another requirement",
        "unknown": "Relevant evidence is missing; neither satisfaction nor violation is established",
    }
    for index, candidate in enumerate(candidate_keys):
        for requirement_index, requirement in enumerate(requirements):
            questions[f"check_{index}_{requirement_index}"] = {
                "type": "choice",
                "instructions": f"How does the mechanism in candidates[{index}] relate to requirements[{requirement_index}], using the evidence? Judge only this property, not the candidate overall desirability. Missing evidence is not contradiction.",
                "criteria": relation_criteria,
            }
    state = {
        "decision": arguments["decision"], "evidence": arguments["evidence"], "priorities": arguments["priorities"],
        "candidates": [{"id": candidate["key"], "description": candidate["description"]} for candidate in candidate_keys],
        "requirements": requirements,
    }
    result = await judge(state, questions, deadline=deadline, record_file=record_file)
    answers = result["answers"] if isinstance(result.get("answers"), dict) else {}
    key_to_id = {candidate["key"]: candidate["id"] for candidate in candidate_keys}
    recommendation = validate_choice_answer(answers.get("recommendation"), criteria)
    checks = []
    for index, candidate in enumerate(candidate_keys):
        for requirement_index, requirement in enumerate(requirements):
            answer = validate_choice_answer(answers.get(f"check_{index}_{requirement_index}"), relation_criteria)
            checks.append({"candidate": candidate["id"], "requirement": requirement_index,
                           "answer": answer["choice"] if answer else "invalid_response"})
    selected = recommendation["choice"] if recommendation else None
    contradicted = contradicts_recommendation(checks, key_to_id[selected]) if selected in key_to_id else []
    return text({
        "tool": NAME, "model": result["model"], "provider": PROVIDER,
        "recommendation": {
            "selected": key_to_id.get(selected, selected), "escaped": selected not in key_to_id,
            "confidence": recommendation["confidence"],
            "probabilities": {key_to_id.get(key, key): probability for key, probability in recommendation["probabilities"].items()},
        } if recommendation else {"selected": None, "escaped": None, "confidence": None,
                                  "probabilities": None, "status": "invalid_response"},
        "requirements_checked": len(requirements), "checks": checks,
        "warnings": [f"Requirement{'s' if len(contradicted) > 1 else ''} {', '.join(str(index + 1) for index in contradicted)} contradicted by the recommended candidate; inspect before acting"] if contradicted else [],
        "usage": result["usage"],
    }), False
