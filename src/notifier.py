import smtplib
import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL", GMAIL_USER)


def _send(subject: str, body_text: str, body_html: str) -> bool:
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        logger.error("GMAIL_USER o GMAIL_APP_PASSWORD no configurados en .env")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = NOTIFY_EMAIL
    msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, NOTIFY_EMAIL, msg.as_string())
        logger.info("Correo enviado a %s", NOTIFY_EMAIL)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Error de autenticación Gmail — verifica GMAIL_APP_PASSWORD en .env")
    except Exception as e:
        logger.error("Error enviando correo: %s", e)
    return False


def send_discount_digest(products: list[dict], query: str, min_pct: int) -> bool:
    subject = f"🔥 Alkosto — Top {len(products)} ofertas con -{min_pct}%+ de descuento ({query})"

    lines = [f"Top ofertas en Alkosto — '{query}' (descuento >= {min_pct}%)\n"]
    for i, p in enumerate(products, 1):
        lines.append(f"{i}. {p['nombre']}")
        lines.append(f"   💰 ${p['precio_cop']:,.0f}  |  Descuento: {p['descuento']}")
        if p.get("precio_original_cop"):
            lines.append(f"   Precio antes: ${p['precio_original_cop']:,.0f}")
        lines.append(f"   🔗 {p['url']}")
        lines.append("")

    body_text = "\n".join(lines)

    rows = "".join(f"""
    <tr style="border-bottom:1px solid #eee">
        <td style="padding:10px;font-size:13px">{i}. {p['nombre']}</td>
        <td style="padding:10px;text-align:right;white-space:nowrap">
            {"<span style='text-decoration:line-through;color:#aaa;font-size:12px'>$" + f"{p['precio_original_cop']:,.0f}" + "</span><br>" if p.get('precio_original_cop') else ""}
            <b style="color:#E30613;font-size:15px">${p['precio_cop']:,.0f}</b>
        </td>
        <td style="padding:10px;text-align:center">
            <span style="background:#E30613;color:white;padding:3px 8px;border-radius:12px;font-weight:bold">{p['descuento']}</span>
        </td>
        <td style="padding:10px;text-align:center">
            <a href="{p['url']}" style="color:#0066cc;font-size:13px">Ver →</a>
        </td>
    </tr>
    """ for i, p in enumerate(products, 1))

    body_html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto">
    <h2 style="color:#E30613">🔥 Top ofertas Alkosto — {query}</h2>
    <p>Productos con <strong>{min_pct}% de descuento o más</strong>, ordenados de mayor a menor oferta:</p>
    <table style="width:100%;border-collapse:collapse;font-size:13px">
        <thead>
            <tr style="background:#E30613;color:white">
                <th style="padding:10px;text-align:left">Producto</th>
                <th style="padding:10px">Precio</th>
                <th style="padding:10px">Descuento</th>
                <th style="padding:10px">Enlace</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    <br>
    <small style="color:#999">Enviado automáticamente por Price Scraper — Alkosto Colombia</small>
    </body></html>
    """

    return _send(subject, body_text, body_html)


def send_price_alert(drops: list[dict], query: str) -> bool:
    subject = f"🔔 Alkosto — {len(drops)} producto(s) bajaron de precio ({query})"

    lines = []
    for p in drops:
        lines.append(f"📦 {p['nombre']}")
        lines.append(f"   Antes: ${p['precio_anterior']:,.0f}  →  Ahora: ${p['precio_cop']:,.0f}  ({p['descuento']})")
        lines.append(f"   🔗 {p['url']}")
        lines.append("")

    body_text = "\n".join(lines)
    body_html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
    <h2 style="color:#E30613">🔔 Bajada de precios — Alkosto</h2>
    {"".join(f'''
    <div style="margin-bottom:16px;padding:12px;border-left:4px solid #E30613;background:#f9f9f9">
        <b>{p["nombre"]}</b><br>
        <span style="text-decoration:line-through;color:#999">${p["precio_anterior"]:,.0f}</span>
        &nbsp;→&nbsp;
        <span style="color:#E30613;font-weight:bold">${p["precio_cop"]:,.0f}</span>
        &nbsp;<span style="background:#E30613;color:white;padding:2px 6px;border-radius:4px">{p["descuento"]}</span><br>
        <a href="{p["url"]}">Ver en Alkosto →</a>
    </div>
    ''' for p in drops)}
    </body></html>
    """

    return _send(subject, body_text, body_html)
