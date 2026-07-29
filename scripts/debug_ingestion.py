"""Interactive CLI debug runner to test Document Parser and Wiki Generator individually."""

import sys
import json
import argparse
from pathlib import Path

# Add root directory to sys.path
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.core.ingestion.parser import parse_document_bytes
from backend.app.core.ingestion.wiki_generator import generate_wiki_pages_from_text


def debug_parse(file_path: str):
    """Run Document Parser on a target file and print formatted return data."""
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

    print(f"\n==================================================")
    print(f"  STEP 1: DEBUGGING DOCUMENT PARSER")
    print(f"  Target File: {path.name}")
    print(f"==================================================\n")

    file_bytes = path.read_bytes()
    result = parse_document_bytes(file_bytes, path.name)

    output = {
        "filename": result["filename"],
        "total_pages": result["total_pages"],
        "character_count": len(result["full_text"]),
        "first_500_chars": result["full_text"][:500],
        "pages_summary": [{"page_number": p["page_number"], "char_len": len(p["text"])} for p in result["pages"]]
    }

    print(json.dumps(output, indent=2))
    print(f"\n[SUCCESS] Document Parser completed successfully.\n")


def debug_wiki(file_or_text: str, user_id: str = "debug_user"):
    """Run Wiki Generator individually and print generated Wiki page objects."""
    path = Path(file_or_text)
    if path.exists():
        if path.suffix.lower() in [".pdf", ".docx", ".doc"]:
            print(f"Parsing '{path.name}' first...")
            parsed = parse_document_bytes(path.read_bytes(), path.name)
            text = parsed["full_text"]
            filename = path.name
        else:
            text = path.read_text(encoding="utf-8")
            filename = path.name
    else:
        text = file_or_text
        filename = "cli_input.txt"

    print(f"\n==================================================")
    print(f"  STEP 2: DEBUGGING WIKI GENERATOR")
    print(f"  Filename: {filename}")
    print(f"  Input Text Length: {len(text)} characters")
    print(f"==================================================\n")

    target_dir = f"wiki/users/{user_id}"
    pages = generate_wiki_pages_from_text(text, filename, wiki_dir=target_dir)

    output = {
        "total_pages_generated": len(pages),
        "target_dir": target_dir,
        "pages": pages
    }

    print(json.dumps(output, indent=2))
    print(f"\n[SUCCESS] Wiki Generator completed successfully.\n")


def main():
    parser = argparse.ArgumentParser(description="WikiLLM Individual Ingestion Debugger")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Parse subcommand
    parse_cmd = subparsers.add_parser("parse", help="Debug Document Parser on a file")
    parse_cmd.add_argument("filepath", help="Path to PDF, DOCX, TXT, or MD file")

    # Wiki subcommand
    wiki_cmd = subparsers.add_parser("wiki", help="Debug Wiki Generator on text or file")
    wiki_cmd.add_argument("input", help="Path to document file or raw text string")
    wiki_cmd.add_argument("--user", default="debug_user", help="User ID for isolated output dir")

    args = parser.parse_args()

    if args.command == "parse":
        debug_parse(args.filepath)
    elif args.command == "wiki":
        debug_wiki(args.input, user_id=args.user)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
