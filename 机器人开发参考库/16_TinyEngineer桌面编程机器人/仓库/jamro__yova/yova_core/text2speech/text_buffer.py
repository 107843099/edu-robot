import re


class TextBuffer:
    def __init__(self, min_chunk_length=15, sentence_endings = ['.', '!', '?', ':', ';']):
        self._buffer = ""
        self._priority_score = 0
        self._min_chunk_length = min_chunk_length
        self._sentence_endings = sentence_endings

    def get_length(self):
        return len(self.get_text())

    def get_text(self):
        return self._buffer.strip()

    def get_priority_score(self):
        return self._priority_score

    def clear(self):
        self._buffer = ""
        self._priority_score = 0

    def append(self, text, priority_score):
        self._buffer += self.clean_chunk(text)
        self._priority_score = max(self._priority_score, priority_score)

    def is_full_sentence(self):
        text = self.get_text()
        if len(text) < self._min_chunk_length or len(text) == 0:
            return False
        for ending in self._sentence_endings:
            if text.endswith(ending):
                return True
        return False

    def clean_chunk(self, text_chunk):
        # remove **
        text_chunk = re.sub(r'\*\*', '', text_chunk, flags=re.DOTALL)
        # remove ```
        text_chunk = re.sub(r'```.*?```', '', text_chunk, flags=re.DOTALL)
        # remove #+
        text_chunk = re.sub(r'#+', '', text_chunk)
        return text_chunk

    def flush(self, require_full_sentence=False):
      if (require_full_sentence and not self.is_full_sentence()):
        return None
      if (self.get_length() == 0):
        return None

      result = {"text": self.get_text(), "priority_score": self.get_priority_score()}
      self.clear()
      return result


