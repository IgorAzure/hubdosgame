import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time

import os

def numero_valido(texto):
    try:
        numero = texto.split('Hours')[0].strip()
        float(numero)
        return numero
    except ValueError:
        return ""
        
def normalizar_nome(nome):

    return "".join(
        caractere.lower()
        for caractere in nome
        if caractere.isalnum()
    )


def buscar_horas(nome_jogo):
    
    resultado = {
            "sucesso": False,
            "historia": "",
            "extra": "",
            "completo": "",
            "solo": "",
            "coop": "",
            "vs": ""
        }
    
    if os.getenv('AMBIENTE') == 'producao':
        print("Scapper desativado")
        return resultado

    opcoes = uc.ChromeOptions()
    ##opcoes.add_argument("--headless=new")

    navegador = uc.Chrome(options=opcoes)

    url = f"https://howlongtobeat.com/?q={nome_jogo.replace(' ', '+')}"

    navegador.get(url)

    print("Aguardando coleta")

    try:

        # Espera os resultados aparecerem
        WebDriverWait(navegador, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@href, '/game/')]")
            )
        )

        # Pequena espera para a página terminar de carregar
        time.sleep(1)

        # Pega todos os links dos jogos
        links_jogos = navegador.find_elements(
            By.XPATH,
            "//a[contains(@href, '/game/')]"
        )

        titulo_encontrado = None

        nome_normalizado = normalizar_nome(nome_jogo)

        print(f"Nome pesquisado: {nome_jogo}")
        print(f"Nome normalizado: {nome_normalizado}")

        # -------------------------------------------------
        # PROCURA POR NOME NORMALIZADO
        # -------------------------------------------------

        for link in links_jogos:

            try:

                titulo = link.text.strip()

                print(f"Resultado encontrado: {titulo}")

                titulo_normalizado = normalizar_nome(titulo)

                if titulo_normalizado == nome_normalizado:

                    titulo_encontrado = titulo

                    print(f"Jogo selecionado: {titulo}")

                    break

            except Exception:

                continue

        # -------------------------------------------------
        # SE NÃO ENCONTROU, TENTA UMA BUSCA PARCIAL
        # -------------------------------------------------

        if titulo_encontrado is None:

            for link in links_jogos:

                try:

                    titulo = link.text.strip()

                    titulo_normalizado = normalizar_nome(titulo)

                    if (
                        nome_normalizado in titulo_normalizado
                        or titulo_normalizado in nome_normalizado
                    ):

                        titulo_encontrado = titulo

                        print(f"Jogo selecionado por aproximação: {titulo}")

                        break

                except Exception:

                    continue

        # -------------------------------------------------
        # NÃO ENCONTROU
        # -------------------------------------------------

        if titulo_encontrado is None:

            print(f"Jogo não encontrado: {nome_jogo}")

            return resultado

        # -------------------------------------------------
        # PROCURA O ELEMENTO NOVAMENTE
        # -------------------------------------------------

        elementos_atualizados = navegador.find_elements(
            By.XPATH,
            "//a[contains(@href, '/game/')]"
        )

        elemento_titulo = None

        for elemento in elementos_atualizados:

            try:

                titulo = elemento.text.strip()

                if titulo == titulo_encontrado:

                    elemento_titulo = elemento

                    break

            except Exception:

                continue

        if elemento_titulo is None:

            print("Não consegui recuperar o elemento do jogo.")

            return resultado

        # -------------------------------------------------
        # PEGA O CARD DO JOGO
        # -------------------------------------------------

        card_completo = elemento_titulo.find_element(
            By.XPATH,
            "../.."
        )

        texto = card_completo.text.replace('½', '.5')

        print("Card encontrado:")
        print(texto)

        # -------------------------------------------------
        # MAIN STORY
        # -------------------------------------------------

        if "Main Story" in texto:

            # tempo_historia = (
            #     texto
            #     .split('Main Story')[1]
            #     .split('Hours')[0]
            #     .strip()
            # )

            resultado["historia"] = numero_valido(texto.split('Main Story')[1])

        # -------------------------------------------------
        # MAIN + EXTRA
        # -------------------------------------------------

        if "Main + Extra" in texto:

            # tempo_extra = (
            #     texto
            #     .split('Main + Extra')[1]
            #     .split('Hours')[0]
            #     .strip()
            # )

            resultado["extra"] = numero_valido(texto.split('Main + Extra')[1])

        # -------------------------------------------------
        # COMPLETIONIST
        # -------------------------------------------------

        if "Completionist" in texto:

            # tempo_comp = (
            #     texto
            #     .split('Completionist')[1]
            #     .split('Hours')[0]
            #     .strip()
            # )

            resultado["completo"] = numero_valido(texto.split('Completionist')[1])
            
        if "Solo" in texto:
            resultado["solo"] = numero_valido(texto.split('Solo')[1])
            
        if "Co-Op" in texto:
            resultado["coop"] = numero_valido(texto.split('Co-Op')[1])
            
        if "Vs." in texto:
            resultado["vs"] = numero_valido(texto.split('Vs.')[1])
            
        if(resultado.get("historia") or resultado.get("extra") or 
        resultado.get("completionist") or resultado.get("solo") or 
        resultado.get("coop") or resultado.get("vs")):
            resultado["sucesso"] = True
        else:
            print("Achou mas nao ha tempo registrado")

        print("Resultado final:")
        print(resultado)

    except Exception as e:

        print(f"Erro: {e}")

    finally:

        print("concluido")

        ##time.sleep(1.5)

        navegador.quit()

    return resultado