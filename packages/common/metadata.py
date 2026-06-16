"""
Service module for querying AWS EC2 metadata endpoints.
Provides region and availability zone information of the running instance.
"""

from __future__ import annotations

from dataclasses import dataclass
import requests

# IMDSv2 token and instance identity document URLs
TOKEN_URL = "http://169.254.169.254/latest/api/token"
IDENTITY_URL = "http://169.254.169.254/latest/dynamic/instance-identity/document"


@dataclass
class InstanceLocation:
    """Dataclass holding region and availability zone information."""
    region: str
    availability_zone: str


class EC2MetadataService:
    """Service to fetch metadata details from the local AWS EC2 IMDSv2."""

    def __init__(self, timeout: tuple[float, float] = (2.0, 3.0)) -> None:
        """
        Initialize the service with connection timeouts.
        
        Args:
            timeout (tuple): A (connect, read) timeout tuple for requests.
        """
        self.timeout = timeout

    def _get_token(self) -> str:
        """
        Retrieve session token for IMDSv2.
        
        Returns:
            str: The raw token string.
        """
        response = requests.put(
            TOKEN_URL,
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.text

    def get_instance_location(self) -> InstanceLocation:
        """
        Fetch region and availability zone from the EC2 instance identity document.
        
        Returns:
            InstanceLocation: Object containing region and availability zone.
        """
        token = self._get_token()
        response = requests.get(
            IDENTITY_URL,
            headers={"X-aws-ec2-metadata-token": token},
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        return InstanceLocation(
            region=data["region"],
            availability_zone=data["availabilityZone"],
        )
