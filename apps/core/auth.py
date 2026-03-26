import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from ninja.security import HttpBearer
from apps.company.models import Company, Branch

class AuthBearer(HttpBearer):
    def authenticate(self, request, token: str):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            company_id = payload.get("company_id")
            branch_id = payload.get("branch_id")
            
            # user_id, company_id, and branch_id are required
            if not user_id or not company_id or not branch_id:
                return None
            
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
            except (ValueError, User.DoesNotExist):
                return None
            
            try:
                company = Company.objects.get(id=company_id)
            except (ValueError, Company.DoesNotExist):
                return None

            try:
                branch = Branch.objects.get(id=branch_id)
            except (ValueError, Branch.DoesNotExist):
                return None
            
            # Store company_id and branch_id in request for later use
            request.company_id = company_id
            request.branch_id = branch_id
            
            # Return both user, company, and branch data
            return {
                'user': user,
                'company': company,
                'branch': branch
            }
            
        except jwt.PyJWTError:
            return None
