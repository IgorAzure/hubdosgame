import os
import urllib.parse
import requests
import re
import time
from flask import Blueprint, redirect, url_for, request, session

from app import db
from app.models import Usuario, Jogo

auth_bp = Blueprint('auth', __name__)
STEAM_API_KEY = os.environ.get('CHAVE_API_STEAM')

@auth_bp.route('/login/steam')
def login_steam():
    steam_openid_url = 'https://steamcommunity.com/openid/login'
    params = {
        'openid.ns': 'http://specs.openid.net/auth/2.0',
        'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.mode': 'checkid_setup',
        
        'openid.return_to': url_for('auth.steam_authorize', _external=True),
        'openid.realm': request.host_url
    }
    
    
    query_string = urllib.parse.urlencode(params)
    
    
    return redirect(f"{steam_openid_url}?{query_string}")

@auth_bp.route('/authorize/steam')
def steam_authorize():
    
    
    claimed_id = request.args.get('openid.claimed_id')
    if not claimed_id:
        return "Falha no login com a Steam", 400

    
    steam_id = re.search(r'\d+', claimed_id).group()

    
    api_url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steam_id}"
    
    
    resposta = requests.get(api_url).json()

    
    jogador = resposta['response']['players'][0]

    usuario = Usuario.query.filter_by(steam_id=steam_id).first()

    if not usuario:
        usuario = Usuario(
            steam_id=steam_id,
            nome=jogador['personaname'],
            foto=jogador['avatarfull']
        )
        db.session.add(usuario)
        db.session.commit()
    
    
    session['usuario'] = {
        'id': usuario.id,
        'nome': jogador['personaname'],
        'foto': jogador['avatarfull'],
        'steam_id': steam_id
    }

    return redirect(url_for('main.home', sincronizar='1'))

@auth_bp.route('/sincronizar')
def sincronizar():
    if 'usuario' not in session:
        return redirect(url_for('auth.login_steam'))

    steam_id = session['usuario']['steam_id']
    meu_id = session['usuario']['id']

    url_owned = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={STEAM_API_KEY}&steamid={steam_id}&include_appinfo=1&format=json"

    try:
        resposta = requests.get(url_owned).json()
        jogos_steam = resposta.get('response', {}).get('games', [])

        # MUDOU AQUI:
        # Antes você fazia uma consulta no banco para cada jogo da Steam.
        # Agora buscamos todos os appids dos jogos que o usuário já tem no banco de uma vez só.
        appids_existentes = {
            jogo.steam_appid
            for jogo in Jogo.query
                .with_entities(Jogo.steam_appid)
                .filter_by(usuario_id=meu_id)
                .all()
        }

        # MUDOU AQUI:
        # Essa lista vai guardar apenas os jogos novos adicionados agora.
        # Depois, o enriquecimento será feito só nesses jogos.
        jogos_novos = []

        for jogo_api in jogos_steam:
            titulo_steam = jogo_api.get('name')
            appid_steam = jogo_api.get('appid')

            if not titulo_steam or not appid_steam:
                continue

            # MUDOU AQUI:
            # Agora a verificação usa steam_appid em vez de título.
            # Isso é mais confiável, porque o appid é único na Steam.
            if appid_steam not in appids_existentes:
                novo_jogo = Jogo(
                    titulo=titulo_steam,
                    genero="Steam",
                    status="Backlog",
                    steam_appid=appid_steam,
                    usuario_id=meu_id
                )

                db.session.add(novo_jogo)

                # MUDOU AQUI:
                # Guardamos o jogo novo numa lista para enriquecer depois.
                jogos_novos.append(novo_jogo)

                # MUDOU AQUI:
                # Já adicionamos o appid no set para evitar duplicação
                # dentro da mesma sincronização.
                appids_existentes.add(appid_steam)

        # Salva os jogos novos no banco.
        db.session.commit()

        # MUDOU AQUI:
        # Antes você buscava no banco todos os jogos com genero="Steam".
        # Agora só enriquece os jogos que foram adicionados nesta sincronização.
        for jogo in jogos_novos:
            url_store = f"http://store.steampowered.com/api/appdetails?appids={jogo.steam_appid}&l=brazilian"

            try:
                res_store = requests.get(url_store)

                if res_store.status_code == 200:
                    dados = res_store.json()
                    str_appid = str(jogo.steam_appid)

                    if dados.get(str_appid, {}).get('success'):
                        info_jogo = dados[str_appid]['data']
                        generos = info_jogo.get('genres', [])

                        if generos:
                            jogo.genero = generos[0]['description']

            except Exception as e:
                print(f"Erro ao enriquecer {jogo.titulo}: {e}")

            # Mantém a pausa para não fazer muitas requisições seguidas na Steam.
            time.sleep(1.5)

        db.session.commit()

    except Exception as e:
        print(f"Erro ao sincronizar: {e}")

    return redirect(url_for('main.home'))


@auth_bp.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('main.home'))

