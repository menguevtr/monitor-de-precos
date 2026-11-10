"""Avisa quando um preço cai abaixo do valor alvo.

O alerta sempre aparece no terminal. O envio por e-mail é opcional e usa
variáveis de ambiente (assim nenhuma senha fica salva no código):

    ALERTA_EMAIL_REMETENTE   e-mail que envia (ex.: seuemail@gmail.com)
    ALERTA_EMAIL_SENHA       senha de app do Gmail (não é a senha normal)
    ALERTA_EMAIL_DESTINO     e-mail que recebe (pode ser o mesmo)
"""

import os
import smtplib
from email.message import EmailMessage


def formatar_reais(valor):
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def montar_mensagem(produto, preco):
    economia = produto["preco_alvo"] - preco
    return (
        f"O preço de \"{produto['nome']}\" caiu para {formatar_reais(preco)} "
        f"(alvo: {formatar_reais(produto['preco_alvo'])}, "
        f"{formatar_reais(economia)} abaixo).\n{produto['url']}"
    )


def email_configurado():
    return all(os.getenv(v) for v in (
        "ALERTA_EMAIL_REMETENTE", "ALERTA_EMAIL_SENHA", "ALERTA_EMAIL_DESTINO",
    ))


def enviar_email(assunto, corpo):
    mensagem = EmailMessage()
    mensagem["Subject"] = assunto
    mensagem["From"] = os.environ["ALERTA_EMAIL_REMETENTE"]
    mensagem["To"] = os.environ["ALERTA_EMAIL_DESTINO"]
    mensagem.set_content(corpo)

    servidor = os.getenv("ALERTA_EMAIL_SERVIDOR", "smtp.gmail.com")
    porta = int(os.getenv("ALERTA_EMAIL_PORTA", "465"))
    with smtplib.SMTP_SSL(servidor, porta, timeout=20) as smtp:
        smtp.login(os.environ["ALERTA_EMAIL_REMETENTE"], os.environ["ALERTA_EMAIL_SENHA"])
        smtp.send_message(mensagem)


def alertar(produto, preco):
    """Mostra o alerta e, se o e-mail estiver configurado, envia também."""
    mensagem = montar_mensagem(produto, preco)
    print(f"\n🔔 ALERTA: {mensagem}\n")

    if email_configurado():
        try:
            enviar_email(f"Preço baixou: {produto['nome']}", mensagem)
            print("   E-mail de alerta enviado.")
        except (smtplib.SMTPException, OSError) as erro:
            print(f"   Não consegui enviar o e-mail: {erro}")
