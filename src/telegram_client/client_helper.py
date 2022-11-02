from src.telegram_client.telegram_client import op_to_user_map, user_to_op_map

def operator_has_assigned(operator_id: int) -> bool:
    print(op_to_user_map)
    return operator_id in op_to_user_map

def user_has_been_assigned(user_id: int) -> bool:
    print(user_to_op_map)
    return user_id in user_to_op_map