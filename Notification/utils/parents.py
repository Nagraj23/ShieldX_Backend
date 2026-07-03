# utils/parents.py

from typing import List, Dict, Optional, Any
from db import get_parents_by_child, Parent # Import the Parent model and lookup function
from services.redis_presence import get_parent_reachability
from models.notification_model import AlertRequest

# --- Utility Model for Actionable Recipient Data ---

class DispatchTarget(Parent):
    """
    An augmented Parent model used by the worker, combining DB metadata
    with live presence data from Redis.
    """
    # These fields are LIVE and come from Redis/Presence system
    is_reachable: bool = False
    live_fcm_token: Optional[str] = None
    
# --- CORE UTILITY FUNCTION ---

async def get_dispatch_targets(child_id: str) -> List[DispatchTarget]:
    """
    1. Fetches static recipient data from the database.
    2. Fetches live reachability (presence/token) from Redis.
    3. Merges the two datasets into a list of actionable targets for the dispatcher.
    """
    # 1. Fetch static metadata from the database (via db.py)
    db_parents: List[Parent] = await get_parents_by_child(child_id)
    
    if not db_parents:
        print(f"UTILITY: No static parent records found for child {child_id}.")
        return []

    dispatch_targets: List[DispatchTarget] = []
    
    # 2. Iterate and fetch live reachability data from Redis
    for parent in db_parents:
        
        # Get live presence data (Fix 2: O(1) Redis read)
        reachability = await get_parent_reachability(parent.id)
        
        # Create the augmented DispatchTarget object
        target = DispatchTarget.parse_obj(parent.dict(by_alias=True))
        
        target.is_reachable = reachability["is_online"]
        target.live_fcm_token = reachability["fcm_token"]
        
        # 3. Apply potential business filtering (e.g., block listed, primary guardian)
        # if target.is_block_listed: continue 
        
        dispatch_targets.append(target)
        
    print(f"UTILITY: Prepared {len(dispatch_targets)} dispatch targets for delivery.")
    return dispatch_targets