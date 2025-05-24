import pytest
from lambda_function.main import parse_receipt

def test_parse_receipt():
    sample_expense_documents = [
        {
            'SummaryFields': [
                {'Type': {'Text': 'TOTAL'}, 'ValueDetection': {'Text': '1234'}}
            ],
            'LineItemGroups': [
                {
                    'LineItems': [
                        {
                            'LineItemExpenseFields': [
                                {'Type': {'Text': 'ITEM'}, 'ValueDetection': {'Text': 'りんご'}},
                                {'Type': {'Text': 'PRICE'}, 'ValueDetection': {'Text': '100'}},
                                {'Type': {'Text': 'QUANTITY'}, 'ValueDetection': {'Text': '2'}},
                            ]
                        },
                        {
                            'LineItemExpenseFields': [
                                {'Type': {'Text': 'ITEM'}, 'ValueDetection': {'Text': 'バナナ'}},
                                {'Type': {'Text': 'PRICE'}, 'ValueDetection': {'Text': '150'}},
                                {'Type': {'Text': 'QUANTITY'}, 'ValueDetection': {'Text': '1'}},
                            ]
                        }
                    ]
                }
            ]
        }
    ]
    result = parse_receipt(sample_expense_documents)
    assert result['total'] == '1234'
    assert result['items'] == [
        {'name': 'りんご', 'price': '100', 'quantity': '2'},
        {'name': 'バナナ', 'price': '150', 'quantity': '1'}
    ] 
