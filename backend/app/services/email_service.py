"""
Serviço de envio de emails via SMTP
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..config import get_settings

settings = get_settings()

# Pool de threads para envio assíncrono
executor = ThreadPoolExecutor(max_workers=3)


class EmailService:
    """Serviço para envio de emails"""
    
    @staticmethod
    def _send_email_sync(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Envia email de forma síncrona (usado internamente).
        """
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            print("⚠️ SMTP não configurado - email não enviado")
            return False
        
        try:
            # Criar mensagem
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL or settings.SMTP_USER}>"
            message["To"] = to_email
            
            # Adicionar versão texto (fallback)
            if text_content:
                part1 = MIMEText(text_content, "plain", "utf-8")
                message.attach(part1)
            
            # Adicionar versão HTML
            part2 = MIMEText(html_content, "html", "utf-8")
            message.attach(part2)
            
            # Conectar e enviar
            context = ssl.create_default_context()
            
            # Configurar timeout (30 segundos)
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
                print(f"🔌 Conectado ao SMTP {settings.SMTP_HOST}:{settings.SMTP_PORT}")
                server.starttls(context=context)
                print("✅ TLS iniciado")
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                print("✅ Login realizado")
                server.sendmail(
                    settings.SMTP_USER,
                    to_email,
                    message.as_string()
                )
                print(f"✅ Email enviado para {to_email}")
            
            print(f"✅ Email enviado para: {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao enviar email para {to_email}: {e}")
            return False
    
    @classmethod
    async def send_email(
        cls,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Envia email de forma assíncrona.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor,
            cls._send_email_sync,
            to_email,
            subject,
            html_content,
            text_content
        )
    
    @classmethod
    async def send_welcome_email(
        cls,
        to_email: str,
        user_name: str,
        temp_password: str,
        license_key: str,
        plan_name: str
    ) -> bool:
        """
        Envia email de boas-vindas com credenciais de acesso.
        """
        subject = "🎉 Bem-vindo ao IFRS 16 - Suas Credenciais de Acesso"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fa;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); padding: 40px 40px; border-radius: 12px 12px 0 0; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600;">
                                📊 IFRS 16
                            </h1>
                            <p style="color: #a8c5e2; margin: 10px 0 0 0; font-size: 14px;">
                                Sistema de Gestão de Arrendamentos
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="color: #1e3a5f; margin: 0 0 20px 0; font-size: 22px;">
                                Olá, {user_name}! 👋
                            </h2>
                            
                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                Sua assinatura do plano <strong style="color: #2d5a87;">{plan_name}</strong> foi ativada com sucesso!
                            </p>
                            
                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                Abaixo estão suas credenciais de acesso ao sistema:
                            </p>
                            
                            <!-- Credentials Box -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f8fafc; border-radius: 8px; margin-bottom: 30px;">
                                <tr>
                                    <td style="padding: 25px;">
                                        <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                            <tr>
                                                <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0;">
                                                    <span style="color: #718096; font-size: 14px;">📧 Email:</span>
                                                    <br>
                                                    <strong style="color: #1e3a5f; font-size: 16px;">{to_email}</strong>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0;">
                                                    <span style="color: #718096; font-size: 14px;">🔑 Senha Temporária:</span>
                                                    <br>
                                                    <code style="background-color: #edf2f7; padding: 8px 12px; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 18px; color: #e53e3e; display: inline-block; margin-top: 5px;">{temp_password}</code>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 10px 0;">
                                                    <span style="color: #718096; font-size: 14px;">🎫 Chave de Licença:</span>
                                                    <br>
                                                    <code style="background-color: #edf2f7; padding: 8px 12px; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 14px; color: #2d5a87; display: inline-block; margin-top: 5px;">{license_key}</code>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Warning -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 0 8px 8px 0; margin-bottom: 30px;">
                                <tr>
                                    <td style="padding: 15px 20px;">
                                        <p style="color: #92400e; font-size: 14px; margin: 0;">
                                            ⚠️ <strong>Importante:</strong> Por segurança, recomendamos que você altere sua senha no primeiro acesso.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- CTA Button -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td align="center">
                                        <a href="{settings.FRONTEND_URL}/login.html" 
                                           style="display: inline-block; background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 8px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 6px rgba(30, 58, 95, 0.3);">
                                            Acessar o Sistema →
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 30px 40px; border-radius: 0 0 12px 12px; text-align: center;">
                            <p style="color: #718096; font-size: 14px; margin: 0 0 10px 0;">
                                Precisa de ajuda? Entre em contato conosco.
                            </p>
                            <p style="color: #a0aec0; font-size: 12px; margin: 0;">
                                © 2025 IFRS 16 - Sistema de Gestão de Arrendamentos
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        text_content = f"""
Olá, {user_name}!

Sua assinatura do plano {plan_name} foi ativada com sucesso!

Suas credenciais de acesso:
- Email: {to_email}
- Senha Temporária: {temp_password}
- Chave de Licença: {license_key}

IMPORTANTE: Por segurança, recomendamos que você altere sua senha no primeiro acesso.

Acesse o sistema em: {settings.FRONTEND_URL}/login.html

Atenciosamente,
Equipe IFRS 16
        """
        
        return await cls.send_email(to_email, subject, html_content, text_content)
    
    @classmethod
    async def send_password_reset_email(
        cls,
        to_email: str,
        user_name: str,
        reset_token: str
    ) -> bool:
        """
        Envia email de redefinição de senha.
        """
        reset_url = f"{settings.FRONTEND_URL}/reset-password.html?token={reset_token}"
        subject = "🔐 Redefinição de Senha - IFRS 16"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fa;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <tr>
                        <td style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); padding: 40px; border-radius: 12px 12px 0 0; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px;">🔐 Redefinição de Senha</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px;">
                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6;">
                                Olá, <strong>{user_name}</strong>!
                            </p>
                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6;">
                                Recebemos uma solicitação para redefinir sua senha. Clique no botão abaixo para criar uma nova senha:
                            </p>
                            <table role="presentation" style="width: 100%; margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{reset_url}" 
                                           style="display: inline-block; background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 8px; font-size: 16px; font-weight: 600;">
                                            Redefinir Senha
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            <p style="color: #718096; font-size: 14px;">
                                Este link expira em 1 hora. Se você não solicitou esta redefinição, ignore este email.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #f8fafc; padding: 20px; border-radius: 0 0 12px 12px; text-align: center;">
                            <p style="color: #a0aec0; font-size: 12px; margin: 0;">
                                © 2025 IFRS 16 - Sistema de Gestão de Arrendamentos
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        text_content = f"""
Olá, {user_name}!

Recebemos uma solicitação para redefinir sua senha.

Clique no link abaixo para criar uma nova senha:
{reset_url}

Este link expira em 1 hora. Se você não solicitou esta redefinição, ignore este email.

Atenciosamente,
Equipe IFRS 16
        """
        
        return await cls.send_email(to_email, subject, html_content, text_content)
    
    @classmethod
    async def send_subscription_confirmation_email(
        cls,
        to_email: str,
        user_name: str,
        plan_name: str,
        next_billing_date: str
    ) -> bool:
        """
        Envia email de confirmação de assinatura/renovação.
        """
        subject = "✅ Confirmação de Assinatura - IFRS 16"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fa;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <tr>
                        <td style="background: linear-gradient(135deg, #059669 0%, #10b981 100%); padding: 40px; border-radius: 12px 12px 0 0; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px;">✅ Assinatura Confirmada!</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px;">
                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6;">
                                Olá, <strong>{user_name}</strong>!
                            </p>
                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6;">
                                Sua assinatura do plano <strong style="color: #059669;">{plan_name}</strong> foi confirmada com sucesso!
                            </p>
                            <table role="presentation" style="width: 100%; background-color: #f0fdf4; border-radius: 8px; margin: 20px 0;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="color: #166534; font-size: 14px; margin: 0;">
                                            📅 Próxima cobrança: <strong>{next_billing_date}</strong>
                                        </p>
                                    </td>
                                </tr>
                            </table>
                            <p style="color: #718096; font-size: 14px;">
                                Você pode gerenciar sua assinatura a qualquer momento através do portal do cliente.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #f8fafc; padding: 20px; border-radius: 0 0 12px 12px; text-align: center;">
                            <p style="color: #a0aec0; font-size: 12px; margin: 0;">
                                © 2025 IFRS 16 - Sistema de Gestão de Arrendamentos
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        text_content = f"""
Olá, {user_name}!

Sua assinatura do plano {plan_name} foi confirmada com sucesso!

Próxima cobrança: {next_billing_date}

Você pode gerenciar sua assinatura a qualquer momento através do portal do cliente.

Atenciosamente,
Equipe IFRS 16
        """
        
        return await cls.send_email(to_email, subject, html_content, text_content)

