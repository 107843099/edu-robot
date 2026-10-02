from openai import AsyncOpenAI
import re
import asyncio
from yova_shared import get_clean_logger, EventEmitter
from yova_core.text2speech.stream_playback import StreamPlayback
from yova_core.text2speech.data_playback import DataPlayback
from yova_core.text2speech.base64_playback import Base64Playback
from yova_core.cost_tracker import CostTracker
from yova_core.text2speech.text_buffer import TextBuffer
from yova_core.text2speech.sentence_queue import SentenceQueue, QueueItemStatus

class SpeechTask(EventEmitter):
    def __init__(self, message_id, api_key, logger, playback_config=None, cost_tracker=None):
        super().__init__(logger)
        self.message_id = message_id
        self.logger = get_clean_logger("speech_task", logger)
        
        self.api_key = api_key
        self.client = AsyncOpenAI(api_key=self.api_key)

        self.current_buffer = TextBuffer()
        self.sentence_queue = SentenceQueue(logger)
        self.audio_task = None
        self.conversion_task = None
        self.current_playback = None
        self.cost_tracker = cost_tracker or CostTracker(logger)
        
        # Use provided playback_config or default values
        if playback_config is not None:
            self.playback_config = playback_config
        else:
            self.playback_config = {
                "model": "gpt-4o-mini-tts",
                "voice": "coral",
                "speed": 1.25,
                "instructions": "Speak in a friendly, engaging tone."
            }
        
        self.is_stopped = False
        self.wait_time = 0.2

    async def append_chunk(self, text_chunk, priority_score=0):
        if self.is_stopped:
            return
        
        is_audio_chunk = text_chunk.startswith("data:audio/")
        
        self.logger.debug(f"Appending chunk: {text_chunk[:100]}...")
        if is_audio_chunk:
            # flush current buffer
            buffer_content = self.current_buffer.flush(require_full_sentence=False)
            if buffer_content:
                self.sentence_queue.append_sentence(buffer_content["text"], buffer_content["priority_score"])
                if not self.conversion_task:
                    self.conversion_task = asyncio.create_task(self.convert_to_speech())

            # add audio chunk to the queue
            self.sentence_queue.append_sentence(text_chunk, priority_score)
            if not self.conversion_task:
                self.conversion_task = asyncio.create_task(self.convert_to_speech())

        else:
            self.current_buffer.append(text_chunk, priority_score)
            buffer_content = self.current_buffer.flush(require_full_sentence=True)
        
            # Check if we have a complete sentence or enough content
            if buffer_content:
                self.sentence_queue.append_sentence(buffer_content["text"], buffer_content["priority_score"])
                if not self.conversion_task:
                    self.conversion_task = asyncio.create_task(self.convert_to_speech())

    async def convert_to_speech(self):
        self.logger.debug(f"Converting to speech...")
        while self.sentence_queue.length_by_status([QueueItemStatus.FRESH]) > 0 and not self.is_stopped:
            sentence_obj = self.sentence_queue.get_by_status([QueueItemStatus.FRESH])
            sentence_obj.status = QueueItemStatus.TTS_IN_PROGRESS
            text = sentence_obj.text
            priority_score = sentence_obj.priority_score

            self.logger.debug(f"Converting sentence (prio: {priority_score}): {text[:100]}...")
            sentence_obj.telemetry["convert_start_time"] = asyncio.get_event_loop().time()
            is_audio_chunk = text.startswith("data:audio/")

            try:
                audio_queue_length = self.sentence_queue.length_by_status([QueueItemStatus.READY_TO_PLAY])
                if is_audio_chunk:
                    self.logger.info(f"Creating Base64 audio playback")
                    playback = Base64Playback(self.logger, text)
                    sentence_obj.telemetry["load_start_time"] = asyncio.get_event_loop().time()
                    await playback.load()
                    sentence_obj.telemetry["load_end_time"] = asyncio.get_event_loop().time()
                    self.logger.debug(f"Base64 audio playback created")
                elif audio_queue_length == 0 and self.current_playback is None:
                    self.logger.info(f"Creating streaming response for text: {text[:100]}...")
                    playback = StreamPlayback(self.client, self.logger, text, self.playback_config, cost_tracker=self.cost_tracker)
                    sentence_obj.telemetry["load_start_time"] = asyncio.get_event_loop().time()
                    await playback.load()
                    sentence_obj.telemetry["load_end_time"] = asyncio.get_event_loop().time()
                    self.logger.debug(f"Streaming response created")
                else: # something is playing, we have time to load a non-streaming response and play it later without latency
                    wait_time = self.wait_time*audio_queue_length
                    self.logger.info(f"Waiting for streaming to finish: {wait_time}s")
                    await asyncio.sleep(wait_time)
                    self.logger.info(f"Creating non-streaming response for text: {text[:100]}...")
                    playback = DataPlayback(self.client, self.logger, text, self.playback_config, cost_tracker=self.cost_tracker)
                    sentence_obj.telemetry["load_start_time"] = asyncio.get_event_loop().time()
                    await playback.load()
                    sentence_obj.telemetry["load_end_time"] = asyncio.get_event_loop().time()
                    self.logger.debug(f"Non-streaming response created")
                
                sentence_obj.playback = playback
                sentence_obj.telemetry["create_time"] = asyncio.get_event_loop().time()
                sentence_obj.status = QueueItemStatus.READY_TO_PLAY
    
                if not self.audio_task:
                    self.logger.info(f"Creating audio task")
                    self.audio_task = asyncio.create_task(self.play_audio())
                else:
                    self.logger.debug(f"Audio task already exists")
                    
            except Exception as e:
                self.logger.error(f"Error in speech synthesis: {e}")
                sentence_obj.status = QueueItemStatus.ERROR
                sentence_obj.error_message = str(e)
                continue
        
        self.logger.debug(f"Conversion finished, setting conversion task to None")
        self.conversion_task = None

    async def play_audio(self):
        
        async def on_playback(data):
            self.logger.info(f"Playing audio: {data['text'][:100]}...")
            await self.emit_event("playing_audio", {"message_id": self.message_id, "text": data["text"]})

        self.logger.debug(f"Playing audio...")

        while self.sentence_queue.length_by_status([QueueItemStatus.READY_TO_PLAY]) > 0 and not self.is_stopped:
            item = self.sentence_queue.get_by_status([QueueItemStatus.READY_TO_PLAY])
            item.telemetry["pop_time"] = asyncio.get_event_loop().time()
            self.current_playback = item.playback
            self.current_playback.add_event_listener("playing_audio", on_playback)
            self.logger.debug(f"Playing audio: {item.text[:100]}...")
            item.telemetry["play_start_time"] = asyncio.get_event_loop().time()
            await self.current_playback.play()
            item.telemetry["play_end_time"] = asyncio.get_event_loop().time()
            self.logger.debug(f"Playback completed")
            item.status = QueueItemStatus.DONE
            self.current_playback = None
            
            self.logger.debug(f"Playback completed, audio queue: {self.sentence_queue.length_by_status([QueueItemStatus.READY_TO_PLAY])}")
            self.logger.debug(f"Playback Telemetry for {item.text[:100]}:")
            self.logger.debug(f" - type: {type(item.playback)}")
            for key, value in item.telemetry.items():
                self.logger.debug(f" - {key}: {round(1000*(value - item.telemetry['create_time']))}ms")
        
        self.logger.debug(f"Audio playback finished, setting audio task to None")
        self.sentence_queue.remove_by_status([QueueItemStatus.DONE])
        self.audio_task = None

    async def complete(self):
        self.logger.debug(f"Completing task: {self.current_buffer.get_text()}")
        if self.current_buffer.get_length() > 0:
            self.sentence_queue.append_sentence(self.current_buffer.get_text(), self.current_buffer.get_priority_score())
            if not self.conversion_task:
                self.conversion_task = asyncio.create_task(self.convert_to_speech())

        self.current_buffer.clear()
        
        # Wait for any pending conversion task to complete
        if self.conversion_task:
            try:
                await self.conversion_task
            except asyncio.CancelledError:
                self.logger.debug("Conversion task was cancelled during completion")
            except Exception as e:
                self.logger.error(f"Error completing conversion task: {e}")
            
        # Wait for any pending audio task to complete
        if self.audio_task:
            try:
                await self.audio_task
            except asyncio.CancelledError:
                self.logger.debug("Audio task was cancelled during completion")
            except Exception as e:
                self.logger.error(f"Error completing audio task: {e}")

    async def stop(self):
        self.logger.info(f"Stopping task: {self.current_buffer.get_text()}")
        
        # stop immediately
        self.sentence_queue.clear()
        self.is_stopped = True

        if self.current_playback:
            self.logger.info(f"Stopping current playback")
            await self.current_playback.stop()
            self.current_playback = None
        else:
            self.logger.info(f"No current playback to stop")

        if self.conversion_task:
            self.logger.info(f"Stopping conversion task")
            try:
                await self.conversion_task
            except asyncio.CancelledError:
                self.logger.debug("Conversion task was cancelled")
            except Exception as e:
                self.logger.error(f"Error stopping conversion task: {e}")
            self.conversion_task = None
        else:
            self.logger.info(f"No conversion task to stop")

        if self.audio_task:
            self.logger.info(f"Stopping audio task")
            try:
                await self.audio_task
            except asyncio.CancelledError:
                self.logger.debug("Audio task was cancelled")
            except Exception as e:
                self.logger.error(f"Error stopping audio task: {e}")
            self.audio_task = None
        else:
            self.logger.info(f"No audio task to stop")