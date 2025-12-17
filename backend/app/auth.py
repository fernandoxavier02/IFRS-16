"""
Autenticação JWT, hash de senha e validação de tokens
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Header, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .config import get_settings
from .database import get_db

settings = get_settings()

# Contexto de criptografia para senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema de segurança HTTP Bearer
security = HTTPBearer(auto_error=False)


# =============================================================================
# FUNÇÕES DE HASH DE SENHA
# =============================================================================

def hash_password(password: str) -> str:
    """
    Gera hash bcrypt da senha.
    
    Args:
        password: Senha em texto plano
    
    Returns:
        Hash bcrypt da senha
    
    Note:
        bcrypt tem limite de 72 bytes, então truncamos se necessário
    """
    # Debug removido para evitar problemas de encoding
    
    # bcrypt tem limite de 72 bytes - truncar por BYTES, não caracteres
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        print(f"⚠️ Senha muito longa ({len(password_bytes)} bytes), truncando para 72 bytes")
        password_bytes = password_bytes[:72]
        password = password_bytes.decode('utf-8', errors='ignore')
        print(f"✅ Senha truncada para {len(password.encode('utf-8'))} bytes")
    
    try:
        result = pwd_context.hash(password)
        print(f"✅ Hash gerado com sucesso")
        return result
    except Exception as e:
        print(f"⚠️ Erro ao gerar hash com passlib: {type(e).__name__}: {e}")
        print(f"   Tentando bcrypt diretamente...")
        # Fallback: usar bcrypt diretamente
        import bcrypt
        salt = bcrypt.gensalt()
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        result = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        print(f"✅ Hash gerado diretamente com bcrypt")
        return result


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha corresponde ao hash.
    
    Args:
        plain_password: Senha em texto plano
        hashed_password: Hash armazenado
    
    Returns:
        True se a senha corresponde, False caso contrário
    
    Note:
        Usa bcrypt diretamente para evitar problemas com passlib
    """
    try:
        import bcrypt
        # bcrypt tem limite de 72 bytes - truncar se necessário
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Verificar senha com bcrypt diretamente
        return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
    except Exception as e:
        # Log do erro mas não expor detalhes
        print(f"Erro ao verificar senha: {type(e).__name__}")
        return False


# =============================================================================
# FUNÇÕES DE TOKEN JWT
# =============================================================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    token_type: str = "access"
) -> str:
    """
    Cria um token JWT com os dados fornecidos.
    
    Args:
        data: Dicionário com dados a incluir no token
        expires_delta: Tempo de expiração customizado (opcional)
        token_type: Tipo do token (access, refresh, etc)
    
    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": token_type
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_admin_token(admin_id: UUID, username: str, role: str) -> str:
    """
    Cria token JWT específico para admin.
    """
    return create_access_token(
        data={
            "sub": str(admin_id),
            "username": username,
            "role": role,
            "user_type": "admin"
        }
    )


def create_user_token(user_id: UUID, email: str) -> str:
    """
    Cria token JWT específico para usuário cliente.
    """
    return create_access_token(
        data={
            "sub": str(user_id),
            "email": email,
            "user_type": "user"
        }
    )


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifica e decodifica um token JWT.
    
    Args:
        token: Token JWT a ser verificado
    
    Returns:
        Payload decodificado ou None se inválido
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def decode_token_unsafe(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodifica um token JWT sem verificar a assinatura.
    Útil para debugging e logs.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_signature": False, "verify_exp": False}
        )
        return payload
    except JWTError:
        return None


# =============================================================================
# DEPENDENCIES DE AUTENTICAÇÃO
# =============================================================================

async def get_current_license(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency que extrai e valida o token JWT do header Authorization.
    Usado para validar licenças na calculadora.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Dependency para obter usuário cliente autenticado.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if payload.get("user_type") != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido apenas para usuários"
        )
    
    # Verificar se usuário existe e está ativo
    from .models import User
    user_id_str = payload.get("sub")
    
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: ID do usuário não encontrado"
        )
    
    try:
        user_id = UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: ID do usuário inválido"
        )
    
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo"
        )
    
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "user": user
    }


async def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Dependency para obter admin autenticado.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if payload.get("user_type") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido apenas para administradores"
        )
    
    # Verificar se admin existe e está ativo
    from .models import AdminUser
    admin_id_str = payload.get("sub")
    
    if not admin_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: ID do administrador não encontrado"
        )
    
    try:
        admin_id = UUID(admin_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: ID do administrador inválido"
        )
    
    result = await db.execute(
        select(AdminUser).where(AdminUser.id == admin_id, AdminUser.is_active == True)
    )
    admin = result.scalar_one_or_none()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrador não encontrado ou inativo"
        )
    
    return {
        "id": str(admin.id),
        "username": admin.username,
        "email": admin.email,
        "role": admin.role.value,
        "admin": admin
    }


async def get_current_user_or_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Dependency que aceita tanto usuário comum quanto admin.
    Retorna o usuário/admin autenticado.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_type = payload.get("user_type")
    
    if user_type == "admin":
        # Retornar como admin
        from .models import AdminUser
        admin_id_str = payload.get("sub")
        
        if not admin_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: ID do administrador não encontrado"
            )
        
        try:
            admin_id = UUID(admin_id_str)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: ID do administrador inválido"
            )
        
        result = await db.execute(
            select(AdminUser).where(AdminUser.id == admin_id, AdminUser.is_active == True)
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Administrador não encontrado ou inativo"
            )
        
        return {
            "id": str(admin.id),
            "email": admin.email,
            "username": admin.username,
            "role": admin.role.value,
            "user_type": "admin",
            "is_admin": True,
            "admin": admin
        }
    
    elif user_type == "user":
        # Retornar como usuário comum
        from .models import User
        user_id_str = payload.get("sub")
        
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: ID do usuário não encontrado"
            )
        
        try:
            user_id = UUID(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: ID do usuário inválido"
            )
        
        result = await db.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado ou inativo"
            )
        
        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "user_type": "user",
            "is_admin": False,
            "user": user
        }
    
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tipo de usuário inválido"
        )


async def get_superadmin(
    admin_data: Dict[str, Any] = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Dependency que requer superadmin.
    """
    if admin_data.get("role") != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido apenas para superadmin"
        )
    return admin_data


# Manter compatibilidade com token fixo para rotas legadas
async def verify_admin_token(
    x_admin_token: str = Header(None, description="Token de administrador (legado)")
) -> bool:
    """
    Dependency que verifica o token de administrador (legado).
    Mantido para compatibilidade com admin.html antigo.
    """
    if x_admin_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de administrador não fornecido"
        )
    
    if x_admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token de administrador inválido"
        )
    
    return True


# =============================================================================
# UTILITÁRIOS
# =============================================================================

def is_token_expired(token: str) -> bool:
    """
    Verifica se um token está expirado.
    """
    try:
        jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return False
    except JWTError:
        return True


def get_token_expiration(token: str) -> Optional[datetime]:
    """
    Obtém a data de expiração de um token.
    """
    payload = decode_token_unsafe(token)
    if payload and "exp" in payload:
        return datetime.fromtimestamp(payload["exp"])
    return None
