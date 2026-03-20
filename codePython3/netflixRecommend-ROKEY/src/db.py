import sqlite3
import pandas as pd

DATA_DB_PATH = "src/assets/data.db" # 데이터 DB
DATA_PATH = 'src/assets/netflix_korea_popular_35_preprocessed.csv' # 영화 데이터
IMAGE_PATH = 'src/assets/netfilx_poster_img_png/' # 이미지 경로

# DB 생성 함수
def init_db():
    db = sqlite3.connect(DATA_DB_PATH)
    cursor = db.cursor()

    # Netflix 테이블 생성
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS netflix (
            movie_id INTEGER PRIMARY KEY,
            title TEXT,
            type TEXT,
            imdb_rating REAL,
            description TEXT,
            release_year INTEGER,
            image_path TEXT
        )
        """
    )
    db.commit()

    # Genre 테이블 생성
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS genre (
            genre_id INTEGER PRIMARY KEY,
            genre TEXT
        )
        """
    )
    db.commit()

    # Genre 테이블 생성
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS netflix_genre (
            movie_id INTEGER,
            genre_id INTEGER,
            PRIMARY KEY (movie_id, genre_id)
        )
        """
    )
    db.commit()

    db.close()

# DB 내용 초기화 함수
def make_db():
    try:
        # DATA DB 초기화
        df = pd.read_csv(DATA_PATH)
        db = sqlite3.connect(DATA_DB_PATH)
        cur = db.cursor()
        genre = []

        # netflix TABLE 초기화
        for i, row in df.iterrows():
            cur.execute(
                'INSERT OR IGNORE INTO netflix VALUES (?, ?, ?, ?, ?, ?, ?)',
                (i, row.title, row.type, row.imdb_rating, row.description, row.release_year, IMAGE_PATH+row.title+'.png')
            )
            lists = list(row.listed_in.split(', '))
            for j in lists:
                if j not in genre:
                    genre.append(j)
        db.commit()

        # genre TABLE 초기화
        genre.sort()
        for i, g in enumerate(genre):
            cur.execute(
                'INSERT OR IGNORE INTO genre VALUES (?, ?)',
                (i, g)
            )
        db.commit()


        # netflix_genre TABLE 초기화
        g_dict = {v: i for i, v in enumerate(genre)}
        for i, row in df.iterrows():
            lists = list(row.listed_in.split(', '))
            for j in lists:
                cur.execute(
                'INSERT OR IGNORE INTO netflix_genre VALUES (?, ?)',
                (i, g_dict[j])
            )
        db.commit()
        db.close()

    except Exception as e:
        print(f'{type(e)} : {e}')


def search_db(conn:sqlite3.Connection, options:dict=None) -> list:
    """
    DB에서 netflix를 검색하는 함수

    option keys:
        title            : str   | None # 검색할 제목
        type             : str   | None # 검색할 타입
        rating           : float | None # 기준 별점
        release_year     : int   | None # 출시 연도
        genre            : str   | None # 장르
        ascending        : bool  | True # 정렬 | 기본 : 오름차순
    
    returns:
        list : dict | 검색한 Netflix 목록 
            title        : str,
            type         : str,
            imdb_rating  : float,
            description  : str,
            release_year : int,
            image_path   : str,
            genre        : list
    """
    cur = conn.cursor()

    # 조건에 따른 쿼리 변경
    query = '''
    SELECT 
        n.title,
        n.type,
        n.imdb_rating,
        n.description,
        n.release_year,
        n.image_path,
        GROUP_CONCAT(g.genre, ', ') AS genre
    FROM netflix n
    JOIN netflix_genre ng ON n.movie_id = ng.movie_id
    JOIN genre g ON ng.genre_id = g.genre_id
    WHERE 1=1
    '''
    params = []

    if options and 'title' in options:
        query += " AND title LIKE ? "
        params.append(f"%{options['title']}%")

    if options and 'type' in options:
        query += " AND type = ? "
        params.append(options['type'])

    if options and 'rating' in options:
        query += " AND imdb_rating >= ? "
        params.append(options['rating'])
    
    if options and 'release_year' in options:
        query += " AND release_year = ? "
        params.append(options['release_year'])

    if options and 'genre' in options:
        query += '''
        AND EXISTS (
            SELECT 1
            FROM netflix_genre ng2
            JOIN genre g2 ON ng2.genre_id = g2.genre_id
            WHERE ng2.movie_id = n.movie_id
            AND g2.genre = ?
        )
        '''
        params.append(options['genre'])

    query += '''
    GROUP BY n.movie_id, n.title
                '''
    
    if options and 'ascending' in options:
        if options['ascending'] :
            query += '''
            ORDER BY imdb_rating ASC
            '''
        else :
            query += '''
                ORDER BY imdb_rating DESC
            '''
    else :
        query += '''
            ORDER BY n.movie_id ASC
            '''
    

    cur.execute(query, params)
    movies = cur.fetchall()

    # 데이터 처리
    result = []
    for movie in movies:
        line = {
            'title':movie[0],
            'type':movie[1],
            'rating':movie[2],
            'description':movie[3],
            'release_year':movie[4],
            'image_path':movie[5],
            'genre':list(movie[6].split(', '))
        }
        result.append(line)

    return result


def test():
    db = sqlite3.connect(DATA_DB_PATH)
    data = search_db(db)
    print(data)

    data = search_db(db, {'title':'Game'})
    print(data)

    data = search_db(db, {'rating':8.8})
    print(data)

    data = search_db(db, {'release_year':2017})
    print(data)

    data = search_db(db, {'genre':'Dramas'})
    print(data)

    data = search_db(db, {'title':'Game', 'rating':8.0, 'release_year':2021, 'genre':'TV Dramas'})
    print(data)
    
    data = search_db(db, {'ascending' : False})
    print(data)

    db.close()


if __name__ == '__main__':
    init_db()
    make_db()
    test()