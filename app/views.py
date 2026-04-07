import requests
from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse 
from django.contrib import messages 
from app.models import Code
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import nltk
from nltk.tokenize import sent_tokenize
from .models import CodeHistory
import random
from django.core.mail import send_mail
from django.conf import settings
import time


def test_email(request):
    send_mail(
        'Test Email',
        'This is a test message',
        'n.h.v.reddy9866@gmail.com',
        ['n.h.v.reddy9866@gmail.com'],
        fail_silently=False,
    )
    return HttpResponse("Email sent")

def index(request):
    return render(request, 'index.html')


def register(request):

    # STEP 3 : RESEND OTP
    if request.method == "POST" and request.POST.get("resend_otp"):
        data = request.session.get('register_data')
        if not data:
            messages.error(request, "Session expired. Please register again.")
            return render(request, 'register.html')

        email = data['email']
        otp = random.randint(100000, 999999)
        request.session['otp'] = otp
        request.session['otp_time'] = time.time()

        send_mail(
            'OTP Verification',
            f'Your new OTP is {otp}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False
        )
        messages.success(request, "New OTP sent to your email")
        return render(request, 'register.html', {'otp_sent': True})

    # STEP 2 : VERIFY OTP
    if request.method == "POST" and request.POST.get("otp"):
        entered_otp = request.POST.get("otp")
        session_otp = request.session.get("otp")
        otp_time = request.session.get("otp_time")
        current_time = time.time()

        if otp_time and current_time - otp_time > 120:
            messages.error(request, "OTP expired. Please click resend OTP.")
            return render(request, 'register.html', {'otp_sent': True})

        if str(entered_otp) == str(session_otp):
            data = request.session.get('register_data')
            Code.objects.create(
                name=data['name'],
                email=data['email'],
                password=data['password'],
                address=data['address'],
                user_type=data['user_type']
            )
            messages.success(request, "Registration Successful")
            return redirect('login')
        else:
            messages.error(request, "Invalid OTP")
            return render(request, 'register.html', {'otp_sent': True})

    # STEP 1 : REGISTER FORM
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        address = request.POST.get('address')
        user_type = request.POST.get('user_type')

        if password == confirm_password:
            if Code.objects.filter(email=email).exists():
                messages.error(request, 'This Email ID already Exists')
                return render(request, 'register.html')

            otp = random.randint(100000, 999999)
            request.session['otp'] = otp
            request.session['otp_time'] = time.time()
            request.session['register_data'] = {
                'name': name,
                'email': email,
                'password': password,
                'address': address,
                'user_type': user_type
            }

            send_mail(
                'OTP Verification',
                f'Your OTP is {otp}',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False
            )
            messages.success(request, "OTP sent to your email")
            return render(request, 'register.html', {'otp_sent': True})
        else:
            messages.error(request, 'Password mismatch')

    return render(request, 'register.html')


def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = Code.objects.filter(email=email).first()
        if user:
            if user.password == password:
                request.session['email'] = user.email
                return redirect('submit_code')
            else:
                messages.error(request, 'Invalid Password')
                return render(request, 'login.html')
        else:
            messages.error(request, 'This Email ID Does not Exists, Please register')
            return render(request, 'register.html')
    return render(request, 'login.html')


def about(request):
    return render(request, 'about.html')


def profile(request):
    email = request.session.get('email')
    user = Code.objects.get(email=email)
    history = CodeHistory.objects.filter(email=email).order_by('-created_at')
    return render(request, 'profile.html', {
        'user': user,
        'history': history
    })


def logout(request):
    request.session.flush()
    return redirect('index')


# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure Gemini API (new google-genai SDK)
client = genai.Client(api_key=GOOGLE_API_KEY)

# Ensure NLTK sentence tokenizer is downloaded
nltk.download('punkt')

MODEL = 'gemini-2.5-flash'


def submit_code(request):
    if request.method == "POST":
        code = request.POST.get('code')
        language = request.POST.get('language')

        prompt = f"""
Analyze the following {language} code.

1. Identify the errors.
2. Explain the problem.
3. Provide the corrected code.
4. Give rating out of 5

IMPORTANT:
Return the corrected code with proper indentation and line breaks.

Code:
{code}
"""
        response = client.models.generate_content(model=MODEL, contents=prompt)
        results = response.text.replace("```", "")

        email = request.session.get('email')
        CodeHistory.objects.create(
            email=email,
            action_type="Code Review",
            language=language,
            input_code=code,
            output_result=results
        )

        return render(request, 'home.html', {
            'results': results,
            'code': code
        })

    return render(request, 'home.html')


def generate_code(request):
    if request.method == "POST":
        prompt_text = request.POST.get("code")
        language = request.POST.get("language")

        prompt = f"""
Generate a {language} program for the following request:

{prompt_text}

Provide clean formatted code and at the last explain how to run and how many methods to run this code step by step
important: generate in a proper text dont use '*"
"""
        response = client.models.generate_content(model=MODEL, contents=prompt)
        results = response.text.replace("```", "")

        email = request.session.get('email')
        CodeHistory.objects.create(
            email=email,
            action_type="Generate Code",
            language=language,
            input_code=prompt,
            output_result=results
        )

        return render(request, 'generate_code.html', {
            'results': results,
            'code': prompt_text
        })

    return render(request, 'generate_code.html')


def analyze_code(request):
    if request.method == "POST":
        code = request.POST.get("code")
        language = request.POST.get("language")

        prompt = f"""
Analyze the following {language} code.

Explain:
1. What the code does
2. Logic used
3. Possible improvements

Code:
{code}
"""
        response = client.models.generate_content(model=MODEL, contents=prompt)
        results = response.text.replace("```", "")

        email = request.session.get('email')
        CodeHistory.objects.create(
            email=email,
            action_type="Analyze Code",
            language=language,
            input_code=code,
            output_result=results
        )

        return render(request, 'analyze_code.html', {
            'results': results,
            'code': code
        })

    return render(request, 'analyze_code.html')


def download_result(request, id):
    obj = CodeHistory.objects.get(id=id)
    response = HttpResponse(obj.output_result, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="result_{id}.txt"'
    return response