import os, csv, sys
from django.http import JsonResponse
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from .services.blocked_list import BlockedListService
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .serializers import *
from django.db import transaction


class MobileNumberViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = MobileNumberSerializer

    def get_queryset(self):
        page_size = self.request.query_params.get('page_size', 50)
        mobile_number = self.request.query_params.get('mobile_number', None)
        try:
            page_size = int(page_size)
        except ValueError:
            page_size = 50

        queryset = MobileNumber.objects.all()
        self.pagination_class.page_size = page_size if page_size else len(queryset)
        if mobile_number:
            queryset = queryset.filter(mobile_number__icontains=mobile_number)
        return queryset

    def create(self, request, *args, **kwargs):
        request.data['creator'] = request.user.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        mobile_number = self.request.data.get('mobile_number', None)
        if not mobile_number:
            raise ValidationError('Mobile number is required.')

        if MobileNumber.objects.filter(mobile_number=mobile_number).exists():
            raise ValidationError('The mobile number already exists.')
        serializer.save()


class AdvertiserViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = AdvertiserSerializer

    def get_queryset(self):
        contact_number = self.request.query_params.get('contact_number', None)
        queryset = Advertiser.objects.all().order_by('contact_number')
        page_size = self.request.query_params.get('page_size', None)
        try:
            page_size = int(page_size)
        except ValueError:
            page_size = 50
        self.pagination_class.page_size = page_size
        if contact_number:
            queryset = queryset.filter(contact_number__icontains=contact_number)
        return queryset

    def create(self, request, *args, **kwargs):
        request.data['creator'] = request.user.id
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        request.data['creator'] = request.user.id
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path='blocked-numbers')
    def blocked_numbers(self, request, pk=None):
        try:
            advertiser = self.get_object()
            blocked_list_service = BlockedListService()

            try:
                page_size = int(self.request.query_params.get('page_size', 10))
                page = int(self.request.query_params.get('page', 1))
            except ValueError:
                return JsonResponse({'error': 'Invalid page_size or page value'}, status=status.HTTP_400_BAD_REQUEST)

            if page_size <= 0 or page <= 0:
                return JsonResponse({'error': 'page_size and page must be positive integers'},
                                    status=status.HTTP_400_BAD_REQUEST)

            blocked_type = self.request.query_params.get('blocked_type', 'both')
            mobile_number = self.request.query_params.get('mobile_number', None)
            blocked_list_response = blocked_list_service.get_blocked_list(advertiser)

            if blocked_list_response.get('err'):
                return JsonResponse({'results': f"IBS Error: {blocked_list_response.get('err')}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            def paginate_list(data_list):
                start = (page - 1) * page_size
                end = start + page_size
                return data_list[start:end]

            blocked_in = blocked_list_response.get('blocked_in', [])
            blocked_out = blocked_list_response.get('blocked_out', [])

            result = {}

            if blocked_type in ['both', 'in']:
                result['blocked_in_count'] = len(blocked_in)
                result['blocked_in'] = paginate_list(blocked_in)
            if blocked_type in ['both', 'out']:
                result['blocked_out_count'] = len(blocked_out)
                result['blocked_out'] = paginate_list(blocked_out)

            if mobile_number:
                result['blocked_in'] = [num for num in result['blocked_in'] if mobile_number in num]
                result['blocked_out'] = [num for num in result['blocked_out'] if mobile_number in num]

            return JsonResponse({'results': result}, status=status.HTTP_200_OK)
        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            return JsonResponse({'row': str(ex) + '////' + str(exc_tb.tb_lineno),
                                 'status': status.HTTP_500_INTERNAL_SERVER_ERROR})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        contact_number = self.request.data.get('contact_number')
        if not contact_number:
            raise ValidationError('Contact number is required.')

        if Advertiser.objects.filter(contact_number=contact_number).exists():
            raise ValidationError('An advertiser with this contact number already exists.')
        blocked_list_service = BlockedListService()
        advertiser_data = blocked_list_service.get_advertiser_chakavak_info(contact_number)
        if advertiser_data['error']:
            raise ValidationError(advertiser_data['error'])

        chakavak_result = advertiser_data.get('result', {})
        if not chakavak_result:
            raise ValidationError('No Chakavak ID found for the provided contact number.')
        chakavak_id = next(iter(chakavak_result.keys()))
        serializer.save(chakavak_id=chakavak_id)


class BlockedListViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated,)

    ALLOWED_FILE_TYPES = ['.csv']
    ALLOWED_CONTENT_TYPES = ['text/csv']
    BLOCKED_IN_STATUS = 'blocked_in'
    BLOCKED_OUT_STATUS = 'blocked_out'
    CHUNK_SIZE = 150

    def create(self, request, *args, **kwargs):
        blocked_in_file = request.FILES.get('blocked_in_file')
        blocked_out_file = request.FILES.get('blocked_out_file')
        blocked_in_number = request.data.get('blocked_in_number')
        blocked_out_number = request.data.get('blocked_out_number')
        action = request.data.get('action')

        advertiser_ids = request.data.get('advertisers_id', '')
        if not advertiser_ids:
            raise ValidationError("Missing 'advertisers_id' field.")

        advertiser_ids = [aid.strip() for aid in advertiser_ids.split(',') if aid.strip().isdigit()]
        advertisers = Advertiser.objects.filter(id__in=advertiser_ids)
        if not advertisers:
            raise ValidationError("No valid advertisers found.")

        blocked_in_numbers = self._extract_numbers_from_file_or_input(blocked_in_file)
        blocked_out_numbers = self._extract_numbers_from_file_or_input(blocked_out_file)

        if blocked_in_number:
            blocked_in_numbers.extend(num.strip() for num in blocked_in_number.split(','))
        if blocked_out_number:
            blocked_out_numbers.extend(num.strip() for num in blocked_out_number.split(','))

        blocked_list_service = BlockedListService()
        blocked_list_records = []

        for advertiser in advertisers:
            success, err = blocked_list_service.set_blocked_list(
                advertiser,
                blocked_in_numbers,
                blocked_out_numbers,
                action=action
            )

            if not success:
                raise ValidationError(f"Failed to sync blocked list for advertiser {advertiser.contact_number}. Error: {err}")

            blocked_list_records.extend(self._create_blocked_list_entries(
                advertiser_id=advertiser.id,
                numbers=blocked_in_numbers,
                creator=request.user,
                status=self.BLOCKED_IN_STATUS
            ))

            blocked_list_records.extend(self._create_blocked_list_entries(
                advertiser_id=advertiser.id,
                numbers=blocked_out_numbers,
                creator=request.user,
                status=self.BLOCKED_OUT_STATUS
            ))

        with transaction.atomic():
            BlockedList.objects.bulk_create(blocked_list_records)

        return Response({"results": "Blocked list updated successfully."}, status=status.HTTP_200_OK)

    def _extract_numbers_from_file_or_input(self, file):
        if not file:
            return []

        file_ext = os.path.splitext(file.name)[-1].lower()
        if file_ext not in self.ALLOWED_FILE_TYPES:
            raise ValidationError(f"Invalid file type '{file_ext}'. Only CSV files are allowed.")

        if file.content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValidationError(f"Invalid content type '{file.content_type}'.")

        decoded_lines = file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_lines)

        numbers = []
        for row in reader:
            cleaned = [item.strip() for item in row if item.strip()]
            numbers.extend(cleaned)

        return numbers

    def _create_blocked_list_entries(self, advertiser_id, numbers, creator, status, ibs_err=''):
        return [
            BlockedList(
                advertiser_id=advertiser_id,
                mobile_number=number,
                creator=creator,
                status=status,
                ibs_err=ibs_err
            )
            for number in numbers
        ]





