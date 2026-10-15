from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import Page
from app.schemas.content import (
    CollectionOut,
    DuaCategoryOut,
    DuaOut,
    HadithOut,
    SearchResults,
    SurahDetail,
    SurahOut,
    TafsirOut,
    VerseOut,
)
from app.services import content as service

router = APIRouter(tags=["content"])
SurahNo = Annotated[int, Path(ge=1, le=114)]
VerseNo = Annotated[int, Path(ge=1)]


@router.get("/surahs", response_model=list[SurahOut])
def surahs(db: Session = Depends(get_db)):
    return service.list_surahs(db)


@router.get("/surahs/{number}", response_model=SurahDetail)
def surah(number: SurahNo, language: str | None = Query(None, max_length=10),
          limit: int = Query(50, ge=1, le=300), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    return service.surah_verses(db, number, language=language, limit=limit, offset=offset)


@router.get("/verses/{surah}/{verse}", response_model=VerseOut)
def verse(surah: SurahNo, verse: VerseNo, language: str | None = Query(None, max_length=10),
          db: Session = Depends(get_db)):
    return service.get_verse(db, surah, verse, language)


@router.get("/verses/{surah}/{verse}/tafsir", response_model=list[TafsirOut])
def tafsir(surah: SurahNo, verse: VerseNo, language: str | None = Query(None, max_length=10),
           db: Session = Depends(get_db)):
    return service.tafsir_for(db, surah, verse, language)


@router.get("/hadith/collections", response_model=list[CollectionOut])
def collections(db: Session = Depends(get_db)):
    return service.list_collections(db)


@router.get("/hadith/collections/{slug}", response_model=Page[HadithOut])
def collection(slug: str, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    items, total = service.collection_records(db, slug, limit=limit, offset=offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/hadith/{hadith_id}", response_model=HadithOut)
def hadith(hadith_id: int, db: Session = Depends(get_db)):
    return service.get_hadith(db, hadith_id)


@router.get("/duas/categories", response_model=list[DuaCategoryOut])
def dua_categories(db: Session = Depends(get_db)):
    return service.dua_categories(db)


@router.get("/duas", response_model=list[DuaOut])
def duas(category: str | None = Query(None, max_length=80), limit: int = Query(50, ge=1, le=100),
         offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    return service.duas(db, category, limit, offset)


@router.get("/search", response_model=SearchResults)
def search(q: str = Query(..., min_length=2, max_length=200), db: Session = Depends(get_db)):
    hits = service.search(db, q.strip())
    note = None if hits else "No approved content matched. Content appears here only after its source is approved."
    return SearchResults(query=q, hits=hits, note=note)
