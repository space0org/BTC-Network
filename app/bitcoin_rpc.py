from bitcoinrpc.authproxy import AuthServiceProxy

def get_rpc_connection():
    rpc_user = "bitcoin"
    rpc_password = "bitcoin"
    rpc_host = "3.107.165.86"
    rpc_port = "18332"
    return AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}")
