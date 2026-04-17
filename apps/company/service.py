from django.db import transaction
from apps.core.helpers import ResponseBuilder, generateSequentialCode
from .models import Company, Branch
from apps.core.tenantQuery import TenantQuery
from apps.accounts.auth_service import CompanyService as AuthCompanyService
import re
import random
import string


class CompanyService:
    @staticmethod
    def update(data, request, company_id):
        try:
            with transaction.atomic():
                company = TenantQuery.updateRecordById(Company, company_id, data, request)
                if not company:
                    raise Exception("Company not found")
                return ResponseBuilder.success(data=company, message="Company updated successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getById(company_id, request):
        try:
            company = TenantQuery.findOneRecord(Company, company_id, {}, request)
            if not company or company.get('status') == 2:
                raise Exception("Company not found")
            return ResponseBuilder.success(data=company, message="Company retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)


class BranchService:
    @staticmethod
    def create(data, request):
        try:
            with transaction.atomic():
                branch = TenantQuery.createRecord(Branch, data, request)
                return ResponseBuilder.success(
                    data=branch,
                    message="Branch created successfully"
                )
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def update(data, request, branch_id):
        try:
            with transaction.atomic():
                branch = TenantQuery.updateRecordById(Branch, branch_id, data, request)
                if not branch:
                    raise Exception("Branch not found")
                return ResponseBuilder.success(data=branch, message="Branch updated successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getById(branch_id, request):
        try:
            branch = TenantQuery.findOneRecord(Branch, branch_id, {}, request)
            if not branch or branch.get('status') == 2:
                raise Exception("Branch not found")
            return ResponseBuilder.success(data=branch, message="Branch retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def dropdownList(request):
        try:
            branches = TenantQuery.findAllRecords(
                Branch,
                {},
                {'attributes': ['id', 'branch_name', 'contact_person_name', 'phone_number'], 'order': ['branch_name']},
                request
            )
            return ResponseBuilder.success(data=branches, message="Dropdown list retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def getAll(data, request):
        try:
            fieldConfig = [["branch_name", True, True], ["contact_person_name", True, True]]
            options = {'attributes': ['id', 'branch_name', 'contact_person_name', 'phone_number', 'email', 'address', 'status', 'company__company_name']}
            result = TenantQuery.fetchPaginatedData(Branch, data, fieldConfig, options, request)
            
            # Rename company__company_name to company for cleaner response
            for branch in result.get('items', []):
                branch['company'] = branch.pop('company__company_name', None)
            
            return ResponseBuilder.success(data=result, message="Branches retrieved successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)

    @staticmethod
    def delete(data, request):
        try:
            with transaction.atomic():
                count = TenantQuery.softDeleteById(Branch, data.get('ids'), request)
                if count == 0:
                    raise Exception("Already deleted")
                return ResponseBuilder.success(message="Branches deleted successfully")
        except Exception as e:
            return ResponseBuilder.error(message=str(e), status_code=400)
