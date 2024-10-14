from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import pymysql
from datetime import timedelta
import os
import uuid
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = 'your_secret_key_here'

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # 세션 지속 시간 설정

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

# 전역 MySQL 연결 객체
db_connection = None

# 첫 요청 때 MySQL 연결
@app.before_first_request
def initialize_db():
    global db_connection
    db_connection = connect_to_db()
    print("데이터베이스 연결에 성공했습니다.")


# 처음으로 로드될 중고거래 홈 라우트
@app.route('/', methods=['GET', 'POST'])
def view_mainHome():
    print("------------------------------")
    print("중고거래 홈 라우트 실행")
    
    # 세션에서 university_name 가져오기
    university_name = session.get('university_name')
    
    # 세션에 university_name이 없거나 "외부인"일 경우, 덕성여자대학교 관련 게시글 정보를 넘기기위해 "덕성여자대학교"로 지정함
    if not university_name or university_name == "외부인":
        university_name = "덕성여자대학교"
    
    # 데이터베이스 연결 상태 확인
    if db_connection and db_connection.open:
        print("데이터베이스 연결 상태: 정상")  
    else:
        print("데이터베이스 연결에 문제가 있습니다.")
    
    try:
        with db_connection.cursor() as cursor:
            # users 테이블과 posts 테이블을 조인하여 해당 대학교의 사용자들이 작성한 중고거래 게시글 가져오기
            sql = """
                SELECT posts.*
                FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE users.university_classification = %s
        AND posts.post_type = '중고거래'
    """
            cursor.execute(sql, (university_name,))
            posts = cursor.fetchall()
            
            print("-----------------------------")
            print(university_name)
            print(posts)            

            # 게시글 정보를 반환
            # university_name(메인홈에 로드할 대학교 이름), posts(해당 대학교 회원이 작성한 게시글 정보)
            # university_name과 posts 데이터를 JSON 형식으로 반환
            return jsonify({
            'university_name': university_name,
            'posts': posts
            })

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return jsonify({"message": "게시글을 가져오는 중 오류가 발생했습니다."}), 500


# 처음으로 로드될 대리구매 홈 라우트
@app.route('/ProxyPurchasePage', methods=['GET', 'POST'])
def ProxyPurchasePage():
    print("------------------------------")
    print("대리구매 홈 라우트 실행")
    
    # 세션에서 university_name 가져오기
    university_name = session.get('university_name')
    
    # 세션에 university_name이 없거나 "외부인"일 경우, 덕성여자대학교 관련 게시글 정보를 넘기기위해 "덕성여자대학교"로 지정함
    if not university_name or university_name == "외부인":
        university_name = "덕성여자대학교"
    
    # 데이터베이스 연결 상태 확인
    if db_connection and db_connection.open:
        print("데이터베이스 연결 상태: 정상")  
    else:
        print("데이터베이스 연결에 문제가 있습니다.")
    
    try:
        with db_connection.cursor() as cursor:
            # users 테이블과 posts 테이블을 조인하여 해당 대학교의 사용자들이 작성한 중고거래 게시글 가져오기
            sql = """
                SELECT posts.*
                FROM posts
        JOIN users ON posts.user_id = users.id
        WHERE users.university_classification = %s
        AND posts.post_type = '대리구매'
    """
            cursor.execute(sql, (university_name,))
            posts = cursor.fetchall()
            
            print("-----------------------------")
            print(university_name)
            print(posts)            

            # 게시글 정보를 반환
            # university_name(메인홈에 로드할 대학교 이름), posts(해당 대학교 회원이 작성한 게시글 정보)
            # university_name과 posts 데이터를 JSON 형식으로 반환
            return jsonify({
            'university_name': university_name,
            'posts': posts
            })

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return jsonify({"message": "게시글을 가져오는 중 오류가 발생했습니다."}), 500


# 메인 홈의 대학교 선택 필터에 DB에 등록된 대학 목록을 띄우기 위해 university_name 정보를 가져오기
@app.route('/get_university_list', methods=['GET', 'POST'])
def get_university_list():
    # 데이터베이스 연결 상태 확인
    if db_connection and db_connection.open:
        print("데이터베이스 연결 상태: 정상")  
    else:
        print("데이터베이스 연결에 문제가 있습니다.")
    
    try:
            with db_connection.cursor() as cursor:
                sql_get_university_name = """
                SELECT university_name FROM university_and_logo
            """
                cursor.execute(sql_get_university_name)
                university_names_list = cursor.fetchall()  # 결과를 가져옴
                
                return jsonify({
                'university_names_list': university_names_list
                })
                
    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return jsonify({"message": "정보를 가져오는 중 오류가 발생했습니다."}), 500



# 회원가입 라우트
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    print("------------------------------")
    print("회원가입 라우트 실행")
    
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
                    message = "이미 등록된 이메일입니다."
                    return jsonify({
                'message': message
                })
                elif nick_name_exists:
                    message = "이미 사용 중인 닉네임입니다."
                    return jsonify({
                'message': message
                })
                
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
                
                # 회원가입 성공 시 홈 페이지로 리다이렉트하며 플래그 전달
                return jsonify({"message": "회원가입 성공"}), 201
    
        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            return jsonify({"message": "회원가입 실패"}), 500

# 로그인 라우트
@app.route('/login', methods=['GET', 'POST'])
def login():
    print("------------------------------")
    print("로그인 라우트 실행")
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
                    return jsonify({"message": "등록된 사용자 정보가 없습니다."})
                else:
                    # 이메일이 존재하는 경우, 비밀번호 해싱 비교
                    if bcrypt.check_password_hash(user['password'], password):
                        # 비밀번호가 일치하면 로그인 성공
                        session['user_id'] = user['id']  # 세션에 사용자 id 저장 
                        session['user_nickName'] = user['nick_name']  # 세션에 사용자 닉네임 저장
                        session['profile_image'] = user['profile_image'] # 세션에 사용자 프로필 이미지 경로 저장
                        
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
                        
                        # 로그인 성공 시
                        return jsonify({
            'message': "로그인 성공",
            'user_id': session['user_id'],
            'user_nickName' : session['user_nickName'],
            'profile_image' : session['profile_image'],
            'university_name' : session['university_name'],
            'university_logo' : session['university_logo']
            })
                        
                    else:
                        # 비밀번호가 틀렸을 때 오류 메시지 전달
                        return jsonify({"message": "비밀번호가 틀렸습니다. 다시 입력해주세요."}), 400
        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            return jsonify({"message": "로그인 중 오류가 발생했습니다."}), 500

# 로그아웃 라우트
@app.route('/logout')
def logout():
    print("------------------------------")
    print("로그아웃 라우트 실행")
    # 세션 정보 삭제
    session.pop('user_id', None)
    session.pop('user_nickName', None)
    
    # 데이터베이스 연결 끊기
    global db_connection
    if db_connection and db_connection.open:
        db_connection.close()
        print("데이터베이스 연결이 끊어졌습니다.")
    
    # 로그아웃 후 
    return jsonify({"message": "로그아웃되었습니다."})


# 글 작성 처리 라우트 (공통 라우트)
@app.route('/write_post', methods=['GET', 'POST'])
def write_post():
        print("------------------------------")
        print("글 작성 라우트 실행")
        # 세션에서 user_id 및 user_nickName 정보 가져오기
        user_id = session.get('user_id')
        user_nickName = session.get('user_nickName')

        print(user_id)
        print(user_nickName)

        # 세션에 사용자 정보가 없으면 로그인 페이지로 리다이렉트
        if not user_id or not user_nickName:
            return jsonify({"message": "로그인 후 이용 가능합니다."})

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
                
                # 글 작성 완료 후 상세 페이지로 리다이렉트
            return jsonify({"message": "게시글 등록 성공"}), 201
                
        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            return jsonify({"message": "게시글 등록 실패"}), 500


# 게시글 수정 처리 라우트
@app.route('/update_post/<int:post_id>', methods=['GET', 'POST'])
def update_post(post_id):
        print("------------------------------")
        print("글 수정 라우트 실행")
        
        # 세션에서 user_id 가져오기
        user_id = session.get('user_id')
        
        # 세션에 user_id가 없으면 로그인 페이지로 리다이렉트
        if not user_id:
            return jsonify({"message": "로그인 후 이용 가능합니다."})
        
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
                    
                    # 수정 완료 후 해당 게시글 상세 페이지로 리다이렉트
                    return redirect(url_for('post_detail', post_id=post_id))
                        
        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            return jsonify({"message": "게시글 수정 실패"}), 500


# 게시글 삭제 처리 라우트
@app.route('/delete_post/<int:post_id>', methods=['GET', 'POST'])
def delete_post(post_id):
    print("------------------------------")
    print("글 삭제 라우트 실행")
    
    # 세션이 없으면 로그인 페이지로 리다이렉트
    if not session:
        return jsonify({"message": "로그인 후 이용 가능합니다."})
    
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
            
            # 삭제 완료 후 메인 페이지로 리다이렉트
            return jsonify({"message": "게시글 삭제 성공"}), 201
            
    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return jsonify({"message": "게시글 삭제 실패"}), 500


# 게시글 상세 보기 처리 라우트
@app.route('/post_detail/<int:post_id>', methods=['GET', 'POST'])
def post_detail(post_id):
    print("------------------------------")
    print("게시글 상세 보기 라우트 실행")
    
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
            
            print(post)
            print("\n")

            # 게시글 정보를 post_detail.html로 전달하여 렌더링
            return jsonify({
            'post': post
            })

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return jsonify({"message": "게시글을 가져오는 중 오류가 발생했습니다."}), 500


# 중고거래 홈에서 특정 학교 필터 선택 시 해당 학교 관련 중고거래 게시글 정보 넘겨주는 라우트
@app.route('/posts_by_university_name/<string:university_name>', methods=['GET', 'POST'])
def posts_by_university_name(university_name):
    print("------------------------------")
    print("중고거래 홈에서 특정 학교 기반 중고거래 게시글 정보 전달 라우트 실행")
    
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
                AND posts.post_type = '중고거래'
            """
            cursor.execute(sql, (university_name,))
            posts = cursor.fetchall()
            
            print("-----------------------------")
            print(posts)
            print("\n")

            # 게시글 정보를 반환
            return jsonify({
            'posts': posts
            })

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return jsonify({"message": "게시글을 가져오는 중 오류가 발생했습니다."}), 500
    

# 대리구매 홈에서 특정 학교 필터 선택 시 해당 학교 관련 대리구매 게시글 정보 넘겨주는 라우트
@app.route('/ProxyPurchase_posts_by_university_name/<string:university_name>', methods=['GET', 'POST'])
def ProxyPurchase_posts_by_university_name(university_name):
    print("------------------------------")
    print("대리구매 홈에서 특정 학교 기반 대리구매 게시글 정보 전달 라우트 실행")
    
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
                AND posts.post_type = '대리구매'
            """
            cursor.execute(sql, (university_name,))
            posts = cursor.fetchall()
            
            print("-----------------------------")
            print(posts)
            print("\n")

            # 게시글 정보를 반환
            return jsonify({
            'posts': posts
            })

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return jsonify({"message": "게시글을 가져오는 중 오류가 발생했습니다."}), 500


# 특정 카테고리 선택 시 해당 카테고리 및 대학 관련 게시글 정보 넘겨주는 라우트
@app.route('/posts_by_category/<string:university_name>/<string:category>', methods=['GET', 'POST'])
def posts_by_category(university_name, category):
    print("------------------------------")
    print("특정 카테고리 및 대학교 기반 게시글 정보 전달 라우트 실행")
    
    # 데이터베이스 연결 상태 확인
    if db_connection and db_connection.open:
        print("데이터베이스 연결 상태: 정상")
    else:
        print("데이터베이스 연결에 문제가 있습니다.")
    
    try:
        with db_connection.cursor() as cursor:
            # users 테이블과 posts 테이블을 조인하여, 특정 대학교의 사용자들이 작성한 특정 카테고리의 게시글 가져오기
            sql = """
                SELECT posts.*
                FROM posts
                JOIN users ON posts.user_id = users.id
                WHERE users.university_classification = %s AND posts.category = %s
            """
            cursor.execute(sql, (university_name, category))
            posts = cursor.fetchall()

            # 게시글 정보를 반환
            return jsonify(posts=posts), 200

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return jsonify({"message": "게시글을 가져오는 중 오류가 발생했습니다."}), 500


# 마이페이지 이동 시 로그인 된 사용자의 중고거래 및 대리구매 글, 찜한 게시글 정보 넘기는 라우트
@app.route('/MyPage', methods=['GET', 'POST'])
def MyPage():
    print("------------------------------")
    print("마이페이지 라우트 실행")
    
    # 세션에서 user_id 정보 가져오기
    user_id = session.get('user_id')
    
    # 세션에 사용자 정보가 없으면 로그인 페이지로 리다이렉트
    if not user_id:
        return jsonify({"message": "로그인 후 이용 가능합니다."})
    
    if db_connection and db_connection.open:
        print("데이터베이스 연결 상태: 정상")
    else:
        print("데이터베이스 연결에 문제가 있습니다.")
    
    try:
        with db_connection.cursor() as cursor:
            # posts 테이블에서 user_id에 따른 모든 중고거래 게시글 가져오기
            sql = "SELECT * FROM posts WHERE user_id = %s AND post_type = '중고거래'"
            cursor.execute(sql, (user_id,))
            posts = cursor.fetchall()
            
            # posts 테이블에서 user_id에 따른 모든 대리구매 게시글 가져오기
            sql = "SELECT * FROM posts WHERE user_id = %s AND post_type = '대리구매'"
            cursor.execute(sql, (user_id,))
            ProxyPurchase_posts = cursor.fetchall()
            
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
            print("Posts:", posts)
            print("\n")
            print("-----------------------------")
            print("ProxyPurchase_posts:", ProxyPurchase_posts)
            print("\n")
            print("-----------------------------")
            print("Bookmarked Posts:", bookmarked_post_data)
            print("\n")

            # 마이페이지로 작성한 글과 찜한 글 정보를 넘김
            return jsonify({
            'posts': posts,
            'ProxyPurchase_posts' : ProxyPurchase_posts,
            'bookmarked_post_data' : bookmarked_post_data
            })
            
    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return jsonify({"message": "게시글을 가져오는 중에 오류가 발생했습니다."}), 500


# 자신이 작성한 중고거래 또는 대리구매 글 자세히 보기 페이지 이동 시 로그인 된 사용자의 중고거래 및 대리구매 정보 넘기는 라우트
@app.route('/MyPosts/<string:post_type>', methods=['GET', 'POST'])
def MyPosts(post_type):
    print("------------------------------")
    print("자신이 작성한 중고거래 또는 대리구매 글 정보 전달 라우트 실행")
    
    # 세션에 사용자 정보가 없으면 로그인 페이지로 리다이렉트
    if not session:
        return jsonify({"message": "로그인 후 이용 가능합니다."})
        
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
            print("\n")

            # 중고거래 및 대리구매 상세 페이지로 작성한 글과 찜한 글 정보를 넘김
            return jsonify(created_posts = created_posts)

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return jsonify({"message": "게시글을 가져오는 중 오류가 발생했습니다."}), 500


# 로그인 된 사용자가 찜한 게시글 정보 넘기는 라우트
@app.route('/My_bookmarked_posts', methods=['GET', 'POST'])
def My_bookmarked_posts():
    print("------------------------------")
    print("로그인 된 사용자가 찜한 게시글 정보 넘기는 라우트 실행")
    
    # 세션에서 user_id 정보 가져오기
    user_id = session.get('user_id')
    
    # 세션에 사용자 정보가 없으면 로그인 페이지로 리다이렉트
    if not user_id:
        return jsonify({"message": "로그인 후 이용 가능합니다."})
    
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
            print("\n")

            # 마이페이지로 작성한 글과 찜한 글 정보를 넘김
            return jsonify(bookmarked_posts=bookmarked_post_data)

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return jsonify({"message": "게시글을 가져오는 중 오류가 발생했습니다."}), 500


# 찜 처리 라우트
@app.route('/bookmark/<int:post_id>', methods=['GET', 'POST'])
def bookmark(post_id):
    print("------------------------------")
    print("찜 처리 라우트 실행")
    
    # 세션에서 user_id 가져오기
    user_id = session.get('user_id')
    
    # 세션에 사용자 정보가 없으면 로그인 페이지로 리다이렉트
    if not user_id:
        return jsonify({"message": "로그인 후 이용 가능합니다."})
    
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
                    return jsonify(message = "이미 찜 한 게시글입니다.")
                
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
                return jsonify(message = "찜 되었습니다.")
            else:
                return jsonify(message = "사용자를 찾을 수 없습니다.")

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return jsonify({"message": "찜 처리에 실패했습니다."}), 500

# 찜 취소 처리 라우트
@app.route('/cancle_bookmark/<int:post_id>', methods=['GET', 'POST'])
def cancle_bookmark(post_id):
    print("------------------------------")
    print("찜 취소 라우트 실행")
    
    # 세션에서 user_id 가져오기
    user_id = session.get('user_id')
    
    # 세션에 사용자 정보가 없으면 로그인 페이지로 리다이렉트
    if not user_id:
        return jsonify({"message": "로그인 후 이용 가능합니다."})
    
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
                
                # 2. bookmarked_posts에 현재 post_id가 있는지 확인 (찜한 게시물인지)
                if bookmarked_posts and str(post_id) in bookmarked_posts.split(','):
                    # 3. post_id를 bookmarked_posts에서 제거
                    updated_bookmarked_posts = ','.join([p for p in bookmarked_posts.split(',') if p != str(post_id)])
                    
                    # users 테이블의 bookmarked_posts 업데이트
                    sql_update_bookmarked_posts = "UPDATE users SET bookmarked_posts = %s WHERE id = %s"
                    cursor.execute(sql_update_bookmarked_posts, (updated_bookmarked_posts, user_id))

                    # 4. posts 테이블에서 해당 post_id의 bookmarked_count 필드 값 감소
                    sql_update_bookmark_count = "UPDATE posts SET bookmarked_count = bookmarked_count - 1 WHERE id = %s"
                    cursor.execute(sql_update_bookmark_count, (post_id,))
                    
                    db_connection.commit()
                    return jsonify({"message": "찜 취소 성공"}), 201
            else:
                return jsonify({"message": "사용자를 찾을 수 없습니다."}), 400

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return jsonify({"message": "찜 취소를 실패했습니다."}), 500


# 대학별 굿즈 정보 가져오는 라우트
@app.route('/get_goods_by_university/<string:university_name>', methods=['GET', 'POST'])
def get_goods_by_university(university_name):
    print("------------------------------")
    print("대학별 굿즈 정보 가져오는 라우트 실행")
    
    # 데이터베이스 연결 상태 확인
    if db_connection and db_connection.open:
        print("데이터베이스 연결 상태: 정상")
    else:
        print("데이터베이스 연결에 문제가 있습니다.")
    
    try:
        with db_connection.cursor() as cursor:
            # goods 테이블에서 university_name에 따른 굿즈 정보 가져오기
            sql_get_goods = "SELECT * FROM goods WHERE university = %s"
            cursor.execute(sql_get_goods, (university_name,))
            goods_list = cursor.fetchall()
            return jsonify(goods_list=goods_list)
            
    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return jsonify({"message": "굿즈 정보를 가져올 수 없습니다."}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)