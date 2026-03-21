from __future__ import annotations

from scriptlib.fnmatchplus import match, match_any


class TestMatch:
    def test_should_return_false_when_no_patterns(self):
        matched, excluded = match("file.txt", [])
        assert matched is False
        assert excluded is False

    def test_should_match_single_allowed_pattern(self):
        matched, excluded = match("file.txt", [("*.txt", False)])
        assert matched is True
        assert excluded is False

    def test_should_match_single_excluded_pattern(self):
        matched, excluded = match("file.txt", [("*.txt", True)])
        assert matched is True
        assert excluded is True

    def test_should_not_match_when_no_pattern_matches(self):
        matched, excluded = match("file.txt", [("*.jpg", False)])
        assert matched is False
        assert excluded is False

    def test_should_respect_last_match_wins(self):
        matched, excluded = match("file.txt", [("*.txt", True), ("*.txt", False)])
        assert matched is True
        assert excluded is False

    def test_should_support_glob_patterns(self):
        patterns = [("*.jpg", False), ("*.png", False), ("*.gif", False)]
        assert match("photo.jpg", patterns) == (True, False)
        assert match("photo.png", patterns) == (True, False)
        assert match("photo.gif", patterns) == (True, False)
        assert match("photo.bmp", patterns) == (False, False)

    def test_should_support_question_mark(self):
        matched, excluded = match("file.txt", [("file.???", False)])
        assert matched is True
        assert excluded is False

    def test_should_support_character_class(self):
        matched, excluded = match("file1.txt", [("file[123].txt", False)])
        assert matched is True
        assert excluded is False

    def test_should_support_negation_pattern(self):
        matched, excluded = match("thumb.jpg", [("*.jpg", False), ("thumb*", True)])
        assert matched is True
        assert excluded is True

    def test_should_handle_complex_patterns(self):
        patterns = [("/dev/sd*", False), ("/dev/nvme*", True)]
        assert match("/dev/sda1", patterns) == (True, False)
        assert match("/dev/sdb2", patterns) == (True, False)
        assert match("/dev/nvme0n1", patterns) == (True, True)
        assert match("/dev/vda1", patterns) == (False, False)


class TestMatchAny:
    def test_should_return_true_for_allowed_match(self):
        assert match_any("file.jpg", [("*.jpg", False)]) is True

    def test_should_return_false_for_excluded_match(self):
        assert match_any("thumb.jpg", [("*.jpg", False), ("thumb*", True)]) is False

    def test_should_return_false_for_no_match(self):
        assert match_any("file.txt", [("*.jpg", False)]) is False

    def test_should_return_false_for_empty_patterns(self):
        assert match_any("file.txt", []) is False

    def test_should_return_true_when_multiple_allowed_patterns(self):
        assert match_any("photo.png", [("*.jpg", False), ("*.png", False)]) is True

    def test_should_return_false_when_all_excluded(self):
        assert match_any("thumb.jpg", [("*.jpg", True)]) is False
