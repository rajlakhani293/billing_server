import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from ninja.security import HttpBearer

class AuthBearer(HttpBearer):
    def authenticate(self, request, token: str):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id: str = payload.get("user_id")
            shop_id: str = payload.get("shop_id")
            
            # Both user_id and shop_id are required
            if not user_id or not shop_id:
                return None
            
            User = get_user_model()
            try:
                user_id_int = int(user_id)
                user = User.objects.get(id=user_id_int)
            except (ValueError, User.DoesNotExist):
                return None
            
            # Store shop_id in request for later use
            request.shop_id = int(shop_id)
            
            return user
            
        except jwt.PyJWTError:
            return None
