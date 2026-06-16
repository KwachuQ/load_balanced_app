from __future__ import annotations

import os
import sys
from fastapi import FastAPI, HTTPException

# Add packages directory to sys.path to allow importing common package modules
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../packages"))
)

from common.metadata import EC2MetadataService

# Initialize FastAPI application and EC2 metadata query service
app = FastAPI(title="Load Balanced App")
metadata_service = EC2MetadataService()


@app.get("/health")
def health() -> dict[str, str]:
    """
    Health check endpoint.
    
    Returns:
        dict: Standard JSON status indicating service availability.
    """
    return {"status": "ok"}


@app.get("/info")
def info() -> dict[str, str]:
    """
    Instance info endpoint retrieving AWS region and availability zone.
    
    Returns:
        dict: Region and availability zone name.
    
    Raises:
        HTTPException: 503 error if EC2 metadata is not accessible.
    """
    try:
        location = metadata_service.get_instance_location()
        return {
            "region": location.region,
            "availability_zone": location.availability_zone,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Metadata unavailable: {exc}"
        )