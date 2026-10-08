import os
import unittest
from unittest.mock import patch

os.environ['INTERCOM_ACCESS_TOKEN'] = 'test-token'
os.environ['INTERCOM_ADMIN_ID'] = 'test-admin'

import intercom


class IncomingReplyTests(unittest.TestCase):
    @patch('intercom.requests.post')
    @patch('intercom._search_open_conversation', return_value='ticket')
    @patch('intercom.find_or_create_contact', return_value='contact')
    def test_followup_incoming_message_is_a_user_reply(self, find_contact, search, post):
        # Existing conversations must not trigger another Signal acknowledgment.
        self.assertIsNone(intercom.create_or_update_conversation('customer-uuid'))
        find_contact.assert_called_once_with('customer-uuid')
        search.assert_called_once_with('contact')
        post.assert_called_once()
        self.assertEqual(post.call_args.args[0], 'https://api.intercom.io/conversations/ticket/reply')
        payload = post.call_args.kwargs['json']
        self.assertEqual(payload['message_type'], 'comment')
        self.assertEqual(payload['type'], 'user')
        self.assertEqual(payload['intercom_user_id'], 'contact')
        self.assertNotIn('admin_id', payload)



if __name__ == '__main__':
    unittest.main()
