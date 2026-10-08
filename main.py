import time
from signal_api import receive_messages, send_signal_message
from intercom import create_or_update_conversation
from reply_notes import record_sent_reply


def main():
    print("📬 Signal-to-Intercom bridge started...")

    while True:
        messages = receive_messages()

        if messages:
            for msg in messages:
                envelope = msg.get("envelope", {})
                if "syncMessage" in envelope:
                    record_sent_reply(envelope)
                    continue

                source = envelope.get("source")
                sourceName = envelope.get("sourceName")
                sourceUuid = envelope.get("sourceUuid")
                data_msg = envelope.get("dataMessage", {})
                message_text = data_msg.get("message")

                if source and message_text:
                    print(f"⭐️ New message from user: {sourceName}")
                    conversationId = create_or_update_conversation(sourceUuid)

                    print(f"📑 Conversation #{conversationId}")

                    message = (
                        "**💬 Thanks for contacting Edge!**\n\n"
                        "We’ve received your message. An Edge support agent will reply here on Signal.\n\n"
                        "*🔒 Your messages remain end-to-end encrypted in Signal. "
                        "Their contents are never copied to our support ticket system.*\n\n"
                        f"`Conversation: {conversationId}`"
                    )

                    if conversationId is not None:
                        print(f"📬 Sending new conversation confirmation message to {sourceName} - Conversation: {conversationId}")
                        send_signal_message(sourceUuid, message)
                else:
                    print("Non-message event, skipping.")
        else:
            print("🕒 No new messages.")
        time.sleep(1)


if __name__ == "__main__":
    main()
