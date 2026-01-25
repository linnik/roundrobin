import argparse
import doctest
import os
import re


_FENCE_START_RE = re.compile(r"^```(?P<info>[^`]*)\s*$")
_FENCE_END_RE = re.compile(r"^```\s*$")


class _MarkdownDoctestChecker(doctest.OutputChecker):
    """
    A slightly more permissive checker for Markdown/README doctests.

    In tracebacks, README examples typically use a standalone "..." line as a
    placeholder for traceback noise. On newer Python versions, tracebacks may
    include extra context lines (source + caret ranges), which vanilla doctest
    will treat as a mismatch. Here, a standalone "..." line is treated as a
    wildcard that can match *any number* of lines until the next expected line.
    """

    def check_output(self, want, got, optionflags):
        if doctest.OutputChecker.check_output(self, want, got, optionflags):
            return True

        want_lines = want.splitlines()
        if not any(line.strip() == "..." for line in want_lines):
            return False

        got_lines = got.splitlines()
        base = doctest.OutputChecker()

        wi = 0
        gi = 0
        while wi < len(want_lines):
            if want_lines[wi].strip() == "...":
                wi += 1
                if wi >= len(want_lines):
                    return True

                next_want = want_lines[wi]
                while gi < len(got_lines) and not base.check_output(
                    next_want, got_lines[gi], optionflags
                ):
                    gi += 1
                if gi >= len(got_lines):
                    return False
                continue

            if gi >= len(got_lines):
                return False
            if not base.check_output(want_lines[wi], got_lines[gi], optionflags):
                return False
            wi += 1
            gi += 1

        return gi == len(got_lines)


def _extract_fenced_blocks(markdown_text, wanted_langs):
    """
    Extract fenced code blocks in order.

    Returns a list of (lang, block_text, start_lineno).

    Note: start_lineno is the 0-based line number to pass to doctest (i.e. the
    first line of block_text is reported as start_lineno + 1).
    """
    blocks = []
    lines = markdown_text.splitlines(True)

    in_block = False
    block_lang = None
    block_start_lineno = None
    block_lines = []

    for idx, line in enumerate(lines, 1):
        if not in_block:
            m = _FENCE_START_RE.match(line)
            if not m:
                continue
            info = (m.group("info") or "").strip()
            lang = (info.split(None, 1)[0] if info else "").lower()
            in_block = True
            block_lang = lang
            block_start_lineno = idx
            block_lines = []
            continue

        if _FENCE_END_RE.match(line):
            in_block = False
            block_text = "".join(block_lines)
            if block_lang in wanted_langs:
                blocks.append((block_lang, block_text, block_start_lineno))
            block_lang = None
            block_start_lineno = None
            block_lines = []
            continue

        block_lines.append(line)

    return blocks


def run_readme_doctests(readme_path, verbose=0):
    """
    Runs doctest-style examples from fenced ```python blocks in README.md.

    All blocks are evaluated in a shared globals dict, in order, to match the
    way the README is read top-to-bottom.
    """
    with open(readme_path, "r") as f:
        markdown_text = f.read()

    blocks = _extract_fenced_blocks(markdown_text, wanted_langs=set(["python", "py"]))

    shared_globs = {"__name__": "__main__"}
    parser = doctest.DocTestParser()
    runner = doctest.DocTestRunner(
        checker=_MarkdownDoctestChecker(),
        verbose=bool(verbose and verbose > 1),
        optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE,
    )

    for block_index, (_lang, block_text, start_lineno) in enumerate(blocks, 1):
        name = "README.md block {}".format(block_index)
        test = parser.get_doctest(
            block_text,
            shared_globs,
            name=name,
            filename=readme_path,
            lineno=start_lineno,
        )
        test.globs = shared_globs
        runner.run(test, clear_globs=False)

    return runner.summarize(verbose=bool(verbose and verbose > 1))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run doctest examples from fenced ```python blocks in README.md"
    )
    parser.add_argument(
        "readme",
        nargs="?",
        default=os.path.join(os.path.dirname(__file__), "README.md"),
        help="Path to README.md (default: repo root README.md)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Print a short summary (use -vv for full doctest output)",
    )
    args = parser.parse_args(argv)

    results = run_readme_doctests(args.readme, verbose=args.verbose)
    if args.verbose:
        status = "PASSED" if results.failed == 0 else "FAILED"
        print(
            "README doctests: {} (attempted {}, failed {})".format(
                status, results.attempted, results.failed
            )
        )
    if results.failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
