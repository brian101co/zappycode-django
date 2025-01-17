import datetime
import json
import requests
import environ
from allauth.account.forms import SignupForm
from django.contrib.auth import authenticate
from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from rest_framework.parsers import JSONParser
from courses.models import Course
from .permissions import IsMember
from .serializers import CourseSerializer, CourseWithSectionsAndLecturesSerializer
from rest_framework import generics, permissions
from sitewide.models import ZappyUser

env = environ.Env()
environ.Env.read_env()


@csrf_exempt
def iap_signup(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        receipt = data['receipt']
        if ZappyUser.objects.filter(apple_receipt=receipt).exists():
            return JsonResponse({'error': 'This In App Purchase has already been used. Please contact nick@ZappyCode.com', 'kick_out': True},
                                status=400)
        verify_url = 'https://buy.itunes.apple.com/verifyReceipt'
        if 'debug' in data:
            if data['debug']:
                verify_url = 'https://sandbox.itunes.apple.com/verifyReceipt'
        receipt_json = json.dumps(
            {"receipt-data": receipt, 'password': env.str('APP_SHARED_SECRET', default='')})
        response = requests.request(
            method='POST',
            url=verify_url,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data=receipt_json
        )

        res_json = response.json()
        try:
            request.POST._mutable = True
            request.POST['email'] = data['email']
            request.POST['password1'] = data['password']
            form = SignupForm(request.POST)
            form.is_valid()
            user = form.save(request)
            user.apple_product_id = res_json['latest_receipt_info'][-1]['product_id']
            user.apple_expires_date = datetime.datetime.fromtimestamp(
                int(res_json['latest_receipt_info'][-1]['expires_date_ms']) / 1000)
            user.active_membership = True
            user.apple_receipt = receipt
            user.save()
            token = Token.objects.create(user=user)
            return JsonResponse({'token': str(token)}, status=201)
        except IntegrityError:
            return JsonResponse({'error': 'That email has already been taken'},
                                status=400)
        except KeyError:
            return JsonResponse({'error': 'We had problems verifying the receipt. Please contact nick@ZappyCode.com', 'kick_out': True},
                                status=400)
        except Exception as e:
            print(e)
            return JsonResponse({'error': 'Something went wrong. Please contact nick@ZappyCode.com', 'kick_out': True},
                                status=400)


@csrf_exempt
def login(request):
    data = JSONParser().parse(request)
    user = authenticate(request, email=data['email'], password=data['password'])
    if user is None:
        return JsonResponse({'error': 'Could not login. Please check username and password'}, status=400)
    else:
        try:
            token = Token.objects.get(user=user)
        except:
            token = Token.objects.create(user=user)
        return JsonResponse({'token': str(token)}, status=200)


class CourseList(generics.ListAPIView):
    queryset = Course.objects.all().filter(published=True).order_by('-release_date')
    serializer_class = CourseSerializer


class CourseWithSectionsAndLectures(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, IsMember]
    queryset = Course.objects.all()
    serializer_class = CourseWithSectionsAndLecturesSerializer
