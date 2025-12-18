"""
MCP Server para Stripe - Conexão direta com API Stripe
Permite gerenciar clientes, assinaturas, pagamentos e webhooks
"""

import os
import json
import stripe
from datetime import datetime
from typing import Optional, List, Dict, Any

# Configuração do Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
stripe.api_key = STRIPE_SECRET_KEY


class StripeMCPServer:
    """
    Servidor MCP para integração direta com Stripe.
    Fornece ferramentas para gerenciar:
    - Clientes
    - Assinaturas
    - Pagamentos
    - Produtos e Preços
    - Webhooks
    """
    
    def __init__(self, api_key: str = None):
        if api_key:
            stripe.api_key = api_key
        elif not stripe.api_key:
            raise ValueError("STRIPE_SECRET_KEY não configurada")
    
    # =========================================================================
    # CLIENTES
    # =========================================================================
    
    async def list_customers(
        self,
        limit: int = 10,
        email: str = None,
        starting_after: str = None
    ) -> List[Dict]:
        """Lista clientes do Stripe"""
        params = {"limit": limit}
        if email:
            params["email"] = email
        if starting_after:
            params["starting_after"] = starting_after
        
        customers = stripe.Customer.list(**params)
        return [self._format_customer(c) for c in customers.data]
    
    async def get_customer(self, customer_id: str) -> Dict:
        """Busca um cliente específico"""
        customer = stripe.Customer.retrieve(customer_id)
        return self._format_customer(customer)
    
    async def create_customer(
        self,
        email: str,
        name: str = None,
        metadata: Dict = None
    ) -> Dict:
        """Cria um novo cliente"""
        params = {"email": email}
        if name:
            params["name"] = name
        if metadata:
            params["metadata"] = metadata
        
        customer = stripe.Customer.create(**params)
        return self._format_customer(customer)
    
    async def update_customer(
        self,
        customer_id: str,
        email: str = None,
        name: str = None,
        metadata: Dict = None
    ) -> Dict:
        """Atualiza um cliente"""
        params = {}
        if email:
            params["email"] = email
        if name:
            params["name"] = name
        if metadata:
            params["metadata"] = metadata
        
        customer = stripe.Customer.modify(customer_id, **params)
        return self._format_customer(customer)
    
    async def delete_customer(self, customer_id: str) -> Dict:
        """Deleta um cliente"""
        result = stripe.Customer.delete(customer_id)
        return {"deleted": result.deleted, "id": result.id}
    
    # =========================================================================
    # ASSINATURAS
    # =========================================================================
    
    async def list_subscriptions(
        self,
        customer_id: str = None,
        status: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """Lista assinaturas"""
        params = {"limit": limit}
        if customer_id:
            params["customer"] = customer_id
        if status:
            params["status"] = status
        
        subscriptions = stripe.Subscription.list(**params)
        return [self._format_subscription(s) for s in subscriptions.data]
    
    async def get_subscription(self, subscription_id: str) -> Dict:
        """Busca uma assinatura específica"""
        subscription = stripe.Subscription.retrieve(subscription_id)
        return self._format_subscription(subscription)
    
    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: int = None
    ) -> Dict:
        """Cria uma nova assinatura"""
        params = {
            "customer": customer_id,
            "items": [{"price": price_id}],
        }
        if trial_days:
            params["trial_period_days"] = trial_days
        
        subscription = stripe.Subscription.create(**params)
        return self._format_subscription(subscription)
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        immediately: bool = False
    ) -> Dict:
        """Cancela uma assinatura"""
        if immediately:
            subscription = stripe.Subscription.delete(subscription_id)
        else:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
        return self._format_subscription(subscription)
    
    async def update_subscription(
        self,
        subscription_id: str,
        price_id: str = None,
        metadata: Dict = None
    ) -> Dict:
        """Atualiza uma assinatura"""
        params = {}
        if price_id:
            subscription = stripe.Subscription.retrieve(subscription_id)
            params["items"] = [{
                "id": subscription["items"]["data"][0].id,
                "price": price_id,
            }]
        if metadata:
            params["metadata"] = metadata
        
        subscription = stripe.Subscription.modify(subscription_id, **params)
        return self._format_subscription(subscription)
    
    # =========================================================================
    # PAGAMENTOS E FATURAS
    # =========================================================================
    
    async def list_invoices(
        self,
        customer_id: str = None,
        status: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """Lista faturas"""
        params = {"limit": limit}
        if customer_id:
            params["customer"] = customer_id
        if status:
            params["status"] = status
        
        invoices = stripe.Invoice.list(**params)
        return [self._format_invoice(i) for i in invoices.data]
    
    async def get_invoice(self, invoice_id: str) -> Dict:
        """Busca uma fatura específica"""
        invoice = stripe.Invoice.retrieve(invoice_id)
        return self._format_invoice(invoice)
    
    async def list_payment_intents(
        self,
        customer_id: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """Lista payment intents"""
        params = {"limit": limit}
        if customer_id:
            params["customer"] = customer_id
        
        intents = stripe.PaymentIntent.list(**params)
        return [self._format_payment_intent(p) for p in intents.data]
    
    async def create_payment_intent(
        self,
        amount: int,
        currency: str = "brl",
        customer_id: str = None,
        metadata: Dict = None
    ) -> Dict:
        """Cria um payment intent"""
        params = {
            "amount": amount,
            "currency": currency,
        }
        if customer_id:
            params["customer"] = customer_id
        if metadata:
            params["metadata"] = metadata
        
        intent = stripe.PaymentIntent.create(**params)
        return self._format_payment_intent(intent)
    
    # =========================================================================
    # PRODUTOS E PREÇOS
    # =========================================================================
    
    async def list_products(self, active: bool = True, limit: int = 10) -> List[Dict]:
        """Lista produtos"""
        products = stripe.Product.list(active=active, limit=limit)
        return [self._format_product(p) for p in products.data]
    
    async def get_product(self, product_id: str) -> Dict:
        """Busca um produto específico"""
        product = stripe.Product.retrieve(product_id)
        return self._format_product(product)
    
    async def list_prices(
        self,
        product_id: str = None,
        active: bool = True,
        limit: int = 10
    ) -> List[Dict]:
        """Lista preços"""
        params = {"active": active, "limit": limit}
        if product_id:
            params["product"] = product_id
        
        prices = stripe.Price.list(**params)
        return [self._format_price(p) for p in prices.data]
    
    async def get_price(self, price_id: str) -> Dict:
        """Busca um preço específico"""
        price = stripe.Price.retrieve(price_id)
        return self._format_price(price)
    
    # =========================================================================
    # CHECKOUT SESSIONS
    # =========================================================================
    
    async def create_checkout_session(
        self,
        price_id: str,
        success_url: str,
        cancel_url: str,
        customer_id: str = None,
        customer_email: str = None,
        mode: str = "subscription",
        metadata: Dict = None
    ) -> Dict:
        """Cria uma sessão de checkout"""
        params = {
            "line_items": [{"price": price_id, "quantity": 1}],
            "mode": mode,
            "success_url": success_url,
            "cancel_url": cancel_url,
        }
        if customer_id:
            params["customer"] = customer_id
        elif customer_email:
            params["customer_email"] = customer_email
        if metadata:
            params["metadata"] = metadata
        
        session = stripe.checkout.Session.create(**params)
        return {
            "id": session.id,
            "url": session.url,
            "status": session.status,
            "customer": session.customer,
            "subscription": session.subscription,
        }
    
    async def get_checkout_session(self, session_id: str) -> Dict:
        """Busca uma sessão de checkout"""
        session = stripe.checkout.Session.retrieve(session_id)
        return {
            "id": session.id,
            "url": session.url,
            "status": session.status,
            "customer": session.customer,
            "subscription": session.subscription,
            "payment_status": session.payment_status,
            "amount_total": session.amount_total,
        }
    
    # =========================================================================
    # WEBHOOKS
    # =========================================================================
    
    async def list_webhook_endpoints(self, limit: int = 10) -> List[Dict]:
        """Lista webhooks configurados"""
        webhooks = stripe.WebhookEndpoint.list(limit=limit)
        return [{
            "id": w.id,
            "url": w.url,
            "status": w.status,
            "enabled_events": w.enabled_events,
            "created": datetime.fromtimestamp(w.created).isoformat(),
        } for w in webhooks.data]
    
    async def create_webhook_endpoint(
        self,
        url: str,
        events: List[str]
    ) -> Dict:
        """Cria um webhook endpoint"""
        webhook = stripe.WebhookEndpoint.create(
            url=url,
            enabled_events=events,
        )
        return {
            "id": webhook.id,
            "url": webhook.url,
            "secret": webhook.secret,
            "status": webhook.status,
            "enabled_events": webhook.enabled_events,
        }
    
    # =========================================================================
    # BALANCE E RELATÓRIOS
    # =========================================================================
    
    async def get_balance(self) -> Dict:
        """Retorna o saldo da conta"""
        balance = stripe.Balance.retrieve()
        return {
            "available": [{
                "amount": b.amount / 100,
                "currency": b.currency,
            } for b in balance.available],
            "pending": [{
                "amount": b.amount / 100,
                "currency": b.currency,
            } for b in balance.pending],
        }
    
    async def list_balance_transactions(
        self,
        limit: int = 10,
        type_filter: str = None
    ) -> List[Dict]:
        """Lista transações do saldo"""
        params = {"limit": limit}
        if type_filter:
            params["type"] = type_filter
        
        transactions = stripe.BalanceTransaction.list(**params)
        return [{
            "id": t.id,
            "amount": t.amount / 100,
            "currency": t.currency,
            "type": t.type,
            "status": t.status,
            "created": datetime.fromtimestamp(t.created).isoformat(),
            "description": t.description,
        } for t in transactions.data]
    
    # =========================================================================
    # FORMATADORES
    # =========================================================================
    
    def _format_customer(self, customer) -> Dict:
        return {
            "id": customer.id,
            "email": customer.email,
            "name": customer.name,
            "created": datetime.fromtimestamp(customer.created).isoformat(),
            "metadata": dict(customer.metadata) if customer.metadata else {},
            "default_source": customer.default_source,
            "currency": customer.currency,
        }
    
    def _format_subscription(self, subscription) -> Dict:
        return {
            "id": subscription.id,
            "customer": subscription.customer,
            "status": subscription.status,
            "current_period_start": datetime.fromtimestamp(
                subscription.current_period_start
            ).isoformat(),
            "current_period_end": datetime.fromtimestamp(
                subscription.current_period_end
            ).isoformat(),
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "items": [{
                "id": item.id,
                "price_id": item.price.id,
                "product_id": item.price.product,
            } for item in subscription["items"]["data"]],
            "metadata": dict(subscription.metadata) if subscription.metadata else {},
        }
    
    def _format_invoice(self, invoice) -> Dict:
        return {
            "id": invoice.id,
            "customer": invoice.customer,
            "status": invoice.status,
            "amount_due": invoice.amount_due / 100,
            "amount_paid": invoice.amount_paid / 100,
            "currency": invoice.currency,
            "created": datetime.fromtimestamp(invoice.created).isoformat(),
            "invoice_pdf": invoice.invoice_pdf,
            "hosted_invoice_url": invoice.hosted_invoice_url,
        }
    
    def _format_payment_intent(self, intent) -> Dict:
        return {
            "id": intent.id,
            "amount": intent.amount / 100,
            "currency": intent.currency,
            "status": intent.status,
            "customer": intent.customer,
            "created": datetime.fromtimestamp(intent.created).isoformat(),
            "metadata": dict(intent.metadata) if intent.metadata else {},
        }
    
    def _format_product(self, product) -> Dict:
        return {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "active": product.active,
            "created": datetime.fromtimestamp(product.created).isoformat(),
            "metadata": dict(product.metadata) if product.metadata else {},
        }
    
    def _format_price(self, price) -> Dict:
        return {
            "id": price.id,
            "product": price.product,
            "active": price.active,
            "currency": price.currency,
            "unit_amount": price.unit_amount / 100 if price.unit_amount else None,
            "recurring": {
                "interval": price.recurring.interval,
                "interval_count": price.recurring.interval_count,
            } if price.recurring else None,
            "type": price.type,
        }


# =========================================================================
# MCP TOOLS DEFINITION
# =========================================================================

MCP_TOOLS = {
    "stripe_list_customers": {
        "description": "Lista clientes do Stripe",
        "parameters": {
            "limit": {"type": "integer", "default": 10},
            "email": {"type": "string", "optional": True},
        }
    },
    "stripe_get_customer": {
        "description": "Busca um cliente específico pelo ID",
        "parameters": {
            "customer_id": {"type": "string", "required": True},
        }
    },
    "stripe_create_customer": {
        "description": "Cria um novo cliente no Stripe",
        "parameters": {
            "email": {"type": "string", "required": True},
            "name": {"type": "string", "optional": True},
        }
    },
    "stripe_list_subscriptions": {
        "description": "Lista assinaturas do Stripe",
        "parameters": {
            "customer_id": {"type": "string", "optional": True},
            "status": {"type": "string", "optional": True},
            "limit": {"type": "integer", "default": 10},
        }
    },
    "stripe_cancel_subscription": {
        "description": "Cancela uma assinatura",
        "parameters": {
            "subscription_id": {"type": "string", "required": True},
            "immediately": {"type": "boolean", "default": False},
        }
    },
    "stripe_list_invoices": {
        "description": "Lista faturas do Stripe",
        "parameters": {
            "customer_id": {"type": "string", "optional": True},
            "limit": {"type": "integer", "default": 10},
        }
    },
    "stripe_list_products": {
        "description": "Lista produtos do Stripe",
        "parameters": {
            "active": {"type": "boolean", "default": True},
            "limit": {"type": "integer", "default": 10},
        }
    },
    "stripe_list_prices": {
        "description": "Lista preços do Stripe",
        "parameters": {
            "product_id": {"type": "string", "optional": True},
            "limit": {"type": "integer", "default": 10},
        }
    },
    "stripe_get_balance": {
        "description": "Retorna o saldo da conta Stripe",
        "parameters": {}
    },
    "stripe_create_checkout_session": {
        "description": "Cria uma sessão de checkout",
        "parameters": {
            "price_id": {"type": "string", "required": True},
            "success_url": {"type": "string", "required": True},
            "cancel_url": {"type": "string", "required": True},
            "customer_email": {"type": "string", "optional": True},
        }
    },
}


if __name__ == "__main__":
    # Teste básico
    import asyncio
    
    async def test():
        server = StripeMCPServer()
        
        # Listar produtos
        products = await server.list_products()
        print("Produtos:", json.dumps(products, indent=2, default=str))
        
        # Listar preços
        prices = await server.list_prices()
        print("Preços:", json.dumps(prices, indent=2, default=str))
        
        # Saldo
        balance = await server.get_balance()
        print("Saldo:", json.dumps(balance, indent=2, default=str))
    
    asyncio.run(test())
