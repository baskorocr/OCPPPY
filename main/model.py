from pydantic import BaseModel, Field
from typing import List, Optional
class RemoteStartTransactionRequest(BaseModel):
    id_tag: str
    connector_id: int = None
    charging_profile: dict = None


class ChargingSchedulePeriod(BaseModel):
    startPeriod: int = Field(..., description="Start period in seconds from the beginning of the charging session")
    limit: float = Field(..., description="Limit in watts (W)")

class ChargingSchedule(BaseModel):
    duration: Optional[int] = Field(None, description="Duration of the charging schedule in seconds")
    startSchedule: Optional[str] = Field(None, description="Start time of the charging schedule in RFC3339 format")
    chargingRateUnit: str = Field(..., description="Unit of charging rate, can be 'W' or 'A'")
    chargingSchedulePeriod: List[ChargingSchedulePeriod] = Field(..., description="List of charging schedule periods")
    minChargingRate: Optional[float] = Field(None, description="Minimum charging rate in watts (W)")

class ChargingProfileRequest(BaseModel):
    chargingProfileId: int = Field(..., description="ID of the charging profile")
    transactionId: int = Field(..., description="ID of the transaction")
    stackLevel: int = Field(..., description="Stack level of the charging profile")
    chargingProfilePurpose: str = Field(..., description="Purpose of the charging profile, e.g., 'TxProfile'")
    chargingProfileKind: str = Field(..., description="Kind of the charging profile, e.g., 'Absolute'")
    recurrencyKind: Optional[str] = Field(None, description="Recurrency kind of the charging profile, e.g., 'Daily'")
    validFrom: Optional[str] = Field(None, description="Start time of the profile validity in RFC3339 format")
    validTo: Optional[str] = Field(None, description="End time of the profile validity in RFC3339 format")
    chargingSchedule: ChargingSchedule = Field(..., description="Charging schedule associated with the profile")