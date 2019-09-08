from django.http import HttpResponse


def test_view(request):
    return HttpResponse("<html><body>Test view</body></html>")
