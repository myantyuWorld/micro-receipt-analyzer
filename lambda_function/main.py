import openai
import boto3
import os
import time
def lambda_handler(event, context):
    # S3イベントからバケット名・キー取得
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # 1. 追加されたファイルをpublic-readにする
    s3 = boto3.client('s3')
    s3.put_object_acl(Bucket=bucket, Key=key, ACL='public-read')

    # S3画像のパブリックURL生成
    region = os.environ.get('AWS_REGION', 'ap-southeast-1')
    image_url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"

    # 数秒まつ
    time.sleep(10)

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
    # TODO: /openai/receipt/analyze-result にPOSTリクエストして、結果を登録する
    # 
    return {"result": result} 
