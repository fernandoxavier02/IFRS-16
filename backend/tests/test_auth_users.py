"""
Testes para autenticação de usuários
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.auth import hash_password


class TestUserRegistration:
    """Testes de registro de usuário"""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, client: AsyncClient):
        """Deve registrar um novo usuário com sucesso"""
        response = await client.post("/api/auth/register", json={
            "name": "Teste Usuario",
            "email": "teste@example.com",
            "password": "Senha123!"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "teste@example.com"
        assert data["name"] == "Teste Usuario"
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, client: AsyncClient, db_session: AsyncSession):
        """Deve rejeitar email duplicado"""
        # Criar usuário primeiro
        user = User(
            email="existente@example.com",
            name="Existente",
            password_hash=hash_password("Senha123!")
        )
        db_session.add(user)
        await db_session.commit()
        
        # Tentar registrar com mesmo email
        response = await client.post("/api/auth/register", json={
            "name": "Outro",
            "email": "existente@example.com",
            "password": "Senha123!"
        })
        
        assert response.status_code == 400
        assert "já está cadastrado" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_user_weak_password(self, client: AsyncClient):
        """Deve rejeitar senha fraca"""
        response = await client.post("/api/auth/register", json={
            "name": "Teste",
            "email": "teste@example.com",
            "password": "fraca"  # Sem maiúscula, sem número
        })
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_register_user_invalid_email(self, client: AsyncClient):
        """Deve rejeitar email inválido"""
        response = await client.post("/api/auth/register", json={
            "name": "Teste",
            "email": "email-invalido",
            "password": "Senha123!"
        })
        
        assert response.status_code == 422


class TestUserLogin:
    """Testes de login de usuário"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, db_session: AsyncSession):
        """Deve fazer login com sucesso"""
        # Criar usuário
        user = User(
            email="login@example.com",
            name="Login Test",
            password_hash=hash_password("Senha123!"),
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        
        # Fazer login
        response = await client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "Senha123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_type"] == "user"
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, db_session: AsyncSession):
        """Deve rejeitar senha incorreta"""
        user = User(
            email="wrong@example.com",
            name="Wrong Pass",
            password_hash=hash_password("Senha123!"),
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        
        response = await client.post("/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "SenhaErrada123!"
        })
        
        assert response.status_code == 401
        assert "incorretos" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Deve rejeitar usuário inexistente"""
        response = await client.post("/api/auth/login", json={
            "email": "naoexiste@example.com",
            "password": "Senha123!"
        })
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client: AsyncClient, db_session: AsyncSession):
        """Deve rejeitar usuário inativo"""
        user = User(
            email="inativo@example.com",
            name="Inativo",
            password_hash=hash_password("Senha123!"),
            is_active=False
        )
        db_session.add(user)
        await db_session.commit()
        
        response = await client.post("/api/auth/login", json={
            "email": "inativo@example.com",
            "password": "Senha123!"
        })
        
        assert response.status_code == 401
        assert "desativada" in response.json()["detail"]


class TestUserMe:
    """Testes do endpoint /me"""
    
    @pytest.mark.asyncio
    async def test_get_me_success(self, client: AsyncClient, db_session: AsyncSession):
        """Deve retornar dados do usuário autenticado"""
        # Criar e logar usuário
        user = User(
            email="me@example.com",
            name="Me Test",
            password_hash=hash_password("Senha123!"),
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        
        login_response = await client.post("/api/auth/login", json={
            "email": "me@example.com",
            "password": "Senha123!"
        })
        token = login_response.json()["access_token"]
        
        # Acessar /me
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["name"] == "Me Test"
    
    @pytest.mark.asyncio
    async def test_get_me_no_token(self, client: AsyncClient):
        """Deve rejeitar acesso sem token"""
        response = await client.get("/api/auth/me")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Deve rejeitar token inválido"""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer token-invalido"}
        )
        assert response.status_code == 401


class TestChangePassword:
    """Testes de alteração de senha"""
    
    @pytest.mark.asyncio
    async def test_change_password_success(self, client: AsyncClient, db_session: AsyncSession):
        """Deve alterar senha com sucesso"""
        user = User(
            email="change@example.com",
            name="Change Pass",
            password_hash=hash_password("SenhaAntiga123!"),
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        
        # Login
        login_response = await client.post("/api/auth/login", json={
            "email": "change@example.com",
            "password": "SenhaAntiga123!"
        })
        token = login_response.json()["access_token"]
        
        # Alterar senha
        response = await client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "SenhaAntiga123!",
                "new_password": "SenhaNova123!"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["success"] == True
        
        # Verificar que nova senha funciona
        new_login = await client.post("/api/auth/login", json={
            "email": "change@example.com",
            "password": "SenhaNova123!"
        })
        assert new_login.status_code == 200
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, client: AsyncClient, db_session: AsyncSession):
        """Deve rejeitar senha atual incorreta"""
        user = User(
            email="wrongcurrent@example.com",
            name="Wrong Current",
            password_hash=hash_password("SenhaCorreta123!"),
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        
        login_response = await client.post("/api/auth/login", json={
            "email": "wrongcurrent@example.com",
            "password": "SenhaCorreta123!"
        })
        token = login_response.json()["access_token"]
        
        response = await client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "SenhaErrada123!",
                "new_password": "SenhaNova123!"
            }
        )
        
        assert response.status_code == 400
        assert "incorreta" in response.json()["detail"]

