import unittest
from unittest.mock import patch, MagicMock
import json
import os
import tempfile
from main import lambda_handler

# python3 -m unittest tests/test_main.py
class TestLambdaHandler(unittest.TestCase):
    def setUp(self):
        # テスト用の環境変数を設定
        os.environ['OPENAI_API_KEY'] = 'test-api-key'
        os.environ['API_BASE_URL'] = 'http://localhost:3000'
        
        # テスト用のS3イベントを作成
        self.test_event = {
            'Records': [{
                's3': {
                    'bucket': {
                        'name': 'test-bucket'
                    },
                    'object': {
                        'key': '123e4567-e89b-12d3-a456-426614174000-household123-20240315123456.jpg'
                    }
                }
            }]
        }

    @patch('boto3.client')
    @patch('openai.OpenAI')
    @patch('requests.post')
    def test_lambda_handler_success(self, mock_requests_post, mock_openai, mock_boto3):
        # S3クライアントのモック設定
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3

        # OpenAIクライアントのモック設定
        mock_openai_client = MagicMock()
        mock_openai.return_value = mock_openai_client
        
        # OpenAIのレスポンスをモック
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "items": [
                {"name": "テスト商品", "price": 100}
            ],
            "total": 100
        })
        mock_openai_client.chat.completions.create.return_value = mock_response

        # requests.postのモック設定
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_requests_post.return_value = mock_post_response

        # テスト実行
        result = lambda_handler(self.test_event, None)

        # アサーション
        self.assertIn('result', result)
        self.assertIsInstance(result['result'], str)
        
        # S3クライアントの呼び出し確認
        mock_s3.put_object_acl.assert_called_once()
        # S3のpublic URLがOpenAIに渡されているか確認
        called_args = mock_openai_client.chat.completions.create.call_args[1]
        image_url = called_args['messages'][0]['content'][1]['image_url']['url']
        self.assertEqual(
            image_url,
            f"https://{self.test_event['Records'][0]['s3']['bucket']['name']}.s3.amazonaws.com/{self.test_event['Records'][0]['s3']['object']['key']}"
        )
        # requests.postが呼ばれているか確認
        mock_requests_post.assert_called_once()

        # requests.postに渡されたjson（リクエストボディ）を検証
        called_kwargs = mock_requests_post.call_args[1]
        expected_payload = {
            "total": 100,
            "s3FilePath": "https://test-bucket.s3.amazonaws.com/123e4567-e89b-12d3-a456-426614174000-household123-20240315123456.jpg",
            "items": [
                {"name": "テスト商品", "price": 100}
            ]
        }
        self.assertEqual(called_kwargs["json"], expected_payload)

    @patch('boto3.client')
    def test_lambda_handler_s3_error(self, mock_boto3):
        # S3クライアントのモック設定（エラーを発生させる）
        mock_s3 = MagicMock()
        mock_s3.download_file.side_effect = Exception('S3 Error')
        mock_boto3.return_value = mock_s3

        # エラーが発生することを確認
        with self.assertRaises(Exception):
            lambda_handler(self.test_event, None)

    def test_lambda_handler_invalid_key_format(self):
        # 不正なキーフォーマットのイベントを作成
        invalid_event = {
            'Records': [{
                's3': {
                    'bucket': {
                        'name': 'test-bucket'
                    },
                    'object': {
                        'key': 'invalid-key-format.jpg'
                    }
                }
            }]
        }

        # エラーが発生することを確認
        with self.assertRaises(ValueError) as context:
            lambda_handler(invalid_event, None)
        
        self.assertIn('Invalid S3 key format', str(context.exception))

if __name__ == '__main__':
    unittest.main() 
