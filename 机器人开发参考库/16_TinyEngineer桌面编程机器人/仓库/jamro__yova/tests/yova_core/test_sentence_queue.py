"""Tests for the SentenceQueue class."""

import pytest
from unittest.mock import Mock
from yova_core.text2speech.sentence_queue import SentenceQueue, QueueItem, QueueItemStatus


class TestQueueItem:
    """Test cases for the QueueItem class."""

    def test_init_default(self):
        """Test QueueItem initialization with default parameters."""
        item = QueueItem("Hello world")
        
        assert item.text == "Hello world"
        assert item.priority_score == 0
        assert item.status == QueueItemStatus.FRESH
        assert item.error_message is None
        assert item.telemetry == {}
        assert item.playback is None

    def test_init_with_priority(self):
        """Test QueueItem initialization with custom priority."""
        item = QueueItem("High priority text", priority_score=5)
        
        assert item.text == "High priority text"
        assert item.priority_score == 5
        assert item.status == QueueItemStatus.FRESH


class TestSentenceQueue:
    """Test cases for the SentenceQueue class."""

    def test_init(self):
        """Test SentenceQueue initialization."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        assert queue.queue == []
        assert queue.logger is not None

    def test_append_sentence_default_priority(self):
        """Test appending sentence with default priority."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        queue.append_sentence("First sentence")
        
        assert len(queue.queue) == 1
        assert queue.queue[0].text == "First sentence"
        assert queue.queue[0].priority_score == 0
        assert queue.queue[0].status == QueueItemStatus.FRESH

    def test_append_sentence_with_priority(self):
        """Test appending sentence with custom priority."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        queue.append_sentence("High priority", priority_score=10)
        
        assert len(queue.queue) == 1
        assert queue.queue[0].text == "High priority"
        assert queue.queue[0].priority_score == 10

    def test_append_multiple_sentences(self):
        """Test appending multiple sentences with same priority."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        # Use same priority to keep all items in queue
        queue.append_sentence("First", 5)
        queue.append_sentence("Second", 5)
        queue.append_sentence("Third", 5)
        
        assert len(queue.queue) == 3
        assert queue.queue[0].text == "First"
        assert queue.queue[1].text == "Second"
        assert queue.queue[2].text == "Third"

    def test_clear(self):
        """Test clearing the queue."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        queue.append_sentence("First", 5)
        queue.append_sentence("Second", 5)
        
        assert len(queue.queue) == 2
        
        queue.clear()
        
        assert len(queue.queue) == 0
        assert queue.queue == []

    def test_filter_by_status_single_status(self):
        """Test filtering by a single status."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        queue.append_sentence("First", 5)
        queue.append_sentence("Second", 5)
        queue.append_sentence("Third", 5)
        
        # Change some statuses
        queue.queue[0].status = QueueItemStatus.READY_TO_PLAY
        queue.queue[1].status = QueueItemStatus.TTS_IN_PROGRESS
        queue.queue[2].status = QueueItemStatus.READY_TO_PLAY
        
        filtered = queue.filter_by_status([QueueItemStatus.READY_TO_PLAY])
        
        assert len(filtered) == 2
        assert filtered[0].text == "First"
        assert filtered[1].text == "Third"

    def test_filter_by_status_multiple_statuses(self):
        """Test filtering by multiple statuses."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        queue.append_sentence("First", 5)
        queue.append_sentence("Second", 5)
        queue.append_sentence("Third", 5)
        queue.append_sentence("Fourth", 5)
        
        queue.queue[0].status = QueueItemStatus.FRESH
        queue.queue[1].status = QueueItemStatus.TTS_IN_PROGRESS
        queue.queue[2].status = QueueItemStatus.READY_TO_PLAY
        queue.queue[3].status = QueueItemStatus.DONE
        
        filtered = queue.filter_by_status([QueueItemStatus.FRESH, QueueItemStatus.DONE])
        
        assert len(filtered) == 2
        assert filtered[0].text == "First"
        assert filtered[1].text == "Fourth"

    def test_filter_by_status_empty_result(self):
        """Test filtering when no items match."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        queue.append_sentence("First", 1)
        queue.queue[0].status = QueueItemStatus.FRESH
        
        filtered = queue.filter_by_status([QueueItemStatus.DONE])
        
        assert len(filtered) == 0
        assert filtered == []

    def test_length_by_status(self):
        """Test counting items by status."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        queue.append_sentence("First", 5)
        queue.append_sentence("Second", 5)
        queue.append_sentence("Third", 5)
        
        queue.queue[0].status = QueueItemStatus.READY_TO_PLAY
        queue.queue[1].status = QueueItemStatus.TTS_IN_PROGRESS
        queue.queue[2].status = QueueItemStatus.READY_TO_PLAY
        
        count = queue.length_by_status([QueueItemStatus.READY_TO_PLAY])
        
        assert count == 2

    def test_length_by_status_multiple(self):
        """Test counting items by multiple statuses."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        queue.append_sentence("First", 5)
        queue.append_sentence("Second", 5)
        queue.append_sentence("Third", 5)
        
        queue.queue[0].status = QueueItemStatus.FRESH
        queue.queue[1].status = QueueItemStatus.TTS_IN_PROGRESS
        queue.queue[2].status = QueueItemStatus.DONE
        
        count = queue.length_by_status([QueueItemStatus.FRESH, QueueItemStatus.DONE])
        
        assert count == 2

    def test_remove_by_status(self):
        """Test removing items by status."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        queue.append_sentence("First", 5)
        queue.append_sentence("Second", 5)
        queue.append_sentence("Third", 5)
        
        queue.queue[0].status = QueueItemStatus.FRESH
        queue.queue[1].status = QueueItemStatus.DONE
        queue.queue[2].status = QueueItemStatus.FRESH
        
        queue.remove_by_status([QueueItemStatus.DONE])
        
        assert len(queue.queue) == 2
        assert queue.queue[0].text == "First"
        assert queue.queue[1].text == "Third"

    def test_remove_by_status_multiple(self):
        """Test removing items by multiple statuses."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        queue.append_sentence("First", 5)
        queue.append_sentence("Second", 5)
        queue.append_sentence("Third", 5)
        queue.append_sentence("Fourth", 5)
        
        queue.queue[0].status = QueueItemStatus.FRESH
        queue.queue[1].status = QueueItemStatus.TTS_IN_PROGRESS
        queue.queue[2].status = QueueItemStatus.READY_TO_PLAY
        queue.queue[3].status = QueueItemStatus.DONE
        
        queue.remove_by_status([QueueItemStatus.TTS_IN_PROGRESS, QueueItemStatus.DONE])
        
        assert len(queue.queue) == 2
        assert queue.queue[0].text == "First"
        assert queue.queue[1].text == "Third"

    def test_remove_by_status_all(self):
        """Test removing all items."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        queue.append_sentence("First", 1)
        queue.append_sentence("Second", 2)
        
        queue.remove_by_status([QueueItemStatus.FRESH])
        
        assert len(queue.queue) == 0

    def test_get_by_status_found(self):
        """Test getting first item by status."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        queue.append_sentence("First", 5)
        queue.append_sentence("Second", 5)
        queue.append_sentence("Third", 5)
        
        queue.queue[0].status = QueueItemStatus.TTS_IN_PROGRESS
        queue.queue[1].status = QueueItemStatus.READY_TO_PLAY
        queue.queue[2].status = QueueItemStatus.READY_TO_PLAY
        
        item = queue.get_by_status([QueueItemStatus.READY_TO_PLAY])
        
        assert item is not None
        assert item.text == "Second"
        assert item.status == QueueItemStatus.READY_TO_PLAY

    def test_get_by_status_not_found(self):
        """Test getting item when no match exists."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        queue.append_sentence("First", 1)
        queue.queue[0].status = QueueItemStatus.FRESH
        
        item = queue.get_by_status([QueueItemStatus.DONE])
        
        assert item is None

    def test_get_by_status_empty_queue(self):
        """Test getting item from empty queue."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        item = queue.get_by_status([QueueItemStatus.FRESH])
        
        assert item is None

    def test_skip_low_priorities_empty_queue(self):
        """Test skip_low_priorities with empty queue."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        queue.skip_low_priorities()
        
        assert len(queue.queue) == 0

    def test_skip_low_priorities_single_item(self):
        """Test skip_low_priorities with single item."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        # Add sentence without triggering skip_low_priorities yet
        queue.queue.append(QueueItem("Only one", priority_score=5))
        queue.skip_low_priorities()
        
        assert len(queue.queue) == 1
        assert queue.queue[0].text == "Only one"

    def test_skip_low_priorities_keeps_highest(self):
        """Test that skip_low_priorities removes low priority items before the highest."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        # Manually add items to avoid triggering skip_low_priorities on append
        queue.queue.append(QueueItem("Low priority 1", priority_score=1))
        queue.queue.append(QueueItem("Low priority 2", priority_score=2))
        queue.queue.append(QueueItem("High priority", priority_score=10))
        queue.queue.append(QueueItem("Medium priority", priority_score=5))
        
        queue.skip_low_priorities()
        
        assert len(queue.queue) == 2
        assert queue.queue[0].text == "High priority"
        assert queue.queue[0].priority_score == 10
        assert queue.queue[1].text == "Medium priority"
        assert queue.queue[1].priority_score == 5

    def test_skip_low_priorities_first_occurrence(self):
        """Test that skip_low_priorities keeps from first occurrence of highest priority."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        # Manually add items
        queue.queue.append(QueueItem("Low 1", priority_score=1))
        queue.queue.append(QueueItem("High 1", priority_score=10))
        queue.queue.append(QueueItem("Medium", priority_score=5))
        queue.queue.append(QueueItem("High 2", priority_score=10))
        queue.queue.append(QueueItem("Low 2", priority_score=2))
        
        queue.skip_low_priorities()
        
        # Should keep from the first item with priority 10 onwards
        assert len(queue.queue) == 4
        assert queue.queue[0].text == "High 1"
        assert queue.queue[1].text == "Medium"
        assert queue.queue[2].text == "High 2"
        assert queue.queue[3].text == "Low 2"

    def test_skip_low_priorities_all_same_priority(self):
        """Test skip_low_priorities when all items have same priority."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        queue.queue.append(QueueItem("First", priority_score=5))
        queue.queue.append(QueueItem("Second", priority_score=5))
        queue.queue.append(QueueItem("Third", priority_score=5))
        
        queue.skip_low_priorities()
        
        # Should keep all items starting from first
        assert len(queue.queue) == 3
        assert queue.queue[0].text == "First"
        assert queue.queue[1].text == "Second"
        assert queue.queue[2].text == "Third"

    def test_append_sentence_triggers_skip_low_priorities(self):
        """Test that append_sentence automatically calls skip_low_priorities."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        # Add some low priority items first
        queue.queue.append(QueueItem("Low 1", priority_score=1))
        queue.queue.append(QueueItem("Low 2", priority_score=2))
        
        # Now append a high priority sentence which should trigger skip
        queue.append_sentence("High priority", priority_score=10)
        
        # The queue should only contain the high priority item
        assert len(queue.queue) == 1
        assert queue.queue[0].text == "High priority"
        assert queue.queue[0].priority_score == 10

    def test_complete_workflow(self):
        """Test complete workflow with different operations."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        # Add sentences
        queue.append_sentence("First", 5)
        queue.append_sentence("Second", 5)
        
        assert len(queue.queue) == 2
        
        # Change statuses
        queue.queue[0].status = QueueItemStatus.TTS_IN_PROGRESS
        queue.queue[1].status = QueueItemStatus.FRESH
        
        # Check statuses
        assert queue.length_by_status([QueueItemStatus.FRESH]) == 1
        assert queue.length_by_status([QueueItemStatus.TTS_IN_PROGRESS]) == 1
        
        # Get item by status
        fresh_item = queue.get_by_status([QueueItemStatus.FRESH])
        assert fresh_item.text == "Second"
        
        # Mark as done and remove
        queue.queue[0].status = QueueItemStatus.DONE
        queue.remove_by_status([QueueItemStatus.DONE])
        
        assert len(queue.queue) == 1
        assert queue.queue[0].text == "Second"

    def test_queue_item_status_enum(self):
        """Test QueueItemStatus enum values."""
        assert QueueItemStatus.FRESH.value == "fresh"
        assert QueueItemStatus.TTS_IN_PROGRESS.value == "tts_in_progress"
        assert QueueItemStatus.READY_TO_PLAY.value == "ready_to_play"
        assert QueueItemStatus.DONE.value == "done"
        assert QueueItemStatus.ERROR.value == "error"

    def test_queue_item_attributes_modification(self):
        """Test modifying QueueItem attributes."""
        item = QueueItem("Test text", priority_score=3)
        
        # Modify status
        item.status = QueueItemStatus.TTS_IN_PROGRESS
        assert item.status == QueueItemStatus.TTS_IN_PROGRESS
        
        # Set error
        item.status = QueueItemStatus.ERROR
        item.error_message = "Test error"
        assert item.error_message == "Test error"
        
        # Add telemetry
        item.telemetry["start_time"] = 123.45
        item.telemetry["end_time"] = 125.67
        assert item.telemetry["start_time"] == 123.45
        assert len(item.telemetry) == 2
        
        # Set playback
        mock_playback = Mock()
        item.playback = mock_playback
        assert item.playback == mock_playback

    def test_skip_low_priorities_with_zero_priority(self):
        """Test skip_low_priorities with zero and positive priorities."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        queue.queue.append(QueueItem("Zero priority", priority_score=0))
        queue.queue.append(QueueItem("Positive priority", priority_score=3))
        queue.queue.append(QueueItem("Another zero", priority_score=0))
        
        queue.skip_low_priorities()
        
        assert len(queue.queue) == 2
        assert queue.queue[0].text == "Positive priority"
        assert queue.queue[1].text == "Another zero"

    def test_skip_low_priorities_with_negative_priority(self):
        """Test skip_low_priorities with negative priorities."""
        logger = Mock()
        queue = SentenceQueue(logger)
        
        queue.queue.append(QueueItem("Negative", priority_score=-5))
        queue.queue.append(QueueItem("Zero", priority_score=0))
        queue.queue.append(QueueItem("Positive", priority_score=3))
        
        queue.skip_low_priorities()
        
        assert len(queue.queue) == 1
        assert queue.queue[0].text == "Positive"
        assert queue.queue[0].priority_score == 3

