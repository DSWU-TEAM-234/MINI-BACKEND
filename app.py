from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import pymysql
from datetime import timedelta
import time
import os
import uuid
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit, join_room, leave_room
# import psycopg2
# from psycopg2.extras import RealDictCursor

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = 'your_secret_key_here'

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # 세션 지속 시간 설정

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

socketio = SocketIO(app, cors_allowed_origins="*")


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 파일 이름에 점('.')이 있고, 확장자가 허용된 확장자 목록(ALLOWED_EXTENSIONS)에 포함되는지 확인하는 함수
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# MySQL 연결 설정 (애플리케이션 시작 시)
def connect_to_db():
    return pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='root',
        database='miniproject',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# pgAdmin 연결
# def connect_to_db():
#     return psycopg2.connect(
#         host='127.0.0.1',
#         user='postgres',
#         password='postgres',
#         database='miniProjects',
#         cursor_factory=RealDictCursor
#     )

# 전역 MySQL 연결 객체
db_connection = None

# 첫 요청 때 MySQL 연결
@app.before_first_request
def initialize_db():
    global db_connection
    db_connection = connect_to_db()
    print("데이터베이스 연결에 성공했습니다.")

# check_image 라우트
@app.route('/check_image', methods=['GET'])
def check_image():
    # university_logo를 세션에서 가져와 check_image.html로 전달
    university_logo = session.get('university_logo')
    return render_template('check_image.html', university_logo=university_logo)

# 홈 라우트
@app.route('/')
def view_mainHome():
    return render_template('used_trade_home.html')

# 회원가입 라우트
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # 폼 데이터 가져오기
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        nick_name = request.form['nick_name']
        university_classification = request.form['university_classification']
        
        # 필수 필드에 대한 None 체크
        if not name or not email or not password or not nick_name:
            error_message = "필수 입력 필드가 누락되었습니다. 모든 필드를 입력해주세요."
            return render_template('signup.html', error_message=error_message)
        
        # 비밀번호 해싱 처리
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # 대학교 이름이 입력되지 않았을 경우 외부인으로 설정
        if not university_classification:
            university_classification = "외부인"
        
        profile_image = request.files.get('profile_image')  # 한 장의 프로필 이미지 파일
        
        # 프로필 이미지 파일 저장
        if profile_image and allowed_file(profile_image.filename):
            # 고유한 파일 이름 생성
            unique_filename = f"{uuid.uuid4().hex}_{profile_image.filename}"
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            profile_image.save(img_path)
            profile_image_path = img_path
        else:
            profile_image_path = None
        
        # 데이터베이스 연결 상태 확인
        if db_connection and db_connection.open:
            print("데이터베이스 연결 상태: 정상")  
        else:
            print("데이터베이스 연결에 문제가 있습니다.")
        
        # 데이터베이스에 회원 정보 저장
        try:
            with db_connection.cursor() as cursor:
                # 이메일 중복 확인
                sql_check_email = "SELECT * FROM users WHERE email = %s"
                cursor.execute(sql_check_email, (email,))
                email_exists = cursor.fetchone()

                # 닉네임 중복 확인
                sql_check_nick_name = "SELECT * FROM users WHERE nick_name = %s"
                cursor.execute(sql_check_nick_name, (nick_name,))
                nick_name_exists = cursor.fetchone()
                
                # 중복된 이메일 또는 닉네임이 있을 경우
                if email_exists:
                    error_message = "이미 등록된 이메일입니다."
                    return render_template('signup.html', error_message=error_message)
                elif nick_name_exists:
                    error_message = "이미 사용 중인 닉네임입니다."
                    return render_template('signup.html', error_message=error_message)
                
                # university_classification이 None이 아닐 경우에만 university_and_logo 테이블에 중복 확인 및 저장
                if university_classification:
                    sql_check_university = "SELECT university_name FROM university_and_logo WHERE university_name = %s"
                    cursor.execute(sql_check_university, (university_classification,))
                    university_exists = cursor.fetchone()

                    # 존재하지 않으면 university_and_logo 테이블에 대학교 이름 저장
                    if not university_exists:
                        sql_insert_university_name = """
                            INSERT INTO university_and_logo (university_name) VALUES (%s)
                        """
                        cursor.execute(sql_insert_university_name, (university_classification,))
                        db_connection.commit()  # 변경 사항 저장
                
                # 데이터 삽입 SQL 쿼리 (중복이 없는 경우)
                sql_insert_user = """
                    INSERT INTO users (name, email, password, nick_name, university_classification, profile_image)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql_insert_user, (name, email, hashed_password, nick_name, university_classification, profile_image_path))
                db_connection.commit()  # 변경 사항 저장
        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            return "회원가입 실패!"
        
        # 회원가입 성공 시 홈 페이지로 리다이렉트하며 플래그 전달
        return redirect(url_for('view_mainHome', signup_success=True))

    # GET 요청 시 회원가입 페이지 렌더링
    return render_template('signup.html')

# 로그인 라우트
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 폼 데이터 가져오기
        email = request.form['email']
        password = request.form['password']
        
        # 데이터베이스 연결 상태 확인
        if db_connection and db_connection.open:
            print("데이터베이스 연결 상태: 정상")  
        else:
            print("데이터베이스 연결에 문제가 있습니다.")
        
        try:
            with db_connection.cursor() as cursor:
                # 사용자가 입력한 이메일이 DB에 존재하는지 확인
                sql = "SELECT * FROM users WHERE email = %s"
                cursor.execute(sql, (email,))
                user = cursor.fetchone()
                print(user)# 해당 이메일로 등록된 사용자 정보 가져오기

                if not user:
                    # 이메일이 존재하지 않을 때 오류 메시지 전달
                    error_message = "등록된 사용자 정보가 없습니다."
                    return render_template('login.html', error_message=error_message)
                else:
                    # 이메일이 존재하는 경우, 비밀번호 해싱 비교
                    if bcrypt.check_password_hash(user['password'], password):
                        # 비밀번호가 일치하면 로그인 성공
                        session['user_id'] = user['id']  # 세션에 사용자 id 저장 
                        session['user_nickName'] = user['nick_name']  # 세션에 사용자 닉네임 저장
                        
                        # 사용자의 isAccepted 여부에 따라 세션에 university_name 저장 (비인증 시 외부인으로)
                        if user['isAccepted'] == "인증":
                            session['university_name'] = user['university_classification']
                        else:
                            session['university_name'] = "외부인"

                        # 사용자의 university_name에 따른 university_logo 가져오기
                        university_name = session.get('university_name')
                        sql_logo = "SELECT university_logo FROM university_and_logo WHERE university_name = %s"
                        cursor.execute(sql_logo, (university_name,))
                        university_logo = cursor.fetchone()

                        if university_logo:
                            session['university_logo'] = university_logo['university_logo']
                        
                        session.permanent = True  # 영구 세션 사용
                        print(session['user_id'])
                        print(session['user_nickName'])
                        print(session['university_name'])
                        print(session['university_logo'])
                        
                        # login_success 파라미터를 True로 설정하여 홈으로 리다이렉트
                        #return redirect(url_for('view_mainHome', login_success=True))
                        # 로그인 성공 시 check_image.html로 리다이렉트
                        return redirect(url_for('check_image'))
                    else:
                        # 비밀번호가 틀렸을 때 오류 메시지 전달
                        error_message = "비밀번호가 틀렸습니다. 다시 입력해주세요."
                        return render_template('login.html', error_message=error_message)
        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            error_message = "로그인 중 오류가 발생했습니다."
            return render_template('login.html', error_message=error_message)
    
    # GET 요청 시 로그인 페이지 렌더링
    return render_template('login.html')

# 로그아웃 라우트
@app.route('/logout')
def logout():
    # 세션 정보 삭제
    session.pop('user_id', None)
    session.pop('user_nickName', None)
    
    # 데이터베이스 연결 끊기
    global db_connection
    if db_connection and db_connection.open:
        db_connection.close()
        print("데이터베이스 연결이 끊어졌습니다.")
    
    # 로그아웃 후 홈 페이지로 리다이렉트
    return redirect(url_for('view_mainHome'))

# 메인 홈의 대학교 선택 필터에서 DB에 등록된 대학 목록을 띄우기 위해 university_name 정보를 넘겨주는 라우트
@app.route('/university_list', methods=['GET'])
def university_list():
    # 데이터베이스 연결 상태 확인
    if db_connection and db_connection.open:
        print("데이터베이스 연결 상태: 정상")  
    else:
        print("데이터베이스 연결에 문제가 있습니다.")
        
    # university_and_logo 테이블에서 university_name 정보만 가져오기
        try:
            with db_connection.cursor() as cursor:
                sql_get_university_name = """
                    SELECT university_name FROM university_and_logo
                """
                cursor.execute(sql_get_university_name)
                university_names = cursor.fetchall()  # 결과를 가져옴
        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            return "error: 데이터 조회 실패!"
        
    # university_names 리스트를 JSON으로 반환
    return university_names

# 글 작성 처리 라우트 (공통 라우트)
@app.route('/write_post', methods=['POST'])
def write_post():
    if request.method == 'POST':
        print("글 작성 라우트 실행")
        # 세션에서 user_id 및 user_nickName 정보 가져오기
        user_id = session.get('user_id')
        user_nickName = session.get('user_nickName')

        print(user_id)
        print(user_nickName)

        # 세션에 사용자 정보가 없으면 로그인 페이지로 리다이렉트
        if not user_id or not user_nickName:
            return redirect(url_for('login'))

        # 폼 데이터 가져오기
        post_type = request.form.get('post_type')
        title = request.form.get('title')
        category = request.form.get('category')
        price = request.form.get('price')
        content = request.form.get('content')
        deal_method = request.form.get('deal_method')
        image = request.files.getlist('image')  # 이미지 파일 목록
        
        # 필수 필드에 대한 None 체크
        if not post_type or not title or not category or not price or not deal_method or not image:
            error_message = "필수 입력 필드가 누락되었습니다. 모든 필드를 입력해주세요."
            return render_template('signup.html', error_message=error_message)
    
        # 이미지 파일 저장
        image_paths = []
        for img in image:
            if img and allowed_file(img.filename):
                print(img.filename)
                unique_filename = f"{uuid.uuid4().hex}_{img.filename}"
                img_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                img.save(img_path)
                image_paths.append(img_path)
            else:
                print("허용되지 않는 파일 형식입니다.")

        image_str = ','.join(image_paths) if image_paths else None
        print(image_str)

        # 데이터베이스 연결 상태 확인
        if db_connection and db_connection.open:
            print("데이터베이스 연결 상태: 정상")  
        else:
            print("데이터베이스 연결에 문제가 있습니다.")
    
        # 데이터베이스에 게시글 저장
        try:
            with db_connection.cursor() as cursor:
                # 데이터 삽입 SQL 쿼리
                # 이미지 파일 이름을 문자열로 변환
                sql = """
                    INSERT INTO posts (user_nickName, title, category, content, deal_method, price, image, post_type, user_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (user_nickName, title, category, content, deal_method, price, image_str, post_type, user_id))
                db_connection.commit()  # 변경 사항 저장
                
                print("저장완료")
                
                # 방금 작성한 게시글의 id 가져오기
                post_id = cursor.lastrowid                
                
        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            return "게시글 등록 실패!"

        # 글 작성 완료 후 메인 페이지로 리다이렉트
        return redirect(url_for('post_detail', post_id=post_id))

# 게시글 수정 처리 라우트
@app.route('/update_post/<int:post_id>', methods=['POST'])
def update_post(post_id):
    if request.method == 'POST':
        # 세션에서 user_id 가져오기
        user_id = session.get('user_id')
        
        # 세션에 user_id가 없으면 로그인 페이지로 리다이렉트
        if not user_id:
            return redirect(url_for('login'))
        
        # 폼 데이터 가져오기
        title = request.form.get('title')
        category = request.form.get('category')
        price = request.form.get('price')
        content = request.form.get('content')
        deal_method = request.form.get('deal_method')
        new_images = request.files.getlist('image')  # 이미지 파일 목록
        
        # 데이터베이스 연결 상태 확인
        if db_connection and db_connection.open:
            print("데이터베이스 연결 상태: 정상")  
        else:
            print("데이터베이스 연결에 문제가 있습니다.")
        
        try:
            with db_connection.cursor() as cursor:
                # 기존 이미지 경로 가져오기
                sql = "SELECT image FROM posts WHERE id = %s AND user_id = %s"
                cursor.execute(sql, (post_id, user_id))
                result = cursor.fetchone()

                if result:
                    # 기존 이미지 경로를 리스트로 분리
                    existing_image_paths = result['image'].split(',') if result['image'] else []

                    # 기존 이미지 파일 삭제
                    for img_path in existing_image_paths:
                        if os.path.exists(img_path):
                            os.remove(img_path)

                    # 새로운 이미지 저장
                    new_image_paths = []
                    for img in new_images:
                        if img:
                            # 고유한 파일 이름 생성
                            unique_filename = f"{uuid.uuid4().hex}_{img.filename}"
                            img_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                            img.save(img_path)
                            new_image_paths.append(img_path)
                        
                    # 새 이미지 경로를 문자열로 변환
                    image_str = ','.join(new_image_paths) if new_image_paths else None

                    # 데이터베이스 업데이트
                    update_sql = """
                        UPDATE posts SET title = %s, category = %s, content = %s,
                        deal_method = %s, price = %s, image = %s
                        WHERE id = %s AND user_id = %s
                    """
                    cursor.execute(update_sql, (title, category, content, deal_method, price, image_str, post_id, user_id))
                    db_connection.commit()
                        
        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            return "게시글 수정 실패!"
    
    # 수정 완료 후 해당 게시글 상세 페이지로 리다이렉트
    return redirect(url_for('read', post_id=post_id))

# 게시글 삭제 처리 라우트
@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    # 데이터베이스 연결 상태 확인
    if db_connection and db_connection.open:
        print("데이터베이스 연결 상태: 정상")
    else:
        print("데이터베이스 연결에 문제가 있습니다.")
        
    try:
        with db_connection.cursor() as cursor:
            # 삭제할 게시글의 이미지 경로 가져오기
            sql_select = "SELECT image FROM posts WHERE id = %s"
            cursor.execute(sql_select, (post_id,))
            result = cursor.fetchone()

            if result and result['image']:
                # 이미지 경로 문자열을 리스트로 변환
                image_paths = result['image'].split(',')

                # 서버에서 이미지 파일 삭제
                for img_path in image_paths:
                    if os.path.exists(img_path):
                        os.remove(img_path)
                        print(f"{img_path} 삭제 완료")
                    else:
                        print(f"{img_path} 파일을 찾을 수 없습니다.")
        
            # 데이터베이스에서 게시글 삭제
            sql_delete = "DELETE FROM posts WHERE id = %s"
            cursor.execute(sql_delete, (post_id,))
            db_connection.commit()  # 변경 사항 저장
            print(f"게시글 {post_id} 삭제 완료")
            
    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return "게시글 삭제 실패!", 500

    # 삭제 완료 후 메인 페이지로 리다이렉트
    return redirect(url_for('view_mainHome'))

# 게시글 상세 보기 처리 라우트
@app.route('/post_detail/<int:post_id>', methods=['GET', 'POST'])
def post_detail(post_id):
    # 데이터베이스 연결 상태 확인
    if db_connection and db_connection.open:
        print("데이터베이스 연결 상태: 정상")  
    else:
        print("데이터베이스 연결에 문제가 있습니다.")
    
    try:
        with db_connection.cursor() as cursor:
            # post 테이블에서 특정 post_id에 따른 게시글 정보 가져오기
            sql = "SELECT * FROM posts WHERE id = %s"
            cursor.execute(sql, (post_id,))
            post = cursor.fetchone()

            if not post:
                return "error: 해당 게시글을 찾을 수 없습니다."

            # 게시글 정보를 post_detail.html로 전달하여 렌더링
            return render_template('post_detail.html', post=post)

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return "error: 게시글을 가져오는 중 오류가 발생했습니다."

# 특정 학교 필터 선택 시 해당 학교 관련 게시글 정보 넘겨주는 라우트
@app.route('/posts_by_university_name/<string:university_name>', methods=['GET', 'POST'])
def posts_by_university_name(university_name):
    # 데이터베이스 연결 상태 확인
    if db_connection and db_connection.open:
        print("데이터베이스 연결 상태: 정상")
    else:
        print("데이터베이스 연결에 문제가 있습니다.")
        
    try:
        with db_connection.cursor() as cursor:
            # users 테이블과 posts 테이블을 조인하여 해당 대학교의 사용자들이 작성한 게시글 가져오기
            sql = """
                SELECT posts.*
                FROM posts
                JOIN users ON posts.user_id = users.id
                WHERE users.university_classification = %s
            """
            cursor.execute(sql, (university_name,))
            posts = cursor.fetchall()
            
            print("-----------------------------")
            print(posts)

            # 게시글이 없을 경우
            if not posts:
                return "해당 대학교의 게시글이 없습니다.", 404

            # 게시글 정보를 반환
            return render_template('post_detail.html', posts=posts)

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return "게시글을 가져오는 중 오류가 발생했습니다.", 500

# 특정 카테고리 선택 시 해당 카테고리 관련 게시글 정보 넘겨주는 라우트
@app.route('/posts_by_category/<string:category>', methods=['GET', 'POST'])
def posts_by_category(category):
    # 데이터베이스 연결 상태 확인
    if db_connection and db_connection.open:
        print("데이터베이스 연결 상태: 정상")
    else:
        print("데이터베이스 연결에 문제가 있습니다.")
    
    try:
        with db_connection.cursor() as cursor:
            # posts 테이블에서 category에 따른 게시글 가져오기
            sql = "SELECT * FROM posts WHERE category = %s"
            cursor.execute(sql, (category,))
            posts = cursor.fetchall()
            
            print("-----------------------------")
            print(posts)

            # 게시글이 없을 경우
            if not posts:
                return "해당 카테고리의 게시글이 없습니다.", 404

            # 게시글 정보를 반환
            return render_template('post_detail.html', posts=posts)

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return "게시글을 가져오는 중 오류가 발생했습니다.", 500

# 마이페이지 이동 시 로그인 된 사용자의 중고거래 및 대리구매 글, 찜한 게시글 정보 넘기는 라우트
@app.route('/MyPage', methods=['GET', 'POST'])
def MyPage():
    # 세션에서 user_id 정보 가져오기
    user_id = session.get('user_id')
    
    if db_connection and db_connection.open:
        print("데이터베이스 연결 상태: 정상")
    else:
        print("데이터베이스 연결에 문제가 있습니다.")
    
    try:
        with db_connection.cursor() as cursor:
            # posts 테이블에서 user_id에 따른 모든 게시글(중고거래 및 대리구매) 가져오기
            sql = "SELECT * FROM posts WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            created_posts = cursor.fetchall()
            
            # users 테이블에서 user_id에 따른 bookmarked_posts 필드 가져오기
            sql = "SELECT bookmarked_posts FROM users WHERE id = %s"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            
            # bookmarked_posts 필드에서 찜한 게시글의 ID 목록을 가져와 posts 테이블에서 해당 게시글들 조회
            bookmarked_posts = result['bookmarked_posts'] if result else None
            bookmarked_post_data = []
            if bookmarked_posts:
                post_ids = bookmarked_posts.split(',')  # 찜한 게시글 ID들을 리스트로 변환
                if post_ids:
                    # 찜한 게시글의 ID들을 이용해 posts 테이블에서 해당 게시글들 가져오기
                    sql = "SELECT * FROM posts WHERE id IN (%s)" % ','.join(['%s'] * len(post_ids))
                    cursor.execute(sql, post_ids)
                    bookmarked_post_data = cursor.fetchall()
            
            # 결과 출력 (디버깅 용도)
            print("-----------------------------")
            print("Created Posts:", created_posts)
            print("-----------------------------")
            print("Bookmarked Posts:", bookmarked_post_data)

            # 마이페이지로 작성한 글과 찜한 글 정보를 넘김
            return render_template('mypage.html', created_posts=created_posts, bookmarked_posts=bookmarked_post_data)

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return "게시글을 가져오는 중 오류가 발생했습니다.", 500

# 자신이 작성한 중고거래 및 대리구매 글 자세히 보기 페이지 이동 시 로그인 된 사용자의 중고거래 및 대리구매 정보 넘기는 라우트
@app.route('/MyPosts/<string:post_type>', methods=['GET', 'POST'])
def MyPosts(post_type):
    # 세션에서 user_id 정보 가져오기
    user_id = session.get('user_id')
    
    if db_connection and db_connection.open:
        print("데이터베이스 연결 상태: 정상")
    else:
        print("데이터베이스 연결에 문제가 있습니다.")
    
    try:
        with db_connection.cursor() as cursor:
            # posts 테이블에서 post_type 따른 모든 게시글(중고거래 및 대리구매) 가져오기
            sql = "SELECT * FROM posts WHERE post_type = %s"
            cursor.execute(sql, (post_type,))
            created_posts = cursor.fetchall()
            
            # 결과 출력 (디버깅 용도)
            print("-----------------------------")
            print("Created Posts:", created_posts)

            # 중고거래 및 대리구매 상세 페이지로 작성한 글과 찜한 글 정보를 넘김
            if post_type == "중고거래":
                return render_template('mypage.html', created_posts=created_posts)
            elif post_type == "대리구매":
                return render_template('mypage.html', created_posts=created_posts)

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return "게시글을 가져오는 중 오류가 발생했습니다.", 500

# 로그인 된 사용자가 찜한 게시글 정보 넘기는 라우트
@app.route('/My_bookmarked_posts', methods=['GET', 'POST'])
def My_bookmarked_posts():
    # 세션에서 user_id 정보 가져오기
    user_id = session.get('user_id')
    
    if db_connection and db_connection.open:
        print("데이터베이스 연결 상태: 정상")
    else:
        print("데이터베이스 연결에 문제가 있습니다.")
    
    try:
        with db_connection.cursor() as cursor:
            # users 테이블에서 user_id에 따른 bookmarked_posts 필드 가져오기
            sql = "SELECT bookmarked_posts FROM users WHERE id = %s"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            
            # bookmarked_posts 필드에서 찜한 게시글의 ID 목록을 가져와 posts 테이블에서 해당 게시글들 조회
            bookmarked_posts = result['bookmarked_posts'] if result else None
            bookmarked_post_data = []
            if bookmarked_posts:
                post_ids = bookmarked_posts.split(',')  # 찜한 게시글 ID들을 리스트로 변환
                if post_ids:
                    # 찜한 게시글의 ID들을 이용해 posts 테이블에서 해당 게시글들 가져오기
                    sql = "SELECT * FROM posts WHERE id IN (%s)" % ','.join(['%s'] * len(post_ids))
                    cursor.execute(sql, post_ids)
                    bookmarked_post_data = cursor.fetchall()
            
            # 결과 출력 (디버깅 용도)
            print("-----------------------------")
            print("Bookmarked Posts:", bookmarked_post_data)

            # 마이페이지로 작성한 글과 찜한 글 정보를 넘김
            return render_template('mypage.html', bookmarked_posts=bookmarked_post_data)

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return "게시글을 가져오는 중 오류가 발생했습니다.", 500


# 찜 처리 라우트
@app.route('/bookmark/<int:post_id>', methods=['GET', 'POST'])
def bookmark(post_id):
    # 세션에서 user_id 가져오기
    user_id = session.get('user_id')
    
    # 세션에 사용자 정보가 없으면 해당 게시글 상세 페이지로 리다이렉트
    if not user_id or not user_id:
        return render_template('post_detail.html')
    
    # 데이터베이스 연결 상태 확인
    if db_connection and db_connection.open:
        print("데이터베이스 연결 상태: 정상")
    else:
        print("데이터베이스 연결에 문제가 있습니다.")
        
    try:
        with db_connection.cursor() as cursor:
            # 1. users 테이블에서 user_id에 따른 bookmarked_posts 정보 가져오기
            sql_get_bookmarked_posts = "SELECT bookmarked_posts FROM users WHERE id = %s"
            cursor.execute(sql_get_bookmarked_posts, (user_id,))
            result = cursor.fetchone()
            if result:
                bookmarked_posts = result['bookmarked_posts']
                
                # 2. bookmarked_posts에 현재 post_id가 이미 있는지 확인
                if bookmarked_posts and str(post_id) in bookmarked_posts.split(','):
                    error_message = "이미 찜 한 게시글입니다."
                    return render_template('post_detail.html', error_message=error_message)
                
                # 3. 찜하지 않은 경우 post_id를 bookmarked_posts에 추가
                if bookmarked_posts:
                    updated_bookmarked_posts = f"{bookmarked_posts},{post_id}"
                else:
                    updated_bookmarked_posts = str(post_id)
                
                # users 테이블의 bookmarked_posts 업데이트
                sql_update_bookmarked_posts = "UPDATE users SET bookmarked_posts = %s WHERE id = %s"
                cursor.execute(sql_update_bookmarked_posts, (updated_bookmarked_posts, user_id))

                # 4. posts 테이블에서 해당 post_id의 bookmarked_count 필드 값 증가
                sql_update_bookmark_count = "UPDATE posts SET bookmarked_count = bookmarked_count + 1 WHERE id = %s"
                cursor.execute(sql_update_bookmark_count, (post_id,))
                
                db_connection.commit()
                error_message = "찜 되었습니다."
                return render_template('post_detail.html', error_message=error_message)
            else:
                error_message = "사용자를 찾을 수 없습니다."
                return render_template('post_detail.html', error_message=error_message)

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        error_message = "찜 처리에 실패했습니다."
        return render_template('post_detail.html', error_message=error_message)

    # 찜 처리 완료 후 해당 게시글 상세 페이지로 리다이렉트
    return redirect('post_detail.html', post_id=post_id)

@app.route('/chat/<int:chat_id>', methods=['GET'])
def get_messages(chat_id):
  db_connection = connect_to_db()
  cursor = db_connection.cursor()
  
  query = "SELECT * FROM messages WHERE chat_id = %s"
  cursor.execute(query, (chat_id,))
  messages = cursor.fetchall()

  result = [{
      'id': msg['id'],
      'sender_id': msg['sender_id'],
      'message_text': msg['message_text'],
      'message_type': msg['message_type'],
      'created_at': msg['created_at'],
      'is_read': msg['is_read']
  } for msg in messages]

  db_connection.close()

  return jsonify(result), 200


# 사용자가 포함되어있는 채팅방 불러오는 API 
# 용도: [글쓰기] 메뉴탭 클릭 시 채팅방 사용자가 포함되어있는 채팅방 목록 보여야된다. 
@app.route('/chatrooms/<int:user_id>', methods=['GET'])
def get_chattingRooms(user_id):
  # 데이터베이스 연결
  db_connection = connect_to_db()
  cursor = db_connection.cursor()

  # SQL 쿼리문 작성 (user_id가 포함된 채팅방 조회)
  query = """
      SELECT chat_room.id, chat_room.name
      FROM chat_member
      JOIN chat_room ON chat_member.chat_id = chat_room.id
      WHERE chat_member.user_id = %s
  """
  
  # 쿼리 실행
  cursor.execute(query, (user_id,))
  
  # 결과 가져오기
  chat_rooms = cursor.fetchall()

  cursor.close()
  db_connection.close()
  
  # JSON 응답 생성
  result = []
  for chat_room in chat_rooms:
      result.append({
          'chat_id': chat_room['id'],
          'name': chat_room['name']
      })

  return jsonify(result), 200
    
@socketio.on("connect")
def handle_connect():
    """
    클라이언트 연결 시 호출
    """
    print("Client connected")


@socketio.on("disconnect")
def handle_disconnect():
    """
    클라이언트 연결 해제 시 호출
    """
    print("Client disconnected")


@socketio.on("join")
def on_join(data):
    room_name = data["room"]

    # TODO: user_id 나중에 토큰(?)에 저장된 값으로 불러오게 변경. 
    # user_id = session.get('user_id')
    user_id = 2

    db_connection = connect_to_db()
    cursor = db_connection.cursor()

    # 1. 채팅방이 존재하는지 확인
    check_chat_room_query = """
        SELECT id FROM chat_room WHERE name = %s
    """
    cursor.execute(check_chat_room_query, (room_name,))
    chat_room = cursor.fetchone()

    # 2. 채팅방이 없으면 새로 생성
    if not chat_room:
        create_chat_room_query = """
            INSERT INTO chat_room (name) VALUES (%s) RETURNING id
        """
        cursor.execute(create_chat_room_query, (room_name,))
        db_connection.commit()
        chat_room = cursor.fetchone()

    chat_room_id = chat_room['id']

    # 3. 사용자가 이미 이 방에 참여했는지 확인
    check_chat_member_query = """
        SELECT id FROM chat_member WHERE chat_id = %s AND user_id = %s
    """
    cursor.execute(check_chat_member_query, (chat_room_id, user_id))
    chat_member = cursor.fetchone()

    # 4. 참여하지 않았으면 ChatMember 테이블에 추가
    if not chat_member:
        insert_chat_member_query = """
            INSERT INTO chat_member (chat_id, user_id) VALUES (%s, %s)
        """
        cursor.execute(insert_chat_member_query, (chat_room_id, user_id))
        db_connection.commit()

    # 5. 클라이언트를 소켓 채팅방에 참여시킴
    join_room(room_name)

    # 6. 클라이언트에게 알림 전송
    emit("status", {"msg": f"User {user_id} has joined the room: {room_name}"}, room=room_name)

    # 데이터베이스 연결 해제
    cursor.close()
    db_connection.close()



@socketio.on("leave")
def on_leave(data):
    """
    클라이언트가 채팅방을 나갈 때 호출되는 이벤트 핸들러입니다.

    Args:
        data (dict): 클라이언트로부터 받은 데이터. 'room' 키를 포함해야 합니다.
    """
    room = data["room"]
    leave_room(room)
    emit("status", {"msg": f"User has left the room: {room}"}, room=room)


@socketio.on("chat")
def handle_chat(data):
    """
    채팅 메시지를 처리하는 이벤트 핸들러입니다.

    Args:
        data (dict): 클라이언트로부터 받은 데이터. 'room', 'message', 'from' 키를 포함해야 합니다.
    """

    # user_id = session.get('user_id')
    user_id = 2

    room_name = data["room"]  # 클라이언트로부터 받은 room (이름)
    message = data["message"]
    from_id = data["from"] 

    print("chat 소켓 값 확인: ", room_name)

    # 데이터베이스 연결
    db_connection = connect_to_db()
    cursor = db_connection.cursor()

    # 채팅방 이름(room_name)을 바탕으로 DB에서 chat_id 조회
    check_chat_room_query = """
        SELECT id FROM chat_room WHERE name = %s
    """
    cursor.execute(check_chat_room_query, (room_name,))
    chat_room = cursor.fetchone()

    if chat_room:
        chat_id = chat_room['id']  # chat_id를 얻음
    else:
        # 해당 room이 없을 경우 처리 (예: 에러 메시지 반환)
        print("채팅방을 찾을 수 없습니다.")
        cursor.close()
        db_connection.close()
        return

    # 메시지를 DB에 저장
    insert_message_query = """
        INSERT INTO messages (chat_id, sender_id, message_text, message_type, created_at)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
    """
    cursor.execute(insert_message_query, (chat_id, user_id, message, 'text', datetime.now()))
    db_connection.commit()
    
    # 새로 저장된 메시지 ID 가져오기
    message_id= cursor.fetchone()['id']

    # json 타입으로 직렬화하기 
    message_data = {
        "type": "chat",
        "message": message,
        "from": from_id,
        "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # 현재 시간
        "message_id": message_id  # 메시지 ID 추가
    }

    # 클라이언트로 메시지 전송
    emit("chat", message_data, room=room_name)
    print(data)

    # 데이터베이스 연결 해제
    cursor.close()
    db_connection.close()

@socketio.on("location")
def handle_location(data):
    """
    위치 정보를 처리하는 이벤트 핸들러입니다.

    Args:
        data (dict): 클라이언트로부터 받은 데이터. 'room', 'location', 'from' 키를 포함해야 합니다.
    """
    room = data["room"]
    location = data["location"]
    from_id = data["from"]
    emit(
        "location",
        {"type": "location", "location": location, "from": from_id},
        room=room,
    )


@socketio.on("real_time_location")
def handle_real_time_location(data):
    """
    실시간 위치 정보를 처리하는 이벤트 핸들러입니다.

    Args:
        data (dict): 클라이언트로부터 받은 데이터. 'room', 'location', 'from' 키를 포함해야 합니다.
    """
    room = data["room"]
    location = data["location"]
    from_id = data["from"]
    timestamp = int(time.time() * 1000)  # 현재 시간을 밀리초로 변환
    emit(
        "real_time_location",
        {
            "type": "real_time_location",
            "location": location,
            "from": from_id,
            "timestamp": timestamp,
        },
        room=room,
        include_self=False,  # 자신을 제외한 다른 클라이언트에게만 전송
    )



if __name__ == '__main__':
    socketio.run(app, debug=True)
    app.run(port=5000, debug=True)