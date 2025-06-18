import time
import json
from signal_api import receive_messages, send_signal_message
from zendesk import create_or_update_ticket, create_new_ticket

print("📬 Signal-to-Zendesk bridge started...")

# Main loop to receive messages from Signal and create Zendesk tickets
while True:
    messages = receive_messages()
    
    if messages:
        print("📩 Raw Signal response:")
        print(json.dumps(messages, indent=2))

        for msg in messages:
            envelope = msg.get("envelope", {})
            source = envelope.get("source")
            sourceNumber = envelope.get("sourceNumber")
            sourceName = envelope.get("sourceName")
            sourceUuid = envelope.get("sourceUuid")
            data_msg = envelope.get("dataMessage", {})
            message_text = data_msg.get("message")

            

            # Run if activity involves a non empty message from a user
            if source and message_text:
                
                # # Search for existing ticket by source UUID
                # print(f"🔎 Checking for existing ticket for source: {source} ({sourceName})")
                # existing_ticket = create_or_update_ticket(source, sourceName, f"[Signal Bridge] {message_text}", sourceUuid)
                # if existing_ticket:

                # If source is same as uuid, use sourceName instead
                print(f"⭐️ New message from user: {sourceName}")
                ticketNum = create_or_update_ticket(sourceNumber, sourceName, sourceUuid, f"[Signal Bridge] {message_text}") # !=> Remove [Signal Bridge] prefix after testing
                
                print(f"📑 Ticket #{ticketNum}")

                # Compose message for auto response to new ticket creation
                message = (
                    f"Ticket: {ticketNum} \n\n"
                    # f"Hello {sourceName},\n\n"
                    "This is an automated response to let you know we have received your message and an Edge agent will be accessing our Signal account soon to respond to any inquiries.\n\n"
                    "Please note: no messages here are shared with Zendesk managing system, keeping all communication private and encrypted by Signal."
                )


                if ticketNum != None:
                    print(f"📬 Sending new ticket confirmation message to {sourceName} - Ticket: {ticketNum}")
                    send_signal_message(sourceUuid, message)
                    
                    # If new ticket created:
                    # Wait for 30 seconds before sending the next message to avoid race condition caused by limitation of Zendesk API
                    time.sleep(30) 
            else:
                print("Non-message event, skipping.")
    else:
        print("🕒 No new messages.")
    # Frequency of checking for new messages
    time.sleep(1)
