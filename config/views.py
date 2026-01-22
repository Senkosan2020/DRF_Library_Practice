from django.http import JsonResponse
from django.shortcuts import redirect

def health(request):
    return JsonResponse({"status": "ok"})

def root_redirect(request):
    return redirect("/docs/")
