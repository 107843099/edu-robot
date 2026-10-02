from yova_client_dev_tools.ui import YovaDevToolsUI
from yova_shared.broker.subscriber import Subscriber
from yova_client_dev_tools.profiler import Profiler
from yova_shared.broker.publisher import Publisher
import uuid
import os
import asyncio
import base64

answer = ''
input_timestamp = None
answer_timestamp = None
chunk_counter = 0

async def push_to_talk_changed_callback(event_data):
    """Callback for push-to-talk change events - publishes to broker"""

    publisher = Publisher()
    try:
        await publisher.connect()
        
        await publisher.publish("dev_tools", "yova.core.input.state", {
            "active": event_data["is_active"]
        })
            
    except Exception as e:
        print(f"Failed to publish to broker: {e}")
    finally:
        await publisher.close()

async def test_question_callback(event_data):
    """Callback for test question events - publishes to broker"""
    publisher = Publisher()
    await publisher.connect()
    await publisher.publish("dev_tools", "yova.api.asr.result", {
        "id": str(uuid.uuid4()),
        "transcript": "Jaka jest stolica Polski?",
        "voice_id": {
          "user_id": None,
          "similarity": None,
          "confidence_level": None,
          "embedding": None
        }
    })


async def test_answer_callback(event_data):
    """Callback for test answer events - publishes to broker"""
    publisher = Publisher()
    message_id = str(uuid.uuid4())
    await publisher.connect()

    async def say(content, priority_score, delay=0.5):
        await asyncio.sleep(delay)
        await publisher.publish("dev_tools", "yova.api.tts.chunk", {
            "id": message_id,
            "content": content,
            "priority_score": priority_score
        })
    
    hmmm_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "yova_shared", "assets", "hmmm_nova_1.wav")
    with open(hmmm_file_path, "rb") as hmmm_file:
        hmmm_data = hmmm_file.read()

    base64_encoded = base64.b64encode(hmmm_data)
    base64_string = base64_encoded.decode('utf-8')
    data_url = f"data:audio/wav;base64,{base64_string}"

    await publisher.publish("dev_tools", "yova.api.tts.chunk", {
        "id": message_id,
        "content": data_url,
        "priority_score": 1
    })

    await say("No dobra, zastanówmy się nad tym...", 1)
    await say("Zróbmy to krok po kroku.", 1)
    await say("Sprawdzę Twój kalendarz na jutro.", 50)
    await say("Zerknę do kalendarza.", 1)
    await say("Sprawdzę pogodę jaka będzie jutro.", 50)
    await say("Zerknę do pogody.", 1)
    await say("Podsumujmy to.", 50)
    await say("Pogoda podczas Twojego pierwszego wystąpienia będzie dobra.", 100)
    await say("Będzie słonecznie.", 100)
    await say("Temperature około 20 stopni.", 100)

    await asyncio.sleep(0.5)
    await publisher.publish("dev_tools", "yova.api.tts.complete", {
        "id": message_id,
        "content": "No dobra, zaczynamy! Ok, teraz już wiem. Mozna zacząć!",
    })

async def test_error_callback(event_data):
    publisher = Publisher()
    await publisher.connect()
    await publisher.publish("dev_tools", "yova.core.error", {
        "error": "Test error",
        "details": "Test error details"
    })

async def subscribe_to_updates(ui):
    global answer, chunk_counter
    async def on_message(topic, message):
        data = message['data']
        global answer, chunk_counter
        
        # yova.core.state.change ========================================================================
        if topic == "yova.core.state.change":
            ui.set_state(data['new_state'])
            ui.loop.draw_screen()

        # yova.api.asr.result ================================================================
        if topic == "yova.api.asr.result":
            ui.set_question(data['transcript'])
            answer = ""
            ui.set_answer(answer)
            ui.loop.draw_screen()

        # yova.api.tts.chunk ================================================================
        if topic == "yova.api.tts.chunk":
            answer += f"[{data['priority_score']}] {data['content']}"
            chunk_counter += 1
            ui.set_answer(answer[:100] + "...")
            ui.loop.draw_screen()

        # yova.api.tts.complete ================================================================
        if topic == "yova.api.tts.complete":
            answer = data['content']
            chunk_counter = 0
            ui.set_answer(answer[:100] + "...")
            ui.loop.draw_screen()

        # yova.*.error ================================================================
        if topic == "yova.core.error" or topic == "yova.api.error":
            ui.set_error_message(data['error'])
            ui.loop.draw_screen()

    subsciber = Subscriber()
    await subsciber.connect()
    await subsciber.subscribe_all([
        "yova"
    ])
    asyncio.create_task(subsciber.listen(on_message))
    
def main():
    """Main entry point for the YOVA Development Tools UI."""
    ui = YovaDevToolsUI()
    profiler = Profiler(ui)
    ui.add_event_listener("push_to_talk_changed", push_to_talk_changed_callback)
    ui.add_event_listener("test_command", test_answer_callback)
    ui.add_event_listener("test_error", test_error_callback)
    ui.set_state("Unknown")

    asyncio.ensure_future(profiler.start())
    asyncio.ensure_future(subscribe_to_updates(ui))

    ui.run()

def run():
    """Synchronous wrapper for the main function."""
    main()

if __name__ == "__main__":
    run()
