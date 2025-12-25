    # from ninja.security import HttpBearer
    # from rest_framework_simplejwt.authentication import JWTAuthentication
    # from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
    # from django.conf import settings

    # class BearerAuth(HttpBearer):
    #     def authenticate(self, request, token):
    #         if token.startswith("Bearer "):
    #             token = token.replace("Bearer ", "")

    #         jwt_auth = JWTAuthentication()
    #         try:
    #             validated_token = jwt_auth.get_validated_token(token)
    #             user = jwt_auth.get_user(validated_token)
                
    #             if user and user.is_active:
    #                 return user
    #         except Exception as e:
    #             print(f"JWT Auth Error: {str(e)}")
    #             return None




import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from ninja.security import HttpBearer

class AuthBearer(HttpBearer):
    def authenticate(self, request, token: str):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id: str = payload.get("user_id")
            if user_id is None:
                return None
            
            User = get_user_model()
            user = User.objects.get(id=user_id)
            return user
            
        except jwt.PyJWTError:
            return None
        except User.DoesNotExist:
            return None
