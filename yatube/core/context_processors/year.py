from django.utils import timezone


# прочитал документацию, но не понял сути aware и naive
def year(request):
    """Добавляет переменную с текущим годом."""
    return {
        'year': timezone.now().year
    }
