import asyncio
import logging
import websockets
from datetime import datetime
from ocpp.routing import on
from ocpp.v16 import ChargePoint as cp
from ocpp.v16 import call_result, call
from ocpp.v16.enums import (Action, AuthorizationStatus, RegistrationStatus, DataTransferStatus, ChargePointStatus, ChargePointErrorCode)
from ocpp.v16.datatypes import IdTagInfo

logging.basicConfig(level=logging.INFO)

charge_points = {}  # Dictionary to hold connected charge points
transaction_ids = {}

class ChargePoint(cp):
    @on(Action.Authorize)
    def on_authorize(self, **kwargs):
        id_tag_info = IdTagInfo(status=AuthorizationStatus.accepted)
        return call_result.Authorize(id_tag_info=id_tag_info)

    @on(Action.BootNotification)
    def on_boot_notification(self, charge_point_vendor: str, charge_point_model: str, **kwargs):
        return call_result.BootNotification(
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
    def on_status_notification(self, connector_id: int, error_code: ChargePointErrorCode, status: ChargePointStatus, **kwargs):
        return call_result.StatusNotification()

    @on(Action.StartTransaction)
    def on_start_transaction(self, **kwargs):
        charge_point_id = self.id
        transaction_id = transaction_ids.get(charge_point_id, 1)
        id_tag_info = IdTagInfo(status=AuthorizationStatus.accepted)
        return call_result.StartTransaction(transaction_id=transaction_id, id_tag_info=id_tag_info)

    @on(Action.RemoteStartTransaction)
    def remote_start_transaction(self, **kwargs):
        status = call_result.RemoteStartStopStatus.rejected
        return call_result.RemoteStartTransaction(status=status)
    
    @on(Action.RemoteStopTransaction)
    def remote_stop_transaction(self, **kwargs):
        return call_result.RemoteStartStopStatus.accepted

    @on(Action.StopTransaction)
    def on_stop_transaction(self, **kwargs):
        id_tag_info = IdTagInfo(status=AuthorizationStatus.accepted)
        return call_result.StopTransaction(id_tag_info=id_tag_info)

    async def request_remote_start_transaction(self, connector_id: int, id_tag: str, charging_profile: dict = None):
        payload = call.RemoteStartTransaction(connector_id=connector_id, id_tag=id_tag, charging_profile=charging_profile)
        response = await self.call(payload)
        if response.status != 'Accepted':
            raise Exception(f"Failed to Remote start transaction: {response.status}")
        return response

    async def request_remote_stop_transaction(self, transaction_id: int, **kwargs):
        payload = call.RemoteStopTransaction(transaction_id=transaction_id)
        response = await self.call(payload)
        if response.status != 'Accepted':
            raise Exception(f"Failed to remote stop transaction: {response.status}")
        return response

async def on_connect(websocket, path):
    try:
        requested_protocols = websocket.request_headers["Sec-WebSocket-Protocol"]
    except KeyError:
        logging.error("Client hasn't requested any Subprotocol. Closing Connection")
        return await websocket.close()

    if websocket.subprotocol:
        logging.info("Protocols Matched: %s", websocket.subprotocol)
    else:
        logging.warning("Protocols Mismatched | Expected Subprotocols: %s, but client supports %s | Closing connection",
                        websocket.available_subprotocols, requested_protocols)
        return await websocket.close()

    path_parts = path.strip("/").split("/")
    if len(path_parts) != 2:
        logging.error("Invalid path format. Closing Connection")
        return await websocket.close()
    
    user_id = path_parts[0]
    charge_point_id = path_parts[1]

    cp = ChargePoint(charge_point_id, websocket)
    if user_id not in charge_points:
        charge_points[user_id] = {}
    charge_points[user_id][charge_point_id] = cp

    logging.info(f"Charge point {charge_point_id} connected under user {user_id}")
    logging.info(f"Current charge points for user {user_id}: {list(charge_points[user_id].keys())}")

    await cp.start()

async def start_websocket_server():
    server = await websockets.serve(on_connect, "0.0.0.0", 9000, subprotocols=["ocpp1.6"])
    logging.info("WebSocket Server Started listening to new connections...")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(start_websocket_server())
