import os
import unittest
from unittest.mock import Mock, patch

os.environ['INTERCOM_ACCESS_TOKEN'] = 'test-token'
os.environ['INTERCOM_ADMIN_ID'] = 'test-admin'

import intercom
import requests


class SearchHintTests(unittest.TestCase):
    def setUp(self):
        intercom._recent_conversations.clear()

    @patch('intercom.tag_conversation')
    @patch('intercom.requests.post')
    def test_creation_adds_user_hint_and_returns_same_id(self, post, tag):
        created = Mock()
        created.json.return_value = {'conversation_id': '123456'}
        post.side_effect = [created, Mock()]
        self.assertEqual(intercom.create_new_conversation('contact'), '123456')
        self.assertEqual(post.call_count, 2)
        self.assertEqual(post.call_args_list[0].args[0], 'https://api.intercom.io/conversations')
        self.assertEqual(post.call_args.kwargs['json'], {
            'message_type': 'comment', 'type': 'user', 'intercom_user_id': 'contact',
            'body': 'Search Signal for Conversation: 123456'
        })
        self.assertEqual(post.call_args.args[0], 'https://api.intercom.io/conversations/123456/reply')
        self.assertEqual(intercom._recent_conversations['contact'], '123456')
        tag.assert_called_once_with('123456', 'signal')

    @patch('intercom.tag_conversation')
    @patch('intercom.requests.post')
    def test_hint_failure_preserves_created_ticket_and_acknowledgment_id(self, post, tag):
        for failure in (requests.Timeout(), requests.HTTPError()):
            with self.subTest(failure=type(failure).__name__):
                created = Mock()
                created.json.return_value = {'conversation_id': '123456'}
                failed_response = Mock()
                failed_response.raise_for_status.side_effect = failure
                post.reset_mock()
                tag.reset_mock()
                post.side_effect = [created, failure if isinstance(failure, requests.Timeout) else failed_response]
                self.assertEqual(intercom.create_new_conversation('contact'), '123456')
                self.assertEqual(intercom._recent_conversations['contact'], '123456')
                self.assertEqual(post.call_count, 2)
                tag.assert_called_once_with('123456', 'signal')

    @patch('intercom.tag_conversation')
    @patch('intercom.requests.post')
    def test_no_hint_without_created_conversation_id(self, post, tag):
        post.return_value.json.return_value = {}
        self.assertIsNone(intercom.create_new_conversation('contact'))
        self.assertEqual(post.call_count, 1)
        tag.assert_not_called()

    @patch('intercom._add_signal_search_hint')
    @patch('intercom.requests.post')
    @patch('intercom._search_open_conversation', return_value='123456')
    @patch('intercom.find_or_create_contact', return_value='contact')
    def test_existing_conversation_does_not_repeat_hint(self, contact, search, post, hint):
        intercom.create_or_update_conversation('customer-uuid')
        hint.assert_not_called()
        post.assert_called_once()
        self.assertEqual(post.call_args.kwargs['json']['body'], 'New Signal message received')


if __name__ == '__main__':
    unittest.main()
