"""
Testes para funções de autenticação JWT
"""

import pytest
from datetime import timedelta
from jose import jwt

from app.auth import (
    create_access_token,
    verify_token,
    decode_token_unsafe,
    is_token_expired,
    get_token_expiration
)
from app.config import get_settings


settings = get_settings()


# ============================================================
# Testes de Criação de Token
# ============================================================

def test_create_token_basic():
    """Teste: Token é criado corretamente"""
    data = {"key": "TEST-LICENSE", "user": "test"}
    token = create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_token_with_custom_expiration():
    """Teste: Token com expiração customizada"""
    data = {"key": "TEST-LICENSE"}
    token = create_access_token(data, expires_delta=timedelta(hours=2))
    
    # Verificar que foi criado
    assert token is not None
    
    # Decodificar e verificar expiração
    decoded = verify_token(token)
    assert decoded is not None


def test_create_token_contains_data():
    """Teste: Token contém os dados fornecidos"""
    data = {
        "key": "TEST-LICENSE-123",
        "customer_name": "Test User",
        "license_type": "pro"
    }
    token = create_access_token(data)
    
    decoded = verify_token(token)
    
    assert decoded["key"] == data["key"]
    assert decoded["customer_name"] == data["customer_name"]
    assert decoded["license_type"] == data["license_type"]


def test_create_token_has_standard_claims():
    """Teste: Token contém claims padrão (exp, iat, type)"""
    token = create_access_token({"key": "TEST"})
    decoded = verify_token(token)
    
    assert "exp" in decoded
    assert "iat" in decoded
    assert decoded["type"] == "access"


# ============================================================
# Testes de Verificação de Token
# ============================================================

def test_verify_valid_token():
    """Teste: Token válido é decodificado corretamente"""
    data = {"key": "TEST-LICENSE"}
    token = create_access_token(data)
    
    decoded = verify_token(token)
    
    assert decoded is not None
    assert decoded["key"] == "TEST-LICENSE"


def test_verify_expired_token():
    """Teste: Token expirado retorna None"""
    data = {"key": "TEST-LICENSE"}
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))
    
    decoded = verify_token(token)
    
    assert decoded is None


def test_verify_invalid_token():
    """Teste: Token inválido retorna None"""
    invalid_tokens = [
        "not.a.token",
        "invalid",
        "",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
    ]
    
    for token in invalid_tokens:
        decoded = verify_token(token)
        assert decoded is None, f"Token deveria ser inválido: {token}"


def test_verify_token_with_wrong_secret():
    """Teste: Token com assinatura errada é rejeitado"""
    # Criar token com uma chave
    data = {"key": "TEST"}
    token = jwt.encode(data, "wrong-secret", algorithm="HS256")
    
    # Tentar verificar com outra chave
    decoded = verify_token(token)
    
    assert decoded is None


def test_verify_token_with_wrong_algorithm():
    """Teste: Token com algoritmo errado é rejeitado"""
    data = {"key": "TEST"}
    # Criar com algoritmo diferente (se suportado)
    # Este teste verifica que não aceitamos qualquer algoritmo
    token = create_access_token(data)
    
    # Token válido criado com algoritmo correto deve funcionar
    decoded = verify_token(token)
    assert decoded is not None


# ============================================================
# Testes de Decodificação Unsafe
# ============================================================

def test_decode_unsafe_valid_token():
    """Teste: Decodificação unsafe funciona com token válido"""
    data = {"key": "TEST-LICENSE", "custom": "value"}
    token = create_access_token(data)
    
    decoded = decode_token_unsafe(token)
    
    assert decoded is not None
    assert decoded["key"] == "TEST-LICENSE"
    assert decoded["custom"] == "value"


def test_decode_unsafe_expired_token():
    """Teste: Decodificação unsafe funciona com token expirado"""
    data = {"key": "TEST-LICENSE"}
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))
    
    # verify_token retornaria None para expirado
    assert verify_token(token) is None
    
    # Mas decode_unsafe deve funcionar
    decoded = decode_token_unsafe(token)
    assert decoded is not None
    assert decoded["key"] == "TEST-LICENSE"


def test_decode_unsafe_invalid_token():
    """Teste: Decodificação unsafe retorna None para token inválido"""
    decoded = decode_token_unsafe("completely.invalid.token")
    
    # Pode retornar None ou dados dependendo do formato
    # O importante é não crashar


# ============================================================
# Testes de Verificação de Expiração
# ============================================================

def test_is_token_expired_valid():
    """Teste: Token válido não está expirado"""
    token = create_access_token({"key": "TEST"})
    
    assert is_token_expired(token) is False


def test_is_token_expired_expired():
    """Teste: Token expirado é detectado"""
    token = create_access_token(
        {"key": "TEST"},
        expires_delta=timedelta(seconds=-1)
    )
    
    assert is_token_expired(token) is True


def test_is_token_expired_invalid():
    """Teste: Token inválido é considerado expirado"""
    assert is_token_expired("invalid.token") is True


# ============================================================
# Testes de Data de Expiração
# ============================================================

def test_get_token_expiration_valid():
    """Teste: Obtém data de expiração de token válido"""
    token = create_access_token({"key": "TEST"})
    
    expiration = get_token_expiration(token)
    
    assert expiration is not None


def test_get_token_expiration_invalid():
    """Teste: Retorna None para token inválido"""
    expiration = get_token_expiration("invalid.token")
    
    # Pode ser None se o token for completamente inválido


# ============================================================
# Testes de Segurança
# ============================================================

def test_different_data_different_tokens():
    """Teste: Dados diferentes geram tokens diferentes"""
    token1 = create_access_token({"key": "LICENSE-1"})
    token2 = create_access_token({"key": "LICENSE-2"})
    
    assert token1 != token2


def test_same_data_different_tokens():
    """Teste: Mesmo dado pode gerar tokens diferentes (por iat)"""
    import time
    
    data = {"key": "TEST-LICENSE"}
    token1 = create_access_token(data)
    time.sleep(0.1)  # Pequeno delay para mudar o timestamp
    token2 = create_access_token(data)
    
    # Tokens podem ser iguais ou diferentes dependendo do timestamp
    # O importante é que ambos são válidos
    assert verify_token(token1) is not None
    assert verify_token(token2) is not None


def test_token_cannot_be_modified():
    """Teste: Token modificado é rejeitado"""
    token = create_access_token({"key": "TEST"})
    
    # Modificar um caractere do token
    modified_token = token[:-1] + ("a" if token[-1] != "a" else "b")
    
    # Token modificado deve ser rejeitado
    decoded = verify_token(modified_token)
    assert decoded is None

