from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .bitcoin_rpc import get_rpc_connection
from typing import List, Dict, Any

app = FastAPI(title="BSV Block Explorer")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bsv-fork-setup-b3rqnweh.devinapps.com", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/api/blocks/latest")
async def get_latest_block() -> Dict[str, Any]:
    try:
        rpc = get_rpc_connection()
        block_count = rpc.getblockcount()
        block_hash = rpc.getblockhash(block_count)
        block = rpc.getblock(block_hash)
        return {
            "height": block_count,
            "hash": block_hash,
            "difficulty": block["difficulty"],
            "size": block["size"],
            "time": block["time"],
            "transactions": len(block["tx"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/blocks/{height}")
async def get_block(height: int) -> Dict[str, Any]:
    try:
        rpc = get_rpc_connection()
        block_hash = rpc.getblockhash(height)
        block = rpc.getblock(block_hash)
        return block
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Block {height} not found")

@app.get("/api/transactions/{txid}")
async def get_transaction(txid: str) -> Dict[str, Any]:
    try:
        rpc = get_rpc_connection()
        tx = rpc.getrawtransaction(txid, 1)
        return tx
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Transaction {txid} not found")

@app.get("/api/transactions/mempool")
async def get_mempool() -> Dict[str, List[Dict[str, Any]]]:
    try:
        rpc = get_rpc_connection()
        mempool_txids = rpc.getrawmempool()
        transactions = []
        for txid in mempool_txids[:10]:  # Limit to 10 most recent
            try:
                tx = rpc.getrawtransaction(txid, 1)
                transactions.append({
                    "txid": txid,
                    "time": tx.get("time", 0),
                    "amount": sum(vout["value"] for vout in tx.get("vout", [])),
                    "fee": 0.00001,  # Placeholder fee
                    "confirmations": 0
                })
            except Exception:
                continue
        return {"transactions": transactions}
    except Exception:
        # Return empty list instead of error for empty mempool
        return {"transactions": []}

@app.get("/api/address/{address}")
async def get_address_info(address: str) -> Dict[str, Any]:
    try:
        rpc = get_rpc_connection()
        # Get unspent transactions
        utxos = rpc.listunspent(0, 9999999, [address])
        
        # Calculate balance from UTXOs
        balance = sum(utxo["amount"] for utxo in utxos)
        
        # Get received transactions
        received_by_address = rpc.listreceivedbyaddress(0, True)
        address_info = next((entry for entry in received_by_address if entry["address"] == address), None)
        
        if address_info is None:
            return {
                "address": address,
                "balance": balance,
                "utxos": utxos,
                "transactions": []
            }
            
        return {
            "address": address,
            "balance": balance,
            "utxos": utxos,
            "transactions": address_info.get("txids", [])
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error fetching address info: {str(e)}")

@app.get("/api/network/info")
async def get_network_info() -> Dict[str, Any]:
    try:
        rpc = get_rpc_connection()
        info = rpc.getnetworkinfo()
        peers = rpc.getpeerinfo()
        blockchain_info = rpc.getblockchaininfo()
        return {
            "connections": info["connections"],
            "peers": peers,
            "blocks": blockchain_info["blocks"],
            "difficulty": blockchain_info["difficulty"],
            "chain": blockchain_info["chain"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
