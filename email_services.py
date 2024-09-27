from flask_mail import Mail, Message
from config import Config


def send_email(subject: str, body: str, recipients: list[str] = None):
    config = Config()
    mail = Mail()
    msg = Message(
        subject=subject,
        recipients=recipients if recipients else config.recipients,
        body=body,
    )
    mail.send(msg)


def send_insufficient_funds_email(order, exchange_name, balance, total_order_value, balance_coin):
    subject = ("Order Execution Failed Due to Insufficient Funds",)
    body = (
        (
            f"Order Details:\n"
            f"- Exchange: {exchange_name}\n"
            f"- Order ID: {order['id']}\n"
            f"- Order Type: {order['type']}\n"
            f"- Side: {order['side']}\n"
            f"- Amount: {order['amount']}\n"
            f"- Symbol: {order['coin_code']}\n"
            f"- Available Balance: {balance} {balance_coin}\n"
            f"- Required Balance: {total_order_value} {balance_coin}\n\n"
            f"Please ensure sufficient funds are available to execute the order."
        ),
    )
    send_email(subject, body)
