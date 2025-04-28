from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from schemas import MovieListResponseSchema
from schemas.movies import MovieDetailResponseSchema

router = APIRouter()

NO_MOVIES_ERROR = "No movies found."
NO_MOVIE_ID_ERROR = "Movie with the given ID was not found."


@router.get(
    "/movies/",
    response_model=MovieListResponseSchema,
    responses={
        404: {
            "content": {
                "application/json": {"example": {"detail": NO_MOVIES_ERROR}}
            },
        }
    },
)
async def read_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
):
    total = await db.scalar(select(func.count()).select_from(MovieModel))
    total_pages = ceil(total / per_page)

    if total == 0 or page > total_pages:
        raise HTTPException(status_code=404, detail=NO_MOVIES_ERROR)

    movies = await db.execute(
        select(MovieModel).limit(per_page).offset((page - 1) * per_page)
    )
    movies = movies.scalars().all()
    movies = [
        MovieDetailResponseSchema.model_validate(movie) for movie in movies
    ]

    url_ = "/theater/movies?page="
    next_page = (
        f"{url_}{page + 1}&per_page={per_page}" if page < total_pages else None
    )
    prev_page = f"{url_}{page - 1}&per_page={per_page}" if page > 1 else None

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total,
    )


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailResponseSchema,
    responses={
        404: {
            "content": {
                "application/json": {"example": {"detail": NO_MOVIE_ID_ERROR}}
            },
        }
    },
)
async def read_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = movie.scalars().first()
    if not movie:
        raise HTTPException(status_code=404, detail=NO_MOVIE_ID_ERROR)
    return MovieDetailResponseSchema.model_validate(movie)
