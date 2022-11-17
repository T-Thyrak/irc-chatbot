from src.errors import ValidationError

def type_valid(type: str) -> str:
    valid = type in [
        'Bug',
        'Improvement',
    ]
    
    if not valid:
        raise ValidationError('Invalid feedback type')
    
    return type
    
def status_valid(status: str) -> str:
    valid = status in [
        'Received',
        'Processing',
        'Ignored',
        'Implemented',
    ]
    
    if not valid:
        raise ValidationError('Invalid feedback status')
    
    return status
    
def selector_valid(selector: str) -> str:
    valid = True
    
    sl = selector.split(',')
    for s in sl:
        s = s.lower()
        if s != '*' \
            and s != 'id' \
            and s != 'sender_psid' \
            and s != 'name' \
            and s != 'feedback_type' \
            and s != 'message' \
            and s != 'feedback_status' \
            and s != 'created_at':
            valid = False
    
    if not valid:
        raise ValidationError('Invalid selector')
    
    return selector
            
def parse_selector(selector: str) -> list[str]:
    sl = selector.split(',')
    if '*' in sl:
        return [
            'id',
            'sender_psid',
            'name',
            'feedback_type',
            'message',
            'feedback_status',
            'created_at',
        ]
    else:
        return sl