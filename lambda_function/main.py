import openai
import boto3
import os
import tempfile
from botocore.config import Config
import re
import requests
import json

def lambda_handler(event, context):
    # S3イベントからバケット名・キー取得
    bucket = event['Records'][0]['s3']['bucket']['name']
    # uuid-household_id-yyyyMMddHHmmss.jpg
    key = event['Records'][0]['s3']['object']['key']
    
    # household_idを抽出（正規表現で安全に）
    m = re.match(r"^[a-f0-9-]+-(.+?)-\d{14}\.jpg$", key)
    if m:
        household_id = m.group(1)
    else:
        raise ValueError(f"Invalid S3 key format: {key}. Expected format: uuid-household_id-yyyyMMddHHmmss.jpg")

    # S3クライアントの設定（タイムアウト対策）
    config = Config(
        connect_timeout=5,
        read_timeout=10,
        retries={'max_attempts': 3}
    )
    s3 = boto3.client('s3', config=config)

    # 1. 追加されたファイルをpublic-readにする
    s3.put_object_acl(Bucket=bucket, Key=key, ACL='public-read')

    # 2. S3のpublic URLを生成
    image_url = f"https://{bucket}.s3.amazonaws.com/{key}"

    # 新しいOpenAIクライアントの初期化
    client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

    # ChatGPT Vision APIにリクエスト
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "このレシート画像から、買った品物一覧(items)の名称(name)・値段(price)・合計金額(total)をJSONで抽出してください。"},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        max_tokens=1024
    )

    result = response.choices[0].message.content
    print(result)

    # 一時ファイルの削除処理は不要
    # os.unlink(temp_file.name)  # ← この行を削除

    # ```json
    # {
    # "items": [
    # {
    #     "name": "大根",
    #     "price": 105
    # }
    # ,
    # {
    #     "name": "たまねぎ",
    #     "price": 105
    # }
    # ,
    # {
    #     "name": "チョコパンBB",
    #     "price": 200
    # }
    # ,
    # {
    #     "name": "ISPポテトS",
    #     "price": 150
    # }
    # ,
    # {
    #     "name": "はさソーダ500ML",
    #     "price": 196
    # }
    # ,
    # {
    #     "name": "姫かま",
    #     "price": 150
    # }

    # ],
    # "discount": {
    # "percentage": 20,
    # "amount": -30
    # },
    # "total": 876
    # }
    # ```
    # 
    # 上記のような結果が得られたので、この結果を元に、バックエンド側にAPIリクエストして、結果を登録する
    # 

    # バックエンドのAPIエンドポイント
    api_url = f"{os.environ['API_BASE_URL']}/openai/{household_id}/receipt/result"
    
    # リクエストヘッダー
    headers = {
        "Content-Type": "application/json"
    }
    
    # リクエストボディ
    payload = {
        "total": json.loads(result)["total"],
        "s3FilePath": image_url,
        "items": [
            {
                "name": item["name"],
                "price": item["price"]
            }
            for item in json.loads(result)["items"]
        ]
    }
    
    # APIリクエストの送信
    response = requests.post(api_url, headers=headers, json=payload)
    
    # レスポンスの確認
    if response.status_code != 200:
        raise Exception(f"API request failed with status code: {response.status_code}")
    # 

    return {"result": result} 
