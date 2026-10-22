from pathlib import Path
import re
import unicodedata


def tokenize(text):
    """Preserve ʻokina and kahakō; separate punctuation into tokens."""
    tokens = []
    i = 0

    def is_word_char(char):
        return (
            unicodedata.category(char)[0] in "LNM"
            or char in "ʻ’'"
        )

    while i < len(text):
        char = text[i]

        if char.isspace():
            i += 1
            continue

        if is_word_char(char):
            j = i + 1
            while j < len(text) and is_word_char(text[j]):
                j += 1

        elif char == "!":
            # Preserve repeated exclamation marks as one token.
            j = i + 1
            while j < len(text) and text[j] == char:
                j += 1

        else:
            j = i + 1

        tokens.append(text[i:j])
        i = j

    return tokens


def extract_sentences(text):
    """Remove timestamps, speaker labels, and ^ markers; split at periods."""
    lines = []

    for line in text.splitlines():
        # Remove a leading timestamp and speaker label, e.g., "13:30 LK".
        line = re.sub(
            r"^\s*\d+:\d+(?::\d+)?\s+[A-Za-z]+\b[ \t]*",
            "",
            line,
        )

        # Replace ^ markers with spaces to prevent words merging.
        line = re.sub(r"\^+", " ", line)

        # Normalize consecutive whitespace.
        line = re.sub(r"\s+", " ", line).strip()

        if line:
            lines.append(line)

    cleaned_text = " ".join(lines)

    # Keep periods with their sentences. Retain final text without a period.
    sentences = re.findall(r"[^.]*\.+|[^.]+$", cleaned_text)

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def get_upos(token):
    """Assign PUNCT to tokens consisting entirely of Unicode punctuation."""
    if token and all(
        unicodedata.category(char).startswith("P")
        for char in token
    ):
        return "PUNCT"

    return "_"


def convert_to_conllu(input_path, output_path):
    """Use document ID + local sentence number as the sentence ID."""
    text = input_path.read_text(encoding="utf-8-sig")
    doc_id = re.sub(r"\s+", "_", input_path.stem.strip())
    blocks = []

    for sentence_number, sentence in enumerate(
        extract_sentences(text), start=1
    ):
        tokens = tokenize(sentence)
        assert "".join(tokens) == "".join(sentence.split())

        rows = []

        if sentence_number == 1:
            rows.append(f"# newdoc id = {doc_id}")

        rows.extend([
            f"# sent_id = {doc_id}_{sentence_number}",
            f"# text = {sentence}",
        ])

        for token_id, token in enumerate(tokens, start=1):
            rows.append(
                "\t".join([
                    str(token_id),    # ID
                    token,            # FORM
                    "_",              # LEMMA
                    get_upos(token),  # UPOS
                    "_",              # XPOS
                    "_",              # FEATS
                    "_",              # HEAD
                    "_",              # DEPREL
                    "_",              # DEPS
                    "_",              # MISC
                ])
            )

        blocks.append("\n".join(rows))

    output_path.write_text(
        "\n\n".join(blocks) + ("\n\n" if blocks else ""),
        encoding="utf-8",
    )

    return len(blocks)


input_folder = Path("./data")
output_folder = Path("./conllu_with_ids")

txt_files = sorted(
    path for path in input_folder.iterdir()
    if path.is_file() and path.suffix.lower() == ".txt"
)

# Document IDs must be unique to prevent duplicate sentence IDs.
doc_ids = [path.stem for path in txt_files]
if len(doc_ids) != len(set(doc_ids)):
    raise ValueError("Duplicate document IDs: use unique input filenames.")

output_folder.mkdir(parents=True, exist_ok=True)

total_sentences = 0

for input_path in txt_files:
    output_path = output_folder / f"{input_path.name}.conllu"
    sentence_count = convert_to_conllu(input_path, output_path)
    total_sentences += sentence_count

    print(f"{input_path.name}: {sentence_count:,} sentences")

print(f"\nTotal sentences: {total_sentences:,}")
print(f"Output folder: {output_folder.resolve()}")