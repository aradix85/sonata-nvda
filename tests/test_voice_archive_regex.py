# coding: utf-8
"""
Tests for VOICE_INFO_REGEX in voice_download.py — the parser used to
identify the language / name / quality of a voice from its archive filename
or its bundled .onnx filename.

The regex is extracted by reading voice_download.py as text rather than
importing it, because voice_download depends on NVDA-only modules (wx,
gui, core, languageHandler, logHandler) that aren't available outside the
NVDA runtime.
"""

import os
import re

import pytest


_VOICE_DOWNLOAD_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "addon",
    "globalPlugins",
    "sonata_tts_global_plugin",
    "voice_download.py",
)


def _extract_voice_info_regex():
    with open(_VOICE_DOWNLOAD_PATH, encoding="utf-8") as f:
        src = f.read()
    m = re.search(
        r"VOICE_INFO_REGEX\s*=\s*re\.compile\(\s*(.*?)\)\s*\n",
        src,
        re.DOTALL,
    )
    assert m, "VOICE_INFO_REGEX definition not found in voice_download.py"
    ns = {"re": re}
    exec(f"VOICE_INFO_REGEX = re.compile({m.group(1)})", ns)
    return ns["VOICE_INFO_REGEX"]


VOICE_INFO_REGEX = _extract_voice_info_regex()


class TestVoiceInfoRegexCanonical:
    """The standard HuggingFace piper-voices naming convention."""

    @pytest.mark.parametrize("stem,language,name,quality", [
        ("en_US-lessac-medium", "en_US", "lessac", "medium"),
        ("en_US-amy-medium", "en_US", "amy", "medium"),
        ("en_GB-southern_english_female-low", "en_GB", "southern_english_female", "low"),
        ("vi_VN-vivos-x_low", "vi_VN", "vivos", "x_low"),
        ("de_DE-thorsten-medium", "de_DE", "thorsten", "medium"),
    ])
    def test_parses_canonical_voice_name(self, stem, language, name, quality):
        m = VOICE_INFO_REGEX.match(stem)
        assert m is not None, f"Failed to parse {stem!r}"
        info = m.groupdict()
        assert info["language"] == language
        assert info["name"] == name
        assert info["quality"] == quality


class TestVoiceInfoRegexDigitsInName:
    """Regression: voices with digits in the name (e.g., MLS dataset speaker IDs).

    Originally reported as mush42/sonata-nvda#2 by @pitermach in 2023.
    """

    @pytest.mark.parametrize("stem,name", [
        ("pl_PL-mls_6892-low", "mls_6892"),
        ("fr_FR-mls_1840-low", "mls_1840"),
        ("nl_NL-mls_5809-low", "mls_5809"),
    ])
    def test_parses_mls_voice_with_digits(self, stem, name):
        m = VOICE_INFO_REGEX.match(stem)
        assert m is not None, f"Failed to parse {stem!r}"
        assert m.groupdict()["name"] == name


class TestVoiceInfoRegexRTVariant:
    """Voices with the +RT (real-time) suffix."""

    @pytest.mark.parametrize("stem,name", [
        ("en_US-amy+RT-medium", "amy+RT"),
        ("en_US-lessac+RT-medium", "lessac+RT"),
    ])
    def test_parses_rt_variant(self, stem, name):
        m = VOICE_INFO_REGEX.match(stem)
        assert m is not None, f"Failed to parse {stem!r}"
        assert m.groupdict()["name"] == name


class TestVoiceInfoRegexQuality:
    """All supported quality tiers."""

    @pytest.mark.parametrize("quality", ["high", "medium", "low", "x-low", "x_low"])
    def test_parses_quality(self, quality):
        stem = f"en_US-amy-{quality}"
        m = VOICE_INFO_REGEX.match(stem)
        assert m is not None, f"Failed to parse {stem!r}"
        assert m.groupdict()["quality"] == quality
