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
        mempool_txids = {}
        try:
            raw_mempool = rpc.getrawmempool()
            for txid in raw_mempool:
                try:
                    info = rpc.getmempoolentry(txid)
                    mempool_txids[txid] = info
                except:
                    continue
        except Exception:
            return {"transactions": []}
        transactions = []
        
        # Sort by time, newest first
        sorted_txids = sorted(mempool_txids.items(), key=lambda x: x[1].get('time', 0), reverse=True)
        
        for txid, info in sorted_txids[:10]:  # Limit to 10 most recent
            try:
                tx = rpc.getrawtransaction(txid, 1)
                
                # Calculate total input value
                input_value = 0
                for vin in tx.get("vin", []):
                    try:
                        prev_tx = rpc.getrawtransaction(vin["txid"], 1)
                        input_value += prev_tx["vout"][vin["vout"]]["value"]
                    except Exception:
                        continue
                
                # Calculate output value and fee
                output_value = sum(vout["value"] for vout in tx.get("vout", []))
                fee = input_value - output_value if input_value > 0 else 0
                
                transactions.append({
                    "txid": txid,
                    "time": tx.get("time", 0),
                    "size": info.get("size", 0),
                    "vsize": info.get("vsize", 0),
                    "amount": output_value,
                    "fee": fee,
                    "fee_per_byte": fee / info.get("size", 1) if fee > 0 else 0,
                    "confirmations": 0,
                    "input_count": len(tx.get("vin", [])),
                    "output_count": len(tx.get("vout", [])),
                })
            except Exception:
                continue
                
        return {"transactions": transactions}
    except Exception:
        # Return empty list instead of error for empty mempool
        return {"transactions": []}

@app.get("/api/address/{address}")
async def get_address_info(address: str, page: int = 1, limit: int = 10) -> Dict[str, Any]:
    try:
        rpc = get_rpc_connection()
        # Handle different address formats
        try:
            # Validate the address
            validate_result = rpc.validateaddress(address)
            if not validate_result.get("isvalid", False):
                raise HTTPException(status_code=400, detail=f"Invalid address format: {address}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error validating address: {str(e)}")
        
        # Get unspent transactions
        utxos = rpc.listunspent(0, 9999999, [address])
        
        # Calculate balance from UTXOs
        balance = sum(utxo["amount"] for utxo in utxos)
        
        # Get received transactions
        received_by_address = rpc.listreceivedbyaddress(0, True)
        address_info = next((entry for entry in received_by_address if entry["address"] == address), None)
        
        # Get transaction details
        txids = address_info.get("txids", []) if address_info else []
        total_txs = len(txids)
        
        # Paginate transactions
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_txids = txids[start_idx:end_idx]
        
        transactions = []
        for txid in paginated_txids:
            try:
                tx = rpc.getrawtransaction(txid, 1)
                
                # Calculate input and output values for this address
                received = sum(vout["value"] for vout in tx.get("vout", [])
                             if any(addr == address for addr in vout.get("scriptPubKey", {}).get("addresses", [])))
                
                sent = 0
                for vin in tx.get("vin", []):
                    try:
                        prev_tx = rpc.getrawtransaction(vin["txid"], 1)
                        prev_vout = prev_tx["vout"][vin["vout"]]
                        if any(addr == address for addr in prev_vout.get("scriptPubKey", {}).get("addresses", [])):
                            sent += prev_vout["value"]
                    except Exception:
                        continue
                
                transactions.append({
                    "txid": txid,
                    "time": tx.get("time", 0),
                    "confirmations": tx.get("confirmations", 0),
                    "received": received,
                    "sent": sent,
                    "net": received - sent,
                    "size": tx.get("size", 0),
                })
            except Exception:
                continue
                
        return {
            "address": address,
            "balance": balance,
            "total_transactions": total_txs,
            "page": page,
            "limit": limit,
            "total_pages": (total_txs + limit - 1) // limit,
            "transactions": transactions,
            "utxos": utxos,
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
