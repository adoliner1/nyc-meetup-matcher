from typing import List, Dict
from sqlalchemy.orm import Session
from ..api.models.user import User
from ..api.models.group import Group

class MatchingService:
    def __init__(self, db: Session):
        self.db = db
    
    def find_potential_group(self, user: User) -> List[User]:
        """
        Find potential group members based on neighborhood preferences and interests.
        Returns a list of users that would make a good group.
        """
        # Get users who share at least one neighborhood with the input user
        potential_members = (
            self.db.query(User)
            .filter(User.id != user.id)
            .filter(User.is_active == True)
            .all()
        )
        
        # Score each potential member based on compatibility
        scored_members = []
        for member in potential_members:
            score = self._calculate_compatibility(user, member)
            if score > 0:  # Only include if there's some compatibility
                scored_members.append((member, score))
        
        # Sort by compatibility score
        scored_members.sort(key=lambda x: x[1], reverse=True)
        
        # Return top 4 most compatible users (to form a group of 5 with the input user)
        return [member for member, _ in scored_members[:4]]
    
    def _calculate_compatibility(self, user1: User, user2: User) -> float:
        """
        Calculate compatibility score between two users based on:
        - Shared neighborhoods
        - Shared interests
        Returns a score between 0 and 1
        """
        # Calculate neighborhood overlap
        shared_neighborhoods = set(user1.neighborhoods) & set(user2.neighborhoods)
        if not shared_neighborhoods:
            return 0  # No compatible neighborhoods, no match
        
        neighborhood_score = len(shared_neighborhoods) / max(
            len(user1.neighborhoods), len(user2.neighborhoods)
        )
        
        # Calculate interest overlap
        shared_interests = set(user1.interests) & set(user2.interests)
        interest_score = len(shared_interests) / max(
            len(user1.interests), len(user2.interests)
        ) if user1.interests and user2.interests else 0.5  # Default if no interests
        
        # Combine scores (weight neighborhoods more heavily)
        return (0.7 * neighborhood_score) + (0.3 * interest_score)