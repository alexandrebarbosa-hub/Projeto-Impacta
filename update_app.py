import os
import shutil
import sys
import ast
import tempfile
import re

app_path = r'C:\Users\alexa\Documents\Impacta\app.py'
bak_path = r'C:\Users\alexa\Documents\Impacta\app.py.bak'
app_dir = os.path.dirname(app_path)

print('=== INICIANDO PRÉ-VALIDAÇÃO SEGURA ===')

if not os.path.exists(app_path):
    print(f'ERRO CRÍTICO: Arquivo {app_path} não encontrado. Operação abortada.')
    sys.exit(1)

with open(app_path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'import streamlit as st' not in content:
    print('ERRO DE VALIDAÇÃO: \'import streamlit as st\' não encontrado. Operação abortada.')
    sys.exit(1)

if 'if "library" not in st.session_state:' not in content:
    print('ERRO DE VALIDAÇÃO: Âncora de session_state não encontrada. Operação abortada.')
    sys.exit(1)

if 'with st.sidebar:' not in content or 'impacta-logo' not in content:
    print('ERRO DE VALIDAÇÃO: Estrutura da barra lateral (sidebar) não encontrada. Operação abortada.')
    sys.exit(1)

if 'if "auth_token" not in st.session_state:' in content:
    print('ERRO DE VALIDAÇÃO: O bloco de inicialização de autenticação já existe em app.py. Operação abortada.')
    sys.exit(1)

required_funcs = ['xano_login', 'xano_signup', 'xano_get_me']
auth_import_pattern = re.compile(r'from\s+services\.xano_auth\s+import\s+([^\n]+)')
match = auth_import_pattern.search(content)

auth_import = ''
if match:
    imported_part = match.group(1).split('#')[0]
    imported_items = [item.strip() for item in imported_part.split(',')]
    if all(fn in imported_items for fn in required_funcs):
        print('AVISO: Importação completa de xano_auth já detectada em app.py.')
    else:
        print('AVISO: Importação parcial detectada. Atualizando a instrução existente para garantir todas as funções.')
        content = auth_import_pattern.sub('from services.xano_auth import xano_login, xano_signup, xano_get_me', content)
else:
    auth_import = 'from services.xano_auth import xano_login, xano_signup, xano_get_me\n'

print('[OK] Todas as pré-condições passaram com sucesso.')

auth_state_init = '''
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False

# Validação silenciosa do token na sessão
if st.session_state.auth_token and not st.session_state.user_name:
    me_res, me_err = xano_get_me(st.session_state.auth_token)
    if me_res and me_res.get("name"):
        st.session_state.user_name = me_res.get("name")
        st.session_state.is_authenticated = True
    else:
        st.session_state.auth_token = None
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.is_authenticated = False
'''

sidebar_auth_ui = '''
    # --- AUTENTICAÇÃO ---
    if not st.session_state.is_authenticated:
        auth_tab1, auth_tab2 = st.tabs(["Entrar", "Criar conta"])
        with auth_tab1:
            with st.form("login_form"):
                l_email = st.text_input("E-mail", key="l_email")
                l_password = st.text_input("Senha", type="password", key="l_password")
                l_submitted = st.form_submit_button("Entrar")
                if l_submitted:
                    if not l_email.strip() or not l_password:
                        st.error("Preencha todos os campos.")
                    else:
                        res, err = xano_login(l_email.strip(), l_password)
                        if err or not res or not res.get("authToken"):
                            st.error("Falha na autenticação. Verifique suas credenciais.")
                        else:
                            token = res.get("authToken")
                            uid = res.get("user_id")
                            me_res, me_err = xano_get_me(token)
                            if me_err or not me_res or not me_res.get("name"):
                                st.error("Não foi possível carregar os dados da sessão. Tente novamente.")
                            else:
                                st.session_state.auth_token = token
                                st.session_state.user_id = uid
                                st.session_state.user_name = me_res.get("name")
                                st.session_state.is_authenticated = True
                                st.success("Login realizado com sucesso!")
                                st.rerun()
        with auth_tab2:
            with st.form("signup_form"):
                s_name = st.text_input("Nome", key="s_name")
                s_email = st.text_input("E-mail", key="s_email")
                s_password = st.text_input("Senha (min. 8)", type="password", key="s_password")
                s_submitted = st.form_submit_button("Cadastrar")
                if s_submitted:
                    if not s_name.strip() or not s_email.strip() or not s_password:
                        st.error("Preencha todos os campos.")
                    else:
                        res, err = xano_signup(s_name.strip(), s_email.strip(), s_password)
                        if err or not res or not res.get("authToken"):
                            st.error("Não foi possível concluir o cadastro. Verifique os dados.")
                        else:
                            token = res.get("authToken")
                            uid = res.get("user_id")
                            me_res, me_err = xano_get_me(token)
                            if me_err or not me_res or not me_res.get("name"):
                                st.error("Não foi possível carregar o perfil da nova conta. Tente fazer login.")
                                st.session_state.auth_token = None
                                st.session_state.user_id = None
                                st.session_state.user_name = None
                                st.session_state.is_authenticated = False
                            else:
                                st.session_state.auth_token = token
                                st.session_state.user_id = uid
                                st.session_state.user_name = me_res.get("name")
                                st.session_state.is_authenticated = True
                                st.success("Conta criada com sucesso!")
                                st.rerun()
    else:
        st.markdown(f"👤 Olá, **{st.session_state.user_name or 'Gamer'}**")
        if st.button("Sair (Logout)"):
            st.session_state.auth_token = None
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.session_state.is_authenticated = False
            st.success("Você saiu da sua conta.")
            st.rerun()
    st.divider()
'''

if auth_import:
    new_content = content.replace('import streamlit as st', auth_import + 'import streamlit as st', 1)
else:
    new_content = content

new_content = new_content.replace('if "library" not in st.session_state:', auth_state_init + '\nif "library" not in st.session_state:', 1)

old_sidebar_header = 'with st.sidebar:\n    st.markdown(\'<div class="impacta-logo">🎮 <span>Impacta</span></div>\', unsafe_allow_html=True)'
if old_sidebar_header not in new_content:
    print('ERRO CRÍTICO: Bloco exato da barra lateral não encontrado em memória. Operação abortada.')
    sys.exit(1)

new_content = new_content.replace(old_sidebar_header, old_sidebar_header + sidebar_auth_ui, 1)

print('Validando sintaxe em memória (ast.parse)...')
try:
    ast.parse(new_content)
    print('[OK] Sintaxe em memória validada com sucesso!')
except SyntaxError as e:
    print(f'ERRO DE SINTAXE EM MEMÓRIA: {e}')
    print('Operação abortada. Nenhum arquivo foi modificado.')
    sys.exit(1)

if not os.path.exists(bak_path):
    shutil.copy2(app_path, bak_path)
    print(f'[OK] Backup criado em: {bak_path}')
else:
    print(f'[INFO] Backup existente preservado em {bak_path} (não sobrescrito).')

print('Gravando arquivo de forma atômica...')
tmp_name = None
try:
    with tempfile.NamedTemporaryFile('w', dir=app_dir, delete=False, encoding='utf-8') as tmp:
        tmp.write(new_content)
        tmp_name = tmp.name
    
    os.replace(tmp_name, app_path)
    print(f'[SUCESSO] Arquivo {app_path} atualizado e gravado atomaticamente com sucesso!')
except Exception as e:
    print(f'ERRO NA GRAVAÇÃO ATÔMICA: {e}')
    if tmp_name and os.path.exists(tmp_name):
        os.remove(tmp_name)
    print(f'Para restaurar o backup original, execute: copy "{bak_path}" "{app_path}"')
    sys.exit(1)
