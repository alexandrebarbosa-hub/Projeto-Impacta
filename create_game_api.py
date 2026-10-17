import os

path = r'C:\Users\alexa\Documents\Impacta\services\external_game_api.py'

if os.path.exists(path):
    print(f"AVISO: O arquivo {path} já existe. Nenhuma alteração foi realizada para preservar o conteúdo existente.")
else:
    code_content = '''import os
import requests
import streamlit as st

def _get_rawg_api_key():
    \"\"\"Obtém a chave da RAWG API de forma segura via st.secrets ou variável de ambiente.\"\"\"
    try:
        if hasattr(st, "secrets") and "RAWG_API_KEY" in st.secrets:
            return st.secrets["RAWG_API_KEY"]
    except Exception:
        pass
    return os.getenv("RAWG_API_KEY", "")

RAWG_BASE_URL = "https://api.rawg.io/api"

def rawg_search_games(query: str, page_size: int = 10):
    \"\"\"
    Busca jogos na RAWG API por nome, com validação estrita de page_size (1 a 40),
    tratamento de erros HTTP (401/403, 429) sem vazamento de chaves, e normalização segura.
    Retorna uma tupla (lista_de_jogos, mensagem_de_erro).
    \"\"\"
    api_key = _get_rawg_api_key()
    if not api_key:
        return None, "Chave da API RAWG não configurada."

    try:
        page_size = int(page_size)
        if not (1 <= page_size <= 40):
            return None, "O número de resultados por página deve estar entre 1 e 40."
    except (TypeError, ValueError):
        return None, "Parâmetro page_size inválido."

    url = f"{RAWG_BASE_URL}/games"
    params = {
        "key": api_key,
        "search": query,
        "page_size": page_size
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.ok:
            try:
                data = response.json()
                raw_results = data.get("results", []) or []
                normalized_games = []
                for item in raw_results:
                    if not isinstance(item, dict):
                        continue
                    
                    genres = [g.get("name") for g in (item.get("genres") or []) if isinstance(g, dict) and g.get("name")]
                    platforms = [p.get("platform", {}).get("name") for p in (item.get("platforms") or []) if isinstance(p, dict) and p.get("platform")]
                    
                    try:
                        raw_rating = float(item.get("rating") or 0.0)
                    except (TypeError, ValueError):
                        raw_rating = 0.0
                    score = round(raw_rating * 2, 1)

                    normalized_games.append({
                        "external_id": item.get("id"),
                        "title": item.get("name") or "Título desconhecido",
                        "genre": ", ".join(genres) if genres else "Outro",
                        "platform": " · ".join(platforms[:3]) if platforms else "Plataforma não informada",
                        "score": score,
                        "cover_url": item.get("background_image"),
                        "release_date": item.get("released"),
                    })
                return normalized_games, None
            except Exception:
                return None, "Erro ao processar dados retornados pela API de jogos."
        else:
            status = response.status_code
            if status in (401, 403):
                return None, "Acesso negado ou chave de API RAWG inválida."
            elif status == 429:
                return None, "Limite de requisições excedido na API de jogos. Tente novamente mais tarde."
            else:
                return None, "Não foi possível buscar jogos no momento. Tente novamente mais tarde."
    except requests.exceptions.RequestException:
        return None, "Erro de conexão ao buscar jogos na API externa."

def rawg_get_game_details(game_id: int):
    \"\"\"
    Obtém detalhes de um jogo específico na RAWG API pelo ID, com tratamento seguro.
    Retorna uma tupla (detalhes_do_jogo, mensagem_de_erro).
    \"\"\"
    api_key = _get_rawg_api_key()
    if not api_key:
        return None, "Chave da API RAWG não configurada."

    try:
        game_id = int(game_id)
    except (TypeError, ValueError):
        return None, "ID de jogo inválido."

    url = f"{RAWG_BASE_URL}/games/{game_id}"
    params = {
        "key": api_key
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.ok:
            try:
                item = response.json()
                if not isinstance(item, dict):
                    return None, "Dados do jogo inválidos."

                genres = [g.get("name") for g in (item.get("genres") or []) if isinstance(g, dict) and g.get("name")]
                platforms = [p.get("platform", {}).get("name") for p in (item.get("platforms") or []) if isinstance(p, dict) and p.get("platform")]
                developers = [d.get("name") for d in (item.get("developers") or []) if isinstance(d, dict) and d.get("name")]

                try:
                    raw_rating = float(item.get("rating") or 0.0)
                except (TypeError, ValueError):
                    raw_rating = 0.0
                score = round(raw_rating * 2, 1)

                details = {
                    "external_id": item.get("id"),
                    "title": item.get("name") or "Título desconhecido",
                    "description": item.get("description_raw") or item.get("description") or "Sem descrição disponível.",
                    "genre": ", ".join(genres) if genres else "Outro",
                    "platform": " · ".join(platforms[:3]) if platforms else "Plataforma não informada",
                    "score": score,
                    "cover_url": item.get("background_image"),
                    "release_date": item.get("released"),
                    "developer": ", ".join(developers) if developers else "Desenvolvedora não informada"
                }
                return details, None
            except Exception:
                return None, "Erro ao processar detalhes do jogo."
        else:
            status = response.status_code
            if status in (401, 403):
                return None, "Acesso negado ou chave de API RAWG inválida."
            elif status == 429:
                return None, "Limite de requisições excedido. Tente novamente mais tarde."
            elif status == 404:
                return None, "Jogo não encontrado."
            else:
                return None, "Não foi possível carregar os detalhes do jogo."
    except requests.exceptions.RequestException:
        return None, "Erro de conexão ao buscar detalhes do jogo."
'''.strip()

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(code_content)
    print(f"[SUCESSO] Arquivo {path} criado com sucesso.")
