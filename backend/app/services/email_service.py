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
            print(
                "[WARN] SMTP nao configurado - email nao enviado "
                f"(SMTP_USER={'OK' if settings.SMTP_USER else 'MISSING'}, "
                f"SMTP_PASSWORD={'OK' if settings.SMTP_PASSWORD else 'MISSING'})"
            )
            return False
        
        try:
            from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USER

            # Criar mensagem
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{settings.SMTP_FROM_NAME} <{from_email}>"
            message["To"] = to_email
            
            # Adicionar versão texto (fallback)
            if text_content:
                part1 = MIMEText(text_content, "plain", "utf-8")
                message.attach(part1)
            
            # Adicionar versão HTML
            part2 = MIMEText(html_content, "html", "utf-8")
            message.attach(part2)
            
            timeout = getattr(settings, 'SMTP_TIMEOUT_SECONDS', 30)
            use_ssl = bool(getattr(settings, 'SMTP_USE_SSL', False))
            use_starttls = bool(getattr(settings, 'SMTP_USE_STARTTLS', True))

            print(
                "[EMAIL] Enviando email via SMTP "
                f"host={settings.SMTP_HOST} port={settings.SMTP_PORT} ssl={use_ssl} starttls={use_starttls} "
                f"from={from_email} to={to_email}"
            )

            context = ssl.create_default_context()

            if use_ssl:
                with smtplib.SMTP_SSL(
                    settings.SMTP_HOST,
                    settings.SMTP_PORT,
                    timeout=timeout,
                    context=context
                ) as server:
                    server.ehlo()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(from_email, [to_email], message.as_string())
            else:
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout) as server:
                    server.ehlo()
                    if use_starttls:
                        server.starttls(context=context)
                        server.ehlo()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(from_email, [to_email], message.as_string())

            print(f"[OK] Email enviado para: {to_email}")
            return True
            
        except Exception as e:
            print(
                "[ERROR] Erro ao enviar email via SMTP "
                f"host={settings.SMTP_HOST} port={settings.SMTP_PORT} "
                f"to={to_email}: {e}"
            )
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
    async def send_registration_confirmation_email(
        cls,
        to_email: str,
        user_name: str
    ) -> bool:
        """
        Envia email de confirmação de cadastro (sem senha temporária).
        """
        subject = "Bem-vindo ao IFRS 16 - Cadastro Confirmado"

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
                                IFRS 16
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
                                Olá, {user_name}!
                            </h2>

                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                Seu cadastro foi realizado com sucesso no sistema IFRS 16!
                            </p>

                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                Você já pode fazer login no sistema utilizando o email <strong>{to_email}</strong> e a senha que você cadastrou.
                            </p>

                            <!-- Info Box -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #dbeafe; border-left: 4px solid #3b82f6; border-radius: 0 8px 8px 0; margin-bottom: 30px;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="color: #1e40af; font-size: 15px; margin: 0 0 12px 0; font-weight: 600;">
                                            Próximo passo: Escolha seu plano
                                        </p>
                                        <p style="color: #1e40af; font-size: 14px; margin: 0; line-height: 1.6;">
                                            Para começar a utilizar a calculadora IFRS 16 e todos os recursos do sistema,
                                            você precisa assinar um dos nossos planos. Acesse a área de preços e escolha
                                            o plano ideal para suas necessidades.
                                        </p>
                                    </td>
                                </tr>
                            </table>

                            <!-- Features List -->
                            <p style="color: #4a5568; font-size: 15px; font-weight: 600; margin: 0 0 12px 0;">
                                O que você pode fazer com o IFRS 16:
                            </p>
                            <ul style="color: #4a5568; font-size: 14px; line-height: 1.8; margin: 0 0 30px 0;">
                                <li>Calcular automaticamente arrendamentos conforme IFRS 16</li>
                                <li>Gerar relatórios completos em Excel, CSV e PDF</li>
                                <li>Gerenciar múltiplos contratos de arrendamento</li>
                                <li>Acompanhar vencimentos e renovações</li>
                            </ul>

                            <!-- CTA Buttons -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                                <tr>
                                    <td align="center" style="padding: 10px;">
                                        <a href="{settings.FRONTEND_URL}/login.html"
                                           style="display: inline-block; background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 8px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 6px rgba(30, 58, 95, 0.3);">
                                            Fazer Login
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td align="center">
                                        <a href="{settings.FRONTEND_URL}/landing.html#pricing"
                                           style="display: inline-block; background: transparent; color: #2d5a87; text-decoration: none; padding: 12px 32px; border-radius: 8px; font-size: 15px; font-weight: 600; border: 2px solid #2d5a87;">
                                            Ver Planos e Preços
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

Seu cadastro foi realizado com sucesso no sistema IFRS 16!

Você já pode fazer login no sistema utilizando o email {to_email} e a senha que você cadastrou.

PRÓXIMO PASSO: Escolha seu plano

Para começar a utilizar a calculadora IFRS 16 e todos os recursos do sistema, você precisa assinar um dos nossos planos.

O que você pode fazer com o IFRS 16:
- Calcular automaticamente arrendamentos conforme IFRS 16
- Gerar relatórios completos em Excel, CSV e PDF
- Gerenciar múltiplos contratos de arrendamento
- Acompanhar vencimentos e renovações

Fazer login: {settings.FRONTEND_URL}/login.html
Ver planos: {settings.FRONTEND_URL}/landing.html#pricing

Atenciosamente,
Equipe IFRS 16
        """

        return await cls.send_email(to_email, subject, html_content, text_content)

    @classmethod
    async def send_email_verification(
        cls,
        to_email: str,
        user_name: str,
        verification_token: str
    ) -> bool:
        """
        Envia email de verificação de email para novos usuários.
        
        Args:
            to_email: Email do destinatário
            user_name: Nome do usuário
            verification_token: Token de verificação
        
        Returns:
            True se enviado com sucesso
        """
        subject = "Confirme seu email - Engine IFRS 16"
        
        verification_url = f"{settings.FRONTEND_URL}/verify-email.html?token={verification_token}"

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
                                IFRS 16
                            </h1>
                            <p style="color: #e2e8f0; margin: 10px 0 0 0; font-size: 14px;">
                                Sistema de Gestão de Arrendamentos
                            </p>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 40px 30px 40px;">
                            <h2 style="color: #2d3748; margin: 0 0 20px 0; font-size: 24px; font-weight: 600;">
                                Confirme seu Email
                            </h2>
                            
                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                Olá, <strong>{user_name}</strong>!
                            </p>
                            
                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                Obrigado por se cadastrar no <strong>Engine IFRS 16</strong>! Para completar seu cadastro e começar a usar o sistema, precisamos confirmar seu endereço de email.
                            </p>
                            
                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                Clique no botão abaixo para confirmar seu email:
                            </p>

                            <!-- CTA Button -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                                <tr>
                                    <td align="center" style="padding: 10px;">
                                        <a href="{verification_url}"
                                           style="display: inline-block; background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 8px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 6px rgba(30, 58, 95, 0.3);">
                                            Confirmar Email
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <div style="background-color: #f7fafc; border-left: 4px solid #4299e1; padding: 16px; border-radius: 4px; margin-bottom: 20px;">
                                <p style="color: #2d3748; font-size: 14px; margin: 0 0 10px 0; font-weight: 600;">
                                    ⏰ Link válido por 24 horas
                                </p>
                                <p style="color: #4a5568; font-size: 14px; margin: 0; line-height: 1.5;">
                                    Este link de confirmação expira em 24 horas. Se você não confirmar seu email dentro deste prazo, será necessário solicitar um novo link.
                                </p>
                            </div>

                            <p style="color: #718096; font-size: 14px; line-height: 1.6; margin: 20px 0 0 0;">
                                Se o botão não funcionar, copie e cole o link abaixo no seu navegador:
                            </p>
                            <p style="color: #4299e1; font-size: 13px; word-break: break-all; margin: 10px 0 0 0;">
                                {verification_url}
                            </p>

                            <div style="border-top: 1px solid #e2e8f0; margin-top: 30px; padding-top: 20px;">
                                <p style="color: #718096; font-size: 14px; line-height: 1.6; margin: 0;">
                                    <strong>Não solicitou este cadastro?</strong><br>
                                    Se você não criou uma conta no Engine IFRS 16, pode ignorar este email com segurança.
                                </p>
                            </div>
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
Confirme seu Email - Engine IFRS 16

Olá, {user_name}!

Obrigado por se cadastrar no Engine IFRS 16! Para completar seu cadastro e começar a usar o sistema, precisamos confirmar seu endereço de email.

Clique no link abaixo para confirmar seu email:
{verification_url}

⏰ IMPORTANTE: Este link é válido por 24 horas.

Se você não solicitou este cadastro, pode ignorar este email com segurança.

Atenciosamente,
Equipe IFRS 16
        """

        return await cls.send_email(to_email, subject, html_content, text_content)

    @classmethod
    async def send_registration_email(
        cls,
        to_email: str,
        user_name: str,
        temp_password: str
    ) -> bool:
        """
        Envia email de boas-vindas para registro manual (sem assinatura).
        """
        subject = "Bem-vindo ao IFRS 16 - Suas Credenciais de Acesso"

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
                                IFRS 16
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
                                Olá, {user_name}!
                            </h2>

                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                Seu cadastro foi realizado com sucesso no sistema IFRS 16!
                            </p>

                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                Abaixo estão suas credenciais de acesso:
                            </p>

                            <!-- Credentials Box -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f8fafc; border-radius: 8px; margin-bottom: 30px;">
                                <tr>
                                    <td style="padding: 25px;">
                                        <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                            <tr>
                                                <td style="padding: 10px 0; border-bottom: 1px solid #e2e8f0;">
                                                    <span style="color: #718096; font-size: 14px;">Email:</span>
                                                    <br>
                                                    <strong style="color: #1e3a5f; font-size: 16px;">{to_email}</strong>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 10px 0;">
                                                    <span style="color: #718096; font-size: 14px;">Senha Temporária:</span>
                                                    <br>
                                                    <code style="background-color: #edf2f7; padding: 8px 12px; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 18px; color: #e53e3e; display: inline-block; margin-top: 5px;">{temp_password}</code>
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
                                            <strong>Importante:</strong> Por segurança, você será obrigado a alterar sua senha no primeiro acesso.
                                        </p>
                                    </td>
                                </tr>
                            </table>

                            <!-- Info Box -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #dbeafe; border-left: 4px solid #3b82f6; border-radius: 0 8px 8px 0; margin-bottom: 30px;">
                                <tr>
                                    <td style="padding: 15px 20px;">
                                        <p style="color: #1e40af; font-size: 14px; margin: 0;">
                                            <strong>Próximo passo:</strong> Para utilizar o sistema, você precisa assinar um dos nossos planos.
                                            Acesse a área de preços após o login para escolher o plano ideal para você.
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
                                            Acessar o Sistema
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

Seu cadastro foi realizado com sucesso no sistema IFRS 16!

Suas credenciais de acesso:
- Email: {to_email}
- Senha Temporária: {temp_password}

IMPORTANTE: Por segurança, você será obrigado a alterar sua senha no primeiro acesso.

PRÓXIMO PASSO: Para utilizar o sistema, você precisa assinar um dos nossos planos.
Acesse a área de preços após o login para escolher o plano ideal para você.

Acesse o sistema em: {settings.FRONTEND_URL}/login.html

Atenciosamente,
Equipe IFRS 16
        """

        return await cls.send_email(to_email, subject, html_content, text_content)

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
        Envia email de boas-vindas com credenciais de acesso (para assinaturas via Stripe).
        """
        subject = "Bem-vindo ao IFRS 16 - Suas Credenciais de Acesso"
        
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
                            
                            <!-- Instructions -->
                            <div style="background-color: #e0f2fe; border-left: 4px solid #0284c7; border-radius: 0 8px 8px 0; padding: 20px; margin-bottom: 30px;">
                                <h3 style="color: #0c4a6e; margin: 0 0 15px 0; font-size: 16px; font-weight: 600;">
                                    📋 Como acessar:
                                </h3>
                                <ol style="color: #0c4a6e; font-size: 14px; line-height: 1.8; margin: 0; padding-left: 20px;">
                                    <li>Clique no botão abaixo para fazer login</li>
                                    <li>Use o email e senha temporária fornecidos</li>
                                    <li>Você será direcionado para validar sua licença</li>
                                    <li>Insira a chave de licença e confirme</li>
                                    <li>Pronto! Você terá acesso à calculadora IFRS 16</li>
                                </ol>
                            </div>
                            
                            <!-- CTA Button -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                                <tr>
                                    <td align="center">
                                        <a href="{settings.FRONTEND_URL}/login.html?license={license_key}" 
                                           style="display: inline-block; background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 8px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 6px rgba(30, 58, 95, 0.3);">
                                            🚀 Fazer Login e Ativar Licença
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="color: #718096; font-size: 13px; text-align: center; margin: 0;">
                                Ou copie e cole o link abaixo no seu navegador:
                            </p>
                            <p style="color: #0284c7; font-size: 12px; text-align: center; word-break: break-all; margin: 10px 0 0 0;">
                                {settings.FRONTEND_URL}/login.html?license={license_key}
                            </p>
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
    async def send_license_activated_email(
        cls,
        to_email: str,
        user_name: str,
        license_key: str,
        plan_name: str
    ) -> bool:
        subject = "✅ Assinatura ativada - Sua licença Engine IFRS 16"

        login_url = f"{settings.FRONTEND_URL}/login.html"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
</head>
<body style=\"margin:0;padding:0;font-family:Arial, sans-serif;background:#f4f7fa;\">
  <div style=\"max-width:600px;margin:0 auto;padding:32px;\">
    <div style=\"background:#ffffff;border-radius:12px;box-shadow:0 6px 18px rgba(0,0,0,.08);overflow:hidden;\">
      <div style=\"background:linear-gradient(135deg,#0b1220,#1b2a44);padding:28px 28px;color:#fff;\">
        <h1 style=\"margin:0;font-size:22px;\">Engine IFRS 16</h1>
        <p style=\"margin:8px 0 0 0;color:#cbd5e1;font-size:14px;\">Licença ativada com sucesso</p>
      </div>
      <div style=\"padding:28px;\">
        <p style=\"margin:0 0 12px 0;color:#111827;font-size:16px;\">Olá, <strong>{user_name}</strong>.</p>
        <p style=\"margin:0 0 16px 0;color:#374151;font-size:15px;line-height:1.6;\">
          Sua assinatura do plano <strong>{plan_name}</strong> foi ativada com sucesso.
        </p>
        <div style=\"background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:16px;margin-bottom:20px;\">
          <p style=\"margin:0 0 6px 0;color:#6b7280;font-size:13px;\">🎫 Chave de Licença</p>
          <p style=\"margin:0;font-family:Courier New, monospace;font-size:15px;color:#111827;font-weight:600;\">{license_key}</p>
        </div>
        
        <div style=\"background:#e0f2fe;border-left:4px solid #0284c7;border-radius:0 8px 8px 0;padding:16px;margin-bottom:20px;\">
          <p style=\"margin:0 0 10px 0;color:#0c4a6e;font-size:14px;font-weight:600;\">📋 Como acessar:</p>
          <ol style=\"margin:0;padding-left:20px;color:#0c4a6e;font-size:13px;line-height:1.7;\">
            <li>Clique no botão abaixo para fazer login</li>
            <li>Use seu email e senha cadastrados</li>
            <li>Você será direcionado para validar sua licença</li>
            <li>Insira a chave de licença e confirme</li>
            <li>Pronto! Acesse a calculadora IFRS 16</li>
          </ol>
        </div>
        
        <div style=\"text-align:center;margin-bottom:16px;\">
          <a href=\"{login_url}?license={license_key}\" style=\"display:inline-block;background:#111827;color:#fff;text-decoration:none;padding:14px 32px;border-radius:10px;font-weight:600;font-size:15px;\">
            🚀 Fazer Login e Ativar Licença
          </a>
        </div>
        
        <p style=\"margin:0;color:#9ca3af;font-size:12px;text-align:center;word-break:break-all;\">
          Ou acesse: {login_url}?license={license_key}
        </p>
      </div>
      <div style=\"padding:18px 28px;background:#f8fafc;color:#9ca3af;font-size:12px;text-align:center;\">
        © 2025 FX Studio AI
      </div>
    </div>
  </div>
</body>
</html>
        """

        text_content = f"""Olá, {user_name}!

Sua assinatura do plano {plan_name} foi ativada com sucesso.

Chave de Licença: {license_key}

Acesse: {login_url}
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

    @classmethod
    async def send_payment_failed_email(
        cls,
        to_email: str,
        user_name: str,
        plan_name: str,
        retry_date: str
    ) -> bool:
        """
        Envia email de alerta de falha de pagamento.
        """
        subject = "Atencao: Falha no Pagamento - IFRS 16"

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
                        <td style="background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); padding: 40px; border-radius: 12px 12px 0 0; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px;">[ALERTA] Falha no Pagamento</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px;">
                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6;">
                                Ola, <strong>{user_name}</strong>,
                            </p>
                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6;">
                                Nao conseguimos processar o pagamento da sua assinatura do plano <strong style="color: #dc2626;">{plan_name}</strong>.
                            </p>
                            <table role="presentation" style="width: 100%; background-color: #fef2f2; border-left: 4px solid #dc2626; border-radius: 0 8px 8px 0; margin: 20px 0;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="color: #991b1b; font-size: 14px; margin: 0 0 10px 0;">
                                            <strong>O que isso significa?</strong>
                                        </p>
                                        <p style="color: #991b1b; font-size: 14px; margin: 0;">
                                            Sua assinatura esta marcada como pendente. Tentaremos processar o pagamento novamente em <strong>{retry_date}</strong>.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6;">
                                <strong>O que voce pode fazer:</strong>
                            </p>
                            <ul style="color: #4a5568; font-size: 15px; line-height: 1.8;">
                                <li>Verifique se ha saldo suficiente no seu cartao</li>
                                <li>Atualize seu metodo de pagamento no portal do cliente</li>
                                <li>Entre em contato com sua operadora de cartao</li>
                            </ul>
                            <table role="presentation" style="width: 100%; margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{settings.FRONTEND_URL}/dashboard.html"
                                           style="display: inline-block; background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 8px; font-size: 16px; font-weight: 600;">
                                            Atualizar Pagamento
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            <p style="color: #718096; font-size: 14px;">
                                Se voce nao atualizar seu metodo de pagamento, sua assinatura sera cancelada e voce perdera o acesso ao sistema.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #f8fafc; padding: 20px; border-radius: 0 0 12px 12px; text-align: center;">
                            <p style="color: #a0aec0; font-size: 12px; margin: 0;">
                                (c) 2025 IFRS 16 - Sistema de Gestao de Arrendamentos
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
Ola, {user_name},

Nao conseguimos processar o pagamento da sua assinatura do plano {plan_name}.

O que isso significa?
Sua assinatura esta marcada como pendente. Tentaremos processar o pagamento novamente em {retry_date}.

O que voce pode fazer:
- Verifique se ha saldo suficiente no seu cartao
- Atualize seu metodo de pagamento no portal do cliente: {settings.FRONTEND_URL}/dashboard.html
- Entre em contato com sua operadora de cartao

Se voce nao atualizar seu metodo de pagamento, sua assinatura sera cancelada e voce perdera o acesso ao sistema.

Atenciosamente,
Equipe IFRS 16
        """

        return await cls.send_email(to_email, subject, html_content, text_content)

    @classmethod
    async def send_subscription_cancelled_email(
        cls,
        to_email: str,
        user_name: str,
        plan_name: str,
        cancel_reason: str = "Solicitacao do cliente"
    ) -> bool:
        """
        Envia email de despedida quando assinatura e cancelada.
        """
        subject = "Sua assinatura foi cancelada - IFRS 16"

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
                        <td style="background: linear-gradient(135deg, #64748b 0%, #94a3b8 100%); padding: 40px; border-radius: 12px 12px 0 0; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Assinatura Cancelada</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px;">
                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6;">
                                Ola, <strong>{user_name}</strong>,
                            </p>
                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6;">
                                Sua assinatura do plano <strong>{plan_name}</strong> foi cancelada.
                            </p>
                            <table role="presentation" style="width: 100%; background-color: #f1f5f9; border-radius: 8px; margin: 20px 0;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="color: #475569; font-size: 14px; margin: 0;">
                                            <strong>Motivo:</strong> {cancel_reason}
                                        </p>
                                    </td>
                                </tr>
                            </table>
                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6;">
                                Sentimos muito em ve-lo partir. Se voce tiver algum feedback sobre o motivo do cancelamento, adorariamos ouvir de voce.
                            </p>
                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6;">
                                <strong>Voce sempre pode voltar!</strong>
                            </p>
                            <p style="color: #4a5568; font-size: 15px; line-height: 1.6;">
                                Seus dados serao mantidos por 90 dias. Se voce decidir renovar sua assinatura neste periodo, tudo estara esperando por voce.
                            </p>
                            <table role="presentation" style="width: 100%; margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{settings.FRONTEND_URL}/pricing.html"
                                           style="display: inline-block; background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 8px; font-size: 16px; font-weight: 600;">
                                            Renovar Assinatura
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            <p style="color: #718096; font-size: 14px; text-align: center;">
                                Obrigado por ter usado o IFRS 16. Esperamos ve-lo novamente em breve!
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #f8fafc; padding: 20px; border-radius: 0 0 12px 12px; text-align: center;">
                            <p style="color: #a0aec0; font-size: 12px; margin: 0;">
                                (c) 2025 IFRS 16 - Sistema de Gestao de Arrendamentos
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
Ola, {user_name},

Sua assinatura do plano {plan_name} foi cancelada.

Motivo: {cancel_reason}

Sentimos muito em ve-lo partir. Se voce tiver algum feedback sobre o motivo do cancelamento, adorariamos ouvir de voce.

Voce sempre pode voltar!

Seus dados serao mantidos por 90 dias. Se voce decidir renovar sua assinatura neste periodo, tudo estara esperando por voce.

Renovar assinatura: {settings.FRONTEND_URL}/pricing.html

Obrigado por ter usado o IFRS 16. Esperamos ve-lo novamente em breve!

Atenciosamente,
Equipe IFRS 16
        """

        return await cls.send_email(to_email, subject, html_content, text_content)

    @classmethod
    async def send_admin_new_subscription_notification(
        cls,
        customer_name: str,
        customer_email: str,
        plan_name: str,
        license_key: str,
        amount: str = "N/A"
    ) -> bool:
        """
        Envia notificacao ao administrador quando ha nova assinatura.
        """
        admin_email = "contato@fxstudioai.com"
        subject = f"[NOVA ASSINATURA] {customer_name} - {plan_name}"

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
                        <td style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 40px; border-radius: 12px 12px 0 0; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Nova Assinatura Recebida!</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px;">
                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6;">
                                <strong>Uma nova assinatura foi criada no sistema IFRS 16!</strong>
                            </p>

                            <table role="presentation" style="width: 100%; background-color: #f0fdf4; border-left: 4px solid #10b981; border-radius: 0 8px 8px 0; margin: 20px 0;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="color: #065f46; font-size: 14px; margin: 0 0 10px 0;">
                                            <strong>Dados do Cliente:</strong>
                                        </p>
                                        <p style="color: #065f46; font-size: 14px; margin: 5px 0;">
                                            <strong>Nome:</strong> {customer_name}
                                        </p>
                                        <p style="color: #065f46; font-size: 14px; margin: 5px 0;">
                                            <strong>Email:</strong> {customer_email}
                                        </p>
                                        <p style="color: #065f46; font-size: 14px; margin: 5px 0;">
                                            <strong>Plano:</strong> {plan_name}
                                        </p>
                                        <p style="color: #065f46; font-size: 14px; margin: 5px 0;">
                                            <strong>Valor:</strong> {amount}
                                        </p>
                                        <p style="color: #065f46; font-size: 14px; margin: 5px 0;">
                                            <strong>Chave de Licenca:</strong> <code style="background-color: #dcfce7; padding: 2px 6px; border-radius: 4px;">{license_key}</code>
                                        </p>
                                    </td>
                                </tr>
                            </table>

                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6;">
                                <strong>Acoes realizadas automaticamente:</strong>
                            </p>
                            <ul style="color: #4a5568; font-size: 15px; line-height: 1.8;">
                                <li>Usuario criado no sistema</li>
                                <li>Licenca gerada e ativada</li>
                                <li>Email de boas-vindas enviado para o cliente</li>
                                <li>Senha temporaria gerada (cliente sera forcado a alterar)</li>
                            </ul>

                            <table role="presentation" style="width: 100%; margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{settings.FRONTEND_URL}/dashboard.html"
                                           style="display: inline-block; background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 8px; font-size: 16px; font-weight: 600;">
                                            Ver Dashboard
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <p style="color: #718096; font-size: 14px; text-align: center;">
                                Esta e uma notificacao automatica do sistema IFRS 16
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #f8fafc; padding: 20px; border-radius: 0 0 12px 12px; text-align: center;">
                            <p style="color: #a0aec0; font-size: 12px; margin: 0;">
                                (c) 2025 IFRS 16 - Sistema de Gestao de Arrendamentos
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
NOVA ASSINATURA RECEBIDA!

Uma nova assinatura foi criada no sistema IFRS 16!

Dados do Cliente:
- Nome: {customer_name}
- Email: {customer_email}
- Plano: {plan_name}
- Valor: {amount}
- Chave de Licenca: {license_key}

Acoes realizadas automaticamente:
- Usuario criado no sistema
- Licenca gerada e ativada
- Email de boas-vindas enviado para o cliente
- Senha temporaria gerada (cliente sera forcado a alterar)

Ver Dashboard: {settings.FRONTEND_URL}/dashboard.html

---
Esta e uma notificacao automatica do sistema IFRS 16
        """

        return await cls.send_email(admin_email, subject, html_content, text_content)

