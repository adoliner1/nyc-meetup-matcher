import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..app.database import Base
from ..app.api.models.user import User
from ..app.services.matching import MatchingService

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture
def db_session():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_matching_service(db_session):
    # Create test users
    users = [
        User(
            email=f"user{i}@test.com",
            phone_number=f"+1555000{i:04d}",
            full_name=f"User {i}",
            neighborhoods=["Manhattan"] if i < 3 else ["Brooklyn"],
            interests=["food", "art"] if i < 2 else ["music", "sports"],
            is_active=True
        )
        for i in range(6)
    ]
    
    for user in users:
        db_session.add(user)
    db_session.commit()
    
    matching_service = MatchingService(db_session)
    
    # Test matching for first user
    matches = matching_service.find_potential_group(users[0])
    
    # Should find users with similar neighborhoods first
    assert len(matches) <= 4  # Should find up to 4 matches
    assert all(user.neighborhoods[0] == "Manhattan" for user in matches[:2])
    
    # Test compatibility calculation
    compatibility = matching_service._calculate_compatibility(users[0], users[1])
    assert compatibility > 0.5  # Should have high compatibility (same neighborhood + interests)