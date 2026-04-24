import time
import json
from signal_api import receive_messages, send_signal_message
from intercom import create_or_update_conversation

print("📬 Signal-to-Intercom bridge started...")

while True:
    messages = receive_messages()

    if messages:
        print("📩 Raw Signal response:")
        print(json.dumps(messages, indent=2))

        for msg in messages:
            envelope = msg.get("envelope", {})
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
                    f"Conversation: {conversationId} \n\n"
                    "This is an automated response to let you know we have received your message and an Edge agent will be accessing our Signal account soon to respond to any inquiries.\n\n"
                    "Please note: no messages here are shared with our ticket managing system, keeping all communication private and encrypted by Signal."
                )

                if conversationId is not None:
                    print(f"📬 Sending new conversation confirmation message to {sourceName} - Conversation: {conversationId}")
                    send_signal_message(sourceUuid, message)
            else:
                print("Non-message event, skipping.")
    else:
        print("🕒 No new messages.")
    time.sleep(1)
