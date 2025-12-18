"""
MCP Server para Firebase - Conexão direta com Firebase Admin SDK
Permite gerenciar:
- Firestore (banco de dados)
- Authentication (usuários)
- Storage (arquivos)
- Hosting (deploy)
"""

import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

# Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, auth, storage
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️ firebase-admin não instalado. Execute: pip install firebase-admin")


class FirebaseMCPServer:
    """
    Servidor MCP para integração direta com Firebase.
    Fornece ferramentas para gerenciar:
    - Firestore Database
    - Firebase Authentication
    - Cloud Storage
    - Hosting
    """
    
    def __init__(
        self,
        credentials_path: str = None,
        project_id: str = None
    ):
        if not FIREBASE_AVAILABLE:
            raise ImportError("firebase-admin não está instalado")
        
        self.project_id = project_id or os.getenv("FIREBASE_PROJECT_ID", "ifrs16-app")
        
        # Inicializar Firebase se ainda não foi inicializado
        if not firebase_admin._apps:
            if credentials_path:
                cred = credentials.Certificate(credentials_path)
            elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                cred = credentials.Certificate(
                    os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                )
            else:
                # Usar credenciais padrão (Application Default Credentials)
                cred = credentials.ApplicationDefault()
            
            firebase_admin.initialize_app(cred, {
                "projectId": self.project_id,
                "storageBucket": f"{self.project_id}.appspot.com"
            })
        
        self.db = firestore.client()
        self.bucket = storage.bucket()
    
    # =========================================================================
    # FIRESTORE - CRUD
    # =========================================================================
    
    async def firestore_list_collections(self) -> List[str]:
        """Lista todas as coleções do Firestore"""
        collections = self.db.collections()
        return [col.id for col in collections]
    
    async def firestore_get_documents(
        self,
        collection: str,
        limit: int = 100,
        order_by: str = None,
        order_direction: str = "ASCENDING",
        where_field: str = None,
        where_op: str = None,
        where_value: Any = None
    ) -> List[Dict]:
        """Lista documentos de uma coleção"""
        query = self.db.collection(collection)
        
        if where_field and where_op and where_value is not None:
            query = query.where(where_field, where_op, where_value)
        
        if order_by:
            direction = (
                firestore.Query.DESCENDING 
                if order_direction.upper() == "DESCENDING" 
                else firestore.Query.ASCENDING
            )
            query = query.order_by(order_by, direction=direction)
        
        query = query.limit(limit)
        docs = query.stream()
        
        return [{
            "id": doc.id,
            "data": doc.to_dict(),
            "create_time": doc.create_time.isoformat() if doc.create_time else None,
            "update_time": doc.update_time.isoformat() if doc.update_time else None,
        } for doc in docs]
    
    async def firestore_get_document(
        self,
        collection: str,
        document_id: str
    ) -> Optional[Dict]:
        """Busca um documento específico"""
        doc_ref = self.db.collection(collection).document(document_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return None
        
        return {
            "id": doc.id,
            "data": doc.to_dict(),
            "create_time": doc.create_time.isoformat() if doc.create_time else None,
            "update_time": doc.update_time.isoformat() if doc.update_time else None,
        }
    
    async def firestore_create_document(
        self,
        collection: str,
        data: Dict,
        document_id: str = None
    ) -> Dict:
        """Cria um novo documento"""
        if document_id:
            doc_ref = self.db.collection(collection).document(document_id)
            doc_ref.set(data)
        else:
            doc_ref = self.db.collection(collection).add(data)[1]
        
        return {
            "id": doc_ref.id,
            "path": doc_ref.path,
            "created": True
        }
    
    async def firestore_update_document(
        self,
        collection: str,
        document_id: str,
        data: Dict,
        merge: bool = True
    ) -> Dict:
        """Atualiza um documento existente"""
        doc_ref = self.db.collection(collection).document(document_id)
        
        if merge:
            doc_ref.set(data, merge=True)
        else:
            doc_ref.update(data)
        
        return {
            "id": document_id,
            "path": doc_ref.path,
            "updated": True
        }
    
    async def firestore_delete_document(
        self,
        collection: str,
        document_id: str
    ) -> Dict:
        """Deleta um documento"""
        doc_ref = self.db.collection(collection).document(document_id)
        doc_ref.delete()
        
        return {
            "id": document_id,
            "deleted": True
        }
    
    async def firestore_batch_write(
        self,
        operations: List[Dict]
    ) -> Dict:
        """
        Executa múltiplas operações em batch.
        
        operations: Lista de dicts com:
        - type: "create", "update", "delete"
        - collection: nome da coleção
        - document_id: ID do documento
        - data: dados (para create/update)
        """
        batch = self.db.batch()
        
        for op in operations:
            doc_ref = self.db.collection(op["collection"]).document(op["document_id"])
            
            if op["type"] == "create":
                batch.set(doc_ref, op["data"])
            elif op["type"] == "update":
                batch.update(doc_ref, op["data"])
            elif op["type"] == "delete":
                batch.delete(doc_ref)
        
        batch.commit()
        
        return {
            "operations_count": len(operations),
            "success": True
        }
    
    # =========================================================================
    # AUTHENTICATION
    # =========================================================================
    
    async def auth_list_users(
        self,
        limit: int = 100,
        page_token: str = None
    ) -> Dict:
        """Lista usuários do Firebase Auth"""
        result = auth.list_users(max_results=limit, page_token=page_token)
        
        users = [{
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "disabled": user.disabled,
            "email_verified": user.email_verified,
            "creation_timestamp": user.user_metadata.creation_timestamp if user.user_metadata else None,
            "last_sign_in_timestamp": user.user_metadata.last_sign_in_timestamp if user.user_metadata else None,
        } for user in result.users]
        
        return {
            "users": users,
            "page_token": result.next_page_token
        }
    
    async def auth_get_user(self, uid: str) -> Optional[Dict]:
        """Busca um usuário pelo UID"""
        try:
            user = auth.get_user(uid)
            return {
                "uid": user.uid,
                "email": user.email,
                "display_name": user.display_name,
                "phone_number": user.phone_number,
                "photo_url": user.photo_url,
                "disabled": user.disabled,
                "email_verified": user.email_verified,
                "custom_claims": user.custom_claims,
                "provider_data": [{
                    "provider_id": p.provider_id,
                    "uid": p.uid,
                    "email": p.email,
                } for p in user.provider_data],
            }
        except auth.UserNotFoundError:
            return None
    
    async def auth_get_user_by_email(self, email: str) -> Optional[Dict]:
        """Busca um usuário pelo email"""
        try:
            user = auth.get_user_by_email(email)
            return await self.auth_get_user(user.uid)
        except auth.UserNotFoundError:
            return None
    
    async def auth_create_user(
        self,
        email: str,
        password: str,
        display_name: str = None,
        disabled: bool = False
    ) -> Dict:
        """Cria um novo usuário"""
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name,
            disabled=disabled
        )
        
        return {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "created": True
        }
    
    async def auth_update_user(
        self,
        uid: str,
        email: str = None,
        password: str = None,
        display_name: str = None,
        disabled: bool = None,
        email_verified: bool = None
    ) -> Dict:
        """Atualiza um usuário"""
        kwargs = {}
        if email:
            kwargs["email"] = email
        if password:
            kwargs["password"] = password
        if display_name is not None:
            kwargs["display_name"] = display_name
        if disabled is not None:
            kwargs["disabled"] = disabled
        if email_verified is not None:
            kwargs["email_verified"] = email_verified
        
        user = auth.update_user(uid, **kwargs)
        
        return {
            "uid": user.uid,
            "email": user.email,
            "updated": True
        }
    
    async def auth_delete_user(self, uid: str) -> Dict:
        """Deleta um usuário"""
        auth.delete_user(uid)
        return {"uid": uid, "deleted": True}
    
    async def auth_set_custom_claims(
        self,
        uid: str,
        claims: Dict
    ) -> Dict:
        """Define custom claims para um usuário"""
        auth.set_custom_user_claims(uid, claims)
        return {"uid": uid, "claims": claims, "updated": True}
    
    async def auth_generate_password_reset_link(self, email: str) -> str:
        """Gera link de reset de senha"""
        return auth.generate_password_reset_link(email)
    
    async def auth_generate_email_verification_link(self, email: str) -> str:
        """Gera link de verificação de email"""
        return auth.generate_email_verification_link(email)
    
    # =========================================================================
    # STORAGE
    # =========================================================================
    
    async def storage_list_files(
        self,
        prefix: str = None,
        max_results: int = 100
    ) -> List[Dict]:
        """Lista arquivos no Storage"""
        blobs = self.bucket.list_blobs(prefix=prefix, max_results=max_results)
        
        return [{
            "name": blob.name,
            "size": blob.size,
            "content_type": blob.content_type,
            "created": blob.time_created.isoformat() if blob.time_created else None,
            "updated": blob.updated.isoformat() if blob.updated else None,
            "public_url": blob.public_url,
        } for blob in blobs]
    
    async def storage_get_file_url(
        self,
        file_path: str,
        expiration_minutes: int = 60
    ) -> str:
        """Gera URL assinada para download"""
        from datetime import timedelta
        
        blob = self.bucket.blob(file_path)
        url = blob.generate_signed_url(
            expiration=timedelta(minutes=expiration_minutes),
            method="GET"
        )
        return url
    
    async def storage_upload_file(
        self,
        file_path: str,
        destination_path: str,
        content_type: str = None
    ) -> Dict:
        """Faz upload de um arquivo"""
        blob = self.bucket.blob(destination_path)
        blob.upload_from_filename(file_path, content_type=content_type)
        
        return {
            "name": blob.name,
            "size": blob.size,
            "public_url": blob.public_url,
            "uploaded": True
        }
    
    async def storage_delete_file(self, file_path: str) -> Dict:
        """Deleta um arquivo"""
        blob = self.bucket.blob(file_path)
        blob.delete()
        
        return {"name": file_path, "deleted": True}
    
    # =========================================================================
    # HOSTING INFO
    # =========================================================================
    
    async def get_project_info(self) -> Dict:
        """Retorna informações do projeto"""
        return {
            "project_id": self.project_id,
            "storage_bucket": f"{self.project_id}.appspot.com",
            "hosting_url": f"https://{self.project_id}.web.app",
            "firestore_url": f"https://console.firebase.google.com/project/{self.project_id}/firestore",
            "auth_url": f"https://console.firebase.google.com/project/{self.project_id}/authentication",
        }


# =========================================================================
# MCP TOOLS DEFINITION
# =========================================================================

MCP_TOOLS = {
    # Firestore
    "firebase_list_collections": {
        "description": "Lista todas as coleções do Firestore",
        "parameters": {}
    },
    "firebase_get_documents": {
        "description": "Lista documentos de uma coleção",
        "parameters": {
            "collection": {"type": "string", "required": True},
            "limit": {"type": "integer", "default": 100},
            "order_by": {"type": "string", "optional": True},
            "where_field": {"type": "string", "optional": True},
            "where_op": {"type": "string", "optional": True},
            "where_value": {"type": "any", "optional": True},
        }
    },
    "firebase_get_document": {
        "description": "Busca um documento específico",
        "parameters": {
            "collection": {"type": "string", "required": True},
            "document_id": {"type": "string", "required": True},
        }
    },
    "firebase_create_document": {
        "description": "Cria um novo documento no Firestore",
        "parameters": {
            "collection": {"type": "string", "required": True},
            "data": {"type": "object", "required": True},
            "document_id": {"type": "string", "optional": True},
        }
    },
    "firebase_update_document": {
        "description": "Atualiza um documento existente",
        "parameters": {
            "collection": {"type": "string", "required": True},
            "document_id": {"type": "string", "required": True},
            "data": {"type": "object", "required": True},
        }
    },
    "firebase_delete_document": {
        "description": "Deleta um documento",
        "parameters": {
            "collection": {"type": "string", "required": True},
            "document_id": {"type": "string", "required": True},
        }
    },
    # Auth
    "firebase_list_users": {
        "description": "Lista usuários do Firebase Auth",
        "parameters": {
            "limit": {"type": "integer", "default": 100},
        }
    },
    "firebase_get_user": {
        "description": "Busca um usuário pelo UID",
        "parameters": {
            "uid": {"type": "string", "required": True},
        }
    },
    "firebase_get_user_by_email": {
        "description": "Busca um usuário pelo email",
        "parameters": {
            "email": {"type": "string", "required": True},
        }
    },
    "firebase_create_user": {
        "description": "Cria um novo usuário no Firebase Auth",
        "parameters": {
            "email": {"type": "string", "required": True},
            "password": {"type": "string", "required": True},
            "display_name": {"type": "string", "optional": True},
        }
    },
    "firebase_delete_user": {
        "description": "Deleta um usuário",
        "parameters": {
            "uid": {"type": "string", "required": True},
        }
    },
    # Storage
    "firebase_list_files": {
        "description": "Lista arquivos no Storage",
        "parameters": {
            "prefix": {"type": "string", "optional": True},
            "max_results": {"type": "integer", "default": 100},
        }
    },
    "firebase_get_file_url": {
        "description": "Gera URL assinada para download de arquivo",
        "parameters": {
            "file_path": {"type": "string", "required": True},
            "expiration_minutes": {"type": "integer", "default": 60},
        }
    },
    # Project
    "firebase_get_project_info": {
        "description": "Retorna informações do projeto Firebase",
        "parameters": {}
    },
}


if __name__ == "__main__":
    # Teste básico
    import asyncio
    
    async def test():
        server = FirebaseMCPServer(project_id="ifrs16-app")
        
        # Info do projeto
        info = await server.get_project_info()
        print("Projeto:", json.dumps(info, indent=2))
        
        # Listar coleções
        collections = await server.firestore_list_collections()
        print("Coleções:", collections)
    
    asyncio.run(test())
