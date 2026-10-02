"""
Main entry point for YOVA API n8n webhook connector.
"""

import asyncio

from yova_api_n8n.n8n_connector import N8nConnector
from yova_shared import get_clean_logger, get_config, setup_logging
from yova_shared.broker import Publisher, Subscriber


async def main():
    root_logger = setup_logging(level="INFO")
    logger = get_clean_logger("main", root_logger)

    n8n_cfg = get_config("n8n")
    webhook_url = (n8n_cfg.get("webhook_url") or "").strip()
    if not webhook_url:
        raise ValueError("n8n.webhook_url is not set in yova.config.json")

    api_connector = N8nConnector(logger)
    await api_connector.configure(n8n_cfg)

    publisher = Publisher()
    await publisher.connect()

    subscriber = Subscriber()
    await subscriber.connect()
    await subscriber.subscribe("yova.api.asr.result")

    async def onMessageChunk(chunk):
        try:
            await publisher.publish(
                "api_connector_n8n",
                "yova.api.tts.chunk",
                {
                    "id": chunk["id"],
                    "content": chunk["text"],
                    "priority_score": chunk["priority_score"],
                },
            )
        except Exception as e:
            logger.error(f"Failed to publish voice response chunk event: {e}")

    async def onMessageCompleted(full_response):
        try:
            await publisher.publish(
                "api_connector_n8n",
                "yova.api.tts.complete",
                {
                    "id": full_response["id"],
                    "content": full_response["text"],
                },
            )
        except Exception as e:
            logger.error(f"Failed to publish voice response completed event: {e}")

    async def onProcessingStarted(data):
        await publisher.publish(
            "api_connector_n8n",
            "yova.api.thinking.start",
            {"id": data["id"]},
        )

    async def onProcessingCompleted(data):
        await publisher.publish(
            "api_connector_n8n",
            "yova.api.thinking.stop",
            {"id": data["id"]},
        )

    api_connector.add_event_listener("message_chunk", onMessageChunk)
    api_connector.add_event_listener("message_completed", onMessageCompleted)
    api_connector.add_event_listener("processing_started", onProcessingStarted)
    api_connector.add_event_listener("processing_completed", onProcessingCompleted)

    await api_connector.connect()

    async def onVoiceCommandDetected(topic, message):
        data = message["data"]

        if data.get("voice_id") and data["voice_id"].get("user_id"):
            detected_user_id = str(data["voice_id"]["user_id"])
            prompt = f"""My name is {data['voice_id']['user_id']}.
            Respond to prompt below using the same language and mentioning my name if suitable:

            Prompt: {data['transcript']}
            """
        else:
            detected_user_id = "anonymous"
            prompt = data["transcript"]

        logger.info(f"Received voice command detection event: {data['transcript']}")

        try:
            await api_connector.send_message(prompt, session_id=detected_user_id)
        except Exception as e:
            logger.error(f"n8n connector error: {e}")
            try:
                await publisher.publish(
                    "api_connector_n8n",
                    "yova.api.error",
                    {"error": "n8n_webhook_failed", "details": str(e)},
                )
            except Exception as pub_e:
                logger.error(f"Failed to publish api error event: {pub_e}")

    asyncio.create_task(subscriber.listen(onVoiceCommandDetected))

    await asyncio.get_event_loop().run_in_executor(None, input)

    await publisher.close()
    await subscriber.close()
    await api_connector.close()


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
