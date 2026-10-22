from pathlib import Path

conllu_folder = Path("./conllu_with_ids")
total_tokens = 0

for path in sorted(conllu_folder.glob("*.conllu")):
    file_tokens = 0

    for line in path.read_text(encoding="utf-8-sig").splitlines():
        # Skip metadata and blank lines.
        if not line.strip() or line.startswith("#"):
            continue

        columns = line.split("\t")

        # Count regular tokens, excluding UPOS=PUNCT.
        # Skip multiword-token and empty-node rows.
        if (
            len(columns) == 10
            and columns[0].isdigit()
            and columns[3] != "PUNCT"
        ):
            file_tokens += 1

    total_tokens += file_tokens
    print(f"{path.name}: {file_tokens:,} tokens")

print(f"\nTotal tokens (excluding PUNCT): {total_tokens:,}")