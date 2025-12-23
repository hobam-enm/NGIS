import streamlit as st
import extra_streamlit_components as stx
import hashlib
import time
import datetime

# ==============================================================================
# 1. 페이지 설정 (최초 실행 필수)
# ==============================================================================
st.set_page_config(
    page_title="부정이슈 현황판",
    layout="wide",
    initial_sidebar_state="collapsed" # 사이드바 강제 숨김
)

# ==============================================================================
# 2. CSS 스타일링 (UI 전체 숨기기 & 풀스크린)
# ==============================================================================
st.markdown("""
<style>
    /* 1. 스트림릿 기본 헤더 및 장식 숨기기 */
    header[data-testid="stHeader"] { display: none !important; }
    div[data-testid="stDecoration"] { display: none !important; }
    
    /* 2. 메인 컨텐츠 영역 여백 제거 (화면 꽉 채우기) */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
    }
    div[data-testid="stAppViewBlock"] {
        padding: 0 !important;
    }
    
    /* 3. 사이드바 관련 요소 숨기기 (혹시 모를 잔재 제거) */
    section[data-testid="stSidebar"] { display: none !important; }
    div[data-testid="collapsedControl"] { display: none !important; }

    /* 4. 아이프레임 컨테이너 스타일 */
    .fullscreen-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: 9999;
        overflow: hidden;
    }
    iframe {
        width: 100%;
        height: 100%;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. 인증 로직 (Dashboard.py 기반)
# ==============================================================================
def _rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

def _hash_password(password: str) -> str:
    return hashlib.sha256(str(password).encode()).hexdigest()

def check_auth():
    """쿠키 및 세션을 이용한 인증 체크"""
    # 쿠키 매니저 초기화
    cookie_manager = stx.CookieManager(key="auth_cookie_manager")
    
    # Secrets 확인
    if "DASHBOARD_PASSWORD" not in st.secrets:
        st.error("Secrets에 'DASHBOARD_PASSWORD'가 설정되지 않았습니다.")
        st.stop()
        
    correct_hash = _hash_password(st.secrets["DASHBOARD_PASSWORD"])
    
    # 쿠키 읽기
    cookies = cookie_manager.get_all()
    cookie_token = cookies.get("sheet_viewer_token")
    
    # 인증 상태 확인 (쿠키 OR 세션)
    is_cookie_valid = (cookie_token == correct_hash)
    is_session_valid = st.session_state.get("auth_success", False)
    
    if is_cookie_valid or is_session_valid:
        if is_cookie_valid and not is_session_valid:
            st.session_state["auth_success"] = True
        return True

    # 로그인 UI (화면 중앙 배치)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div style='margin-top: 20vh;'></div>", unsafe_allow_html=True)
        st.markdown("### 🔒 접근 제한")
        input_pwd = st.text_input("비밀번호", type="password")
        
        if st.button("접속하기", use_container_width=True):
            if _hash_password(input_pwd) == correct_hash:
                # 쿠키 굽기 (1일 유효)
                expires = datetime.datetime.now() + datetime.timedelta(days=1)
                cookie_manager.set("sheet_viewer_token", correct_hash, expires_at=expires)
                
                # 세션 업데이트 및 리로드
                st.session_state["auth_success"] = True
                st.success("인증 성공")
                time.sleep(0.5)
                _rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")
    
    return False

# ==============================================================================
# 4. 메인 실행 (인증 통과 시 구글 시트 렌더링)
# ==============================================================================
if check_auth():
    # Secrets에서 타겟 URL 가져오기
    target_url = st.secrets.get("TARGET_SHEET_URL")
    
    if not target_url:
        st.error("Secrets에 'TARGET_SHEET_URL'이 설정되지 않았습니다.")
    else:
        # ip.py 스타일의 iframe 임베딩 (Full Screen CSS 적용)
        st.markdown(f"""
            <div class="fullscreen-container">
                <iframe src="{target_url}"></iframe>
            </div>
        """, unsafe_allow_html=True)