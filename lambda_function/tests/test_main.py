import unittest
from unittest.mock import patch, MagicMock
import json
import os
import tempfile
from main import lambda_handler

class TestLambdaHandler(unittest.TestCase):
    def setUp(self):
        # テスト用の環境変数を設定
        os.environ['OPENAI_API_KEY'] = 'test-api-key'
        
        # テスト用のS3イベントを作成
        self.test_event = {
            'Records': [{
                's3': {
                    'bucket': {
                        'name': 'test-bucket'
                    },
                    'object': {
                        'key': 'test-image.jpg'
                    }
                }
            }]
        }

    @patch('boto3.client')
    @patch('openai.OpenAI')
    def test_lambda_handler_success(self, mock_openai, mock_boto3):
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

    @patch('boto3.client')
    def test_lambda_handler_s3_error(self, mock_boto3):
        # S3クライアントのモック設定（エラーを発生させる）
        mock_s3 = MagicMock()
        mock_s3.download_file.side_effect = Exception('S3 Error')
        mock_boto3.return_value = mock_s3

        # エラーが発生することを確認
        with self.assertRaises(Exception):
            lambda_handler(self.test_event, None)

if __name__ == '__main__':
    unittest.main() 
