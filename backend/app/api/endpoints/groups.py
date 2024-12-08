from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ...database import get_db
from ..schemas.group import Group, GroupCreate, GroupUpdate
from ..models.group import Group as GroupModel
from ..models.user import User as UserModel
from ...services.matching import MatchingService
from ...services.notification import NotificationService

router = APIRouter()

@router.post("/groups/", response_model=Group)
async def create_group(
    group: GroupCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Create new group
    db_group = GroupModel(
        meeting_time=group.meeting_time,
        location=group.location,
        status="pending"
    )
    
    # Add members to group
    for member_id in group.member_ids:
        user = db.query(UserModel).filter(UserModel.id == member_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User {member_id} not found")
        db_group.members.append(user)
    
    db.add(db_group)
    db.commit()
    db.refresh(db_group)

    # Send notifications to all members
    notification_service = NotificationService()
    users_info = [
        {"email": user.email, "phone_number": user.phone_number}
        for user in db_group.members
    ]
    
    background_tasks.add_task(
        notification_service.send_group_proposal,
        users_info,
        db_group.location,
        db_group.meeting_time.strftime("%Y-%m-%d %H:%M")
    )
    
    return db_group

@router.get("/groups/", response_model=List[Group])
def read_groups(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    groups = db.query(GroupModel).offset(skip).limit(limit).all()
    return groups

@router.get("/groups/{group_id}", response_model=Group)
def read_group(group_id: int, db: Session = Depends(get_db)):
    db_group = db.query(GroupModel).filter(GroupModel.id == group_id).first()
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return db_group

@router.put("/groups/{group_id}", response_model=Group)
async def update_group(
    group_id: int, 
    group: GroupUpdate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_group = db.query(GroupModel).filter(GroupModel.id == group_id).first()
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Update status and other fields
    for field, value in group.model_dump(exclude_unset=True).items():
        setattr(db_group, field, value)
    
    # If status changes to "confirmed", create group chat and notify members
    if group.status == "confirmed" and db_group.chat_group_id is None:
        notification_service = NotificationService()
        users_info = [
            {"email": user.email, "phone_number": user.phone_number}
            for user in db_group.members
        ]
        
        # Create group chat
        chat_group_id = await notification_service.create_group_chat(users_info)
        db_group.chat_group_id = chat_group_id
        
        # Send confirmation notifications
        background_tasks.add_task(
            notification_service.send_group_confirmation,
            users_info,
            db_group.location,
            db_group.meeting_time.strftime("%Y-%m-%d %H:%M"),
            chat_group_id
        )
    
    db.commit()
    db.refresh(db_group)
    return db_group

@router.post("/groups/match/{user_id}", response_model=Group)
async def match_user_to_group(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Get the user
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find potential group members
    matching_service = MatchingService(db)
    potential_members = matching_service.find_potential_group(user)
    
    if len(potential_members) < 4:
        raise HTTPException(
            status_code=400, 
            detail="Not enough compatible users found for a group"
        )
    
    # Create a new group with these members
    # Find a location that works for everyone (using the first shared neighborhood)
    shared_neighborhoods = set(user.neighborhoods)
    for member in potential_members:
        shared_neighborhoods &= set(member.neighborhoods)
    
    if not shared_neighborhoods:
        raise HTTPException(
            status_code=400,
            detail="No common neighborhood found for the group"
        )
    
    # Create the group
    group = GroupModel(
        meeting_time=datetime.utcnow(),  # This should be determined based on preferences
        location=list(shared_neighborhoods)[0],
        status="pending"
    )
    
    # Add all members
    group.members.append(user)
    for member in potential_members:
        group.members.append(member)
    
    db.add(group)
    db.commit()
    db.refresh(group)
    
    # Send notifications
    notification_service = NotificationService()
    users_info = [
        {"email": member.email, "phone_number": member.phone_number}
        for member in group.members
    ]
    
    background_tasks.add_task(
        notification_service.send_group_proposal,
        users_info,
        group.location,
        group.meeting_time.strftime("%Y-%m-%d %H:%M")
    )
    
    return group