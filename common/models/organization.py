from rococo.models import Organization as BaseOrganization
from typing import List, Optional
from dataclasses import dataclass
from common.app_config import config

@dataclass(kw_only=True)
class Organization(BaseOrganization):
    logo_url: Optional[str] = None
    subdomain: Optional[str] = None
    
    def as_dict(self):
        """
        Convert the Organization instance to a dictionary.
        Includes CloudFront URL for logo if present.
        
        Returns:
            dict: Dictionary representation of the Organization instance
        """
        # Get the base dictionary from parent class
        result = super().as_dict()
        
        # Add CloudFront domain to logo_url if it exists
        if self.logo_url:
            cloudfront_domain = config.CLOUDFRONT_DISTRIBUTION_DOMAIN
            result['logo_url'] = f"{cloudfront_domain}/{self.logo_url}"
        
        # Include subdomain if it exists
        if self.subdomain is not None:
            result['subdomain'] = self.subdomain
            
        return result
