# **NetflixRecommendRokey**

Netflix 콘텐츠 데이터를 기반으로 영화 및 시리즈 정보를 조회할 수 있는 **Python GUI 기반 추천 앱**입니다. \
Rokey 부트캠프 Python 심화 과정에서 **데이터 처리, SQLite DB 활용, GUI 애플리케이션 개발**을 연습하기 위해 제작한 프로젝트입니다.


---


# **프로젝트 개요**

Netflix 콘텐츠 데이터를 활용하여 제목, 장르, 평점, 개봉 연도 등의 조건으로 콘텐츠를 검색하고 조회할 수 있는 애플리케이션입니다.

Python 기반 GUI 프레임워크 **Flet**을 사용하여 인터페이스를 구성하고, \
**Pandas**로 데이터를 전처리한 뒤 **SQLite** 데이터베이스에 저장하여 조회하도록 구현했습니다.


---


# **주요 기능**



* 영화 / 시리즈 콘텐츠 검색
* 제목 기반 콘텐츠 조회
* 장르 기반 필터링
* 평점 기준 검색
* 개봉 연도 기준 검색
* SQLite 데이터베이스 기반 콘텐츠 조회


---


# **실행 방법**


### **1. 저장소 클론**


```
git clone https://github.com/your-id/NetflixRecommendRokey.git
cd NetflixRecommendRokey
```



### **2. 가상환경 생성**


```
python -m venv venv
```



### **3. 가상환경 활성화**

Linux / Mac


```
source venv/bin/activate
```


Windows


```
venv\Scripts\activate
```



### **4. 패키지 설치**


```
pip install -r requirements.txt
```



### **5. 실행**


```
flet run
```



---


# **사용 기술**


### **Language**



* Python


### **UI**



* Flet


### **Data Processing**



* Pandas


### **Database**



* SQLite


---


# **데이터 출처**

Netflix 콘텐츠 데이터는 아래 Kaggle 데이터셋을 사용했습니다.

Kaggle Netflix Dataset \
[https://www.kaggle.com/](https://www.kaggle.com/)

데이터는 Pandas를 이용해 전처리 후 SQLite 데이터베이스에 저장하여 사용했습니다.

## Dataset

Netflix Movies and TV Shows Dataset  
Source: Kaggle  
https://www.kaggle.com/datasets/shivamb/netflix-shows

---


# **프로젝트 구조**
```
NetflixRecommendRokey/
│
├─ src/
├─ assets/
│ ├─ netflix_poster_img_png/
│ ├─ data.db
│ ├─ icon.png
│ ├─ netflix_korea_popular_35.csv
│ ├─ netflix_korea_popular_35_prep.csv
│ ├─ netflix_titles.csv
│ └─ splash_android.png
├─ demo/
│ ├─ image1.png
│ ├─ image2.png
│ └─ image3.png
│
├─ db.py
├─ main.py
├─ requirements.txt
└─ README.md
```
---


# **데이터베이스 구조**

프로젝트에서는 다음과 같은 테이블 구조를 사용했습니다.


### **netflix**


<table>
  <tr>
   <td><strong>column</strong>
   </td>
   <td><strong>description</strong>
   </td>
  </tr>
  <tr>
   <td>movie_id
   </td>
   <td>콘텐츠 ID
   </td>
  </tr>
  <tr>
   <td>title
   </td>
   <td>작품 제목
   </td>
  </tr>
  <tr>
   <td>type
   </td>
   <td>영화 / 시리즈
   </td>
  </tr>
  <tr>
   <td>imdb_rating
   </td>
   <td>평점
   </td>
  </tr>
  <tr>
   <td>description
   </td>
   <td>작품 설명
   </td>
  </tr>
  <tr>
   <td>release_year
   </td>
   <td>개봉 연도
   </td>
  </tr>
  <tr>
   <td>image_path
   </td>
   <td>이미지 경로
   </td>
  </tr>
</table>



### **genre**


<table>
  <tr>
   <td><strong>column</strong>
   </td>
   <td><strong>description</strong>
   </td>
  </tr>
  <tr>
   <td>genre_id
   </td>
   <td>장르 ID
   </td>
  </tr>
  <tr>
   <td>genre
   </td>
   <td>장르 이름
   </td>
  </tr>
</table>



### **netflix_genre**


<table>
  <tr>
   <td><strong>column</strong>
   </td>
   <td><strong>description</strong>
   </td>
  </tr>
  <tr>
   <td>movie_id
   </td>
   <td>콘텐츠 ID
   </td>
  </tr>
  <tr>
   <td>genre_id
   </td>
   <td>장르 ID
   </td>
  </tr>
</table>



---


# **개발 목적**

이 프로젝트를 통해 다음 내용을 학습하는 것을 목표로 했습니다.



* Flet을 이용한 Python GUI 애플리케이션 개발
* Pandas를 활용한 데이터 전처리
* SQLite 기반 데이터 관리
* SQL 쿼리를 이용한 조건 검색 기능 구현


---

## Demo

### Main Screen
![Main Screen](./demo/image1.png)

### Search Screen
![Search Screen](./demo/image2.png)

### Detail Screen
![Detail Screen](./demo/image3.png)

---
# **License**

This project is for educational purposes.

---
## Disclaimer

This project is for educational purposes only.

Movie images belong to Netflix and their respective copyright holders.
They are not included in the repository.