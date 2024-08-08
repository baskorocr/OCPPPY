import asyncio
import logging
from fastapi import FastAPI, HTTPException, Path
import uvicorn
from model import RemoteStartTransactionRequest, ChargingProfileRequest
from ocpp_server import charge_points, transaction_ids, ChargePoint, start_websocket_server

logging.basicConfig(level=logging.INFO)
app = FastAPI()

@app.post("/{user_id}/{charge_point_id}/remote_start_transaction")
async def remote_start_transaction(request: RemoteStartTransactionRequest, charge_point_id: str = Path(..., description="ID of the charge point"), user_id: str = Path(..., description="ID of the user")):
    logging.info(f"Charge Points: {charge_points}")
    if charge_point_id not in charge_points and charge_point_id not in charge_points[user_id]:
        raise HTTPException(status_code=404, detail="Charge point not connected")

    cp = charge_points[user_id][charge_point_id]
    logging.info(f"Charge Point Object: {cp}")

    transaction_id = request.charging_profile.get("transactionId", None)
    if transaction_id is not None:
        transaction_ids[charge_point_id] = transaction_id

    await cp.request_remote_start_transaction(
        connector_id=request.connector_id,
        id_tag=request.id_tag,
        charging_profile=request.charging_profile
    )
    return {"message": "Remote start transaction requested"}

@app.get("/{user_id}/count_charge_points")
async def count_charge_points(user_id: str = Path(..., description="ID of the user")):
    if user_id not in charge_points:
        raise HTTPException(status_code=404, detail="User not found")

    charge_point_count = len(charge_points[user_id])
    logging.info(f"User {user_id} has {charge_point_count} charge points connected")

    return {"user_id": user_id, "charge_point_count": charge_point_count}

@app.get("/{charge_point_id}/remote_stop_transaction")
async def remote_stop_transaction(charge_point_id: str = Path(...)):
    if charge_point_id not in charge_points:
        raise HTTPException(status_code=404, detail="Charge point not connected")

    cp = charge_points[charge_point_id]
    transaction_id = transaction_ids.get(charge_point_id, 1)

    await cp.request_remote_stop_transaction(transaction_id=transaction_id)
    return {"message": "Remote stop transaction requested"}

@app.post("/{charge_point_id}/limitkWh")
async def limit_kWh(request: ChargingProfileRequest, charge_point_id: str = Path(...)):
    if charge_point_id not in charge_points:
        raise HTTPException(status_code=404, detail="Charge point not connected")

    cp = charge_points[charge_point_id]
    await cp.set_charging_profile(request.dict())
    
    return {"message": "Charging profile set successfully"}

async def main():
    loop = asyncio.get_event_loop()
    # Start the WebSocket server
    loop.create_task(start_websocket_server())
    # Run FastAPI application
    config = uvicorn.Config(app, host="0.0.0.0", port=8080, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
