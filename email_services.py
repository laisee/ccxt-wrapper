from flask import Flask
from flask_mail import Mail, Message
from config import Config


def send_email(subject: str, body: str, recipients: list[str] | None = None):
    config = Config()
    app = Flask(__name__)
    app.config.update(
        MAIL_SERVER=config.mail_server,
        MAIL_PORT=config.mail_port,
        MAIL_USE_TLS=config.mail_use_tls,
        MAIL_USERNAME=config.mail_username,
        MAIL_PASSWORD=config.mail_password,
        MAIL_DEFAULT_SENDER=config.mail_default_sender,
    )
    mail = Mail(app)
    msg = Message(
        subject=subject,
        recipients=recipients if recipients else config.recipients,
        body=body,
    )
    with app.app_context():
        mail.send(msg)


def send_insufficient_funds_email(order, exchange_name, balance, total_order_value, balance_coin):
    subject = "Order Execution Failed Due to Insufficient Funds"
    body = (
        f"Order Details:\n"
        f"- Exchange: {exchange_name}\n"
        f"- Order ID: {order['id']}\n"
        f"- Order Type: {order['type']}\n"
        f"- Side: {order['side']}\n"
        f"- Amount: {order['amount']}\n"
        f"- Symbol: {order['coin_code']}\n"
        f"- Available Balance: {balance} {balance_coin}\n"
        f"- Required Balance: {total_order_value} {balance_coin}\n\n"
        "Please ensure sufficient funds are available to execute the order."
    )
    send_email(subject, body)
