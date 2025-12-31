"""
Testes de Carga para Sistema de Sessões Simultâneas

Para executar:
pip install locust

# Teste local
locust -f locustfile.py --host=http://localhost:8000

# Teste produção
locust -f locustfile.py --host=https://ifrs16-backend-1051753255664.us-central1.run.app

# Abrir navegador em http://localhost:8089
"""

from locust import HttpUser, task, between, events
import uuid
import random


class SessionUser(HttpUser):
    """
    Simula usuário real que:
    - Faz login
    - Envia heartbeat periodicamente
    - Lista sessões ativas ocasionalmente
    - Faz logout
    """
    wait_time = between(1, 5)  # Aguarda 1-5 segundos entre tarefas

    def on_start(self):
        """Executado quando usuário inicia simulação"""
        # Criar credenciais únicas
        unique_id = str(uuid.uuid4())[:8]
        self.email = f"load-test-{unique_id}@test.com"
        self.password = "Test123!"
        self.name = f"Load Test User {unique_id}"

        # Tentar fazer login (usuário pode não existir)
        login_response = self.client.post(
            "/api/auth/login",
            json={
                "email": self.email,
                "password": self.password
            },
            name="Login"
        )

        if login_response.status_code == 200:
            # Login bem-sucedido
            data = login_response.json()
            self.auth_token = data.get("access_token")
            self.session_token = data.get("session_token")
            print(f"[OK] Login bem-sucedido: {self.email}")
        else:
            # Usuário não existe, criar conta
            print(f"[INFO] Criando usuário: {self.email}")

            register_response = self.client.post(
                "/api/auth/register",
                json={
                    "email": self.email,
                    "name": self.name,
                    "password": self.password
                },
                name="Register"
            )

            if register_response.status_code in [200, 201]:
                # Fazer login após registro
                login_response = self.client.post(
                    "/api/auth/login",
                    json={
                        "email": self.email,
                        "password": self.password
                    },
                    name="Login após registro"
                )

                if login_response.status_code == 200:
                    data = login_response.json()
                    self.auth_token = data.get("access_token")
                    self.session_token = data.get("session_token")
                    print(f"[OK] Login pós-registro: {self.email}")
                else:
                    print(f"[ERRO] Falha no login pós-registro: {self.email}")
                    self.auth_token = None
                    self.session_token = None
            else:
                print(f"[ERRO] Falha no registro: {self.email}")
                self.auth_token = None
                self.session_token = None

    @task(10)
    def heartbeat(self):
        """
        Envia heartbeat para manter sessão ativa
        Peso 10 = executado com mais frequência
        """
        if not self.auth_token or not self.session_token:
            return

        response = self.client.post(
            f"/api/auth/sessions/heartbeat?session_token={self.session_token}",
            headers={"Authorization": f"Bearer {self.auth_token}"},
            name="Heartbeat"
        )

        if response.status_code == 401:
            print(f"[WARN] Sessão expirada para {self.email}")
            # Tentar fazer novo login
            self.on_start()

    @task(2)
    def list_active_sessions(self):
        """
        Lista sessões ativas do usuário
        Peso 2 = menos frequente que heartbeat
        """
        if not self.auth_token:
            return

        self.client.get(
            "/api/auth/sessions/active",
            headers={"Authorization": f"Bearer {self.auth_token}"},
            name="List Sessions"
        )

    @task(1)
    def verify_token(self):
        """
        Verifica se token ainda é válido
        Peso 1 = ainda menos frequente
        """
        if not self.auth_token:
            return

        self.client.get(
            "/api/auth/verify-token",
            headers={"Authorization": f"Bearer {self.auth_token}"},
            name="Verify Token"
        )

    def on_stop(self):
        """Executado quando usuário para simulação (logout)"""
        if self.auth_token and self.session_token:
            self.client.post(
                f"/api/auth/sessions/terminate?session_token={self.session_token}",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                name="Logout"
            )
            print(f"[OK] Logout: {self.email}")


class MultiDeviceUser(HttpUser):
    """
    Simula usuário tentando usar múltiplos dispositivos
    Testa o sistema de limite de sessões
    """
    wait_time = between(2, 10)

    def on_start(self):
        """Setup inicial"""
        unique_id = str(uuid.uuid4())[:8]
        self.email = f"multi-device-{unique_id}@test.com"
        self.password = "Test123!"
        self.sessions = []

        # Registrar usuário
        self.client.post(
            "/api/auth/register",
            json={
                "email": self.email,
                "name": f"Multi Device {unique_id}",
                "password": self.password
            },
            name="Register"
        )

    @task
    def create_multiple_sessions(self):
        """
        Tenta criar múltiplas sessões (simula múltiplos dispositivos)
        """
        # Simular diferentes User-Agents
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)",
            "Mozilla/5.0 (Linux; Android 11)",
            "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)"
        ]

        # Fazer login com User-Agent aleatório
        user_agent = random.choice(user_agents)
        response = self.client.post(
            "/api/auth/login",
            json={
                "email": self.email,
                "password": self.password
            },
            headers={"User-Agent": user_agent},
            name="Login (multi-device)"
        )

        if response.status_code == 200:
            data = response.json()
            session_info = {
                "auth_token": data.get("access_token"),
                "session_token": data.get("session_token"),
                "user_agent": user_agent
            }
            self.sessions.append(session_info)
            print(f"[INFO] Sessão criada: {user_agent[:30]}... Total: {len(self.sessions)}")

            # Tentar heartbeat em sessões antigas (podem estar invalidadas)
            for old_session in self.sessions[:-1]:
                self.client.post(
                    f"/api/auth/sessions/heartbeat?session_token={old_session['session_token']}",
                    headers={"Authorization": f"Bearer {old_session['auth_token']}"},
                    name="Heartbeat (old session)"
                )


class StressTestUser(HttpUser):
    """
    Teste de estresse - máxima carga
    """
    wait_time = between(0.1, 1)  # Requisições muito rápidas

    def on_start(self):
        """Login rápido"""
        unique_id = str(uuid.uuid4())[:8]
        self.email = f"stress-{unique_id}@test.com"
        self.password = "Test123!"

        self.client.post("/api/auth/register", json={
            "email": self.email,
            "name": "Stress User",
            "password": self.password
        })

        response = self.client.post("/api/auth/login", json={
            "email": self.email,
            "password": self.password
        })

        if response.status_code == 200:
            data = response.json()
            self.auth_token = data["access_token"]
            self.session_token = data["session_token"]
        else:
            self.auth_token = None
            self.session_token = None

    @task(20)
    def rapid_heartbeat(self):
        """Heartbeat muito frequente"""
        if not self.auth_token:
            return

        self.client.post(
            f"/api/auth/sessions/heartbeat?session_token={self.session_token}",
            headers={"Authorization": f"Bearer {self.auth_token}"},
            name="Rapid Heartbeat"
        )


# =============================================================================
# EVENTOS DE MONITORAMENTO
# =============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Executado quando teste inicia"""
    print("\n" + "="*80)
    print("🚀 INICIANDO TESTE DE CARGA - SISTEMA DE SESSÕES")
    print("="*80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Executado quando teste termina"""
    print("\n" + "="*80)
    print("✅ TESTE DE CARGA FINALIZADO")
    print("="*80 + "\n")

    # Estatísticas
    stats = environment.stats
    print(f"Total de requisições: {stats.total.num_requests}")
    print(f"Falhas: {stats.total.num_failures}")
    print(f"Taxa de erro: {stats.total.fail_ratio * 100:.2f}%")
    print(f"RPS médio: {stats.total.total_rps:.2f}")
    print(f"Tempo médio de resposta: {stats.total.avg_response_time:.2f}ms")
    print(f"P95: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"P99: {stats.total.get_response_time_percentile(0.99):.2f}ms")


# =============================================================================
# CONFIGURAÇÃO DE CENÁRIOS
# =============================================================================

# Descomentar para usar cenários customizados

# from locust import LoadTestShape

# class StepLoadShape(LoadTestShape):
#     """
#     Carga em degraus:
#     - 0-60s: 10 usuários
#     - 60-120s: 50 usuários
#     - 120-180s: 100 usuários
#     - 180-240s: 200 usuários
#     """
#     step_time = 60
#     step_load = 10
#     spawn_rate = 10
#     time_limit = 240

#     def tick(self):
#         run_time = self.get_run_time()

#         if run_time < self.time_limit:
#             current_step = int(run_time // self.step_time)
#             return (current_step + 1) * self.step_load, self.spawn_rate
#         return None
