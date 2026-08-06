"""Stage 8: Log Maintenance Engine.

Appends detailed ingestion run logs to log.md in the user's wiki directory.
Strictly appends new entries without ever rewriting previous log entries.
Logs:
- timestamp
- document name
- pages created
- pages updated
- entities discovered
- concepts discovered
- contradictions found
"""

import datetime
from pathlib import Path
from typing import Dict, Any, List


def append_ingestion_log(
    wiki_dir: str,
    document_name: str,
    wiki_update_results: Dict[str, Any],
    knowledge_json: Dict[str, Any]
) -> str:
    """Execute Stage 8 Log Maintenance by appending run record to log.md.

    Args:
        wiki_dir: Directory of user's wiki.
        document_name: Filename of the ingested source document.
        wiki_update_results: Results dict from Stage 6 Wiki Engine.
        knowledge_json: Knowledge extraction JSON from Stage 5.

    Returns:
        Path of the updated log.md file.
    """
    target_dir = Path(wiki_dir)
    log_path = target_dir / "log.md"


    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    pages_created = wiki_update_results.get("pages_created", [])
    pages_updated = wiki_update_results.get("pages_updated", [])
    
    entities = knowledge_json.get("entities", [])
    concepts = knowledge_json.get("concepts", [])
    contradictions = knowledge_json.get("contradictions", [])

    created_str = ", ".join(f"`{p}`" for p in pages_created) if pages_created else "None"
    updated_str = ", ".join(f"`{p}`" for p in pages_updated) if pages_updated else "None"
    entities_str = ", ".join(f"`{e.get('name')}`" for e in entities) if entities else "None"
    concepts_str = ", ".join(f"`{c.get('name')}`" for c in concepts) if concepts else "None"
    
    contradictions_lines = []
    if contradictions:
        for c in contradictions:
            contradictions_lines.append(f"  - **Subject**: {c.get('subject')} | Conflict: {c.get('explanation', 'None')}")
        contradictions_str = "\n" + "\n".join(contradictions_lines)
    else:
        contradictions_str = "None"

    log_entry = f"""
## [{now_iso}] Ingestion Run: `{document_name}`

- **Document Name**: `{document_name}`
- **Pages Created ({len(pages_created)})**: {created_str}
- **Pages Updated ({len(pages_updated)})**: {updated_str}
- **Entities Discovered ({len(entities)})**: {entities_str}
- **Concepts Discovered ({len(concepts)})**: {concepts_str}
- **Contradictions Found ({len(contradictions)})**: {contradictions_str}

---
"""

    return str(log_path)


