from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.intent import Intent
from app.schemas import IntentCreate, IntentUpdate, IntentOut

router = APIRouter(prefix="/intents", tags=["Intents"])

@router.get("/", response_model=list[IntentOut])
def get_intents(db: Session = Depends(get_db)):
    return db.query(Intent).all()

@router.get("/{intent_id}", response_model=IntentOut)
def get_intent(intent_id: int, db: Session = Depends(get_db)):
    intent = db.query(Intent).filter(Intent.id == intent_id).first()
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")
    return intent

@router.post("/", response_model=IntentOut)
def create_intent(
    intent: IntentCreate,
    session_id: str = Header(...),
    db: Session = Depends(get_db)
):
    db_intent = Intent(
        session_id=session_id,
        name=intent.name,
        description=intent.description,
        parameters=intent.parameters,
        context=intent.context,
    )
    db.add(db_intent)
    db.commit()
    db.refresh(db_intent)
    return db_intent

@router.put("/{intent_id}", response_model=IntentOut)
def update_intent(intent_id: int, updated: IntentUpdate, db: Session = Depends(get_db)):
    intent = db.query(Intent).filter(Intent.id == intent_id).first()
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")
    
    for field, value in updated.dict(exclude_unset=True).items():
        setattr(intent, field, value)

    db.commit()
    db.refresh(intent)
    return intent

@router.delete("/{intent_id}")
def delete_intent(intent_id: int, db: Session = Depends(get_db)):
    intent = db.query(Intent).filter(Intent.id == intent_id).first()
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")

    db.delete(intent)
    db.commit()
    return {"message": "Intent deleted successfully"}
