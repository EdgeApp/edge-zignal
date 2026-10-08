"""Metadata-only notes for direct replies sent from linked Signal devices."""
from collections import OrderedDict

import requests

from intercom import add_signal_response_note
from signal_api import SIGNAL_BRIDGE_NUMBER, resolve_device_name

# Bound memory while suppressing repeated sync events within this process.
_recorded_replies = OrderedDict()
MAX_RECORDED_REPLIES = 10000


def record_sent_reply(envelope):
    sent = (envelope.get("syncMessage") or {}).get("sentMessage")
    if not isinstance(sent, dict):
        return
    # Only the support account's outgoing sync messages represent agent replies.
    sources = (envelope.get("source"), envelope.get("sourceNumber"), envelope.get("sourceUuid"))
    if not SIGNAL_BRIDGE_NUMBER or SIGNAL_BRIDGE_NUMBER not in sources:
        return
    recipient = sent.get("destinationUuid")
    timestamp = sent.get("timestamp")
    if not recipient or recipient == envelope.get("sourceUuid") or sent.get("groupInfo"):
        return
    if not isinstance(timestamp, int) or isinstance(timestamp, bool) or timestamp <= 0:
        return
    # Exclude receipts, reactions, deletes and other non-reply sync events.
    if not any(sent.get(field) for field in ("message", "attachments", "sticker", "contacts")):
        return
    key = (envelope.get("sourceDevice"), recipient, timestamp)
    if key in _recorded_replies:
        return
    name = resolve_device_name(envelope.get("sourceDevice"), timestamp)
    try:
        if not add_signal_response_note(recipient, name):
            return
    except (requests.RequestException, ValueError, KeyError):
        print("Failed to record Signal response note in Intercom.")
        return
    _recorded_replies[key] = None
    if len(_recorded_replies) > MAX_RECORDED_REPLIES:
        _recorded_replies.popitem(last=False)
