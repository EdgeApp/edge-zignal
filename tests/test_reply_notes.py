import copy
import os
import unittest
from unittest.mock import Mock, patch

# Never load real credentials or contact external services in these tests.
os.environ['INTERCOM_ACCESS_TOKEN'] = 'test-token'
os.environ['INTERCOM_ADMIN_ID'] = 'test-admin'
os.environ['SIGNAL_BRIDGE_NUMBER'] = '+15550000000'

import intercom
import main
import reply_notes
import signal_api


def response(data, error=None):
    result = Mock()
    result.json.return_value = data
    result.raise_for_status.side_effect = error
    return result


class ReplyTests(unittest.TestCase):
    def setUp(self):
        reply_notes._recorded_replies.clear()
        self.event = {
            'sourceNumber': '+15550000000', 'sourceUuid': 'support-uuid', 'sourceDevice': 2,
            'syncMessage': {'sentMessage': {
                'destinationUuid': 'customer-uuid', 'timestamp': 2000,
                'message': 'Private reply text'
            }}
        }
        self.lookup = patch('reply_notes.resolve_device_name', return_value='jared-mac').start()
        self.note = patch('reply_notes.add_signal_response_note', return_value=True).start()
        self.addCleanup(patch.stopall)

    def test_reply_metadata_and_duplicate_suppression(self):
        reply_notes.record_sent_reply(self.event)
        reply_notes.record_sent_reply(self.event)
        self.lookup.assert_called_once_with(2, 2000)
        self.note.assert_called_once_with('customer-uuid', 'jared-mac')

    def test_attachment_only_reply(self):
        sent = self.event['syncMessage']['sentMessage']
        sent['message'] = None
        sent['attachments'] = [{'id': 'private-attachment'}]
        reply_notes.record_sent_reply(self.event)
        self.note.assert_called_once()

    def test_non_reply_events_are_ignored(self):
        events = [
            {'sourceNumber': '+15550000000', 'syncMessage': {'readMessages': [{}]}},
            {'dataMessage': {'message': 'Incoming message'}}
        ]
        for change in [
            {'groupInfo': {'groupId': 'group'}},
            {'destinationUuid': None}, {'destinationUuid': 'support-uuid'},
            {'timestamp': None}, {'message': None, 'reaction': {'emoji': '👍'}}
        ]:
            event = copy.deepcopy(self.event)
            event['syncMessage']['sentMessage'].update(change)
            events.append(event)
        event = copy.deepcopy(self.event)
        event['sourceNumber'] = '+15551111111'
        events.append(event)
        for event in events:
            reply_notes.record_sent_reply(event)
        self.lookup.assert_not_called()
        self.note.assert_not_called()

    def test_failure_does_not_crash_or_mark_reply_recorded(self):
        self.note.side_effect = [signal_api.requests.Timeout(), True]
        reply_notes.record_sent_reply(self.event)
        reply_notes.record_sent_reply(self.event)
        self.assertEqual(self.note.call_count, 2)

    def test_unknown_name_is_passed_to_note(self):
        self.lookup.return_value = None
        reply_notes.record_sent_reply(self.event)
        self.note.assert_called_once_with('customer-uuid', None)

    def test_sync_event_does_not_trigger_incoming_acknowledgment(self):
        with patch('main.receive_messages', return_value=[{'envelope': self.event}]), \
             patch('main.create_or_update_conversation') as incoming, \
             patch('main.send_signal_message') as send, \
             patch('main.time.sleep', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                main.main()
        self.note.assert_called_once()
        incoming.assert_not_called()
        send.assert_not_called()

    def test_incoming_message_still_creates_conversation_and_acknowledges(self):
        event = {'envelope': {'source': '+15551111111', 'sourceUuid': 'customer-uuid',
                              'dataMessage': {'message': 'Hello'}}}
        with patch('main.receive_messages', return_value=[event]), \
             patch('main.create_or_update_conversation', return_value='ticket') as incoming, \
             patch('main.send_signal_message') as send, \
             patch('main.time.sleep', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                main.main()
        incoming.assert_called_once_with('customer-uuid')
        self.assertEqual(send.call_args.args[0], 'customer-uuid')
        self.note.assert_not_called()


class DeviceTests(unittest.TestCase):
    @patch('signal_api.requests.get')
    def test_refreshes_name_after_relink_or_id_reuse(self, get):
        get.side_effect = [response([{'id': 2, 'name': 'jared-mac', 'creation_timestamp': 1000}]),
                           response([{'id': 2, 'name': 'other-mac', 'creation_timestamp': 3000}]),
                           response([{'id': 3, 'name': 'jared-mac', 'creation_timestamp': 3000}])]
        self.assertEqual(signal_api.resolve_device_name(2, 2000), 'jared-mac')
        self.assertIsNone(signal_api.resolve_device_name(2, 2000))
        self.assertEqual(signal_api.resolve_device_name(3, 4000), 'jared-mac')
        self.assertEqual(get.call_count, 3)
        self.assertTrue(get.call_args.args[0].endswith('/v1/devices/+15550000000'))

    @patch('signal_api.requests.get')
    def test_missing_or_unavailable_name_falls_back(self, get):
        for data in [[], {}, [{'id': 2, 'creation_timestamp': 1000}],
                     [{'id': 2, 'name': 'jared-mac'}]]:
            get.return_value = response(data)
            self.assertIsNone(signal_api.resolve_device_name(2, 2000))
        get.side_effect = signal_api.requests.Timeout()
        self.assertIsNone(signal_api.resolve_device_name(2, 2000))


class IntercomTests(unittest.TestCase):
    def setUp(self):
        intercom._recent_conversations.clear()

    @patch('intercom.requests.post')
    def test_note_author_recipient_privacy_and_html_escaping(self, post):
        post.side_effect = [response({'data': [{'id': 'contact'}]}),
                            response({'conversations': [{'id': 'ticket'}]}), response({})]
        self.assertTrue(intercom.add_signal_response_note('customer-uuid', 'jared-<mac>'))
        contact_query = post.call_args_list[0].kwargs['json']['query']
        self.assertEqual(contact_query['value'], intercom.hash_uuid('customer-uuid'))
        self.assertEqual(post.call_args.args[0], 'https://api.intercom.io/conversations/ticket/reply')
        self.assertEqual(post.call_args.kwargs['json'], {
            'message_type': 'note', 'type': 'admin', 'admin_id': 'test-admin',
            'body': '<p>Response sent in Signal by <b>jared-&lt;mac&gt;</b>.</p>'
        })

    @patch('intercom.requests.post')
    def test_missing_contact_does_not_create_contact_or_ticket(self, post):
        post.return_value = response({'data': []})
        self.assertFalse(intercom.add_signal_response_note('customer-uuid', 'jared-mac'))
        self.assertEqual(post.call_count, 1)

    @patch('intercom.requests.post')
    def test_missing_conversation_does_not_create_ticket(self, post):
        post.side_effect = [response({'data': [{'id': 'contact'}]}), response({'conversations': []})]
        self.assertFalse(intercom.add_signal_response_note('customer-uuid', 'jared-mac'))
        self.assertEqual(post.call_count, 2)

    @patch('intercom.requests.post')
    def test_index_lag_uses_recent_conversation_and_unknown_name(self, post):
        intercom._recent_conversations['contact'] = 'recent-ticket'
        post.side_effect = [response({'data': [{'id': 'contact'}]}), response({'conversations': []}), response({})]
        self.assertTrue(intercom.add_signal_response_note('customer-uuid', None))
        self.assertIn('/recent-ticket/reply', post.call_args.args[0])
        self.assertEqual(post.call_args.kwargs['json']['body'], '<p>Response sent in Signal by <b>unknown device</b>.</p>')

    @patch('intercom.requests.get')
    @patch('intercom.requests.post')
    def test_partial_index_lag_prefers_cached_ticket_only_while_open(self, post, get):
        intercom._recent_conversations['contact'] = 'new-ticket'
        for state, expected in [('open', 'new-ticket'), ('closed', 'old-ticket')]:
            with self.subTest(state=state):
                get.return_value = response({'state': state})
                get.return_value.status_code = 200
                post.side_effect = [response({'data': [{'id': 'contact'}]}),
                                    response({'conversations': [{'id': 'old-ticket'}]}),
                                    response({})]
                self.assertTrue(intercom.add_signal_response_note('customer-uuid', 'jared-mac'))
                self.assertIn(f'/{expected}/reply', post.call_args.args[0])

    @patch('intercom.requests.post')
    def test_api_failure_is_not_treated_as_success(self, post):
        post.return_value = response({}, signal_api.requests.HTTPError())
        with self.assertRaises(signal_api.requests.HTTPError):
            intercom.add_signal_response_note('customer-uuid', None)


if __name__ == '__main__':
    unittest.main()
