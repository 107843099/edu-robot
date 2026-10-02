from enum import Enum
from yova_shared import get_clean_logger

class QueueItemStatus(Enum):
    FRESH = "fresh"
    TTS_IN_PROGRESS = "tts_in_progress"
    READY_TO_PLAY = "ready_to_play"
    DONE = "done"
    ERROR = "error"


class QueueItem:
    def __init__(self, text, priority_score=0):
        self.text = text
        self.priority_score = priority_score
        self.status = QueueItemStatus.FRESH
        self.error_message = None
        self.telemetry = {}
        self.playback = None

class SentenceQueue:
    def __init__(self, logger):
        self.logger = get_clean_logger("sentence_queue", logger)
        self.queue = []

    def append_sentence(self, text, priority_score=0):
        self.logger.debug(f"Appending sentence: [p:{priority_score}] {text[:100]}...")
        self.queue.append(QueueItem(text, priority_score))
        self.skip_low_priorities()

    def length_by_status(self, status_list):
        return len(self.filter_by_status(status_list))

    def filter_by_status(self, status_list):
        return [item for item in self.queue if item.status in status_list]

    def remove_by_status(self, status_list):
        self.logger.debug(f"Removing by status: {status_list}")
        self.queue = [item for item in self.queue if item.status not in status_list]

    def get_by_status(self, status_list):
        filtered_queue = self.filter_by_status(status_list)
        if len(filtered_queue) == 0:
            return None
        return filtered_queue[0]

    def clear(self):
        self.logger.debug(f"Clearing queue")
        self.queue = []

    def skip_low_priorities(self):
        self.logger.debug(f"Filtering priority queue: {[[item.priority_score, item.text[:100]] for item in self.queue]}")
      
        if len(self.queue) == 0:
            return
            
        max_priority = max(item.priority_score for item in self.queue)
        
        # Find the first occurrence of the highest priority item
        first_max_priority_index = None
        for i, item in enumerate(self.queue):
            if item.priority_score == max_priority:
                first_max_priority_index = i
                break
        
        self.queue = self.queue[first_max_priority_index:]
        return
        