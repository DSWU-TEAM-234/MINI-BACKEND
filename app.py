from flask import Flask, request, render_template, redirect, url_for, session
import pymysql
from datetime import timedelta
import os
import uuid

app = Flask(__name__)
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
        
        # 대학교 이름이 입력되지 않았을 경우 None으로 설정
        if not university_classification:
            university_classification = None
        
        # 데이터베이스 연결 상태 확인
        if db_connection and db_connection.open:
            print("데이터베이스 연결 상태: 정상")  
        else:
            print("데이터베이스 연결에 문제가 있습니다.")
        
        # 데이터베이스에 회원 정보 저장
        try:
            with db_connection.cursor() as cursor:
                # 데이터 삽입 SQL 쿼리
                sql = """
                    INSERT INTO users (name, email, password, nick_name, university_classification)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (name, email, password, nick_name, university_classification))
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
                cursor.execute(sql, (email))
                user = cursor.fetchone()
                print(user)# 해당 이메일로 등록된 사용자 정보 가져오기

                if not user:
                    # 이메일이 존재하지 않을 때 오류 메시지 전달
                    error_message = "등록된 사용자 정보가 없습니다."
                    return render_template('login.html', error_message=error_message)
                else:
                    # 이메일이 존재하는 경우, 비밀번호 확인
                    if user['password'] == password:
                        # 비밀번호가 일치하면 로그인 성공
                        session['user_id'] = user['id']
                        session['user_nickName'] = user['nick_name']
                        session.permanent = True  # 영구 세션 사용
                        print(session['user_id'])
                        print(session['user_nickName'])
                        # login_success 파라미터를 True로 설정하여 홈으로 리다이렉트
                        return redirect(url_for('view_mainHome', login_success=True))
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
    
        # 이미지 파일 저장
        image_paths = []
        for img in image:
            if img and allowed_file(img.filename):
                unique_filename = f"{uuid.uuid4().hex}_{img.filename}"
                img_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                img.save(img_path)
                image_paths.append(img_path)
            else:
                print("허용되지 않는 파일 형식입니다.")

        image_str = ','.join(image_paths) if image_paths else None


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
        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            return "게시글 등록 실패!"

        # 글 작성 완료 후 메인 페이지로 리다이렉트
        return redirect(url_for('view_mainHome'))

# 게시글 상세 보기 처리 라우트
@app.route('/read_posts', methods=['POST'])
def read_posts():
    if request.method == 'POST':
        # 세션에서 user_id 가져오기
        user_id = session.get('user_id')
        
        # 데이터베이스 연결 상태 확인
        if db_connection and db_connection.open:
            print("데이터베이스 연결 상태: 정상")  
        else:
            print("데이터베이스 연결에 문제가 있습니다.")
            
        try:
            with db_connection.cursor() as cursor:
                # post 테이블에서 user_id에 따른 정보 가져오기
                sql = "SELECT * FROM posts WHERE user_id = %s"
                cursor.execute(sql, (user_id))
                user_posts = cursor.fetchall()  # 모든 게시글 가져오기
                
                # 결과 출력 (예시로 콘솔에 출력)
                if user_posts:
                    for post in user_posts:
                        print(post)
                else:
                    print("작성한 게시물이 없습니다.")
                    
        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            return "게시글을 가져오는 중 오류가 발생했습니다."
    
    # 게시글 목록을 상세 보기 페이지로 전달
    return render_template('post_detail.html', posts=user_posts)

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

if __name__ == '__main__':
    app.run(port=5000, debug=True)