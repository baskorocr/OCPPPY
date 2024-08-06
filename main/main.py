import asyncio
import logging
import websockets
import uuid
from fastapi import FastAPI, HTTPException, Path, Body
from model import (RemoteStartTransactionRequest,ChargingProfileRequest)
from datetime import datetime
from ocpp.routing import on
from ocpp.v16 import ChargePoint as cp
from ocpp.v16 import call_result, call
from ocpp.v16.enums import (Action,
    AuthorizationStatus,
    ChargePointErrorCode,
    ChargePointStatus,
    DataTransferStatus,
    RegistrationStatus,
    ResetStatus,
    ResetType,)
from ocpp.v16.datatypes import IdTagInfo
import uvicorn  # Add this import
import random

logging.basicConfig(level=logging.INFO)

charge_points = {}  # Dictionary to hold connected charge points
transaction_ids = {}

class ChargePoint(cp):
    
    @on(Action.Authorize)
    def on_authorize(self, **kwargs):
        id_tag_info = IdTagInfo(status=AuthorizationStatus.accepted)
        return call_result.AuthorizePayload(id_tag_info=id_tag_info)

    @on(Action.BootNotification)
    def on_boot_notification(
        self,
        charge_point_vendor: str,
        charge_point_model: str,
        **kwargs
    ):
        return call_result.BootNotificationPayload (
            current_time=datetime.utcnow().isoformat(),
            interval=900,
            status=RegistrationStatus.accepted,
        )

    @on(Action.DataTransfer)
    def on_data_transfer(self, **kwargs):
        return call_result.DataTransferPayload(
            status=DataTransferStatus.unknown_vendor_id,
            data="Please implement me"
        )

    @on(Action.Heartbeat)
    def on_heartbeat(self, **kwargs):
        return call_result.HeartbeatPayload(
            current_time=datetime.utcnow().isoformat(),
        )

    @on(Action.MeterValues)
    def on_meter_values(self, **kwargs):
        return call_result.MeterValues()

    @on(Action.StatusNotification)
    def on_status_notification(
        self,
        connector_id: int,
        error_code: ChargePointErrorCode,
        status: ChargePointStatus,
        **kwargs
    ):
        return call_result.StatusNotificationPayload(
           
        )

    @on(Action.StartTransaction)
 
    def on_start_transaction(self, **kwargs):
        charge_point_id = self.id 
        transaction_id = transaction_ids.get(charge_point_id, 1)
        
        id_tag_info = IdTagInfo(status=AuthorizationStatus.accepted)
        return call_result.StartTransactionPayload(transaction_id=transaction_id,
                                            id_tag_info=id_tag_info)

    @on(Action.StopTransaction)
    def on_stop_transaction(self, **kwargs):
        return call_result.StopTransactionPayload()
   
    async def request_reset(self, **kwargs):
        request = call.Reset(ResetType.hard)
        response = await self.call(request)

        if response.status == ResetStatus.accepted:
            logging.info("Reset requested")

    async def request_get_configuration(self, **kwargs):
        payload = call.GetConfiguration(**kwargs)
        return await self.call(payload)

    async def request_change_configuration(self, **kwargs):
        payload = call.ChangeConfiguration(**kwargs)
        return await self.call(payload)
    
    async def request_remote_start_transaction(self, connector_id: int, id_tag: str, charging_profile: dict = None):
            payload = call.RemoteStartTransactionPayload(
              
                connector_id=connector_id,
                id_tag=id_tag,
                charging_profile=charging_profile
                
            )
            print(payload)
            response = await self.call(payload)
            if response.status != 'Accepted':
                raise Exception(f"Failed to start transaction: {response.status}")
            return response

    async def request_remote_stop_transaction(self, **kwargs):
        payload = call.RemoteStopTransaction(**kwargs)
        return await self.call(payload)

    async def request_update_firmware(self, **kwargs):
        payload = call.UpdateFirmware(**kwargs)
        return await self.call(payload)

    async def request_keco(self, **kwargs):
        payload = call.DataTransfer(**kwargs)
        return await self.call(payload)
    
    async def set_charging_profile(self, charging_profile):
        # Implement the logic to set the charging profile
        pass

async def on_connect(websocket, path):
    try:
        requested_protocols = websocket.request_headers["Sec-WebSocket-Protocol"]
    except KeyError:
        logging.error("Client hasn't requested any Subprotocol. Closing Connection")
        return await websocket.close()

    if websocket.subprotocol:
        logging.info("Protocols Matched: %s", websocket.subprotocol)
    else:
        logging.warning(
            "Protocols Mismatched | Expected Subprotocols: %s,"
            " but client supports  %s | Closing connection",
            websocket.available_subprotocols,
            requested_protocols,
        )
        return await websocket.close()

    charge_point_id = path.strip("/ocpp")
    cp = ChargePoint(charge_point_id, websocket)
    charge_points[charge_point_id] = cp

    await cp.start()

async def start_websocket_server():
    server = await websockets.serve(
        on_connect, "0.0.0.0", 9000, subprotocols=["ocpp1.6"]
    )
    logging.info("WebSocket Server Started listening to new connections...")
    await server.wait_closed()

app = FastAPI()



@app.post("/{charge_point_id}/remote_start_transaction")
async def remote_start_transaction(request: RemoteStartTransactionRequest, charge_point_id: str = Path(..., description="ID of the charge point")):
     # Replace with your logic to get the charge point ID
    if charge_point_id not in charge_points:
        raise HTTPException(status_code=404, detail="Charge point not connected")

    cp = charge_points[charge_point_id]

    transaction_id = request.charging_profile.get("transactionId", None)
    if transaction_id is not None:
        transaction_ids[charge_point_id] = transaction_id

    await cp.request_remote_start_transaction(
        connector_id=request.connector_id,
        id_tag=request.id_tag,
        
        charging_profile=request.charging_profile
    )
    return {"message": "Remote start transaction requested"}

@app.post("/{charge_point_id}/limitkWh")
async def limit_kWh(request: ChargingProfileRequest, charge_point_id: str = Path(...)):
    if charge_point_id not in charge_points:
        raise HTTPException(status_code=404, detail="Charge point not connected")
    
    
    cp = charge_points[charge_point_id]
    await cp.set_charging_profile(request.dict())
    
    return {"message": "Charging profile set successfully"}

if __name__ == "__main__":
    async def main():
        # Start the WebSocket server
        websocket_task = asyncio.create_task(start_websocket_server())
        
        # Start the FastAPI server
        config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        api_task = asyncio.create_task(server.serve())
        
        await asyncio.gather(websocket_task, api_task)
    
    asyncio.run(main())
