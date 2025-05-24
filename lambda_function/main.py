import boto3

def parse_receipt(expense_documents):
    items = []
    total = None
    for doc in expense_documents:
        # 合計金額
        for field in doc.get('SummaryFields', []):
            if field.get('Type', {}).get('Text') == 'TOTAL':
                total = field.get('ValueDetection', {}).get('Text')
        # 商品ごとの明細
        for group in doc.get('LineItemGroups', []):
            for line_item in group.get('LineItems', []):
                item = {}
                for expense_field in line_item.get('LineItemExpenseFields', []):
                    field_type = expense_field.get('Type', {}).get('Text')
                    value = expense_field.get('ValueDetection', {}).get('Text')
                    if field_type == 'ITEM':
                        item['name'] = value
                    elif field_type == 'PRICE':
                        item['price'] = value
                    elif field_type == 'QUANTITY':
                        item['quantity'] = value
                if item:
                    items.append(item)
    return {'items': items, 'total': total}

def lambda_handler(event, context):
    # S3イベントからバケット名とキーを取得
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']

    textract = boto3.client('textract')
    response = textract.analyze_expense(
        Document={'S3Object': {'Bucket': bucket, 'Name': key}}
    )
    result = parse_receipt(response.get('ExpenseDocuments', []))
    print(result)
    return result 
