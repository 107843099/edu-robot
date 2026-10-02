import json
import unittest

from gateway.app import ChatRequest, _extract_json_content, _mock_response


class GatewayContractTests(unittest.TestCase):
    def test_extract_json_bounds_device_contract(self):
        result = _extract_json_content('```json\n{"reply_text":"ok","action":99,"expression":-5,"repeat":9}\n```')
        self.assertEqual(result["action"], 18)
        self.assertEqual(result["expression"], -1)
        self.assertEqual(result["repeat"], 4)

    def test_extract_json_rejects_non_object(self):
        with self.assertRaises((ValueError, json.JSONDecodeError)):
            _extract_json_content('[1, 2, 3]')

    def test_mock_response_is_openai_compatible(self):
        request = ChatRequest(messages=[{"role": "user", "content": "你好"}])
        response = _mock_response(request)
        self.assertEqual(response["object"], "chat.completion")
        self.assertEqual(response["choices"][0]["message"]["role"], "assistant")


if __name__ == "__main__":
    unittest.main()
