"""Plain-text audit report for one log."""

from .correction import correction_for_audit


def _literal_label(log, literal):
    item_id, value = literal
    item = log.item_map()[item_id]
    return "%s=%s" % (item_id, "yes" if value else "no")


def _witness_text(log, violation):
    labels = [_literal_label(log, literal)
              for literal in violation.witness]
    kinds = []
    for kind in violation.path_kinds:
        kinds.append(kind or "?")
    steps = []
    for index, label in enumerate(labels):
        steps.append(label)
        if index < len(kinds):
            steps.append("-[%s]->" % kinds[index])
    return " ".join(steps)


def format_audit_report(log, audit, correction=None):
    if correction is None:
        correction = correction_for_audit(audit)
    items = log.item_map()
    lines = []
    lines.append("Logic Closure Contradiction Audit -- report")
    lines.append("===========================================")
    lines.append("Log: %s (%d items, %d declared relations, %d "
                 "logically linked pairs)"
                 % (log.name, len(log.items), len(log.relations),
                    len(audit.linked_pairs)))
    lines.append("")
    lines.append("Closure violations: %d (%d direct, %d transitive)"
                 % (len(audit.violations), audit.direct_count,
                    audit.transitive_count))
    lines.append("Directly broken declared relations: %d"
                 % len(audit.broken_relations))
    lines.append("Violation rate over linked pairs: %.3f"
                 % audit.violation_rate)
    lines.append("Confidence-weighted violation rate: %.3f"
                 % audit.weighted_violation_rate)
    lines.append("")
    if audit.violations:
        lines.append("Violations (pair, witness path):")
        for violation in audit.violations:
            first, second = violation.pair
            lines.append("  %s x %s [%s] (conf %.2f / %.2f)"
                         % (first, second,
                            "direct" if violation.direct
                            else "transitive, %d edges"
                            % violation.path_length,
                            log.confidence(first),
                            log.confidence(second)))
            lines.append("    %s" % _witness_text(log, violation))
        lines.append("")
    lines.append("Minimal correction set: %d item(s)%s"
                 % (correction["size"],
                    " (exact)" if correction["exact"]
                    else " (greedy -- graph over exact cap)"))
    for item_id in correction["items"]:
        item = items[item_id]
        lines.append("  flip %s: %s (recorded %s, conf %.2f)"
                     % (item_id, item.text,
                        "yes" if log.answer(item_id) else "no",
                        log.confidence(item_id)))
    lines.append("Greedy correction set size: %d"
                 % correction["greedy_size"])
    lines.append("")
    return "\n".join(lines)
