import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from ninja.security import HttpBearer
from apps.shops.models import Shop

class AuthBearer(HttpBearer):
    def authenticate(self, request, token: str):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            shop_id = payload.get("shop_id")
            
            # Both user_id and shop_id are required
            if not user_id or not shop_id:
                return None
            
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
            except (ValueError, User.DoesNotExist):
                return None
            
            try:
                shop = Shop.objects.get(id=shop_id)
            except (ValueError, Shop.DoesNotExist):
                return None
            
            # Store shop_id in request for later use
            request.shop_id = shop_id
            
            # Return both user and shop data
            return {
                'user': user,
                'shop': shop
            }
            
        except jwt.PyJWTError:
            return None
