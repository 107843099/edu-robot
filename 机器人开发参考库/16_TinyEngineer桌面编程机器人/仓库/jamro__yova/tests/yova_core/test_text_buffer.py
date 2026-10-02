"""Tests for the TextBuffer class."""

import pytest
from yova_core.text2speech.text_buffer import TextBuffer


class TestTextBuffer:
    """Test cases for the TextBuffer class."""

    def test_init_default(self):
        """Test TextBuffer initialization with default parameters."""
        buffer = TextBuffer()
        
        assert buffer.get_text() == ""
        assert buffer.get_length() == 0
        assert buffer.get_priority_score() == 0
        assert buffer._min_chunk_length == 15
        assert buffer._sentence_endings == ['.', '!', '?', ':', ';']

    def test_init_custom_parameters(self):
        """Test TextBuffer initialization with custom parameters."""
        buffer = TextBuffer(min_chunk_length=20, sentence_endings=['.', '!'])
        
        assert buffer.get_text() == ""
        assert buffer.get_length() == 0
        assert buffer.get_priority_score() == 0
        assert buffer._min_chunk_length == 20
        assert buffer._sentence_endings == ['.', '!']

    def test_append_simple_text(self):
        """Test appending simple text."""
        buffer = TextBuffer()
        buffer.append("Hello world", 0)
        
        assert buffer.get_text() == "Hello world"
        assert buffer.get_length() == 11
        assert buffer.get_priority_score() == 0

    def test_append_multiple_times(self):
        """Test appending text multiple times."""
        buffer = TextBuffer()
        buffer.append("Hello ", 0)
        buffer.append("world", 0)
        buffer.append("!", 0)
        
        assert buffer.get_text() == "Hello world!"
        assert buffer.get_length() == 12

    def test_append_with_priority_score(self):
        """Test appending text with priority scores."""
        buffer = TextBuffer()
        buffer.append("Low priority", 2)
        
        assert buffer.get_priority_score() == 2
        
        buffer.append(" High priority", 5)
        assert buffer.get_priority_score() == 5  # Should use max priority
        
        buffer.append(" Lower priority", 3)
        assert buffer.get_priority_score() == 5  # Should still be max

    def test_clear(self):
        """Test clearing the buffer."""
        buffer = TextBuffer()
        buffer.append("Some text", 3)
        
        assert buffer.get_text() == "Some text"
        assert buffer.get_priority_score() == 3
        
        buffer.clear()
        
        assert buffer.get_text() == ""
        assert buffer.get_length() == 0
        assert buffer.get_priority_score() == 0

    def test_clean_chunk_remove_bold(self):
        """Test cleaning chunk removes ** for bold text."""
        buffer = TextBuffer()
        
        result = buffer.clean_chunk("Hello **world**!")
        assert result == "Hello world!"
        
        result = buffer.clean_chunk("**Bold** text **here**")
        assert result == "Bold text here"

    def test_clean_chunk_remove_code_blocks(self):
        """Test cleaning chunk removes ``` code blocks."""
        buffer = TextBuffer()
        
        result = buffer.clean_chunk("Here's code: ```print('hello')``` end")
        assert result == "Here's code:  end"
        
        result = buffer.clean_chunk("```code block``` text ```another```")
        assert result == " text "

    def test_clean_chunk_remove_headers(self):
        """Test cleaning chunk removes # headers."""
        buffer = TextBuffer()
        
        result = buffer.clean_chunk("## Header text")
        assert result == " Header text"
        
        result = buffer.clean_chunk("### Level 3 header")
        assert result == " Level 3 header"

    def test_clean_chunk_multiple_patterns(self):
        """Test cleaning chunk with multiple markdown patterns."""
        buffer = TextBuffer()
        
        result = buffer.clean_chunk("**Bold** ```code``` ### Header")
        assert result == "Bold   Header"

    def test_clean_chunk_empty_string(self):
        """Test cleaning empty string."""
        buffer = TextBuffer()
        
        result = buffer.clean_chunk("")
        assert result == ""

    def test_append_with_markdown_cleaning(self):
        """Test that append automatically cleans markdown."""
        buffer = TextBuffer()
        buffer.append("**Bold** text", 0)
        
        assert buffer.get_text() == "Bold text"

    def test_is_full_sentence_with_period(self):
        """Test is_full_sentence with period ending."""
        buffer = TextBuffer()
        buffer.append("This is a complete sentence.", 0)
        
        assert buffer.is_full_sentence() is True

    def test_is_full_sentence_with_exclamation(self):
        """Test is_full_sentence with exclamation mark."""
        buffer = TextBuffer()
        buffer.append("This is exciting!", 0)
        
        assert buffer.is_full_sentence() is True

    def test_is_full_sentence_with_question(self):
        """Test is_full_sentence with question mark."""
        buffer = TextBuffer()
        buffer.append("Is this a question?", 0)
        
        assert buffer.is_full_sentence() is True

    def test_is_full_sentence_with_colon(self):
        """Test is_full_sentence with colon."""
        buffer = TextBuffer()
        buffer.append("Here's a longer list:", 0)
        
        assert buffer.is_full_sentence() is True

    def test_is_full_sentence_with_semicolon(self):
        """Test is_full_sentence with semicolon."""
        buffer = TextBuffer()
        buffer.append("First part; second part;", 0)
        
        assert buffer.is_full_sentence() is True

    def test_is_full_sentence_incomplete(self):
        """Test is_full_sentence with incomplete sentence."""
        buffer = TextBuffer()
        buffer.append("This is incomplete", 0)
        
        assert buffer.is_full_sentence() is False

    def test_is_full_sentence_too_short(self):
        """Test is_full_sentence with text shorter than min_chunk_length."""
        buffer = TextBuffer()
        buffer.append("Short.", 0)
        
        # Default min_chunk_length is 15
        assert buffer.is_full_sentence() is False

    def test_is_full_sentence_empty(self):
        """Test is_full_sentence with empty buffer."""
        buffer = TextBuffer()
        
        assert buffer.is_full_sentence() is False

    def test_is_full_sentence_custom_min_length(self):
        """Test is_full_sentence with custom min_chunk_length."""
        buffer = TextBuffer(min_chunk_length=5)
        buffer.append("Short.", 0)
        
        assert buffer.is_full_sentence() is True

    def test_flush_with_full_sentence_required(self):
        """Test flush when full sentence is required."""
        buffer = TextBuffer()
        buffer.append("This is a complete sentence.", 3)
        
        result = buffer.flush(require_full_sentence=True)
        
        assert result == {"text": "This is a complete sentence.", "priority_score": 3}
        assert buffer.get_text() == ""
        assert buffer.get_priority_score() == 0

    def test_flush_incomplete_sentence_when_required(self):
        """Test flush with incomplete sentence when full sentence is required."""
        buffer = TextBuffer()
        buffer.append("Incomplete", 2)
        
        result = buffer.flush(require_full_sentence=True)
        
        assert result is None
        # Buffer should not be cleared
        assert buffer.get_text() == "Incomplete"
        assert buffer.get_priority_score() == 2

    def test_flush_without_full_sentence_requirement(self):
        """Test flush without requiring full sentence."""
        buffer = TextBuffer()
        buffer.append("Incomplete", 2)
        
        result = buffer.flush(require_full_sentence=False)
        
        assert result == {"text": "Incomplete", "priority_score": 2}
        assert buffer.get_text() == ""
        assert buffer.get_priority_score() == 0

    def test_flush_empty_buffer(self):
        """Test flush with empty buffer."""
        buffer = TextBuffer()
        
        result = buffer.flush(require_full_sentence=False)
        assert result is None
        
        result = buffer.flush(require_full_sentence=True)
        assert result is None

    def test_flush_multiple_times(self):
        """Test flushing multiple times."""
        buffer = TextBuffer()
        
        buffer.append("First sentence.", 1)
        result1 = buffer.flush(require_full_sentence=True)
        assert result1 == {"text": "First sentence.", "priority_score": 1}
        assert buffer.get_text() == ""
        
        buffer.append("Second sentence.", 2)
        result2 = buffer.flush(require_full_sentence=True)
        assert result2 == {"text": "Second sentence.", "priority_score": 2}
        assert buffer.get_text() == ""

    def test_get_length_with_various_content(self):
        """Test get_length returns correct length."""
        buffer = TextBuffer()
        
        assert buffer.get_length() == 0
        
        buffer.append("Hello", 0)
        assert buffer.get_length() == 5
        
        buffer.append(" world", 0)
        assert buffer.get_length() == 11

    def test_priority_score_tracking(self):
        """Test priority score always uses maximum value."""
        buffer = TextBuffer()
        
        buffer.append("Text 1", 5)
        assert buffer.get_priority_score() == 5
        
        buffer.append("Text 2", 3)
        assert buffer.get_priority_score() == 5
        
        buffer.append("Text 3", 8)
        assert buffer.get_priority_score() == 8
        
        buffer.append("Text 4", 1)
        assert buffer.get_priority_score() == 8

    def test_complete_workflow(self):
        """Test complete workflow: append, check, flush, repeat."""
        buffer = TextBuffer()
        
        # Add incomplete text
        buffer.append("Hello", 1)
        assert buffer.is_full_sentence() is False
        assert buffer.flush(require_full_sentence=True) is None
        
        # Complete the sentence
        buffer.append(" there world.", 2)
        assert buffer.is_full_sentence() is True
        assert buffer.get_priority_score() == 2
        
        # Flush it
        result = buffer.flush(require_full_sentence=True)
        assert result == {"text": "Hello there world.", "priority_score": 2}
        assert buffer.get_text() == ""
        
        # Start new sentence
        buffer.append("This is next sentence.", 3)
        result = buffer.flush(require_full_sentence=True)
        assert result == {"text": "This is next sentence.", "priority_score": 3}

    def test_custom_sentence_endings(self):
        """Test with custom sentence endings."""
        buffer = TextBuffer(sentence_endings=['.', '!'])
        
        buffer.append("Ends with period.", 0)
        assert buffer.is_full_sentence() is True
        
        buffer.clear()
        buffer.append("Ends with exclamation!", 0)
        assert buffer.is_full_sentence() is True
        
        buffer.clear()
        buffer.append("Ends with question?", 0)
        assert buffer.is_full_sentence() is False  # ? not in custom endings
        
        buffer.clear()
        buffer.append("Ends with colon:", 0)
        assert buffer.is_full_sentence() is False  # : not in custom endings

